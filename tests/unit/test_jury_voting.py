"""Unit tests for LLM-based jury voting."""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
import json

from src.jury_orchestrator import JuryOrchestrator, JurorPersona
from src.models import CaseContent
from src.llm_service import LLMService
from src.config import LLMConfig


@pytest.fixture
def mock_llm_service():
    """Create a mock LLM service."""
    service = MagicMock(spec=LLMService)
    service.generate_response = AsyncMock()
    return service


@pytest.fixture
def sample_case_content():
    """Create sample case content for testing."""
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
                "title": "Evidence 1",
                "description": "Test evidence",
                "timestamp": "2024-01-01T00:00:00Z",
                "presentedBy": "prosecution",
                "significance": "Test"
            }
        ] * 5,  # Need 5-7 evidence items
        "timeline": [],
        "groundTruth": {
            "actualVerdict": "guilty",
            "keyFacts": ["fact1"],
            "reasoningCriteria": {
                "requiredEvidenceReferences": [],
                "logicalFallacies": [],
                "coherenceThreshold": 0.5
            }
        }
    })


@pytest.mark.asyncio
async def test_generate_ai_vote_with_llm(mock_llm_service, sample_case_content):
    """Test that _generate_ai_vote calls LLM and returns vote with reasoning."""
    # Setup
    orchestrator = JuryOrchestrator(llm_service=mock_llm_service)
    orchestrator.case_content = sample_case_content
    orchestrator.deliberation_statements = []
    
    juror = JurorPersona(
        id="juror_1",
        type="active_ai",
        persona="evidence_purist",
        systemPrompt="You are an evidence purist."
    )
    
    # Mock LLM response
    mock_llm_service.generate_response.return_value = json.dumps({
        "vote": "guilty",
        "reasoning": "The evidence clearly shows guilt."
    })
    
    # Execute
    vote, reasoning = await orchestrator._generate_ai_vote(juror)
    
    # Verify
    assert vote == "guilty"
    assert reasoning == "The evidence clearly shows guilt."
    assert mock_llm_service.generate_response.called
    
    # Check that LLM was called with correct parameters
    call_args = mock_llm_service.generate_response.call_args
    assert call_args.kwargs['temperature'] == 0.3
    assert call_args.kwargs['timeout'] == 10
    assert call_args.kwargs['max_tokens'] == 150
    assert call_args.kwargs['response_format'] == {"type": "json_object"}


@pytest.mark.asyncio
async def test_generate_ai_vote_fallback_on_error(mock_llm_service, sample_case_content):
    """Test that _generate_ai_vote falls back to heuristic on LLM error."""
    # Setup
    orchestrator = JuryOrchestrator(llm_service=mock_llm_service)
    orchestrator.case_content = sample_case_content
    orchestrator.deliberation_statements = []
    
    juror = JurorPersona(
        id="juror_2",
        type="active_ai",
        persona="sympathetic_doubter",
        systemPrompt="You are a sympathetic doubter."
    )
    
    # Mock LLM to raise an error
    mock_llm_service.generate_response.side_effect = Exception("LLM error")
    
    # Execute
    vote, reasoning = await orchestrator._generate_ai_vote(juror)
    
    # Verify fallback behavior (sympathetic_doubter should vote not_guilty)
    assert vote == "not_guilty"
    assert "Fallback vote" in reasoning


@pytest.mark.asyncio
async def test_generate_ai_vote_invalid_response(mock_llm_service, sample_case_content):
    """Test that _generate_ai_vote handles invalid LLM responses."""
    # Setup
    orchestrator = JuryOrchestrator(llm_service=mock_llm_service)
    orchestrator.case_content = sample_case_content
    orchestrator.deliberation_statements = []
    
    juror = JurorPersona(
        id="juror_3",
        type="active_ai",
        persona="moral_absolutist",
        systemPrompt="You are a moral absolutist."
    )
    
    # Mock LLM to return invalid vote
    mock_llm_service.generate_response.return_value = json.dumps({
        "vote": "maybe",  # Invalid vote
        "reasoning": "I'm not sure."
    })
    
    # Execute
    vote, reasoning = await orchestrator._generate_ai_vote(juror)
    
    # Verify fallback behavior (moral_absolutist now uses balanced MD5 hash like other jurors)
    # juror_3 MD5 hash is odd → not_guilty
    assert vote == "not_guilty"
    assert "Fallback vote" in reasoning


@pytest.mark.asyncio
async def test_collect_votes_stores_reasoning(mock_llm_service, sample_case_content):
    """Test that collect_votes stores vote reasoning for dual reveal."""
    # Setup
    orchestrator = JuryOrchestrator(llm_service=mock_llm_service)
    orchestrator.initialize_jury(sample_case_content)
    
    # Mock LLM responses for all AI jurors
    mock_llm_service.generate_response.return_value = json.dumps({
        "vote": "guilty",
        "reasoning": "Test reasoning"
    })
    
    # Execute
    result = await orchestrator.collect_votes("not_guilty")
    
    # Verify
    assert hasattr(orchestrator, 'vote_reasoning')
    assert len(orchestrator.vote_reasoning) == 7  # 7 AI jurors
    for juror_id, reasoning in orchestrator.vote_reasoning.items():
        assert reasoning == "Test reasoning"


@pytest.mark.asyncio
async def test_reveal_jurors_includes_vote_reasoning(mock_llm_service, sample_case_content):
    """Test that reveal_jurors includes vote reasoning in key_statements."""
    # Setup
    orchestrator = JuryOrchestrator(llm_service=mock_llm_service)
    orchestrator.initialize_jury(sample_case_content)
    
    # Mock LLM responses
    mock_llm_service.generate_response.return_value = json.dumps({
        "vote": "guilty",
        "reasoning": "The evidence is compelling."
    })
    
    # Collect votes
    result = await orchestrator.collect_votes("guilty")
    
    # Reveal jurors
    reveals = orchestrator.reveal_jurors(result)
    
    # Verify that active AI jurors have vote reasoning in key_statements
    active_ai_reveals = [r for r in reveals if r.type == "active_ai"]
    assert len(active_ai_reveals) == 3
    
    for reveal in active_ai_reveals:
        # Should have vote reasoning as last statement
        assert any("Vote reasoning:" in stmt for stmt in reveal.key_statements)


@pytest.mark.asyncio
async def test_generate_ai_vote_without_llm_service(sample_case_content):
    """Test that _generate_ai_vote works without LLM service (fallback only)."""
    # Setup
    orchestrator = JuryOrchestrator(llm_service=None)
    orchestrator.case_content = sample_case_content
    orchestrator.deliberation_statements = []
    
    juror = JurorPersona(
        id="juror_1",
        type="active_ai",
        persona="sympathetic_doubter",
        systemPrompt="You are a sympathetic doubter."
    )
    
    # Execute
    vote, reasoning = await orchestrator._generate_ai_vote(juror)
    
    # Verify fallback behavior
    assert vote == "not_guilty"
    assert "persona" in reasoning.lower()
