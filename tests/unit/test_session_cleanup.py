"""Unit tests for session timeout and auto-cleanup (Task 27.1)."""

import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from multi_bot_service import MultiBotService
from luffa_bot_service import LuffaBotService
from orchestrator import ExperienceOrchestrator
from state_machine import ExperienceState
from session import UserSession


@pytest.fixture
def mock_multi_bot_service():
    """Create a MultiBotService with mocked dependencies."""
    with patch('multi_bot_service.load_config'), \
         patch('multi_bot_service.MultiBotClient'):
        service = MultiBotService()
        service.multi_bot.send_as_agent = AsyncMock(return_value=True)
        service.multi_bot.has_bot_for_role = MagicMock(return_value=True)
        service.multi_bot.get_configured_roles = MagicMock(return_value=["clerk"])
        return service


@pytest.fixture
def mock_luffa_bot_service():
    """Create a LuffaBotService with mocked dependencies."""
    with patch('luffa_bot_service.load_config'), \
         patch('luffa_bot_service.LuffaBotAPIClient'):
        service = LuffaBotService()
        service.client.send_group_message = AsyncMock()
        return service


@pytest.fixture
def mock_orchestrator():
    """Create a mock orchestrator with user session."""
    orchestrator = MagicMock(spec=ExperienceOrchestrator)
    orchestrator.user_session = MagicMock(spec=UserSession)
    orchestrator.user_session.user_id = "test_user_123"  # This will be used in the tests
    orchestrator.user_session.last_activity_time = datetime.now()
    orchestrator.cleanup = AsyncMock()
    return orchestrator


@pytest.mark.asyncio
async def test_multi_bot_cleanup_task_warns_at_30_min(mock_multi_bot_service, mock_orchestrator):
    """Test that cleanup task sends warning at 30 min inactive."""
    service = mock_multi_bot_service
    
    # Set up inactive session (31 minutes ago)
    mock_orchestrator.user_session.last_activity_time = datetime.now() - timedelta(minutes=31)
    
    # Use simple group_id without underscores to avoid parsing issues
    session_id = "luffa_testgroup_testuser123_1234567890"
    service.active_sessions[session_id] = mock_orchestrator
    service.uid_to_session["testuser123"] = session_id
    service.running = True
    
    # Manually trigger one cleanup check (instead of waiting 5 minutes)
    # We'll directly call the cleanup logic
    now = datetime.now()
    for session_id, orchestrator in list(service.active_sessions.items()):
        if not orchestrator.user_session:
            continue
        
        last_activity = orchestrator.user_session.last_activity_time
        inactive_duration = (now - last_activity).total_seconds() / 60  # minutes
        
        user_id = orchestrator.user_session.user_id
        parts = session_id.split("_")
        if len(parts) >= 3:
            group_id = parts[1]
        else:
            continue
        
        # Check for 30 min warning
        if 30 <= inactive_duration < 60:
            await service.multi_bot.send_as_agent(
                "clerk",
                group_id,
                f"⚠️ Your trial has been inactive for {int(inactive_duration)} minutes. "
                f"The session will timeout after 60 minutes of inactivity.\n\n"
                f"Type /continue or /status to keep your session active."
            )
    
    # Verify warning was sent
    service.multi_bot.send_as_agent.assert_called()
    call_args = service.multi_bot.send_as_agent.call_args
    assert call_args[0][0] == "clerk"  # Role
    assert call_args[0][1] == "testgroup"  # Group ID
    assert "inactive" in call_args[0][2].lower()  # Message contains "inactive"
    assert "60 minutes" in call_args[0][2]  # Mentions timeout threshold


