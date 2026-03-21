# Task 22.2: Command Handlers Implementation

## Overview

Task 22.2 completes the Luffa Bot integration by implementing command handlers for user interactions. Building on the polling loop from task 22.1, these handlers process user commands and provide appropriate responses via Luffa Bot.

## Implementation Status

✅ **COMPLETE** - All command handlers were already implemented in `src/orchestrator.py` as part of task 22.1. Task 22.2 added comprehensive test coverage.

## Command Handlers Implemented

### 1. `/start` Command (Lines 637-654)
**Purpose**: Begin a new trial experience

**Implementation**:
- Initializes the orchestrator if not already done
- Starts the experience by transitioning to hook scene
- Sends hook scene content to user
- Prompts user to continue

**Error Handling**:
- Handles initialization failures
- Provides clear error messages to user

### 2. `/vote` Command (Lines 684-721)
**Purpose**: Submit user's verdict

**Implementation**:
- Validates vote argument (must be "guilty" or "not_guilty")
- Collects votes from all jurors
- Evaluates user's reasoning
- Assembles and presents dual reveal
- Shows verdict, ground truth, and reasoning assessment

**Error Handling**:
- Validates vote format
- Provides usage instructions for invalid votes
- Handles missing vote arguments
- Handles vote submission failures

### 3. `/help` Command (Lines 750-771)
**Purpose**: Provide procedural guidance

**Implementation**:
- Displays comprehensive help text
- Lists all available commands
- Explains the experience flow
- Uses clear formatting with emojis

**Content Includes**:
- Command list with descriptions
- Step-by-step experience flow
- Usage examples

### 4. Invalid Command Handling (Line 603)
**Purpose**: Handle unrecognized commands gracefully

**Implementation**:
- Detects commands not in the recognized list
- Sends friendly error message
- Suggests using `/help` for available commands
- Includes the invalid command in the error message

## Additional Command Handlers

The implementation also includes these supporting commands:

- `/continue` - Advance to next trial stage
- `/evidence` - View evidence board
- `/status` - Check trial progress

## Test Coverage

Added comprehensive tests in `tests/unit/test_message_polling.py`:

### New Tests Added

1. **test_handle_help_command**
   - Verifies help message is sent
   - Checks all commands are listed
   - Validates message formatting

2. **test_handle_invalid_command**
   - Tests error handling for unrecognized commands
   - Verifies error message content
   - Checks help suggestion is included

3. **test_handle_vote_command_invalid_vote**
   - Tests invalid vote values (e.g., "maybe")
   - Verifies error message with usage instructions
   - Checks both valid options are shown

4. **test_handle_vote_command_missing_argument**
   - Tests `/vote` without argument
   - Verifies appropriate error message
   - Checks usage instructions are provided

### Existing Tests (from Task 22.1)

- test_handle_start_command
- test_handle_vote_command
- test_route_command_message
- test_polling_loop_calls_receive_messages
- test_message_deduplication
- test_polling_loop_error_handling

## Test Results

All 15 tests pass successfully:

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
tests/unit/test_message_polling.py::test_handle_help_command PASSED
tests/unit/test_message_polling.py::test_handle_invalid_command PASSED
tests/unit/test_message_polling.py::test_handle_vote_command_invalid_vote PASSED
tests/unit/test_message_polling.py::test_handle_vote_command_missing_argument PASSED

15 passed in 16.38s
```

## Requirements Validation

### Requirement 13.4: Procedural Question Response
✅ **SATISFIED** - `/help` command provides comprehensive procedural guidance

**Evidence**:
- Help text includes all commands
- Explains experience flow
- Provides clear usage instructions
- Responds within 5 seconds (async handler)

### Error Handling Requirements
✅ **SATISFIED** - All command handlers include error handling

**Evidence**:
- Invalid commands return helpful error messages
- Invalid vote values are validated
- Missing arguments are detected
- All errors suggest using `/help`

## Integration with Orchestrator

The command handlers integrate seamlessly with the orchestrator's existing methods:

1. **State Management**: Handlers check current state before executing actions
2. **Component Coordination**: Handlers call appropriate orchestrator methods
3. **Message Routing**: Commands are routed through `_handle_command_message()`
4. **Response Delivery**: All responses use `_send_message()` helper

## Message Flow

```
User sends command
    ↓
Polling loop receives message
    ↓
_route_message() checks if command
    ↓
_handle_command_message() parses command
    ↓
Specific handler (_handle_start_command, etc.)
    ↓
Orchestrator method (initialize, start_experience, etc.)
    ↓
_send_message() sends response to user
```

## Error Handling Strategy

All command handlers follow consistent error handling:

1. **Validation**: Check arguments before processing
2. **Clear Messages**: Provide specific error descriptions
3. **Guidance**: Suggest correct usage or `/help`
4. **Graceful Degradation**: Continue operation after errors
5. **Logging**: Errors logged via error_handler

## Next Steps

Task 22.2 is complete. The next task (22.3) will implement group message broadcasting for trial stages.

## Files Modified

- `tests/unit/test_message_polling.py` - Added 4 new tests for command handlers

## Files Reviewed (No Changes Needed)

- `src/orchestrator.py` - Command handlers already implemented
- `.kiro/specs/veritas-courtroom-experience/requirements.md` - Requirements verified
- `.kiro/specs/veritas-courtroom-experience/design.md` - Design reviewed
- `.kiro/specs/veritas-courtroom-experience/tasks.md` - Task details confirmed
