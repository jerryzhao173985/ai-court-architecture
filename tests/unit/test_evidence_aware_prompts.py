"""Unit tests for evidence-aware deliberation prompts (Task 25.2)."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from src.jury_orchestrator import JuryOrchestrator, JurorPersona
from src.models import CaseContent, EvidenceItem
from src.session import DeliberationTurn
from src.llm_service import LLMService


@pytest.fixture
def sample_case_content():
    """Create sample case content with multiple evidence items."""
    return CaseContent.model_validate({
        "caseId": "test-001",
        "title": "Test Case",
        "narrative": {
            "hookScene": "Test hook",
            "chargeText": "Test charge",
            "victimProfile": {
                "name": "Victim",
                "role": "victim",
                "background": "Test background",
                "relevantFacts": ["fact1"]
            },
            "defendantProfile": {
                "name": "Defendant",
                "role": "defendant",
                "background": "Test background",
                "relevantFacts": ["fact1"]
            },
            "witnessProfiles": []
        },
        "evidence": [
            {
                "id": "e1",
                "type": "physical",
                "title": "Bloody Knife",
                "description": "A knife with blood stains found at the scene",
                "timestamp": "2024-01-01T00:00:00Z",
                "presentedBy": "prosecution",
                "significance": "Murder weapon"
            },
            {
                "id": "e2",
                "type": "testimonial",
                "title": "Witness Statement",
                "description": "Witness saw defendant near the scene",
                "timestamp": "2024-01-01T01:00:00Z",
                "presentedBy": "prosecution",
                "significance": "Places defendant at scene"
            },
            {
                "id": "e3",
                "type": "documentary",
                "title": "Phone Records",
                "description": "Phone records show defendant called victim",
                "timestamp": "2024-01-01T02:00:00Z",
                "presentedBy": "prosecution",
                "significance": "Shows contact"
            },
            {
                "id": "e4",
                "type": "physical",
                "title": "Fingerprints",
                "description": "Defendant's fingerprints on the weapon",
                "timestamp": "2024-01-01T03:00:00Z",
                "presentedBy": "prosecution",
                "significance": "Links defendant to weapon"
            },
            {
                "id": "e5",
                "type": "testimonial",
                "title": "Alibi Testimony",
                "description": "Friend claims defendant was elsewhere",
                "timestamp": "2024-01-01T04:00:00Z",
                "presentedBy": "defence",
                "significance": "Provides alibi"
            }
        ],
        "timeline": [],
        "groundTruth": {
            "actualVerdict": "guilty",
            "keyFacts": ["fact1"],
            "reasoningCriteria": {
                "requiredEvidenceReferences": ["e1", "e2"],
                "logicalFallacies": [],
                "coherenceThreshold": 0.5
            }
        }
    })


@pytest.fixture
def mock_llm_service():
    """Create a mock LLM service."""
    service = MagicMock(spec=LLMService)
    service.provider = "openai"
    service.generate_with_fallback = AsyncMock(return_value=("Test response", False))
    return service


@pytest.mark.asyncio
async def test_evidence_references_detected_and_appended(mock_llm_service, sample_case_content):
    """Test that evidence references are detected and appended to juror prompts."""
    # Setup
    orchestrator = JuryOrchestrator(llm_service=mock_llm_service)
    orchestrator.initialize_jury(sample_case_content)
    orchestrator.start_deliberation()
    
    # Add a user statement that references evidence
    user_statement = "I think the Bloody Knife is crucial evidence. The Fingerprints also link the defendant to the crime."
    user_turn = DeliberationTurn(
        juror_id="juror_human",
        statement=user_statement,
        timestamp=datetime.now(),
        evidence_references=[]
    )
    orchestrator.deliberation_statements.append(user_turn)
    
    # Get a juror to respond
    juror = orchestrator.jurors[0]  # First active AI juror
    
    # Execute
    await orchestrator._generate_juror_response(juror, user_statement)
    
    # Verify that LLM was called with evidence section in prompt
    call_args = mock_llm_service.generate_with_fallback.call_args
    user_prompt = call_args.kwargs['user_prompt']
    
    # Check that USER REFERENCED EVIDENCE section is present
    assert "USER REFERENCED EVIDENCE:" in user_prompt
    assert "Bloody Knife" in user_prompt
    assert "A knife with blood stains found at the scene" in user_prompt
    assert "Fingerprints" in user_prompt
    assert "Defendant's fingerprints on the weapon" in user_prompt


@pytest.mark.asyncio
async def test_juror_engaged_evidence_tracking(mock_llm_service, sample_case_content):
    """Test that jurors track which evidence they've already engaged with."""
    # Setup
    orchestrator = JuryOrchestrator(llm_service=mock_llm_service)
    orchestrator.initialize_jury(sample_case_content)
    orchestrator.start_deliberation()
    
    # Add a user statement that references evidence
    user_statement = "The Bloody Knife is crucial evidence."
    user_turn = DeliberationTurn(
        juror_id="juror_human",
        statement=user_statement,
        timestamp=datetime.now(),
        evidence_references=[]
    )
    orchestrator.deliberation_statements.append(user_turn)
    
    juror = orchestrator.jurors[0]
    
    # First response - should include evidence
    await orchestrator._generate_juror_response(juror, user_statement)
    
    # Verify evidence was tracked
    assert juror.id in orchestrator.juror_engaged_evidence
    assert "e1" in orchestrator.juror_engaged_evidence[juror.id]
    
    # Get the first call's prompt
    first_call_prompt = mock_llm_service.generate_with_fallback.call_args.kwargs['user_prompt']
    assert "USER REFERENCED EVIDENCE:" in first_call_prompt
    
    # Second response with same evidence - should NOT include it again
    await orchestrator._generate_juror_response(juror, user_statement)
    
    # Get the second call's prompt
    second_call_prompt = mock_llm_service.generate_with_fallback.call_args.kwargs['user_prompt']
    
    # Evidence should not be repeated
    # Count occurrences of "USER REFERENCED EVIDENCE:"
    first_count = first_call_prompt.count("USER REFERENCED EVIDENCE:")
    second_count = second_call_prompt.count("USER REFERENCED EVIDENCE:")
    
    # Second call should not have the evidence section (or have it but empty)
    assert second_count == 0 or "Bloody Knife" not in second_call_prompt.split("USER REFERENCED EVIDENCE:")[-1]


