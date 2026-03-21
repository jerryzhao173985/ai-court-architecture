"""Unit tests for message polling loop in orchestrator (Task 22.1)."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.orchestrator import ExperienceOrchestrator
from src.state_machine import ExperienceState
from src.config import AppConfig, LLMConfig, LuffaConfig


@pytest.fixture
def mock_config():
    """Create mock configuration."""
    return AppConfig(
        llm=LLMConfig(
            provider="openai",
            api_key="test-key",
            model="gpt-4"
        ),
        luffa=LuffaConfig(
            api_base_url="https://apibot.luffa.im/robot",
            api_key="test-secret",
            bot_enabled=True
        )
    )


@pytest.fixture
async def orchestrator(mock_config):
    """Create orchestrator instance with mocked dependencies."""
    with patch('src.orchestrator.LLMService'), \
         patch('src.orchestrator.LuffaAPIClient') as mock_client:
        
        # Mock the client's receive_messages method
        mock_client_instance = AsyncMock()
        mock_client_instance.receive_messages = AsyncMock(return_value=[])
        mock_client_instance.send_group_message = AsyncMock()
        mock_client_instance.send_dm = AsyncMock()
        mock_client.return_value = mock_client_instance
        
        orch = ExperienceOrchestrator(
            session_id="test-session",
            user_id="test-user",
            case_id="blackthorn-hall-001",
            config=mock_config
        )
        
        # Replace the client with our mock
        orch.luffa_client = mock_client_instance
        
        yield orch
        
        # Cleanup
        if orch._polling_active:
            await orch.stop_message_polling()


@pytest.mark.asyncio
async def test_start_message_polling(orchestrator):
    """Test starting the message polling loop."""
    # Start polling
    await orchestrator.start_message_polling()
    
    # Verify polling is active
    assert orchestrator._polling_active is True
    assert orchestrator._polling_task is not None
    
    # Wait a bit to ensure loop runs
    await asyncio.sleep(0.1)
    
    # Stop polling
    await orchestrator.stop_message_polling()
    
    # Verify polling stopped
    assert orchestrator._polling_active is False


@pytest.mark.asyncio
async def test_stop_message_polling(orchestrator):
    """Test stopping the message polling loop."""
    # Start polling
    await orchestrator.start_message_polling()
    assert orchestrator._polling_active is True
    
    # Stop polling
    await orchestrator.stop_message_polling()
    
    # Verify stopped
    assert orchestrator._polling_active is False
    assert orchestrator._polling_task is None


@pytest.mark.asyncio
async def test_polling_loop_calls_receive_messages(orchestrator):
    """Test that polling loop calls receive_messages every second."""
    # Start polling
    await orchestrator.start_message_polling()
    
    # Wait for at least 2 polling cycles (2+ seconds)
    await asyncio.sleep(2.5)
    
    # Stop polling
    await orchestrator.stop_message_polling()
    
    # Verify receive_messages was called multiple times
    assert orchestrator.luffa_client.receive_messages.call_count >= 2


@pytest.mark.asyncio
async def test_message_deduplication(orchestrator):
    """Test that message deduplication works (handled by client)."""
    # Mock messages with duplicate msgId
    messages = [
        {
            "uid": "group-123",
            "type": 1,
            "text": "/help",
            "msgId": "msg-001",
            "sender_uid": "user-456",
            "atList": [],
            "urlLink": None
        }
    ]
    
    # The client's receive_messages already handles deduplication
    # We just verify it returns the messages
    orchestrator.luffa_client.receive_messages.return_value = messages
    
    # Start polling
    await orchestrator.start_message_polling()
    
    # Wait for one cycle
    await asyncio.sleep(1.5)
    
    # Stop polling
    await orchestrator.stop_message_polling()
    
    # Verify receive_messages was called
    assert orchestrator.luffa_client.receive_messages.called


@pytest.mark.asyncio
async def test_route_command_message(orchestrator):
    """Test routing of command messages."""
    # Mock a command message
    messages = [
        {
            "uid": "group-123",
            "type": 1,
            "text": "/help",
            "msgId": "msg-001",
            "sender_uid": "user-456",
            "atList": [],
            "urlLink": None
        }
    ]
    
    orchestrator.luffa_client.receive_messages.return_value = messages
    
    # Start polling
    await orchestrator.start_message_polling()
    
    # Wait for message to be processed
    await asyncio.sleep(1.5)
    
    # Stop polling
    await orchestrator.stop_message_polling()
    
    # Verify send_group_message was called (help response)
    assert orchestrator.luffa_client.send_group_message.called


@pytest.mark.asyncio
async def test_route_deliberation_message(orchestrator):
    """Test routing of deliberation messages."""
    # Initialize orchestrator
    with patch.object(orchestrator, 'initialize', new_callable=AsyncMock) as mock_init:
        mock_init.return_value = {"success": True, "greeting": {"content": "Welcome"}}
        await orchestrator.initialize()
    
    # Set state to deliberation
    with patch.object(orchestrator, 'state_machine') as mock_sm:
        mock_sm.current_state = ExperienceState.JURY_DELIBERATION
        
        # Mock submit_deliberation_statement
        with patch.object(orchestrator, 'submit_deliberation_statement', new_callable=AsyncMock) as mock_submit:
            mock_submit.return_value = {
                "success": True,
                "turns": [{"statement": "User statement"}],
                "deliberation_ended": False
            }
            
            # Mock a deliberation message
            messages = [
                {
                    "uid": "group-123",
                    "type": 1,
                    "text": "I think the defendant is guilty based on the evidence.",
                    "msgId": "msg-002",
                    "sender_uid": "user-456",
                    "atList": [],
                    "urlLink": None
                }
            ]
            
            orchestrator.luffa_client.receive_messages.return_value = messages
            
            # Start polling
            await orchestrator.start_message_polling()
            
            # Wait for message to be processed
            await asyncio.sleep(1.5)
            
            # Stop polling
            await orchestrator.stop_message_polling()
            
            # Verify submit_deliberation_statement was called
            assert mock_submit.called


@pytest.mark.asyncio
async def test_polling_loop_error_handling(orchestrator):
    """Test that polling loop handles errors gracefully."""
    # Make receive_messages raise an error
    orchestrator.luffa_client.receive_messages.side_effect = Exception("Network error")
    
    # Start polling
    await orchestrator.start_message_polling()
    
    # Wait for error to occur and backoff
    await asyncio.sleep(1.5)
    
    # Verify polling is still active (didn't crash)
    assert orchestrator._polling_active is True
    
    # Stop polling
    await orchestrator.stop_message_polling()


@pytest.mark.asyncio
async def test_register_custom_message_handler(orchestrator):
    """Test registering custom message handlers."""
    # Create a custom handler
    custom_handler = AsyncMock()
    
    # Register handler for a specific group
    orchestrator.register_message_handler("group-123", custom_handler)
    
    # Verify handler is registered
    assert "group-123" in orchestrator._message_handlers
    assert orchestrator._message_handlers["group-123"] == custom_handler
    
    # Unregister handler
    orchestrator.unregister_message_handler("group-123")
    
    # Verify handler is removed
    assert "group-123" not in orchestrator._message_handlers


@pytest.mark.asyncio
async def test_handle_start_command(orchestrator):
    """Test /start command handling."""
    # Mock initialize and start_experience
    with patch.object(orchestrator, 'initialize', new_callable=AsyncMock) as mock_init, \
         patch.object(orchestrator, 'start_experience', new_callable=AsyncMock) as mock_start:
        
        mock_init.return_value = {
            "success": True,
            "greeting": {"content": "Welcome to VERITAS"}
        }
        
        mock_start.return_value = {
            "success": True,
            "hook_content": {"content": "A dark and stormy night..."},
            "announcement": {"content": "Hook Scene"}
        }
        
        # Simulate /start command
        msg = {
            "uid": "group-123",
            "type": 1,
            "text": "/start",
            "msgId": "msg-003"
        }
        
        await orchestrator._handle_command_message(msg)
        
        # Verify initialize and start_experience were called
        assert mock_init.called
        assert mock_start.called
        
        # Verify at least one message was sent
        assert orchestrator.luffa_client.send_group_message.call_count >= 1


@pytest.mark.asyncio
async def test_handle_vote_command(orchestrator):
    """Test /vote command handling."""
    # Mock submit_vote
    with patch.object(orchestrator, 'submit_vote', new_callable=AsyncMock) as mock_vote:
        mock_vote.return_value = {
            "success": True,
            "dual_reveal": {
                "verdict": {
                    "verdict": "guilty",
                    "guiltyCount": 5,
                    "notGuiltyCount": 3
                },
                "groundTruth": {
                    "actualVerdict": "not_guilty",
                    "explanation": "The defendant was innocent."
                },
                "reasoningAssessment": {
                    "category": "sound_incorrect",
                    "evidenceScore": 0.8,
                    "coherenceScore": 0.9,
                    "feedback": "Good reasoning, wrong verdict."
                }
            }
        }
        
        # Simulate /vote command
        msg = {
            "uid": "group-123",
            "type": 1,
            "text": "/vote guilty",
            "msgId": "msg-004"
        }
        
        await orchestrator._handle_command_message(msg)
        
        # Verify submit_vote was called
        assert mock_vote.called
        assert mock_vote.call_args[0][0] == "guilty"
        
        # Verify dual reveal messages were sent
        assert orchestrator.luffa_client.send_group_message.call_count >= 4


@pytest.mark.asyncio
async def test_polling_interval_is_one_second(orchestrator):
    """Test that polling interval is exactly 1 second."""
    call_times = []
    
    # Track when receive_messages is called
    async def track_call():
        call_times.append(asyncio.get_event_loop().time())
        return []
    
    orchestrator.luffa_client.receive_messages = track_call
    
    # Start polling
    await orchestrator.start_message_polling()
    
    # Wait for 3 calls
    await asyncio.sleep(3.5)
    
    # Stop polling
    await orchestrator.stop_message_polling()
    
    # Verify at least 3 calls occurred
    assert len(call_times) >= 3
    
    # Verify intervals are approximately 1 second
    if len(call_times) >= 2:
        intervals = [call_times[i+1] - call_times[i] for i in range(len(call_times)-1)]
        for interval in intervals:
            # Allow some tolerance (0.9 to 1.2 seconds)
            assert 0.9 <= interval <= 1.2, f"Interval {interval} is not close to 1 second"


@pytest.mark.asyncio
async def test_handle_help_command(orchestrator):
    """Test /help command handling."""
    # Simulate /help command
    msg = {
        "uid": "group-123",
        "type": 1,
        "text": "/help",
        "msgId": "msg-005"
    }
    
    await orchestrator._handle_command_message(msg)
    
    # Verify help message was sent
    assert orchestrator.luffa_client.send_group_message.called
    
    # Get the sent message
    call_args = orchestrator.luffa_client.send_group_message.call_args
    sent_message = call_args[0][1]
    
    # Verify help text contains key information
    assert "VERITAS COURTROOM EXPERIENCE" in sent_message
    assert "/start" in sent_message
    assert "/vote" in sent_message
    assert "/help" in sent_message
    assert "/continue" in sent_message
    assert "/evidence" in sent_message
    assert "/status" in sent_message


@pytest.mark.asyncio
async def test_handle_invalid_command(orchestrator):
    """Test error handling for invalid commands."""
    # Simulate invalid command
    msg = {
        "uid": "group-123",
        "type": 1,
        "text": "/invalid_command",
        "msgId": "msg-006"
    }
    
    await orchestrator._handle_command_message(msg)
    
    # Verify error message was sent
    assert orchestrator.luffa_client.send_group_message.called
    
    # Get the sent message
    call_args = orchestrator.luffa_client.send_group_message.call_args
    sent_message = call_args[0][1]
    
    # Verify error message contains appropriate text
    assert "Unknown command" in sent_message
    assert "/invalid_command" in sent_message
    assert "/help" in sent_message


@pytest.mark.asyncio
async def test_handle_vote_command_invalid_vote(orchestrator):
    """Test /vote command with invalid vote value."""
    # Simulate /vote command with invalid value
    msg = {
        "uid": "group-123",
        "type": 1,
        "text": "/vote maybe",
        "msgId": "msg-007"
    }
    
    await orchestrator._handle_command_message(msg)
    
    # Verify error message was sent
    assert orchestrator.luffa_client.send_group_message.called
    
    # Get the sent message
    call_args = orchestrator.luffa_client.send_group_message.call_args
    sent_message = call_args[0][1]
    
    # Verify error message contains appropriate text
    assert "Invalid vote" in sent_message
    assert "/vote guilty" in sent_message
    assert "/vote not_guilty" in sent_message


@pytest.mark.asyncio
async def test_handle_vote_command_missing_argument(orchestrator):
    """Test /vote command without vote argument."""
    # Simulate /vote command without argument
    msg = {
        "uid": "group-123",
        "type": 1,
        "text": "/vote",
        "msgId": "msg-008"
    }
    
    await orchestrator._handle_command_message(msg)
    
    # Verify error message was sent
    assert orchestrator.luffa_client.send_group_message.called
    
    # Get the sent message
    call_args = orchestrator.luffa_client.send_group_message.call_args
    sent_message = call_args[0][1]
    
    # Verify error message contains appropriate text
    assert "Invalid vote" in sent_message


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
