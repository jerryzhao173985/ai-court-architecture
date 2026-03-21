"""Unit tests for rate limit and timeout user feedback."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))
from trial_orchestrator import TrialOrchestrator, AgentResponse
from multi_bot_service import MultiBotService
from llm_service import LLMService, RateLimiter
from config import LLMConfig
from state_machine import ExperienceState
from models import CaseContent, CaseNarrative, CharacterProfile, EvidenceItem, GroundTruth, ReasoningCriteria


@pytest.fixture
def llm_config():
    """Create test LLM configuration."""
    return LLMConfig(
        provider="openai",
        apiKey="test-key",
        model="gpt-4",
        temperature=0.7,
        max_tokens=100,
        timeout=30,
        connectionPoolSize=5,
        connectTimeout=10,
        readTimeout=30,
        maxRetries=3,
        retryDelay=0.1,
        rateLimitRpm=10,
        rateLimitTpm=1000
    )


@pytest.fixture
def mock_case_data():
    """Create mock case data."""
    return CaseContent(
        caseId="test-case-001",
        title="Test Case",
        narrative=CaseNarrative(
            hookScene="Test Hook",
            chargeText="Test Charge",
            victimProfile=CharacterProfile(
                name="Test Victim",
                role="Victim",
                background="Test",
                relevantFacts=[]
            ),
            defendantProfile=CharacterProfile(
                name="Test Defendant",
                role="Defendant",
                background="Test",
                relevantFacts=[]
            ),
            witnessProfiles=[]
        ),
        evidence=[
            EvidenceItem(
                id="evidence-001",
                type="physical",
                title="Test Evidence 1",
                description="Test",
                timestamp="2024-01-15T20:20:00Z",
                presentedBy="defence",
                significance="Test"
            ),
            EvidenceItem(
                id="evidence-002",
                type="testimonial",
                title="Test Evidence 2",
                description="Test",
                timestamp="2024-01-15T20:00:00Z",
                presentedBy="prosecution",
                significance="Test"
            ),
            EvidenceItem(
                id="evidence-003",
                type="documentary",
                title="Test Evidence 3",
                description="Test",
                timestamp="2024-01-16T10:00:00Z",
                presentedBy="prosecution",
                significance="Test"
            ),
            EvidenceItem(
                id="evidence-004",
                type="physical",
                title="Test Evidence 4",
                description="Test",
                timestamp="2024-01-15T21:00:00Z",
                presentedBy="prosecution",
                significance="Test"
            ),
            EvidenceItem(
                id="evidence-005",
                type="testimonial",
                title="Test Evidence 5",
                description="Test",
                timestamp="2024-01-16T11:00:00Z",
                presentedBy="prosecution",
                significance="Test"
            )
        ],
        timeline=[],
        groundTruth=GroundTruth(
            actualVerdict="not_guilty",
            keyFacts=["Test"],
            reasoningCriteria=ReasoningCriteria(
                requiredEvidenceReferences=["evidence-001"],
                logicalFallacies=[],
                coherenceThreshold=0.7
            )
        )
    )


@pytest.mark.asyncio
async def test_generate_agent_response_includes_rate_limit_warning(llm_config, mock_case_data):
    """Test that _generate_agent_response includes rate_limit_warning in metadata."""
    with patch('openai.AsyncOpenAI'):
        llm_service = LLMService(llm_config)
        orchestrator = TrialOrchestrator(llm_service=llm_service)
        orchestrator.initialize_agents(mock_case_data)
        
        # Fill up rate limiter to trigger warning
        for _ in range(10):
            await llm_service._rate_limiter.acquire(100)
        
        # Mock the LLM response
        with patch.object(llm_service, 'generate_with_fallback', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = ("Test response", False)
            
            # Generate response
            response = await orchestrator._generate_agent_response("clerk", ExperienceState.CHARGE_READING)
            
            # Verify rate_limit_warning is in metadata
            assert "rate_limit_warning" in response.metadata
            assert response.metadata["rate_limit_warning"] is True


@pytest.mark.asyncio
async def test_generate_agent_response_no_rate_limit_warning_when_under_limit(llm_config, mock_case_data):
    """Test that rate_limit_warning is False when under rate limit."""
    with patch('openai.AsyncOpenAI'):
        llm_service = LLMService(llm_config)
        orchestrator = TrialOrchestrator(llm_service=llm_service)
        orchestrator.initialize_agents(mock_case_data)
        
        # Mock the LLM response
        with patch.object(llm_service, 'generate_with_fallback', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = ("Test response", False)
            
            # Generate response
            response = await orchestrator._generate_agent_response("clerk", ExperienceState.CHARGE_READING)
            
            # Verify rate_limit_warning is False
            assert "rate_limit_warning" in response.metadata
            assert response.metadata["rate_limit_warning"] is False


@pytest.mark.asyncio
async def test_generate_agent_response_timeout_metadata(llm_config, mock_case_data):
    """Test that timeout errors set timeout metadata."""
    with patch('openai.AsyncOpenAI'):
        llm_service = LLMService(llm_config)
        orchestrator = TrialOrchestrator(llm_service=llm_service)
        orchestrator.initialize_agents(mock_case_data)
        
        # Mock timeout error
        with patch.object(llm_service, 'generate_with_fallback', new_callable=AsyncMock) as mock_generate:
            mock_generate.side_effect = asyncio.TimeoutError("Request timed out")
            
            # Generate response
            response = await orchestrator._generate_agent_response("clerk", ExperienceState.CHARGE_READING)
            
            # Verify timeout metadata
            assert "timeout" in response.metadata
            assert response.metadata["timeout"] is True
            assert response.metadata.get("fallback") is True


@pytest.mark.asyncio
async def test_send_agent_response_shows_rate_limit_message():
    """Test that send_agent_response shows rate limit message when flag is set."""
    # Create mock multi_bot client
    mock_multi_bot_client = MagicMock()
    mock_multi_bot_client.send_as_agent = AsyncMock(return_value=True)
    
    # Create service and inject mock
    with patch('src.multi_bot_service.load_config'), \
         patch('src.multi_bot_service.MultiBotClient', return_value=mock_multi_bot_client):
        service = MultiBotService()
        service.multi_bot = mock_multi_bot_client
        
        # Create response with rate_limit_warning
        response = {
            "agentRole": "clerk",
            "content": "Test content",
            "metadata": {
                "rate_limit_warning": True
            }
        }
        
        # Send response
        await service.send_agent_response("test_group", response)
        
        # Verify rate limit message was sent
        calls = mock_multi_bot_client.send_as_agent.call_args_list
        assert len(calls) >= 2
        
        # First call should be the rate limit warning
        first_call = calls[0]
        assert first_call[0][0] == "clerk"  # agent role
        assert "⏳ The court needs a moment..." in first_call[0][2]  # message


@pytest.mark.asyncio
async def test_send_agent_response_shows_timeout_message():
    """Test that send_agent_response shows timeout message when flag is set."""
    # Create mock multi_bot client
    mock_multi_bot_client = MagicMock()
    mock_multi_bot_client.send_as_agent = AsyncMock(return_value=True)
    
    # Create service and inject mock
    with patch('src.multi_bot_service.load_config'), \
         patch('src.multi_bot_service.MultiBotClient', return_value=mock_multi_bot_client):
        service = MultiBotService()
        service.multi_bot = mock_multi_bot_client
        
        # Create response with timeout flag
        response = {
            "agentRole": "prosecution",
            "content": "Test content",
            "metadata": {
                "timeout": True
            }
        }
        
        # Send response
        await service.send_agent_response("test_group", response)
        
        # Verify timeout message was sent
        calls = mock_multi_bot_client.send_as_agent.call_args_list
        assert len(calls) >= 2
        
        # First call should be the timeout warning
        first_call = calls[0]
        assert first_call[0][0] == "clerk"  # agent role
        assert "⚠️" in first_call[0][2]  # message contains warning emoji
        assert "Prosecution" in first_call[0][2]  # role name
        assert "composing their response" in first_call[0][2]


@pytest.mark.asyncio
async def test_send_agent_response_no_warning_messages_when_no_flags():
    """Test that no warning messages are sent when flags are not set."""
    # Create mock multi_bot client
    mock_multi_bot_client = MagicMock()
    mock_multi_bot_client.send_as_agent = AsyncMock(return_value=True)
    
    # Create service and inject mock
    with patch('src.multi_bot_service.load_config'), \
         patch('src.multi_bot_service.MultiBotClient', return_value=mock_multi_bot_client):
        service = MultiBotService()
        service.multi_bot = mock_multi_bot_client
        
        # Create response without flags
        response = {
            "agentRole": "clerk",
            "content": "Test content",
            "metadata": {}
        }
        
        # Send response
        await service.send_agent_response("test_group", response)
        
        # Verify only one message was sent (the actual response)
        calls = mock_multi_bot_client.send_as_agent.call_args_list
        assert len(calls) == 1
        
        # Should be the formatted agent response
        call = calls[0]
        assert "📋 **CLERK**" in call[0][2]
        assert "Test content" in call[0][2]
