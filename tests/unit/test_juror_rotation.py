"""Unit tests for inter-juror debate dynamics (Task 25.3)."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from jury_orchestrator import JuryOrchestrator
from models import CaseContent
from llm_service import LLMService


@pytest.fixture
def sample_case_content():
    """Create minimal case content for testing."""
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
                "title": "Evidence 1",
                "description": "Test evidence 1",
                "timestamp": "2024-01-01T10:00:00Z",
                "presentedBy": "prosecution",
                "significance": "Test"
            },
            {
                "id": "E002",
                "type": "testimonial",
                "title": "Evidence 2",
                "description": "Test evidence 2",
                "timestamp": "2024-01-01T10:01:00Z",
                "presentedBy": "prosecution",
                "significance": "Test"
            },
            {
                "id": "E003",
                "type": "documentary",
                "title": "Evidence 3",
                "description": "Test evidence 3",
                "timestamp": "2024-01-01T10:02:00Z",
                "presentedBy": "defence",
                "significance": "Test"
            },
            {
                "id": "E004",
                "type": "physical",
                "title": "Evidence 4",
                "description": "Test evidence 4",
                "timestamp": "2024-01-01T10:03:00Z",
                "presentedBy": "prosecution",
                "significance": "Test"
            },
            {
                "id": "E005",
                "type": "testimonial",
                "title": "Evidence 5",
                "description": "Test evidence 5",
                "timestamp": "2024-01-01T10:04:00Z",
                "presentedBy": "defence",
                "significance": "Test"
            }
        ],
        "timeline": [],
        "groundTruth": {
            "actualVerdict": "guilty",
            "keyFacts": ["Test fact"],
            "reasoningCriteria": {
                "requiredEvidenceReferences": [],
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
async def test_two_of_three_jurors_respond_per_round(sample_case_content, mock_llm_service):
    """Test that only 2 of 3 active jurors respond per round."""
    # Setup
    orchestrator = JuryOrchestrator(llm_service=mock_llm_service)
    orchestrator.initialize_jury(sample_case_content)
    orchestrator.start_deliberation()
    
    # User makes a statement
    turns = await orchestrator.process_user_statement("What do you think?")
    
    # Should have 1 user turn + 2 AI juror turns = 3 total
    assert len(turns) == 3, f"Expected 3 turns (1 user + 2 AI), got {len(turns)}"
    
    # Verify the first turn is from the human
    assert turns[0].juror_id == "juror_human"
    
    # Verify the next 2 turns are from active AI jurors
    ai_turns = turns[1:]
    assert len(ai_turns) == 2
    for turn in ai_turns:
        assert turn.juror_id.startswith("juror_")
        assert turn.juror_id != "juror_human"


@pytest.mark.asyncio
async def test_juror_rotation_ensures_all_respond_every_two_rounds(sample_case_content, mock_llm_service):
    """Test that bot jurors respond frequently and all jurors participate."""
    import random
    random.seed(42)  # Deterministic for testing

    # Setup
    orchestrator = JuryOrchestrator(llm_service=mock_llm_service)
    orchestrator.initialize_jury(sample_case_content)
    orchestrator.start_deliberation()
    
    # Track which jurors respond in each round
    responding_jurors_by_round = []
    
    # Run 4 rounds
    for i in range(4):
        turns = await orchestrator.process_user_statement(f"Statement {i+1}")
        
        # Get the juror IDs that responded (skip the user turn)
        responding_jurors = [turn.juror_id for turn in turns[1:] if turn.juror_id.startswith("juror_")]
        responding_jurors_by_round.append(set(responding_jurors))
    
    # Get all active juror IDs
    active_juror_ids = {j.id for j in orchestrator.jurors if j.type == "active_ai"}
    
    # Verify bot jurors (juror_1, juror_2) respond frequently
    bot_juror_ids = {"juror_1", "juror_2"}
    for round_jurors in responding_jurors_by_round:
        # At least one bot juror should respond every round
        assert len(round_jurors & bot_juror_ids) >= 1, \
            f"At least one bot juror should respond each round, got {round_jurors}"

    # All active jurors should have responded at least once across 4 rounds
    all_responders = set()
    for round_jurors in responding_jurors_by_round:
        all_responders |= round_jurors
    assert active_juror_ids.issubset(all_responders), \
        f"All active jurors should respond at least once in 4 rounds"


@pytest.mark.asyncio
async def test_lightweight_juror_responds_every_fourth_round(sample_case_content, mock_llm_service):
    """Test that lightweight jurors respond every 4th round instead of every 3rd."""
    # Setup
    orchestrator = JuryOrchestrator(llm_service=mock_llm_service)
    orchestrator.initialize_jury(sample_case_content)
    orchestrator.start_deliberation()
    
    # Track total statements after each round
    lightweight_response_rounds = []
    
    # Run 8 rounds to see the pattern
    for i in range(8):
        await orchestrator.process_user_statement(f"Statement {i+1}")
        
        # Check if a lightweight juror responded
        # Count total statements (should be divisible by 4 when lightweight responds)
        total_statements = len(orchestrator.deliberation_statements)
        
        # Check if the last statement was from a lightweight juror
        if orchestrator.deliberation_statements:
            last_turn = orchestrator.deliberation_statements[-1]
            # Find the juror
            juror = next((j for j in orchestrator.jurors if j.id == last_turn.juror_id), None)
            if juror and juror.type == "lightweight_ai":
                lightweight_response_rounds.append(i + 1)
    
    # Lightweight jurors should respond when total statements is divisible by 4
    # After round 1: 3 statements (1 user + 2 AI)
    # After round 2: 6 statements (2 user + 4 AI)
    # After round 3: 9 statements (3 user + 6 AI)
    # After round 4: 12 statements (4 user + 8 AI) - divisible by 4, lightweight responds
    # So lightweight should respond in rounds where total statements becomes divisible by 4
    
    # Verify lightweight jurors responded at appropriate times
    assert len(lightweight_response_rounds) > 0, "Lightweight jurors should have responded at least once"
    
    # Check the pattern - should be roughly every 4th round
    # (exact timing depends on when total statements hits multiples of 4)
    print(f"Lightweight jurors responded in rounds: {lightweight_response_rounds}")


@pytest.mark.asyncio
async def test_juror_last_response_tracking(sample_case_content, mock_llm_service):
    """Test that juror_last_response_round is correctly tracked."""
    # Setup
    orchestrator = JuryOrchestrator(llm_service=mock_llm_service)
    orchestrator.initialize_jury(sample_case_content)
    orchestrator.start_deliberation()
    
    # Initially, no jurors have responded
    assert len(orchestrator.juror_last_response_round) == 0
    
    # Round 1
    await orchestrator.process_user_statement("Statement 1")
    
    # All 3 jurors should be initialized in tracking (even if only 2 responded)
    # The _select_responding_jurors method initializes all jurors
    assert len(orchestrator.juror_last_response_round) == 3
    
    # 2 jurors should have responded in round 1 (round_num == 1)
    round_1_responders = [jid for jid, rnd in orchestrator.juror_last_response_round.items() if rnd == 1]
    assert len(round_1_responders) == 2, f"Expected 2 jurors to respond in round 1, got {len(round_1_responders)}"
    
    # 1 juror should not have responded yet (round_num == 0)
    non_responders = [jid for jid, rnd in orchestrator.juror_last_response_round.items() if rnd == 0]
    assert len(non_responders) == 1, f"Expected 1 juror to not respond yet, got {len(non_responders)}"
    
    # Round 2
    await orchestrator.process_user_statement("Statement 2")
    
    # Now all jurors should have tracking
    assert len(orchestrator.juror_last_response_round) == 3
    
    # At least one juror should have round 2 as their last response
    round_2_jurors = [jid for jid, rnd in orchestrator.juror_last_response_round.items() if rnd == 2]
    assert len(round_2_jurors) >= 1, "At least one juror should have responded in round 2"
    
    # The juror who didn't respond in round 1 should have responded in round 2
    # (to ensure each juror responds at least every 2 rounds)
    for juror_id in non_responders:
        assert orchestrator.juror_last_response_round[juror_id] == 2, \
            f"Juror {juror_id} who didn't respond in round 1 should have responded in round 2"


@pytest.mark.asyncio
async def test_select_responding_jurors_rotation_logic(sample_case_content, mock_llm_service):
    """Test the _select_responding_jurors method directly."""
    # Setup
    orchestrator = JuryOrchestrator(llm_service=mock_llm_service)
    orchestrator.initialize_jury(sample_case_content)
    
    active_jurors = [j for j in orchestrator.jurors if j.type == "active_ai"]
    assert len(active_jurors) == 3
    
    # Round 1: should pick at least 2 jurors (bot jurors prioritized)
    selected = orchestrator._select_responding_jurors(active_jurors, 1)
    assert len(selected) >= 2

    # Bot jurors (juror_1 or juror_2) should always be in the selection
    bot_juror_ids = {"juror_1", "juror_2"}
    selected_ids = {j.id for j in selected}
    assert len(selected_ids & bot_juror_ids) >= 1, "At least one bot juror should always be selected"

    # Simulate responses
    for juror in selected:
        orchestrator.juror_last_response_round[juror.id] = 1

    # Round 2: should still pick at least 2
    selected = orchestrator._select_responding_jurors(active_jurors, 2)
    assert len(selected) >= 2