@pytest.mark.asyncio
async def test_different_jurors_track_separately(mock_llm_service, sample_case_content):
    """Test that different jurors track engaged evidence separately."""
    # Setup
    orchestrator = JuryOrchestrator(llm_service=mock_llm_service)
    orchestrator.initialize_jury(sample_case_content)
    orchestrator.start_deliberation()
    
    # Add a user statement that references evidence
    user_statement = "The Bloody Knife is crucial evidence."
    user_turn = DeliberationTurn(
        juror_id="juror_human",
        statement=user_statement,
        timestamp=datetime.now(),
        evidence_references=[]
    )
    orchestrator.deliberation_statements.append(user_turn)
    
    juror1 = orchestrator.jurors[0]
    juror2 = orchestrator.jurors[1]
    
    # First juror responds
    await orchestrator._generate_juror_response(juror1, user_statement)
    
    # Verify juror1 tracked the evidence
    assert juror1.id in orchestrator.juror_engaged_evidence
    assert "e1" in orchestrator.juror_engaged_evidence[juror1.id]
    
    # Second juror responds - should still see the evidence
    await orchestrator._generate_juror_response(juror2, user_statement)
    
    # Get the second juror's prompt
    second_juror_prompt = mock_llm_service.generate_with_fallback.call_args.kwargs['user_prompt']
    
    # Second juror should see the evidence (not engaged yet)
    assert "USER REFERENCED EVIDENCE:" in second_juror_prompt
    assert "Bloody Knife" in second_juror_prompt
    
    # Verify juror2 now tracked the evidence
    assert juror2.id in orchestrator.juror_engaged_evidence
    assert "e1" in orchestrator.juror_engaged_evidence[juror2.id]


