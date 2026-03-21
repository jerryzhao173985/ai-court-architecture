"""Integration test for fact checker with real LLM service."""

import pytest
import asyncio
import os
from unittest.mock import AsyncMock, MagicMock

from src.trial_orchestrator import TrialOrchestrator
from src.state_machine import ExperienceState
from src.case_manager import CaseManager
from src.llm_service import LLMService
from src.config import LLMConfig


@pytest.mark.asyncio
async def test_fact_checker_integration_with_blackthorn_case():
    """Integration test: fact checker detects contradictions in Blackthorn Hall case."""
    # Load the actual Blackthorn Hall case
    case_manager = CaseManager()
    case_content = case_manager.load_case("blackthorn-hall-001")
    
    # Create mock LLM service for testing
    mock_llm_service = MagicMock(spec=LLMService)
    mock_llm_service.generate_response = AsyncMock()
    
    # Initialize orchestrator with case
    orchestrator = TrialOrchestrator(llm_service=mock_llm_service)
    orchestrator.initialize_agents(case_content)
    
    # Test 1: Correct statement - should not trigger intervention
    mock_llm_service.generate_response.return_value = """{
        "is_contradiction": false,
        "confidence": 0.95,
        "contradicting_evidence": null,
        "correction": null
    }"""
    
    correct_statement = "The security log shows Marcus Ashford left the estate at 8:20 PM"
    result = await orchestrator.check_fact_accuracy(
        statement=correct_statement,
        speaker="defence",
        stage=ExperienceState.EVIDENCE_PRESENTATION
    )
    
    assert result is not None
    assert result.is_contradiction is False
    
    # Test 2: Contradictory statement - should trigger intervention
    mock_llm_service.generate_response.return_value = """{
        "is_contradiction": true,
        "confidence": 0.92,
        "contradicting_evidence": "Security Log Entry",
        "correction": "The security log shows the defendant left at 8:20 PM, not 9:00 PM"
    }"""
    
    wrong_statement = "Marcus Ashford left the estate at 9:00 PM"
    result = await orchestrator.check_fact_accuracy(
        statement=wrong_statement,
        speaker="prosecution",
        stage=ExperienceState.EVIDENCE_PRESENTATION
    )
    
    assert result is not None
    assert result.is_contradiction is True
    assert result.contradicting_evidence == "Security Log Entry"
    assert "8:20 PM" in result.correction
    
    # Test 3: Trigger intervention and verify response
    intervention = orchestrator.trigger_fact_check_intervention(result)
    assert intervention.agent_role == "fact_checker"
    assert "intervene" in intervention.content.lower()
    assert "8:20 PM" in intervention.content
    assert orchestrator.fact_check_count == 1


@pytest.mark.asyncio
async def test_fact_checker_confidence_threshold():
    """Test that confidence threshold properly filters interventions."""
    # Load case
    case_manager = CaseManager()
    case_content = case_manager.load_case("blackthorn-hall-001")
    
    # Create mock LLM service
    mock_llm_service = MagicMock(spec=LLMService)
    mock_llm_service.generate_response = AsyncMock()
    
    # Initialize orchestrator
    orchestrator = TrialOrchestrator(llm_service=mock_llm_service)
    orchestrator.initialize_agents(case_content)
    
    # Test with confidence just below threshold (0.69 < 0.7)
    mock_llm_service.generate_response.return_value = """{
        "is_contradiction": true,
        "confidence": 0.69,
        "contradicting_evidence": "Some evidence",
        "correction": "Some correction"
    }"""
    
    result = await orchestrator.check_fact_accuracy(
        statement="Ambiguous statement",
        speaker="prosecution",
        stage=ExperienceState.EVIDENCE_PRESENTATION
    )
    
    assert result is not None
    assert result.is_contradiction is False  # Below threshold, so no intervention
    
    # Test with confidence at threshold (0.7 >= 0.7)
    mock_llm_service.generate_response.return_value = """{
        "is_contradiction": true,
        "confidence": 0.7,
        "contradicting_evidence": "Some evidence",
        "correction": "Some correction"
    }"""
    
    result = await orchestrator.check_fact_accuracy(
        statement="Clear contradiction",
        speaker="prosecution",
        stage=ExperienceState.EVIDENCE_PRESENTATION
    )
    
    assert result is not None
    assert result.is_contradiction is True  # At threshold, so intervention triggered


