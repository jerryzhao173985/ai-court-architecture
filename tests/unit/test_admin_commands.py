"""Unit tests for admin commands in multi-bot service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.multi_bot_service import MultiBotService
from src.orchestrator import ExperienceOrchestrator
from src.session import UserSession
from src.state_machine import ExperienceState


@pytest.fixture
def mock_config():
    """Create mock configuration."""
    config = MagicMock()
    config.admin_uids = ["admin_user_1", "admin_user_2"]
    config.luffa.bot_enabled = True
    return config


@pytest.fixture
def mock_multi_bot_client():
    """Create mock multi-bot client."""
    client = MagicMock()
    client.send_as_agent = AsyncMock()
    client.has_bot_for_role = MagicMock(return_value=True)
    client.get_configured_roles = MagicMock(return_value=["clerk"])
    client.bot_uids = []
    return client


@pytest.fixture
def service(mock_config, mock_multi_bot_client):
    """Create MultiBotService instance with mocks."""
    with patch("src.multi_bot_service.load_config", return_value=mock_config):
        with patch("src.multi_bot_service.MultiBotClient", return_value=mock_multi_bot_client):
            service = MultiBotService()
            return service


@pytest.mark.asyncio
async def test_metrics_command_admin_access(service, mock_multi_bot_client):
    """Test that admin users can access /metrics command."""
    group_id = "test_group"
    admin_uid = "admin_user_1"
    
    with patch("src.multi_bot_service.get_metrics_collector") as mock_get_collector:
        # Mock metrics collector
        mock_collector = MagicMock()
        mock_collector.get_summary.return_value = {
            "agent_responses": {
                "overall": {
                    "count": 10,
                    "avg_duration_ms": 1500,
                    "p95_duration_ms": 2000,
                    "success_rate": 0.95,
                    "fallback_rate": 0.05
                },
                "by_role": {
                    "clerk": {
                        "count": 5,
                        "avg_duration_ms": 1200
                    }
                },
                "by_stage": {}
            },
            "state_transitions": {
                "count": 8,
                "avg_duration_ms": 500,
                "p95_duration_ms": 800,
                "success_rate": 1.0
            },
            "reasoning_evaluation": {
                "count": 3,
                "avg_duration_ms": 3000,
                "success_rate": 1.0,
                "category_distribution": {"sound_correct": 2, "sound_incorrect": 1}
            },
            "sessions": {
                "total_sessions": 2,
                "completed_sessions": 1,
                "completion_rate": 0.5,
                "avg_duration_ms": 120000,
                "avg_agent_calls": 15,
                "avg_state_transitions": 8
            }
        }
        mock_get_collector.return_value = mock_collector
        
        # Execute command
        await service.show_metrics(group_id, admin_uid)
        
        # Verify metrics were sent
        mock_multi_bot_client.send_as_agent.assert_called_once()
        call_args = mock_multi_bot_client.send_as_agent.call_args
        
        assert call_args[0][0] == "clerk"
        assert call_args[0][1] == group_id
        message = call_args[0][2]
        
        # Verify message contains key metrics
        assert "VERITAS PERFORMANCE METRICS" in message
        assert "Agent Responses:" in message
        assert "Total calls: 10" in message
        assert "State Transitions:" in message
        assert "Reasoning Evaluations:" in message
        assert "Sessions:" in message


@pytest.mark.asyncio
async def test_metrics_command_non_admin_denied(service, mock_multi_bot_client):
    """Test that non-admin users cannot access /metrics command."""
    group_id = "test_group"
    non_admin_uid = "regular_user"
    
    # Execute command
    await service.show_metrics(group_id, non_admin_uid)
    
    # Verify access denied message was sent
    mock_multi_bot_client.send_as_agent.assert_called_once()
    call_args = mock_multi_bot_client.send_as_agent.call_args
    
    assert call_args[0][0] == "clerk"
    assert call_args[0][1] == group_id
    assert "only available to administrators" in call_args[0][2]


@pytest.mark.asyncio
async def test_sessions_command_admin_access(service, mock_multi_bot_client):
    """Test that admin users can access /sessions command."""
    group_id = "test_group"
    admin_uid = "admin_user_2"
    
    # Create mock active sessions
    mock_session_1 = MagicMock(spec=UserSession)
    mock_session_1.current_state = ExperienceState.PROSECUTION_OPENING
    mock_session_1.start_time = datetime.now()
    mock_session_1.case_id = "case_001"
    
    mock_orchestrator_1 = MagicMock(spec=ExperienceOrchestrator)
    mock_orchestrator_1.user_session = mock_session_1
    
    mock_session_2 = MagicMock(spec=UserSession)
    mock_session_2.current_state = ExperienceState.JURY_DELIBERATION
    mock_session_2.start_time = datetime.now()
    mock_session_2.case_id = "case_002"
    
    mock_orchestrator_2 = MagicMock(spec=ExperienceOrchestrator)
    mock_orchestrator_2.user_session = mock_session_2
    
    service.active_sessions = {
        "session_1": mock_orchestrator_1,
        "session_2": mock_orchestrator_2
    }
    
    # Execute command
    await service.show_sessions(group_id, admin_uid)
    
    # Verify sessions info was sent
    mock_multi_bot_client.send_as_agent.assert_called_once()
    call_args = mock_multi_bot_client.send_as_agent.call_args
    
    assert call_args[0][0] == "clerk"
    assert call_args[0][1] == group_id
    message = call_args[0][2]
    
    # Verify message contains session info
    assert "ACTIVE SESSIONS (2)" in message
    assert "session_1" in message
    assert "session_2" in message
    assert "PROSECUTION_OPENING" in message
    assert "JURY_DELIBERATION" in message
    assert "case_001" in message
    assert "case_002" in message


@pytest.mark.asyncio
async def test_sessions_command_no_active_sessions(service, mock_multi_bot_client):
    """Test /sessions command when no sessions are active."""
    group_id = "test_group"
    admin_uid = "admin_user_1"
    
    service.active_sessions = {}
    
    # Execute command
    await service.show_sessions(group_id, admin_uid)
    
    # Verify message was sent
    mock_multi_bot_client.send_as_agent.assert_called_once()
    call_args = mock_multi_bot_client.send_as_agent.call_args
    
    assert call_args[0][0] == "clerk"
    assert call_args[0][1] == group_id
    assert "No active sessions" in call_args[0][2]


@pytest.mark.asyncio
async def test_sessions_command_non_admin_denied(service, mock_multi_bot_client):
    """Test that non-admin users cannot access /sessions command."""
    group_id = "test_group"
    non_admin_uid = "regular_user"
    
    # Execute command
    await service.show_sessions(group_id, non_admin_uid)
    
    # Verify access denied message was sent
    mock_multi_bot_client.send_as_agent.assert_called_once()
    call_args = mock_multi_bot_client.send_as_agent.call_args
    
    assert call_args[0][0] == "clerk"
    assert call_args[0][1] == group_id
    assert "only available to administrators" in call_args[0][2]


@pytest.mark.asyncio
async def test_handle_command_routes_metrics(service, mock_multi_bot_client):
    """Test that /metrics command is routed correctly."""
    group_id = "test_group"
    admin_uid = "admin_user_1"
    
    with patch.object(service, "show_metrics", new_callable=AsyncMock) as mock_show_metrics:
        await service.handle_command("/metrics", group_id, admin_uid, 1)
        mock_show_metrics.assert_called_once_with(group_id, admin_uid)


@pytest.mark.asyncio
async def test_handle_command_routes_sessions(service, mock_multi_bot_client):
    """Test that /sessions command is routed correctly."""
    group_id = "test_group"
    admin_uid = "admin_user_1"
    
    with patch.object(service, "show_sessions", new_callable=AsyncMock) as mock_show_sessions:
        await service.handle_command("/sessions", group_id, admin_uid, 1)
        mock_show_sessions.assert_called_once_with(group_id, admin_uid)