@pytest.mark.asyncio
async def test_multiple_evidence_items_appended(mock_llm_service, sample_case_content):
    """Test that multiple evidence items are all appended to the prompt."""
    # Setup
    orchestrator = JuryOrchestrator(llm_service=mock_llm_service)
    orchestrator.initialize_jury(sample_case_content)
    orchestrator.start_deliberation()
    
    # Add a user statement that references multiple evidence items
    user_statement = "The Bloody Knife, Witness Statement, and Phone Records all point to guilt."
    user_turn = DeliberationTurn(
        juror_id="juror_human",
        statement=user_statement,
        timestamp=datetime.now(),
        evidence_references=[]
    )
    orchestrator.deliberation_statements.append(user_turn)
    
    juror = orchestrator.jurors[0]
    
    # Execute
    await orchestrator._generate_juror_response(juror, user_statement)
    
    # Verify all evidence items are in the prompt
    call_args = mock_llm_service.generate_with_fallback.call_args
    user_prompt = call_args.kwargs['user_prompt']
    
    assert "USER REFERENCED EVIDENCE:" in user_prompt
    assert "Bloody Knife" in user_prompt
    assert "Witness Statement" in user_prompt
    assert "Phone Records" in user_prompt


@pytest.mark.asyncio
async def test_no_evidence_references_no_section(mock_llm_service, sample_case_content):
    """Test that no evidence section is added when user doesn't reference evidence."""
    # Setup
    orchestrator = JuryOrchestrator(llm_service=mock_llm_service)
    orchestrator.initialize_jury(sample_case_content)
    orchestrator.start_deliberation()
    
    # Add a user statement that doesn't reference evidence
    user_statement = "I think we need to consider reasonable doubt here."
    user_turn = DeliberationTurn(
        juror_id="juror_human",
        statement=user_statement,
        timestamp=datetime.now(),
        evidence_references=[]
    )
    orchestrator.deliberation_statements.append(user_turn)
    
    juror = orchestrator.jurors[0]
    
    # Execute
    await orchestrator._generate_juror_response(juror, user_statement)
    
    # Verify no evidence section is added
    call_args = mock_llm_service.generate_with_fallback.call_args
    user_prompt = call_args.kwargs['user_prompt']
    
    assert "USER REFERENCED EVIDENCE:" not in user_prompt


@pytest.mark.asyncio
async def test_evidence_detection_by_id(mock_llm_service, sample_case_content):
    """Test that evidence can be detected by ID reference."""
    # Setup
    orchestrator = JuryOrchestrator(llm_service=mock_llm_service)
    orchestrator.initialize_jury(sample_case_content)
    orchestrator.start_deliberation()
    
    # Add a user statement that references evidence by ID
    user_statement = "Looking at evidence e1 and e2, I think the case is clear."
    user_turn = DeliberationTurn(
        juror_id="juror_human",
        statement=user_statement,
        timestamp=datetime.now(),
        evidence_references=[]
    )
    orchestrator.deliberation_statements.append(user_turn)
    
    juror = orchestrator.jurors[0]
    
    # Execute
    await orchestrator._generate_juror_response(juror, user_statement)
    
    # Verify evidence was detected and appended
    call_args = mock_llm_service.generate_with_fallback.call_args
    user_prompt = call_args.kwargs['user_prompt']
    
    assert "USER REFERENCED EVIDENCE:" in user_prompt
    # Should include the evidence items referenced by ID
    assert "Bloody Knife" in user_prompt or "Witness Statement" in user_prompt
