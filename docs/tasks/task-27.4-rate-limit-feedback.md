# Task 27.4: User Feedback on Rate Limits and Errors

## Overview
Implemented user-friendly feedback messages for rate limiting and timeout scenarios to improve the user experience during trial interactions.

## Implementation

### 1. RateLimiter Enhancement (`src/llm_service.py`)

Added `check_would_block()` method to the `RateLimiter` class:
- **Purpose**: Check if a request would be blocked by rate limits WITHOUT modifying state
- **Returns**: `True` if rate limit would block, `False` otherwise
- **Logic**: 
  - Counts recent requests (within last 60 seconds)
  - Calculates recent token usage
  - Checks both request and token limits
  - Does NOT modify internal state (read-only check)

```python
def check_would_block(self, estimated_tokens: int = 1000) -> bool:
    """Check if acquire() would block without modifying state."""
    now = time.time()
    cutoff = now - 60
    
    # Count recent requests
    recent_requests = sum(1 for t in self.request_times if t >= cutoff)
    if recent_requests >= self.max_requests_per_minute:
        return True
    
    # Count recent tokens
    recent_tokens = sum(count for timestamp, count in self.token_usage if timestamp >= cutoff)
    if recent_tokens + estimated_tokens > self.max_tokens_per_minute:
        return True
    
    return False
```

### 2. Trial Orchestrator Updates (`src/trial_orchestrator.py`)

Enhanced `_generate_agent_response()` method:

#### Rate Limit Detection
- Before calling LLM, checks if rate limiter would block
- Estimates tokens using same logic as `generate_response()`
- Adds `rate_limit_warning` flag to response metadata

#### Timeout Handling
- Added specific `asyncio.TimeoutError` exception handler
- Returns fallback response with `timeout` flag in metadata
- Provides user-friendly error message

#### Metadata Structure
Response metadata now includes:
- `rate_limit_warning`: Boolean indicating if rate limit was reached
- `timeout`: Boolean indicating if request timed out
- `used_fallback`: Boolean indicating if fallback was used
- `stage`: Current trial stage

### 3. Multi-Bot Service Updates (`src/multi_bot_service.py`)

Enhanced `send_agent_response()` method to display user feedback:

#### Rate Limit Message
When `rate_limit_warning` is True:
```
⏳ The court needs a moment...
```
- Sent from clerk bot
- Displayed before the actual agent response
- 1-second delay before continuing

#### Timeout Message
When `timeout` is True:
```
⚠️ {Role} is composing their response...
```
- Sent from clerk bot
- Role name is formatted (e.g., "Prosecution", "Defence")
- Displayed before the fallback response
- 1-second delay before continuing

## Testing

### Unit Tests (`tests/unit/test_rate_limit_feedback.py`)

Created comprehensive test suite covering:

1. **Rate Limit Warning Tests**
   - `test_generate_agent_response_includes_rate_limit_warning`: Verifies warning flag when rate limit reached
   - `test_generate_agent_response_no_rate_limit_warning_when_under_limit`: Verifies no warning when under limit

2. **Timeout Tests**
   - `test_generate_agent_response_timeout_metadata`: Verifies timeout flag and fallback on timeout

3. **Message Display Tests**
   - `test_send_agent_response_shows_rate_limit_message`: Verifies rate limit message is sent
   - `test_send_agent_response_shows_timeout_message`: Verifies timeout message is sent
   - `test_send_agent_response_no_warning_messages_when_no_flags`: Verifies no messages when flags not set

### Rate Limiter Tests (`tests/unit/test_llm_connection_pooling.py`)

Added tests for new `check_would_block()` method:
- `test_rate_limiter_check_would_block`: Verifies prediction without state modification
- `test_rate_limiter_check_would_block_token_limit`: Verifies token limit detection

All tests pass successfully.

## User Experience Flow

### Normal Operation
1. User triggers trial action
2. Agent response generated normally
3. Response displayed without warnings

### Rate Limit Scenario
1. User triggers trial action
2. Rate limiter detects limit would be reached
3. User sees: "⏳ The court needs a moment..."
4. System waits for rate limit to clear
5. Agent response generated and displayed

### Timeout Scenario
1. User triggers trial action
2. LLM request times out
3. User sees: "⚠️ {Role} is composing their response..."
4. Fallback response displayed
5. Trial continues without interruption

## Benefits

1. **Transparency**: Users understand when delays occur
2. **Professional**: Maintains courtroom atmosphere with appropriate messaging
3. **Non-blocking**: System continues to function with fallbacks
4. **Informative**: Clear indication of what's happening behind the scenes
5. **Graceful Degradation**: Fallback responses ensure trial never gets stuck

## Technical Notes

- Rate limit check is non-blocking and doesn't modify state
- Timeout handling is separate from general exceptions
- Messages are sent from clerk bot to maintain consistency
- Delays (1 second) prevent message flooding
- Metadata structure is extensible for future enhancements

## Files Modified

1. `src/llm_service.py` - Added `check_would_block()` method
2. `src/trial_orchestrator.py` - Enhanced error handling and metadata
3. `src/multi_bot_service.py` - Added user feedback messages
4. `tests/unit/test_rate_limit_feedback.py` - New comprehensive test suite
5. `tests/unit/test_llm_connection_pooling.py` - Added rate limiter tests

## Verification

All tests pass:
- ✅ 6/6 rate limit feedback tests
- ✅ 14/14 LLM connection pooling tests
- ✅ Existing fact checker tests still pass
- ✅ No diagnostic errors in modified files
