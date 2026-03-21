# Task 22.1: Message Polling Loop Implementation

## Overview

Implemented a background message polling loop in the `ExperienceOrchestrator` class that enables real-time message handling from Luffa Bot. This allows the orchestrator to autonomously receive and process messages without requiring external coordination.

## Implementation Details

### Core Features

1. **Background Polling Task**
   - Polls the `/receive` endpoint every 1 second
   - Runs as an asyncio background task
   - Can be started and stopped independently

2. **Message Parsing and Routing**
   - Automatically parses incoming messages
   - Routes commands (starting with `/`) to command handlers
   - Routes regular messages to deliberation handlers
   - Supports custom message handlers per user/group

3. **Message Deduplication**
   - Deduplication handled by `LuffaAPIClient` using `seen_message_ids` set
   - Prevents duplicate processing of the same message
   - Automatically prunes old message IDs to prevent memory growth

### API Methods

#### Starting and Stopping

```python
# Start the polling loop
await orchestrator.start_message_polling()

# Stop the polling loop
await orchestrator.stop_message_polling()
```

#### Custom Message Handlers

```python
# Register a custom handler for a specific group
async def my_handler(msg: dict):
    print(f"Received: {msg.get('text')}")

orchestrator.register_message_handler("group-123", my_handler)

# Unregister when done
orchestrator.unregister_message_handler("group-123")
```

### Supported Commands

The polling loop automatically handles these commands:

- `/start` - Begin a new trial
- `/continue` - Advance to next trial stage
- `/vote guilty|not_guilty` - Cast a vote
- `/evidence` - View evidence board
- `/status` - Check trial progress
- `/help` - Show help message

### Message Flow

```
Luffa Bot API
    ↓
receive_messages() [every 1 second]
    ↓
Message Deduplication (by msgId)
    ↓
_route_message()
    ↓
    ├─→ Command? → _handle_command_message()
    │                ↓
    │                ├─→ /start → _handle_start_command()
    │                ├─→ /continue → _handle_continue_command()
    │                ├─→ /vote → _handle_vote_command()
    │                ├─→ /evidence → _handle_evidence_command()
    │                ├─→ /status → _handle_status_command()
    │                └─→ /help → _handle_help_command()
    │
    └─→ Regular message → Custom handler or deliberation handler
```

## Requirements Satisfied

- **Requirement 13.1**: Luffa Bot greets users and explains the experience
- **Requirement 13.2**: Luffa Bot announces stage transitions
- **Requirement 13.4**: Luffa Bot responds to procedural questions

## Testing

### Unit Tests

Created comprehensive unit tests in `tests/unit/test_message_polling.py`:

- ✅ `test_start_message_polling` - Verify polling starts correctly
- ✅ `test_stop_message_polling` - Verify polling stops correctly
- ✅ `test_polling_loop_calls_receive_messages` - Verify polling frequency
- ✅ `test_message_deduplication` - Verify deduplication works
- ✅ `test_route_command_message` - Verify command routing
- ✅ `test_route_deliberation_message` - Verify deliberation routing
- ✅ `test_polling_loop_error_handling` - Verify error resilience
- ✅ `test_register_custom_message_handler` - Verify custom handlers
- ✅ `test_handle_start_command` - Verify /start command
- ✅ `test_handle_vote_command` - Verify /vote command
- ✅ `test_polling_interval_is_one_second` - Verify 1-second interval

All tests pass successfully.

### Test Results

```
tests/unit/test_message_polling.py::test_start_message_polling PASSED
tests/unit/test_message_polling.py::test_stop_message_polling PASSED
tests/unit/test_message_polling.py::test_polling_loop_calls_receive_messages PASSED
tests/unit/test_message_polling.py::test_message_deduplication PASSED
tests/unit/test_message_polling.py::test_route_command_message PASSED
tests/unit/test_message_polling.py::test_route_deliberation_message PASSED
tests/unit/test_message_polling.py::test_polling_loop_error_handling PASSED
tests/unit/test_message_polling.py::test_register_custom_message_handler PASSED
tests/unit/test_message_polling.py::test_handle_start_command PASSED
tests/unit/test_message_polling.py::test_handle_vote_command PASSED
tests/unit/test_message_polling.py::test_polling_interval_is_one_second PASSED

11 passed in 16.44s
```

## Usage Example

See `examples/polling_loop_demo.py` for a complete demonstration:

```python
from src.orchestrator import ExperienceOrchestrator
from src.config import load_config

# Create orchestrator
config = load_config()
orchestrator = ExperienceOrchestrator(
    session_id="session-001",
    user_id="user-123",
    case_id="blackthorn-hall-001",
    config=config
)

# Initialize
await orchestrator.initialize()

# Start polling loop
await orchestrator.start_message_polling()

# Messages are now automatically processed
# ...

# Stop when done
await orchestrator.stop_message_polling()
```

## Error Handling

The polling loop includes robust error handling:

1. **Network Errors**: Backs off for 5 seconds on error, then retries
2. **Message Processing Errors**: Logs error but continues polling
3. **Graceful Shutdown**: Properly cancels background task on stop

## Performance Considerations

- **Polling Interval**: 1 second (configurable if needed)
- **Memory Management**: Message ID deduplication set is pruned at 10,000 entries
- **Concurrency**: Uses asyncio for non-blocking operation
- **Error Backoff**: 5-second delay after errors to avoid tight error loops

## Integration with Existing Code

The polling loop integrates seamlessly with:

- `LuffaBotService` - Can use orchestrator's polling or run its own
- `LuffaAPIClient` - Handles actual API calls and deduplication
- `StateMachine` - Respects current state for message routing
- `JuryOrchestrator` - Routes deliberation messages appropriately

## Future Enhancements

Potential improvements for future tasks:

1. Configurable polling interval
2. Message priority queue
3. Rate limiting for outgoing messages
4. Message history/logging
5. Webhook support as alternative to polling

## Related Files

- `src/orchestrator.py` - Main implementation
- `src/luffa_client.py` - API client with deduplication
- `src/luffa_bot_service.py` - Alternative service-based implementation
- `tests/unit/test_message_polling.py` - Unit tests
- `examples/polling_loop_demo.py` - Usage demonstration

## Conclusion

Task 22.1 is complete. The message polling loop is fully implemented, tested, and documented. The orchestrator can now autonomously receive and process Luffa Bot messages with proper deduplication and error handling.
