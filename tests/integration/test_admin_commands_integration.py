"""Integration tests for admin commands."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.multi_bot_service import MultiBotService
from src.orchestrator import ExperienceOrchestrator
from src.session import UserSession
from src.state_machine import ExperienceState
from src.metrics import get_metrics_collector, reset_metrics


@pytest.fixture
def mock_config_with_admin():
    """Create mock configuration with admin users."""
    config = MagicMock()
    config.admin_uids = ["admin_123", "admin_456"]
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
def service_with_admin(mock_config_with_admin, mock_multi_bot_client):
    """Create MultiBotService instance with admin configuration."""
    with patch("src.multi_bot_service.load_config", return_value=mock_config_with_admin):
        with patch("src.multi_bot_service.MultiBotClient", return_value=mock_multi_bot_client):
            service = MultiBotService()
            return service


@pytest.mark.asyncio
async def test_admin_workflow_metrics_and_sessions(service_with_admin, mock_multi_bot_client):
    """Test complete admin workflow: check metrics and sessions."""
    # Reset metrics for clean test
    reset_metrics()
    
    group_id = "test_group_123"
    admin_uid = "admin_123"
    
    # Simulate some metrics being collected
    collector = get_metrics_collector()
    await collector.start_session("session_1", "case_001")
    
    # Create mock active session
    mock_session = MagicMock(spec=UserSession)
    mock_session.current_state = ExperienceState.PROSECUTION_OPENING
    mock_session.start_time = datetime.now()
    mock_session.case_id = "case_001"
    
    mock_orchestrator = MagicMock(spec=ExperienceOrchestrator)
    mock_orchestrator.user_session = mock_session
    
    service_with_admin.active_sessions = {
        "session_1": mock_orchestrator
    }
    
    # Test /sessions command
    await service_with_admin.show_sessions(group_id, admin_uid)
    
    # Verify sessions message was sent
    assert mock_multi_bot_client.send_as_agent.call_count == 1
    sessions_call = mock_multi_bot_client.send_as_agent.call_args_list[0]
    assert sessions_call[0][0] == "clerk"
    assert sessions_call[0][1] == group_id
    sessions_message = sessions_call[0][2]
    assert "ACTIVE SESSIONS (1)" in sessions_message
    assert "session_1" in sessions_message
    
    # Reset mock
    mock_multi_bot_client.send_as_agent.reset_mock()
    
    # Test /metrics command
    await service_with_admin.show_metrics(group_id, admin_uid)
    
    # Verify metrics message was sent
    assert mock_multi_bot_client.send_as_agent.call_count == 1
    metrics_call = mock_multi_bot_client.send_as_agent.call_args_list[0]
    assert metrics_call[0][0] == "clerk"
    assert metrics_call[0][1] == group_id
    metrics_message = metrics_call[0][2]
    assert "VERITAS PERFORMANCE METRICS" in metrics_message
    assert "Sessions:" in metrics_message


@pytest.mark.asyncio
async def test_non_admin_cannot_access_commands(service_with_admin, mock_multi_bot_client):
    """Test that non-admin users are denied access to admin commands."""
    group_id = "test_group_123"
    non_admin_uid = "regular_user_789"
    
    # Try /metrics
    await service_with_admin.show_metrics(group_id, non_admin_uid)
    
    # Verify access denied
    assert mock_multi_bot_client.send_as_agent.call_count == 1
    call = mock_multi_bot_client.send_as_agent.call_args_list[0]
    assert "only available to administrators" in call[0][2]
    
    # Reset mock
    mock_multi_bot_client.send_as_agent.reset_mock()
    
    # Try /sessions
    await service_with_admin.show_sessions(group_id, non_admin_uid)
    
    # Verify access denied
    assert mock_multi_bot_client.send_as_agent.call_count == 1
    call = mock_multi_bot_client.send_as_agent.call_args_list[0]
    assert "only available to administrators" in call[0][2]


@pytest.mark.asyncio
async def test_handle_command_integration(service_with_admin, mock_multi_bot_client):
    """Test that admin commands are properly routed through handle_command."""
    group_id = "test_group_123"
    admin_uid = "admin_456"
    
    # Create mock session for /sessions command
    mock_session = MagicMock(spec=UserSession)
    mock_session.current_state = ExperienceState.JURY_DELIBERATION
    mock_session.start_time = datetime.now()
    mock_session.case_id = "case_002"
    
    mock_orchestrator = MagicMock(spec=ExperienceOrchestrator)
    mock_orchestrator.user_session = mock_session
    
    service_with_admin.active_sessions = {
        "session_2": mock_orchestrator
    }
    
    # Test /metrics through handle_command
    await service_with_admin.handle_command("/metrics", group_id, admin_uid, 1)
    
    # Verify metrics was called
    assert mock_multi_bot_client.send_as_agent.call_count == 1
    metrics_call = mock_multi_bot_client.send_as_agent.call_args_list[0]
    assert "VERITAS PERFORMANCE METRICS" in metrics_call[0][2]
    
    # Reset mock
    mock_multi_bot_client.send_as_agent.reset_mock()
    
    # Test /sessions through handle_command
    await service_with_admin.handle_command("/sessions", group_id, admin_uid, 1)
    
    # Verify sessions was called
    assert mock_multi_bot_client.send_as_agent.call_count == 1
    sessions_call = mock_multi_bot_client.send_as_agent.call_args_list[0]
    assert "ACTIVE SESSIONS (1)" in sessions_call[0][2]
    assert "session_2" in sessions_call[0][2]
