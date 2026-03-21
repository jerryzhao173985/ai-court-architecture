# Task 22.3: Group Message Broadcasting for Trial Stages

## Overview

Implemented group message broadcasting with visual formatting (emojis and structure) and interactive buttons for trial stage transitions. This enhancement improves the user experience in group chats by providing clear, visually appealing stage announcements with contextual action buttons.

## Implementation Details

### 1. Enhanced Stage Announcements with Visual Formatting

Updated `LuffaBot.announce_stage()` in `src/luffa_integration.py` to include:
- **Emojis** for each stage to provide visual cues
- **Structured formatting** with clear headers and descriptions
- **Consistent styling** across all trial stages

#### Stage Emoji Mapping:
- 🎭 Hook Scene - "THE TRIAL BEGINS"
- ⚖️ Charge Reading - "CHARGE READING"
- 👔 Prosecution Opening - "PROSECUTION OPENING"
- 🛡️ Defence Opening - "DEFENCE OPENING"
- 📋 Evidence Presentation - "EVIDENCE PRESENTATION"
- ❓ Cross-Examination - "CROSS-EXAMINATION"
- 👔 Prosecution Closing - "PROSECUTION CLOSING"
- 🛡️ Defence Closing - "DEFENCE CLOSING"
- ⚖️ Judge's Summing Up - "JUDGE'S SUMMING UP"
- 🗣️ Jury Deliberation - "JURY DELIBERATION"
- 🗳️ Anonymous Vote - "TIME TO VOTE"
- 📊 Verdict Reveal - "VERDICT REVEAL"
- ✅ Completed - "TRIAL COMPLETE"

### 2. Interactive Button System

Implemented `LuffaBot.broadcast_stage_to_group()` method that adds contextual buttons based on the current stage:

#### Button Types:

**Continue Buttons** (Visible to all users):
- Added to all trial stages (Hook Scene through Judge's Summing Up)
- Button: "▶️ Continue" → `/continue`
- Allows users to progress through the trial
- Uses `isHidden: "0"` for visibility

**Vote Buttons** (Hidden from other users):
- Added to Anonymous Vote stage
- Buttons:
  - "✅ GUILTY" → `/vote guilty`
  - "❌ NOT GUILTY" → `/vote not_guilty`
- Uses `isHidden: "1"` for privacy
- Ensures anonymous voting

**Evidence Button** (Visible to all users):
- Added to Jury Deliberation stage
- Button: "📋 View Evidence" → `/evidence`
- Allows quick access to evidence board during deliberation

**No Buttons**:
- Dual Reveal and Completed stages have no buttons
- These are informational stages that don't require user action

### 3. Button Configuration

All buttons use:
- `dismiss_type: "select"` - Buttons persist after clicking
- Appropriate `isHidden` values for privacy control
- Clear emoji indicators for visual recognition
- Command selectors that integrate with existing command handlers

### 4. Orchestrator Integration

Updated `ExperienceOrchestrator` in `src/orchestrator.py`:

**New Method**: `broadcast_stage_to_group(group_id: str)`
- Broadcasts current stage announcement to group
- Includes visual formatting and buttons
- Handles errors gracefully

**Updated Command Handlers**:
- `_handle_start_command()` - Broadcasts hook scene to groups
- `_handle_continue_command()` - Broadcasts next stage to groups
- Both methods detect group messages (type == 1) and use broadcasting

### 5. Error Handling

Implemented robust error handling:
- Graceful failure when API client not initialized
- Logs errors without interrupting user experience
- Returns detailed error information for debugging
- Continues with fallback behavior on API failures

## Testing

Created comprehensive unit tests in `tests/unit/test_group_broadcasting.py`:

### Test Coverage:

**Stage Announcement Formatting** (9 tests):
- Verifies all stages include appropriate emojis
- Checks for structured formatting with headers
- Validates content completeness

**Group Broadcasting with Buttons** (8 tests):
- Tests continue button inclusion for trial stages
- Verifies vote buttons for voting stage
- Checks evidence button for deliberation
- Tests button visibility settings
- Validates error handling

**Button Configuration** (3 tests):
- Verifies continue buttons visible to all
- Confirms vote buttons hidden from others
- Checks dismiss type configuration

**Stage Transition Broadcasting** (2 tests):
- Tests metadata inclusion in broadcasts
- Verifies API response handling

**All 21 tests pass successfully.**

## Requirements Validated

This implementation validates:
- **Requirement 13.2**: Stage announcements on transitions
- **Requirement 13.3**: SuperBox launch prompts (via buttons)
- **Requirement 13.4**: User interaction handling

## API Integration

The implementation uses the Luffa Bot API's `send_group_message` endpoint with:
- `text`: Formatted announcement with emojis
- `buttons`: Array of button objects with name, selector, isHidden
- `type`: "2" for messages with buttons
- `dismiss_type`: "select" to persist buttons

## Usage Example

```python
# In orchestrator when advancing stage
result = await self.advance_trial_stage()

# Broadcast to group if this is a group message
if msg.get("type") == 1:  # Group message
    await self.broadcast_stage_to_group(group_id)
```

## Benefits

1. **Enhanced User Experience**: Visual emojis make stages instantly recognizable
2. **Reduced Friction**: Buttons eliminate need to type commands
3. **Privacy Protection**: Hidden vote buttons maintain anonymity
4. **Clear Progression**: Continue buttons guide users through the trial
5. **Contextual Actions**: Buttons appear only when relevant

## Files Modified

- `src/luffa_integration.py` - Enhanced announcements and added broadcasting
- `src/orchestrator.py` - Added broadcast method and updated command handlers
- `tests/unit/test_group_broadcasting.py` - Comprehensive test suite

## Next Steps

Task 22.3 is complete. The next task (22.4) will implement session management tied to Luffa user IDs for multi-user support.

## Notes

- Buttons use Luffa Bot API's button format with selector commands
- All buttons integrate with existing command handlers (/continue, /vote, /evidence)
- Visual formatting follows courtroom theme with appropriate emojis
- Implementation is backward compatible with DM-based interactions
