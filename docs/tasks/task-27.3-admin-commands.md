# Task 27.3: Admin Commands for Operators

## Overview
Implemented admin-only commands `/metrics` and `/sessions` for system operators to monitor VERITAS performance and active sessions.

## Implementation

### 1. Configuration Changes (`src/config.py`)
- Added `admin_uids: list[str]` field to `AppConfig` dataclass
- Parse from `VERITAS_ADMIN_UIDS` environment variable (comma-separated list)
- Updated `.env.example` with documentation for the new configuration

### 2. Multi-Bot Service Changes (`src/multi_bot_service.py`)
- Imported `get_metrics_collector` from metrics module
- Added `/metrics` command handler in `handle_command()` method
- Added `/sessions` command handler in `handle_command()` method
- Implemented `show_metrics()` method:
  - Checks if sender is in `admin_uids` list
  - Retrieves metrics summary from `get_metrics_collector().get_summary()`
  - Formats metrics as readable text for chat display
  - Sends via clerk bot
- Implemented `show_sessions()` method:
  - Checks if sender is in `admin_uids` list
  - Iterates through `self.active_sessions`
  - Shows count, state, duration, and case ID for each session
  - Sends via clerk bot

### 3. Access Control
Both admin commands check `sender_uid in self.config.admin_uids` before processing:
- If authorized: Display requested information
- If unauthorized: Send "⚠️ This command is only available to administrators."

## Usage

### Configuration
Add admin user UIDs to `.env`:
```bash
VERITAS_ADMIN_UIDS=uid_123,uid_456,uid_789
```

### Commands

#### `/metrics`
Shows comprehensive performance metrics:
- **Agent Responses**: Total calls, avg/p95 duration, success rate, fallback rate
- **By Role**: Per-agent statistics
- **State Transitions**: Count, duration, success rate
- **Reasoning Evaluations**: Count, duration, category distribution
- **Sessions**: Total, completed, completion rate, avg duration/calls/transitions

Example output:
```
📊 VERITAS PERFORMANCE METRICS

**Agent Responses:**
• Total calls: 45
• Avg duration: 1500ms
• P95 duration: 2500ms
• Success rate: 95.6%
• Fallback rate: 4.4%

**By Role:**
• clerk: 10 calls, avg 1200ms
• prosecution: 12 calls, avg 1600ms
• defence: 12 calls, avg 1550ms

**State Transitions:**
• Total: 32
• Avg duration: 450ms
• P95 duration: 800ms
• Success rate: 100.0%

**Reasoning Evaluations:**
• Total: 8
• Avg duration: 3200ms
• Success rate: 100.0%
• Categories: {'sound_correct': 5, 'sound_incorrect': 3}

**Sessions:**
• Total: 4
• Completed: 3
• Completion rate: 75.0%
• Avg duration: 180.5s
• Avg agent calls: 11.3
• Avg state transitions: 8.0
```

#### `/sessions`
Shows active sessions with details:
- Session ID
- Current state
- Duration (in minutes)
- Case ID

Example output:
```
📋 ACTIVE SESSIONS (2)

**Session:** luffa_group123_user456_1234567890
• State: PROSECUTION_OPENING
• Duration: 5 minutes
• Case: blackthorn-hall-001

**Session:** luffa_group456_user789_1234567891
• State: JURY_DELIBERATION
• Duration: 12 minutes
• Case: digital-deception-002
```

## Testing

### Unit Tests (`tests/unit/test_admin_commands.py`)
- ✅ Admin users can access `/metrics` command
- ✅ Non-admin users are denied access to `/metrics`
- ✅ Admin users can access `/sessions` command
- ✅ Non-admin users are denied access to `/sessions`
- ✅ `/sessions` shows "No active sessions" when empty
- ✅ Commands are properly routed through `handle_command()`

### Integration Tests (`tests/integration/test_admin_commands_integration.py`)
- ✅ Complete admin workflow: check metrics and sessions
- ✅ Non-admin users cannot access commands
- ✅ Commands work through `handle_command()` routing

All 10 tests pass successfully.

## Security Considerations
- Admin commands are protected by UID-based access control
- Only users listed in `VERITAS_ADMIN_UIDS` can execute these commands
- Unauthorized access attempts are logged and denied with clear message
- No sensitive information (API keys, secrets) is exposed in command output

## Benefits
1. **Operational Visibility**: Operators can monitor system performance in real-time
2. **Session Management**: Track active sessions and their progress
3. **Performance Monitoring**: Identify slow agents, bottlenecks, and issues
4. **Troubleshooting**: Quickly diagnose problems with specific sessions
5. **Capacity Planning**: Understand system load and usage patterns

## Future Enhancements
Potential improvements for future tasks:
- Add `/metrics <case_id>` to show case-specific statistics
- Add `/session <session_id>` to show detailed session info
- Add `/kill <session_id>` to forcefully terminate a session
- Add `/health` to show system health status
- Add metrics export to JSON/CSV for analysis
- Add alerting when metrics exceed thresholds
