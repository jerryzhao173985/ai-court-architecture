"""Unit tests for bot failover functionality (Task 27.2)."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))
from multi_bot_client_sdk import MultiBotSDKClient, LuffaAPIError
from metrics import get_metrics_collector, reset_metrics
from config import LuffaConfig, LuffaBotConfig


@pytest.fixture
def mock_config():
    """Create a mock Luffa config with multiple bots."""
    config = MagicMock(spec=LuffaConfig)
    config.api_base_url = "https://apibot.luffa.im/robot"
    
    # Configure bots
    config.clerk_bot = LuffaBotConfig(
        uid="clerk_uid",
        secret="clerk_secret",
        enabled=True
    )
    config.prosecution_bot = LuffaBotConfig(
        uid="prosecution_uid",
        secret="prosecution_secret",
        enabled=True
    )
    config.defence_bot = LuffaBotConfig(
        uid="defence_uid",
        secret="defence_secret",
        enabled=True
    )
    config.judge_bot = LuffaBotConfig(
        uid="judge_uid",
        secret="judge_secret",
        enabled=True
    )
    config.fact_checker_bot = None
    config.witness_1_bot = None
    config.witness_2_bot = None
    config.defendant_bot = None
    config.juror_bots = {}
    
    return config


@pytest.fixture
def metrics_collector():
    """Create a fresh metrics collector for each test."""
    reset_metrics()
    return get_metrics_collector()


@pytest.mark.asyncio
async def test_send_as_agent_success_first_attempt(mock_config):
    """Test successful send on first attempt (no retry needed)."""
    client = MultiBotSDKClient(mock_config)
    
    # Mock successful API response
    client._make_request = AsyncMock(return_value={"code": 200, "msg": "ok"})
    
    result = await client.send_as_agent(
        agent_role="prosecution",
        group_id="test_group",
        message="Test message"
    )
    
    assert result is True
    # Should only call once (no retry)
    assert client._make_request.call_count == 1


@pytest.mark.asyncio
async def test_send_as_agent_retry_on_empty_response(mock_config):
    """Test retry logic when API returns empty response."""
    client = MultiBotSDKClient(mock_config)
    
    # First attempt returns empty, second succeeds
    client._make_request = AsyncMock(
        side_effect=[
            {},  # Empty response
            {"code": 200, "msg": "ok"}  # Success on retry
        ]
    )
    
    result = await client.send_as_agent(
        agent_role="prosecution",
        group_id="test_group",
        message="Test message"
    )
    
    assert result is True
    # Should call twice (initial + retry)
    assert client._make_request.call_count == 2


@pytest.mark.asyncio
async def test_send_as_agent_retry_on_http_error(mock_config):
    """Test retry logic when API returns HTTP error."""
    client = MultiBotSDKClient(mock_config)
    
    # First attempt fails, second succeeds
    client._make_request = AsyncMock(
        side_effect=[
            LuffaAPIError("/sendGroup", 500, "Server error"),
            {"code": 200, "msg": "ok"}
        ]
    )
    
    result = await client.send_as_agent(
        agent_role="prosecution",
        group_id="test_group",
        message="Test message"
    )
    
    assert result is True
    # Should call twice (initial + retry)
    assert client._make_request.call_count == 2


@pytest.mark.asyncio
async def test_send_as_agent_failover_to_clerk(mock_config, metrics_collector):
    """Test failover to clerk bot when both attempts fail."""
    client = MultiBotSDKClient(mock_config)
    
    # Track calls to identify which bot is being used
    call_count = 0
    
    async def mock_request(endpoint, data):
        nonlocal call_count
        call_count += 1
        
        # First 2 calls (prosecution attempts) fail
        if call_count <= 2:
            raise LuffaAPIError(endpoint, 500, "Server error")
        # Third call (clerk failover) succeeds
        return {"code": 200, "msg": "ok"}
    
    client._make_request = AsyncMock(side_effect=mock_request)
    
    # Start a session for metrics tracking
    await metrics_collector.start_session("test_session", "test_case")
    
    result = await client.send_as_agent(
        agent_role="prosecution",
        group_id="test_group",
        message="Test message",
        session_id="test_session"
    )
    
    assert result is True
    # Should call 3 times: 2 prosecution attempts + 1 clerk failover
    assert client._make_request.call_count == 3
    
    # Verify failover was tracked in metrics
    session_metrics = metrics_collector._session_metrics["test_session"]
    assert session_metrics.bot_failovers == 1


@pytest.mark.asyncio
async def test_send_as_agent_no_failover_for_clerk(mock_config):
    """Test that clerk bot does not failover to itself."""
    client = MultiBotSDKClient(mock_config)
    
    # All attempts fail
    client._make_request = AsyncMock(
        side_effect=LuffaAPIError("/sendGroup", 500, "Server error")
    )
    
    result = await client.send_as_agent(
        agent_role="clerk",
        group_id="test_group",
        message="Test message"
    )
    
    assert result is False
    # Should only call twice (initial + retry, no failover)
    assert client._make_request.call_count == 2


@pytest.mark.asyncio
async def test_send_as_agent_failover_message_prefix(mock_config):
    """Test that failover message includes role prefix."""
    client = MultiBotSDKClient(mock_config)
    
    call_count = 0
    captured_messages = []
    
    async def mock_request(endpoint, data):
        nonlocal call_count
        call_count += 1
        
        # Capture the message being sent
        if "msg" in data:
            import json
            msg_obj = json.loads(data["msg"])
            captured_messages.append(msg_obj.get("text", ""))
        
        # First 2 calls fail, third succeeds
        if call_count <= 2:
            raise LuffaAPIError(endpoint, 500, "Server error")
        return {"code": 200, "msg": "ok"}
    
    client._make_request = AsyncMock(side_effect=mock_request)
    
    result = await client.send_as_agent(
        agent_role="prosecution",
        group_id="test_group",
        message="Original message"
    )
    
    assert result is True
    # Verify the failover message has the role prefix
    assert len(captured_messages) == 3
    assert captured_messages[2] == "[Prosecution] Original message"


@pytest.mark.asyncio
async def test_send_as_agent_failover_without_session_id(mock_config):
    """Test failover works even without session_id (no metrics tracking)."""
    client = MultiBotSDKClient(mock_config)
    
    call_count = 0
    
    async def mock_request(endpoint, data):
        nonlocal call_count
        call_count += 1
        
        # First 2 calls fail, third succeeds
        if call_count <= 2:
            raise LuffaAPIError(endpoint, 500, "Server error")
        return {"code": 200, "msg": "ok"}
    
    client._make_request = AsyncMock(side_effect=mock_request)
    
    # No session_id provided
    result = await client.send_as_agent(
        agent_role="defence",
        group_id="test_group",
        message="Test message"
    )
    
    assert result is True
    # Should still failover successfully
    assert client._make_request.call_count == 3


@pytest.mark.asyncio
async def test_metrics_record_bot_failover(metrics_collector):
    """Test that record_bot_failover increments the counter."""
    # Start a session
    await metrics_collector.start_session("test_session", "test_case")
    
    # Record multiple failovers
    await metrics_collector.record_bot_failover("test_session")
    await metrics_collector.record_bot_failover("test_session")
    await metrics_collector.record_bot_failover("test_session")
    
    # Verify count
    session_metrics = metrics_collector._session_metrics["test_session"]
    assert session_metrics.bot_failovers == 3


@pytest.mark.asyncio
async def test_send_as_agent_dm_failover(mock_config):
    """Test failover works for DM messages."""
    client = MultiBotSDKClient(mock_config)
    
    call_count = 0
    
    async def mock_request(endpoint, data):
        nonlocal call_count
        call_count += 1
        
        # First 2 calls fail, third succeeds
        if call_count <= 2:
            raise LuffaAPIError(endpoint, 500, "Server error")
        return {"code": 200, "msg": "ok"}
    
    client._make_request = AsyncMock(side_effect=mock_request)
    
    result = await client.send_as_agent(
        agent_role="judge",
        group_id="user_id",
        message="DM message",
        is_dm=True
    )
    
    assert result is True
    # Should failover to clerk for DM as well
    assert client._make_request.call_count == 3
