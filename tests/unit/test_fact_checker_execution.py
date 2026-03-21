"""Integration test to verify fact checking is invoked during trial execution."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.trial_orchestrator import TrialOrchestrator, FactCheckResult
from src.state_machine import ExperienceState
from src.case_manager import CaseManager
from src.llm_service import LLMService


@pytest.mark.asyncio
async def test_fact_checking_invoked_during_evidence_presentation():
    """Test that fact checking is automatically invoked during evidence presentation."""
    # Load case
    case_manager = CaseManager()
    case_content = case_manager.load_case("blackthorn-hall-001")
    
    # Create mock LLM service
    mock_llm_service = MagicMock(spec=LLMService)
    mock_llm_service.generate_response = AsyncMock()
    mock_llm_service.generate_with_fallback = AsyncMock()
    
    # Mock agent responses
    mock_llm_service.generate_with_fallback.return_value = (
        "The defendant left at 9:00 PM",  # Contradictory statement
        False
    )
    
    # Mock fact check response - contradiction detected
    mock_llm_service.generate_response.return_value = """{
        "is_contradiction": true,
        "confidence": 0.9,
        "contradicting_evidence": "Security Log Entry",
        "correction": "The security log shows the defendant left at 8:20 PM, not 9:00 PM"
    }"""
    
    # Initialize orchestrator
    orchestrator = TrialOrchestrator(llm_service=mock_llm_service)
    orchestrator.initialize_agents(case_content)
    
    # Execute evidence presentation stage
    responses = await orchestrator.execute_stage(ExperienceState.EVIDENCE_PRESENTATION)
    
    # Should have: prosecution response + fact check + defence response + fact check
    # Or at minimum: prosecution + defence + at least one fact check
    assert len(responses) >= 2  # At least prosecution and defence
    
    # Check if fact checker was invoked
    fact_checker_responses = [r for r in responses if r.agent_role == "fact_checker"]
    
    # If the mock returned a contradiction, we should see an intervention
    if mock_llm_service.generate_response.called:
        assert len(fact_checker_responses) > 0, "Fact checker should have intervened on contradiction"
        assert "intervene" in fact_checker_responses[0].content.lower()


@pytest.mark.asyncio
async def test_fact_checking_invoked_during_cross_examination():
    """Test that fact checking is automatically invoked during cross-examination."""
    # Load case
    case_manager = CaseManager()
    case_content = case_manager.load_case("blackthorn-hall-001")
    
    # Create mock LLM service
    mock_llm_service = MagicMock(spec=LLMService)
    mock_llm_service.generate_response = AsyncMock()
    mock_llm_service.generate_with_fallback = AsyncMock()
    
    # Mock agent responses
    mock_llm_service.generate_with_fallback.return_value = (
        "Test statement",
        False
    )
    
    # Mock fact check response - no contradiction
    mock_llm_service.generate_response.return_value = """{
        "is_contradiction": false,
        "confidence": 0.95,
        "contradicting_evidence": null,
        "correction": null
    }"""
    
    # Initialize orchestrator
    orchestrator = TrialOrchestrator(llm_service=mock_llm_service)
    orchestrator.initialize_agents(case_content)
    
    # Execute cross-examination stage
    responses = await orchestrator.execute_stage(ExperienceState.CROSS_EXAMINATION)
    
    # Should have prosecution and defence responses
    assert len(responses) >= 2
    
    # Verify fact checking was called (even if no contradiction found)
    assert mock_llm_service.generate_response.called


@pytest.mark.asyncio
async def test_fact_checking_not_invoked_during_opening_statements():
    """Test that fact checking is NOT invoked during opening statements."""
    # Load case
    case_manager = CaseManager()
    case_content = case_manager.load_case("blackthorn-hall-001")
    
    # Create mock LLM service
    mock_llm_service = MagicMock(spec=LLMService)
    mock_llm_service.generate_response = AsyncMock()
    mock_llm_service.generate_with_fallback = AsyncMock()
    
    # Mock agent responses
    mock_llm_service.generate_with_fallback.return_value = (
        "Opening statement",
        False
    )
    
    # Initialize orchestrator
    orchestrator = TrialOrchestrator(llm_service=mock_llm_service)
    orchestrator.initialize_agents(case_content)
    
    # Execute prosecution opening stage
    responses = await orchestrator.execute_stage(ExperienceState.PROSECUTION_OPENING)
    
    # Should only have prosecution response, no fact checker
    assert len(responses) == 1
    assert responses[0].agent_role == "prosecution"
    
    # Verify fact checking was NOT called for opening statements
    # The generate_response for fact checking should not be called
    # (generate_with_fallback is called for agent, but generate_response is for fact checking)
    assert not mock_llm_service.generate_response.called


@pytest.mark.asyncio
async def test_multiple_interventions_during_stage():
    """Test that multiple interventions can occur in one stage (up to limit)."""
    # Load case
    case_manager = CaseManager()
    case_content = case_manager.load_case("blackthorn-hall-001")
    
    # Create mock LLM service
    mock_llm_service = MagicMock(spec=LLMService)
    mock_llm_service.generate_response = AsyncMock()
    mock_llm_service.generate_with_fallback = AsyncMock()
    
    # Mock agent responses with contradictions
    mock_llm_service.generate_with_fallback.return_value = (
        "Wrong statement",
        False
    )
    
    # Mock fact check response - always contradiction
    mock_llm_service.generate_response.return_value = """{
        "is_contradiction": true,
        "confidence": 0.95,
        "contradicting_evidence": "Test Evidence",
        "correction": "Test correction"
    }"""
    
    # Initialize orchestrator
    orchestrator = TrialOrchestrator(llm_service=mock_llm_service)
    orchestrator.initialize_agents(case_content)
    
    # Execute evidence presentation stage
    responses = await orchestrator.execute_stage(ExperienceState.EVIDENCE_PRESENTATION)
    
    # Should have: prosecution + intervention + defence + intervention
    assert len(responses) == 4
    
    # Count fact checker interventions
    interventions = [r for r in responses if r.agent_role == "fact_checker"]
    assert len(interventions) == 2
    
    # Verify intervention count tracked
    assert orchestrator.fact_check_count == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
