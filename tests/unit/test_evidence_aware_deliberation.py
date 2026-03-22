"""Unit tests for evidence-aware deliberation prompts (Task 25.2)."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from jury_orchestrator import JuryOrchestrator
from models import CaseContent, EvidenceItem
from session import DeliberationTurn
from llm_service import LLMService
from reasoning_evaluator import ReasoningEvaluator


@pytest.fixture
def sample_case_content():
    """Create sample case content with evidence items."""
    return CaseContent.model_validate({
        "caseId": "test-001",
        "title": "Test Case",
        "narrative": {
            "hookScene": "Test hook",
            "chargeText": "Test charge",
            "victimProfile": {
                "name": "Victim",
                "role": "victim",
                "background": "Test",
                "relevantFacts": []
            },
            "defendantProfile": {
                "name": "Defendant",
                "role": "defendant",
                "background": "Test",
                "relevantFacts": []
            },
            "witnessProfiles": []
        },
        "evidence": [
            {
                "id": "E001",
                "type": "physical",
                "title": "Bloody Knife",
                "description": "A kitchen knife with blood stains found at the scene",
                "timestamp": "2024-01-01T10:00:00Z",
                "presentedBy": "prosecution",
                "significance": "Potential murder weapon"
            },
            {
                "id": "E002",
                "type": "testimonial",
                "title": "Witness Statement",
                "description": "Neighbor heard arguing at 9:45 PM",
                "timestamp": "2024-01-01T09:45:00Z",
                "presentedBy": "prosecution",
                "significance": "Establishes timeline"
            },
            {
                "id": "E003",
                "type": "documentary",
                "title": "Phone Records",
                "description": "Call logs showing contact between victim and defendant",
                "timestamp": "2024-01-01T09:30:00Z",
                "presentedBy": "defence",
                "significance": "Shows prior relationship"
            },
            {
                "id": "E004",
                "type": "physical",
                "title": "Fingerprints",
                "description": "Fingerprints found on the weapon",
                "timestamp": "2024-01-01T10:15:00Z",
                "presentedBy": "prosecution",
                "significance": "Links defendant to weapon"
            },
            {
                "id": "E005",
                "type": "documentary",
                "title": "Security Footage",
                "description": "CCTV showing defendant near the scene",
                "timestamp": "2024-01-01T09:50:00Z",
                "presentedBy": "prosecution",
                "significance": "Places defendant at scene"
            }
        ],
        "timeline": [],
        "groundTruth": {
            "actualVerdict": "guilty",
            "keyFacts": ["Test fact"],
            "reasoningCriteria": {
                "requiredEvidenceReferences": ["E001"],
                "logicalFallacies": [],
                "coherenceThreshold": 0.6
            }
        }
    })


@pytest.fixture
def mock_llm_service():
    """Create mock LLM service."""
    service = MagicMock(spec=LLMService)
    service.provider = "openai"
    service.generate_with_fallback = AsyncMock(return_value=("Test response", False))
    return service


@pytest.mark.asyncio
async def test_evidence_references_detected_and_appended(sample_case_content, mock_llm_service):
    """Test that evidence references are detected and appended to juror prompts."""
    # Setup
    orchestrator = JuryOrchestrator(llm_service=mock_llm_service)
    orchestrator.initialize_jury(sample_case_content)
    orchestrator.start_deliberation()
    
    # User makes a statement referencing evidence
    user_statement = "I think the bloody knife (E001) is crucial evidence here."
    
    # Process user statement
    turns = await orchestrator.process_user_statement(user_statement, evidence_references=["E001"])
    
    # Verify that the LLM was called with evidence section
    # Get the first active AI juror
    active_juror = next(j for j in orchestrator.jurors if j.type == "active_ai")
    
    # Check that generate_with_fallback was called
    assert orchestrator.llm_service.generate_with_fallback.called
    
    # Get the call arguments
    call_args = orchestrator.llm_service.generate_with_fallback.call_args
    user_prompt = call_args.kwargs['user_prompt']
    
    # Verify evidence section was appended
    assert "USER REFERENCED EVIDENCE:" in user_prompt
    assert "Bloody Knife" in user_prompt
    assert "A kitchen knife with blood stains found at the scene" in user_prompt


@pytest.mark.asyncio
async def test_evidence_tracking_prevents_repetition(sample_case_content, mock_llm_service):
    """Test that jurors don't repeat commentary on the same evidence."""
    import random
    random.seed(100)  # Deterministic for testing

    # Setup
    orchestrator = JuryOrchestrator(llm_service=mock_llm_service)
    orchestrator.initialize_jury(sample_case_content)
    orchestrator.start_deliberation()
    
    # User makes first statement referencing E001
    await orchestrator.process_user_statement(
        "The bloody knife is important.",
        evidence_references=["E001"]
    )
    
    # Get first active juror
    active_juror = orchestrator.jurors[0]
    
    # Verify E001 is now in engaged evidence for this juror
    assert "E001" in orchestrator.juror_engaged_evidence.get(active_juror.id, set())
    
    # Reset mock
    orchestrator.llm_service.generate_with_fallback.reset_mock()
    
    # User makes second statement also referencing E001
    await orchestrator.process_user_statement(
        "Let's talk more about the bloody knife.",
        evidence_references=["E001"]
    )
    
    # Check that the FIRST active juror's prompt doesn't repeat E001
    # (they already engaged with it in round 1)
    # Look through all calls to find the one for active_juror
    found_repeat = False
    for call in orchestrator.llm_service.generate_with_fallback.call_args_list:
        prompt = call.kwargs.get('user_prompt', '')
        agent = call.kwargs.get('agent_role', '')
        # Only check the active juror that already engaged with E001
        if f"juror_{active_juror.id}" in agent or active_juror.id in agent:
            if "USER REFERENCED EVIDENCE:" in prompt and "E001" in prompt:
                found_repeat = True

    # The active juror who already engaged with E001 should NOT see it again
    assert not found_repeat, "Juror should not see E001 evidence section again"


