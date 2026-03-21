"""Unit tests for fact checker LLM-based contradiction detection."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from src.trial_orchestrator import TrialOrchestrator, FactCheckResult
from src.state_machine import ExperienceState
from src.models import CaseContent, CaseNarrative, CharacterProfile, EvidenceItem, GroundTruth, ReasoningCriteria
from src.llm_service import LLMService


@pytest.fixture
def sample_case():
    """Create a sample case for testing."""
    return CaseContent(
        caseId="test-case-001",
        title="Test Case",
        narrative=CaseNarrative(
            hookScene="A test scene",
            chargeText="Murder",
            victimProfile=CharacterProfile(
                name="John Victim",
                role="Victim",
                background="Test victim",
                relevantFacts=["Found dead at 9:00 PM"]
            ),
            defendantProfile=CharacterProfile(
                name="Jane Defendant",
                role="Defendant",
                background="Test defendant",
                relevantFacts=["Was at the scene"]
            ),
            witnessProfiles=[]
        ),
        evidence=[
            EvidenceItem(
                id="evidence-001",
                type="physical",
                title="Security Log",
                description="Shows defendant left at 8:20 PM",
                timestamp="2024-01-15T20:20:00Z",
                presentedBy="defence",
                significance="Establishes timeline"
            ),
            EvidenceItem(
                id="evidence-002",
                type="testimonial",
                title="Witness Statement",
                description="Housekeeper saw confrontation at 8:00 PM",
                timestamp="2024-01-15T20:00:00Z",
                presentedBy="prosecution",
                significance="Places defendant at scene"
            ),
            EvidenceItem(
                id="evidence-003",
                type="documentary",
                title="Toxicology Report",
                description="Victim died from digoxin poisoning",
                timestamp="2024-01-16T10:00:00Z",
                presentedBy="prosecution",
                significance="Establishes cause of death"
            ),
            EvidenceItem(
                id="evidence-004",
                type="physical",
                title="Medicine Cabinet",
                description="Contains digoxin medication",
                timestamp="2024-01-15T21:00:00Z",
                presentedBy="prosecution",
                significance="Shows access to poison"
            ),
            EvidenceItem(
                id="evidence-005",
                type="testimonial",
                title="Doctor's Statement",
                description="Victim had no prescription for digoxin",
                timestamp="2024-01-16T11:00:00Z",
                presentedBy="prosecution",
                significance="Rules out accidental overdose"
            )
        ],
        timeline=[],
        groundTruth=GroundTruth(
            actualVerdict="not_guilty",
            keyFacts=["Timeline is tight", "No direct evidence"],
            reasoningCriteria=ReasoningCriteria(
                requiredEvidenceReferences=["evidence-001"],
                logicalFallacies=["appeal_to_emotion"],
                coherenceThreshold=0.7
            )
        )
    )


@pytest.fixture
def mock_llm_service():
    """Create a mock LLM service."""
    service = MagicMock(spec=LLMService)
    service.generate_response = AsyncMock()
    return service


@pytest.mark.asyncio
async def test_fact_checker_detects_contradiction_with_high_confidence(sample_case, mock_llm_service):
    """Test that fact checker detects contradictions when LLM returns high confidence."""
    # Setup
    orchestrator = TrialOrchestrator(llm_service=mock_llm_service)
    orchestrator.initialize_agents(sample_case)
    
    # Mock LLM response indicating contradiction with high confidence
    mock_llm_service.generate_response.return_value = """{
        "is_contradiction": true,
        "confidence": 0.9,
        "contradicting_evidence": "Security Log",
        "correction": "The security log shows the defendant left at 8:20 PM, not 9:00 PM"
    }"""
    
    # Test
    statement = "The defendant left the scene at 9:00 PM"
    result = await orchestrator.check_fact_accuracy(
        statement=statement,
        speaker="prosecution",
        stage=ExperienceState.EVIDENCE_PRESENTATION
    )
    
    # Assert
    assert result is not None
    assert result.is_contradiction is True
    assert result.contradicting_evidence == "Security Log"
    assert "8:20 PM" in result.correction


@pytest.mark.asyncio
async def test_fact_checker_ignores_low_confidence_contradiction(sample_case, mock_llm_service):
    """Test that fact checker ignores contradictions below confidence threshold."""
    # Setup
    orchestrator = TrialOrchestrator(llm_service=mock_llm_service)
    orchestrator.initialize_agents(sample_case)
    
    # Mock LLM response indicating contradiction with low confidence
    mock_llm_service.generate_response.return_value = """{
        "is_contradiction": true,
        "confidence": 0.5,
        "contradicting_evidence": "Security Log",
        "correction": "Possible timing discrepancy"
    }"""
    
    # Test
    statement = "The defendant may have left around 8:30 PM"
    result = await orchestrator.check_fact_accuracy(
        statement=statement,
        speaker="prosecution",
        stage=ExperienceState.EVIDENCE_PRESENTATION
    )
    
    # Assert
    assert result is not None
    assert result.is_contradiction is False


@pytest.mark.asyncio
async def test_fact_checker_no_contradiction(sample_case, mock_llm_service):
    """Test that fact checker returns no contradiction for accurate statements."""
    # Setup
    orchestrator = TrialOrchestrator(llm_service=mock_llm_service)
    orchestrator.initialize_agents(sample_case)
    
    # Mock LLM response indicating no contradiction
    mock_llm_service.generate_response.return_value = """{
        "is_contradiction": false,
        "confidence": 0.95,
        "contradicting_evidence": null,
        "correction": null
    }"""
    
    # Test
    statement = "The security log shows the defendant left at 8:20 PM"
    result = await orchestrator.check_fact_accuracy(
        statement=statement,
        speaker="prosecution",
        stage=ExperienceState.EVIDENCE_PRESENTATION
    )
    
    # Assert
    assert result is not None
    assert result.is_contradiction is False


@pytest.mark.asyncio
async def test_fact_checker_respects_stage_restrictions(sample_case, mock_llm_service):
    """Test that fact checker only operates during evidence presentation and cross-examination."""
    # Setup
    orchestrator = TrialOrchestrator(llm_service=mock_llm_service)
    orchestrator.initialize_agents(sample_case)
    
    # Test during opening statement (should not check)
    result = await orchestrator.check_fact_accuracy(
        statement="The defendant is guilty",
        speaker="prosecution",
        stage=ExperienceState.PROSECUTION_OPENING
    )
    assert result is None
    
    # Test during closing statement (should not check)
    result = await orchestrator.check_fact_accuracy(
        statement="The defendant is guilty",
        speaker="prosecution",
        stage=ExperienceState.PROSECUTION_CLOSING
    )
    assert result is None
    
    # Mock LLM for valid stages
    mock_llm_service.generate_response.return_value = """{
        "is_contradiction": false,
        "confidence": 0.95,
        "contradicting_evidence": null,
        "correction": null
    }"""
    
    # Test during evidence presentation (should check)
    result = await orchestrator.check_fact_accuracy(
        statement="The evidence shows...",
        speaker="prosecution",
        stage=ExperienceState.EVIDENCE_PRESENTATION
    )
    assert result is not None
    
    # Test during cross-examination (should check)
    result = await orchestrator.check_fact_accuracy(
        statement="The witness testified...",
        speaker="defence",
        stage=ExperienceState.CROSS_EXAMINATION
    )
    assert result is not None


@pytest.mark.asyncio
async def test_fact_checker_respects_intervention_limit(sample_case, mock_llm_service):
    """Test that fact checker stops after 3 interventions."""
    # Setup
    orchestrator = TrialOrchestrator(llm_service=mock_llm_service)
    orchestrator.initialize_agents(sample_case)
    
    # Mock LLM to always return contradiction
    mock_llm_service.generate_response.return_value = """{
        "is_contradiction": true,
        "confidence": 0.9,
        "contradicting_evidence": "Security Log",
        "correction": "Timing error"
    }"""
    
    # First 3 interventions should work
    for i in range(3):
        result = await orchestrator.check_fact_accuracy(
            statement=f"Wrong statement {i}",
            speaker="prosecution",
            stage=ExperienceState.EVIDENCE_PRESENTATION
        )
        assert result is not None
        if result.is_contradiction:
            orchestrator.fact_check_count += 1
    
    # 4th intervention should be blocked
    result = await orchestrator.check_fact_accuracy(
        statement="Wrong statement 4",
        speaker="prosecution",
        stage=ExperienceState.EVIDENCE_PRESENTATION
    )
    assert result is None


@pytest.mark.asyncio
async def test_fact_checker_handles_llm_errors_gracefully(sample_case, mock_llm_service):
    """Test that fact checker handles LLM errors without crashing."""
    # Setup
    orchestrator = TrialOrchestrator(llm_service=mock_llm_service)
    orchestrator.initialize_agents(sample_case)
    
    # Mock LLM to raise an exception
    mock_llm_service.generate_response.side_effect = Exception("LLM service error")
    
    # Test
    result = await orchestrator.check_fact_accuracy(
        statement="Some statement",
        speaker="prosecution",
        stage=ExperienceState.EVIDENCE_PRESENTATION
    )
    
    # Assert - should return no contradiction on error
    assert result is not None
    assert result.is_contradiction is False


@pytest.mark.asyncio
async def test_fact_checker_handles_invalid_json_response(sample_case, mock_llm_service):
    """Test that fact checker handles invalid JSON from LLM gracefully."""
    # Setup
    orchestrator = TrialOrchestrator(llm_service=mock_llm_service)
    orchestrator.initialize_agents(sample_case)
    
    # Mock LLM to return invalid JSON
    mock_llm_service.generate_response.return_value = "This is not valid JSON"
    
    # Test
    result = await orchestrator.check_fact_accuracy(
        statement="Some statement",
        speaker="prosecution",
        stage=ExperienceState.EVIDENCE_PRESENTATION
    )
    
    # Assert - should return no contradiction on parse error
    assert result is not None
    assert result.is_contradiction is False


@pytest.mark.asyncio
async def test_fact_checker_without_llm_service(sample_case):
    """Test that fact checker works without LLM service (returns no contradiction)."""
    # Setup - no LLM service
    orchestrator = TrialOrchestrator(llm_service=None)
    orchestrator.initialize_agents(sample_case)
    
    # Test
    result = await orchestrator.check_fact_accuracy(
        statement="Some statement",
        speaker="prosecution",
        stage=ExperienceState.EVIDENCE_PRESENTATION
    )
    
    # Assert - should return no contradiction when no LLM available
    assert result is not None
    assert result.is_contradiction is False


@pytest.mark.asyncio
async def test_build_evidence_context(sample_case, mock_llm_service):
    """Test that evidence context is properly formatted."""
    # Setup
    orchestrator = TrialOrchestrator(llm_service=mock_llm_service)
    orchestrator.initialize_agents(sample_case)
    
    # Test
    context = orchestrator._build_evidence_context()
    
    # Assert
    assert "Security Log" in context
    assert "Shows defendant left at 8:20 PM" in context
    assert "Witness Statement" in context
    assert "Toxicology Report" in context
    assert "Establishes timeline" in context