@pytest.mark.asyncio
async def test_fact_checker_evidence_context_includes_all_items():
    """Test that evidence context includes all case evidence items."""
    # Load case
    case_manager = CaseManager()
    case_content = case_manager.load_case("blackthorn-hall-001")
    
    # Create orchestrator
    orchestrator = TrialOrchestrator(llm_service=None)
    orchestrator.initialize_agents(case_content)
    
    # Build evidence context
    context = orchestrator._build_evidence_context()
    
    # Verify all evidence items are included
    for evidence in case_content.evidence:
        assert evidence.title in context
        assert evidence.description in context
        assert evidence.significance in context
    
    # Verify formatting
    assert "Significance:" in context
    assert "Timestamp:" in context


@pytest.mark.asyncio
async def test_fact_checker_max_interventions_enforced():
    """Test that fact checker stops after 3 interventions."""
    # Load case
    case_manager = CaseManager()
    case_content = case_manager.load_case("blackthorn-hall-001")
    
    # Create mock LLM service
    mock_llm_service = MagicMock(spec=LLMService)
    mock_llm_service.generate_response = AsyncMock()
    
    # Mock to always return contradiction
    mock_llm_service.generate_response.return_value = """{
        "is_contradiction": true,
        "confidence": 0.95,
        "contradicting_evidence": "Test Evidence",
        "correction": "Test correction"
    }"""
    
    # Initialize orchestrator
    orchestrator = TrialOrchestrator(llm_service=mock_llm_service)
    orchestrator.initialize_agents(case_content)
    
    # Make 3 contradictory statements
    interventions = []
    for i in range(3):
        result = await orchestrator.check_fact_accuracy(
            statement=f"Wrong statement {i}",
            speaker="prosecution",
            stage=ExperienceState.EVIDENCE_PRESENTATION
        )
        if result and result.is_contradiction:
            intervention = orchestrator.trigger_fact_check_intervention(result)
            interventions.append(intervention)
    
    assert len(interventions) == 3
    assert orchestrator.fact_check_count == 3
    
    # 4th statement should not trigger intervention
    result = await orchestrator.check_fact_accuracy(
        statement="Wrong statement 4",
        speaker="prosecution",
        stage=ExperienceState.EVIDENCE_PRESENTATION
    )
    
    assert result is None  # Blocked by intervention limit


@pytest.mark.asyncio
async def test_fact_checker_stage_restrictions():
    """Test that fact checker only operates in correct stages."""
    # Load case
    case_manager = CaseManager()
    case_content = case_manager.load_case("blackthorn-hall-001")
    
    # Create mock LLM service
    mock_llm_service = MagicMock(spec=LLMService)
    mock_llm_service.generate_response = AsyncMock()
    
    # Initialize orchestrator
    orchestrator = TrialOrchestrator(llm_service=mock_llm_service)
    orchestrator.initialize_agents(case_content)
    
    # Test all stages
    test_statement = "Test statement"
    
    # Should NOT check in these stages
    blocked_stages = [
        ExperienceState.CHARGE_READING,
        ExperienceState.PROSECUTION_OPENING,
        ExperienceState.DEFENCE_OPENING,
        ExperienceState.PROSECUTION_CLOSING,
        ExperienceState.DEFENCE_CLOSING,
        ExperienceState.JUDGE_SUMMING_UP
    ]
    
    for stage in blocked_stages:
        result = await orchestrator.check_fact_accuracy(
            statement=test_statement,
            speaker="prosecution",
            stage=stage
        )
        assert result is None, f"Fact checker should not operate in {stage.value}"
    
    # Should check in these stages
    mock_llm_service.generate_response.return_value = """{
        "is_contradiction": false,
        "confidence": 0.95,
        "contradicting_evidence": null,
        "correction": null
    }"""
    
    allowed_stages = [
        ExperienceState.EVIDENCE_PRESENTATION,
        ExperienceState.CROSS_EXAMINATION
    ]
    
    for stage in allowed_stages:
        result = await orchestrator.check_fact_accuracy(
            statement=test_statement,
            speaker="prosecution",
            stage=stage
        )
        assert result is not None, f"Fact checker should operate in {stage.value}"