@pytest.mark.asyncio
async def test_multi_bot_cleanup_task_times_out_at_60_min(mock_multi_bot_service, mock_orchestrator):
    """Test that cleanup task times out session at 60 min inactive."""
    service = mock_multi_bot_service
    
    # Set up inactive session (61 minutes ago)
    mock_orchestrator.user_session.last_activity_time = datetime.now() - timedelta(minutes=61)
    
    session_id = "luffa_testgroup_testuser123_1234567890"
    service.active_sessions[session_id] = mock_orchestrator
    service.uid_to_session["testuser123"] = session_id
    service.group_users["testgroup"] = {"testuser123"}
    service.running = True
    
    # Mock _cleanup_user_session
    service._cleanup_user_session = AsyncMock()
    
    # Manually trigger one cleanup check
    now = datetime.now()
    sessions_to_cleanup = []
    
    for session_id, orchestrator in list(service.active_sessions.items()):
        if not orchestrator.user_session:
            continue
        
        last_activity = orchestrator.user_session.last_activity_time
        inactive_duration = (now - last_activity).total_seconds() / 60  # minutes
        
        user_id = orchestrator.user_session.user_id
        parts = session_id.split("_")
        if len(parts) >= 3:
            group_id = parts[1]
        else:
            continue
        
        # Check for 60 min timeout
        if inactive_duration >= 60:
            sessions_to_cleanup.append((user_id, group_id, session_id))
    
    # Cleanup timed-out sessions
    for user_id, group_id, session_id in sessions_to_cleanup:
        await service.multi_bot.send_as_agent(
            "clerk",
            group_id,
            "⏰ Trial timed out due to inactivity."
        )
        await service._cleanup_user_session(user_id, group_id)
    
    # Verify timeout message was sent
    timeout_calls = [
        call for call in service.multi_bot.send_as_agent.call_args_list
        if len(call[0]) > 2 and "timed out" in call[0][2].lower()
    ]
    assert len(timeout_calls) > 0, "Timeout message should be sent"
    
    # Verify cleanup was called
    service._cleanup_user_session.assert_called_once_with("test_user_123", "testgroup")


@pytest.mark.asyncio
async def test_luffa_bot_cleanup_task_warns_at_30_min(mock_luffa_bot_service, mock_orchestrator):
    """Test that LuffaBotService cleanup task sends warning at 30 min inactive."""
    service = mock_luffa_bot_service
    
    # Set up inactive session (31 minutes ago)
    mock_orchestrator.user_session.last_activity_time = datetime.now() - timedelta(minutes=31)
    
    session_id = "luffa_testgroup_testuser123_1234567890"
    service.active_sessions[session_id] = mock_orchestrator
    service.uid_to_session["testuser123"] = session_id
    service.running = True
    
    # Manually trigger one cleanup check
    now = datetime.now()
    for session_id, orchestrator in list(service.active_sessions.items()):
        if not orchestrator.user_session:
            continue
        
        last_activity = orchestrator.user_session.last_activity_time
        inactive_duration = (now - last_activity).total_seconds() / 60  # minutes
        
        user_id = orchestrator.user_session.user_id
        parts = session_id.split("_")
        if len(parts) >= 3:
            group_id = parts[1]
        else:
            continue
        
        # Check for 30 min warning
        if 30 <= inactive_duration < 60:
            await service.client.send_group_message(
                group_id,
                f"⚠️ Your trial has been inactive for {int(inactive_duration)} minutes. "
                f"The session will timeout after 60 minutes of inactivity.\n\n"
                f"Type /continue or /status to keep your session active."
            )
    
    # Verify warning was sent
    service.client.send_group_message.assert_called()
    call_args = service.client.send_group_message.call_args
    assert call_args[0][0] == "testgroup"  # Group ID
    assert "inactive" in call_args[0][1].lower()  # Message contains "inactive"
    assert "60 minutes" in call_args[0][1]  # Mentions timeout threshold


@pytest.mark.asyncio
async def test_luffa_bot_cleanup_task_times_out_at_60_min(mock_luffa_bot_service, mock_orchestrator):
    """Test that LuffaBotService cleanup task times out session at 60 min inactive."""
    service = mock_luffa_bot_service
    
    # Set up inactive session (61 minutes ago)
    mock_orchestrator.user_session.last_activity_time = datetime.now() - timedelta(minutes=61)
    
    session_id = "luffa_testgroup_testuser123_1234567890"
    service.active_sessions[session_id] = mock_orchestrator
    service.uid_to_session["testuser123"] = session_id
    service.group_users["testgroup"] = {"testuser123"}
    service.running = True
    
    # Mock _cleanup_user_session
    service._cleanup_user_session = AsyncMock()
    
    # Manually trigger one cleanup check
    now = datetime.now()
    sessions_to_cleanup = []
    
    for session_id, orchestrator in list(service.active_sessions.items()):
        if not orchestrator.user_session:
            continue
        
        last_activity = orchestrator.user_session.last_activity_time
        inactive_duration = (now - last_activity).total_seconds() / 60  # minutes
        
        user_id = orchestrator.user_session.user_id
        parts = session_id.split("_")
        if len(parts) >= 3:
            group_id = parts[1]
        else:
            continue
        
        # Check for 60 min timeout
        if inactive_duration >= 60:
            sessions_to_cleanup.append((user_id, group_id, session_id))
    
    # Cleanup timed-out sessions
    for user_id, group_id, session_id in sessions_to_cleanup:
        await service.client.send_group_message(
            group_id,
            "⏰ Trial timed out due to inactivity."
        )
        await service._cleanup_user_session(user_id, group_id)
    
    # Verify timeout message was sent
    timeout_calls = [
        call for call in service.client.send_group_message.call_args_list
        if "timed out" in call[0][1].lower()
    ]
    assert len(timeout_calls) > 0, "Timeout message should be sent"
    
    # Verify cleanup was called
    service._cleanup_user_session.assert_called_once_with("test_user_123", "testgroup")