@pytest.mark.asyncio
async def test_multiple_evidence_items_appended(sample_case_content, mock_llm_service):
    """Test that multiple evidence items are all appended when referenced."""
    # Setup
    orchestrator = JuryOrchestrator(llm_service=mock_llm_service)
    orchestrator.initialize_jury(sample_case_content)
    orchestrator.start_deliberation()
    
    # User references multiple evidence items
    user_statement = "Both the knife (E001) and the witness statement (E002) are important."
    
    # Process user statement
    await orchestrator.process_user_statement(
        user_statement,
        evidence_references=["E001", "E002"]
    )
    
    # Get the call arguments
    call_args = orchestrator.llm_service.generate_with_fallback.call_args
    user_prompt = call_args.kwargs['user_prompt']
    
    # Verify both evidence items are in the prompt
    assert "USER REFERENCED EVIDENCE:" in user_prompt
    assert "Bloody Knife" in user_prompt
    assert "Witness Statement" in user_prompt
    assert "kitchen knife with blood stains" in user_prompt
    assert "Neighbor heard arguing" in user_prompt


@pytest.mark.asyncio
async def test_different_jurors_track_separately(sample_case_content, mock_llm_service):
    """Test that different jurors track engaged evidence separately."""
    # Setup
    orchestrator = JuryOrchestrator(llm_service=mock_llm_service)
    orchestrator.initialize_jury(sample_case_content)
    orchestrator.start_deliberation()
    
    # User references E001
    await orchestrator.process_user_statement(
        "The bloody knife is crucial.",
        evidence_references=["E001"]
    )
    
    # Get the three active jurors
    active_jurors = [j for j in orchestrator.jurors if j.type == "active_ai"]
    
    # Only 2 of 3 active jurors should have responded (Task 25.3: inter-juror debate dynamics)
    # So only 2 should have E001 in their engaged evidence
    jurors_with_e001 = [j for j in active_jurors if "E001" in orchestrator.juror_engaged_evidence.get(j.id, set())]
    assert len(jurors_with_e001) == 2, "Expected 2 of 3 active jurors to have engaged with E001"
    
    # Reset mock
    orchestrator.llm_service.generate_with_fallback.reset_mock()
    
    # User references E002 (new evidence) - this will trigger 2 more jurors
    await orchestrator.process_user_statement(
        "The witness statement is also important.",
        evidence_references=["E002"]
    )
    
    # Now check that jurors track evidence separately
    # The 2 jurors who responded in round 2 should have E002
    jurors_with_e002 = [j for j in active_jurors if "E002" in orchestrator.juror_engaged_evidence.get(j.id, set())]
    assert len(jurors_with_e002) == 2, "Expected 2 of 3 active jurors to have engaged with E002"
    
    # At least one juror should have both E001 and E002 (if they responded in both rounds)
    # Or they might be different jurors due to rotation
    all_engaged_evidence = {j.id: orchestrator.juror_engaged_evidence.get(j.id, set()) for j in active_jurors}
    
    # Verify that evidence tracking is working per-juror
    for juror_id, evidence_set in all_engaged_evidence.items():
        # Each juror should have at most 2 evidence items (E001 and/or E002)
        assert len(evidence_set) <= 2
        # Each evidence item should be either E001 or E002
        for evidence_id in evidence_set:
            assert evidence_id in ["E001", "E002"]


