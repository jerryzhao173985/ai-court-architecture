"""Tests for juror identity display in deliberation messages (Task 25.4)."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from jury_orchestrator import JuryOrchestrator, JUROR_DISPLAY
from models import CaseContent


@pytest.fixture
def sample_case():
    """Create a minimal case for testing."""
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


def test_juror_display_constant_exists():
    """Test that JUROR_DISPLAY constant is defined correctly."""
    assert "evidence_purist" in JUROR_DISPLAY
    assert "sympathetic_doubter" in JUROR_DISPLAY
    assert "moral_absolutist" in JUROR_DISPLAY
    
    # Check structure: (emoji, display_name)
    assert JUROR_DISPLAY["evidence_purist"] == ("🔬", "Evidence Purist")
    assert JUROR_DISPLAY["sympathetic_doubter"] == ("🤔", "Sympathetic Doubter")
    assert JUROR_DISPLAY["moral_absolutist"] == ("⚖️", "Moral Absolutist")


def test_get_juror_display_info_for_active_ai_jurors(sample_case):
    """Test getting display info for active AI jurors with personas."""
    orchestrator = JuryOrchestrator()
    orchestrator.initialize_jury(sample_case)
    
    # Test evidence purist (juror_1)
    emoji, name = orchestrator.get_juror_display_info("juror_1")
    assert emoji == "🔬"
    assert name == "Evidence Purist"
    
    # Test sympathetic doubter (juror_2)
    emoji, name = orchestrator.get_juror_display_info("juror_2")
    assert emoji == "🤔"
    assert name == "Sympathetic Doubter"
    
    # Test moral absolutist (juror_3)
    emoji, name = orchestrator.get_juror_display_info("juror_3")
    assert emoji == "⚖️"
    assert name == "Moral Absolutist"


def test_get_juror_display_info_for_lightweight_jurors(sample_case):
    """Test getting display info for lightweight AI jurors."""
    orchestrator = JuryOrchestrator()
    orchestrator.initialize_jury(sample_case)
    
    # Test lightweight jurors (juror_4 through juror_7)
    for i in range(4, 8):
        juror_id = f"juror_{i}"
        emoji, name = orchestrator.get_juror_display_info(juror_id)
        assert emoji == "👤"
        assert name == f"Juror {i}"


def test_get_juror_display_info_for_human_juror(sample_case):
    """Test getting display info for human juror."""
    orchestrator = JuryOrchestrator()
    orchestrator.initialize_jury(sample_case)
    
    emoji, name = orchestrator.get_juror_display_info("juror_human")
    assert emoji == "👤"
    assert name == "You"


def test_get_juror_display_info_for_unknown_juror(sample_case):
    """Test getting display info for unknown juror ID."""
    orchestrator = JuryOrchestrator()
    orchestrator.initialize_jury(sample_case)
    
    emoji, name = orchestrator.get_juror_display_info("unknown_juror")
    assert emoji == "👤"
    assert name == "AI Juror"


@pytest.mark.asyncio
async def test_deliberation_message_format_in_orchestrator(sample_case):
    """Test that deliberation turns can be formatted with juror identity."""
    # Create mock LLM service
    mock_llm = AsyncMock()
    mock_llm.generate_with_fallback = AsyncMock(return_value=("Test response", False))
    
    orchestrator = JuryOrchestrator(llm_service=mock_llm)
    orchestrator.initialize_jury(sample_case)
    orchestrator.start_deliberation()
    
    # Process a user statement
    turns = await orchestrator.process_user_statement("What do you think?")
    
    # Verify we can get display info for each responding juror
    for turn in turns[1:]:  # Skip user turn
        juror_id = turn.juror_id
        emoji, name = orchestrator.get_juror_display_info(juror_id)
        
        # Verify we got valid display info
        assert emoji in ["🔬", "🤔", "⚖️", "👤"]
        assert name in ["Evidence Purist", "Sympathetic Doubter", "Moral Absolutist"] or name.startswith("Juror ")
        
        # Verify we can format the message
        juror_num = juror_id.replace("juror_", "")
        formatted = f"{emoji} {name} (Juror {juror_num}): {turn.statement}"
        
        # Check format is correct
        assert formatted.startswith(emoji)
        assert name in formatted
        assert f"(Juror {juror_num})" in formatted
        assert turn.statement in formatted


def test_juror_display_info_consistency_across_calls(sample_case):
    """Test that display info is consistent across multiple calls."""
    orchestrator = JuryOrchestrator()
    orchestrator.initialize_jury(sample_case)
    
    # Call multiple times for same juror
    for _ in range(5):
        emoji1, name1 = orchestrator.get_juror_display_info("juror_1")
        emoji2, name2 = orchestrator.get_juror_display_info("juror_1")
        
        assert emoji1 == emoji2 == "🔬"
        assert name1 == name2 == "Evidence Purist"