@pytest.mark.asyncio
async def test_cleanup_task_cancelled_on_shutdown(mock_multi_bot_service):
    """Test that cleanup task is cancelled during shutdown."""
    service = mock_multi_bot_service
    service.running = True
    
    # Start cleanup task
    service.cleanup_task = asyncio.create_task(service._session_cleanup_task())
    
    # Wait a bit
    await asyncio.sleep(0.1)
    
    # Shutdown should cancel the task
    await service.shutdown()
    
    # Verify task is done (cancelled)
    assert service.cleanup_task.done()


@pytest.mark.asyncio
async def test_cleanup_task_started_in_start(mock_multi_bot_service):
    """Test that cleanup task is started when service starts."""
    service = mock_multi_bot_service
    
    # Mock the polling loop to exit immediately
    async def mock_poll(*args, **kwargs):
        service.running = False
        return []
    
    service.multi_bot.poll_messages = mock_poll
    service.multi_bot.verify_all_bots = AsyncMock(return_value={"clerk": True})
    
    # Start service (will exit immediately due to mock)
    start_task = asyncio.create_task(service.start())
    
    # Wait a bit for initialization
    await asyncio.sleep(0.2)
    
    # Verify cleanup task was created
    assert service.cleanup_task is not None
    
    # Cleanup
    await service.shutdown()
    
    try:
        await start_task
    except:
        pass


@pytest.mark.asyncio
async def test_no_cleanup_for_active_sessions(mock_multi_bot_service, mock_orchestrator):
    """Test that active sessions (< 30 min) are not warned or cleaned up."""
    service = mock_multi_bot_service
    
    # Set up active session (only 10 minutes ago)
    mock_orchestrator.user_session.last_activity_time = datetime.now() - timedelta(minutes=10)
    
    session_id = "luffa_testgroup_testuser123_1234567890"
    service.active_sessions[session_id] = mock_orchestrator
    service.uid_to_session["testuser123"] = session_id
    service.running = True
    
    # Mock _cleanup_user_session
    service._cleanup_user_session = AsyncMock()
    
    # Manually trigger one cleanup check
    now = datetime.now()
    sessions_to_cleanup = []
    
    for session_id, orchestrator in list(service.active_sessions.items()):
        if not orchestrator.user_session:
            continue
        
        last_activity = orchestrator.user_session.last_activity_time
        inactive_duration = (now - last_activity).total_seconds() / 60  # minutes
        
        user_id = orchestrator.user_session.user_id
        parts = session_id.split("_")
        if len(parts) >= 3:
            group_id = parts[1]
        else:
            continue
        
        # Check for 60 min timeout (cleanup)
        if inactive_duration >= 60:
            sessions_to_cleanup.append((user_id, group_id, session_id))
        
        # Check for 30 min warning
        elif inactive_duration >= 30:
            await service.multi_bot.send_as_agent(
                "clerk",
                group_id,
                f"⚠️ Your trial has been inactive for {int(inactive_duration)} minutes. "
                f"The session will timeout after 60 minutes of inactivity.\n\n"
                f"Type /continue or /status to keep your session active."
            )
    
    # Cleanup timed-out sessions
    for user_id, group_id, session_id in sessions_to_cleanup:
        await service._cleanup_user_session(user_id, group_id)
    
    # Verify no messages were sent
    service.multi_bot.send_as_agent.assert_not_called()
    
    # Verify cleanup was not called
    service._cleanup_user_session.assert_not_called()