@pytest.mark.asyncio
async def test_reasoning_evaluator_tracks_evidence(sample_case_content, mock_llm_service):
    """Test that reasoning evaluator correctly tracks evidence references."""
    # Setup
    orchestrator = JuryOrchestrator(llm_service=mock_llm_service)
    orchestrator.initialize_jury(sample_case_content)
    orchestrator.start_deliberation()
    
    # Create user statements with evidence references
    user_turn_1 = DeliberationTurn(
        juror_id="juror_human",
        statement="The bloody knife found at the scene is damning evidence.",
        timestamp=datetime.now(),
        evidence_references=["E001"]
    )
    
    user_turn_2 = DeliberationTurn(
        juror_id="juror_human",
        statement="The witness heard arguing, which establishes the timeline.",
        timestamp=datetime.now(),
        evidence_references=["E002"]
    )
    
    # Track evidence references
    referenced_ids = orchestrator.reasoning_evaluator.track_evidence_references([user_turn_1, user_turn_2])
    
    # Verify both evidence items were tracked
    assert "E001" in referenced_ids
    assert "E002" in referenced_ids


@pytest.mark.asyncio
async def test_no_evidence_section_when_no_references(sample_case_content, mock_llm_service):
    """Test that no evidence section is added when user doesn't reference evidence."""
    # Setup
    orchestrator = JuryOrchestrator(llm_service=mock_llm_service)
    orchestrator.initialize_jury(sample_case_content)
    orchestrator.start_deliberation()
    
    # User makes a statement without evidence references
    await orchestrator.process_user_statement(
        "I'm not sure what to think about this case.",
        evidence_references=[]
    )
    
    # Get the call arguments
    call_args = orchestrator.llm_service.generate_with_fallback.call_args
    user_prompt = call_args.kwargs['user_prompt']
    
    # Verify no evidence section was added
    assert "USER REFERENCED EVIDENCE:" not in user_prompt


@pytest.mark.asyncio
async def test_lightweight_jurors_also_get_evidence_context(sample_case_content, mock_llm_service):
    """Test that lightweight jurors also receive evidence context when appropriate."""
    # Setup
    orchestrator = JuryOrchestrator(llm_service=mock_llm_service)
    orchestrator.initialize_jury(sample_case_content)
    orchestrator.start_deliberation()
    
    # Make enough statements to trigger lightweight juror response
    await orchestrator.process_user_statement("First statement", evidence_references=[])
    await orchestrator.process_user_statement("Second statement", evidence_references=[])
    
    # Reset mock
    orchestrator.llm_service.generate_with_fallback.reset_mock()
    
    # Third statement with evidence reference (should trigger lightweight juror)
    await orchestrator.process_user_statement(
        "The bloody knife is important.",
        evidence_references=["E001"]
    )
    
    # Check if any lightweight juror was called
    # The lightweight juror should also get the evidence context
    if orchestrator.llm_service.generate_with_fallback.call_count > 3:
        # At least one lightweight juror responded
        # Check the last call (likely the lightweight juror)
        call_args = orchestrator.llm_service.generate_with_fallback.call_args_list[-1]
        user_prompt = call_args.kwargs['user_prompt']
        
        # Lightweight juror should also see evidence context
        assert "USER REFERENCED EVIDENCE:" in user_prompt or "Bloody Knife" in user_prompt
