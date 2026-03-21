# Task 25.3: Inter-Juror Debate Dynamics

## Overview

Implemented dynamic jury deliberation where only 2 of 3 active AI jurors respond per round, creating more realistic debate patterns rather than having all 3 jurors respond every time.

## Changes Made

### 1. Modified `process_user_statement()` in `src/jury_orchestrator.py`

**Before:**
- All 3 active AI jurors responded to every user statement
- Lightweight jurors responded every 3rd round

**After:**
- Only 2 of 3 active AI jurors respond per round
- Rotation logic ensures each juror responds at least every 2 rounds
- Lightweight jurors respond every 4th round (changed from 3rd)

### 2. Added `_select_responding_jurors()` Method

New method that implements intelligent juror rotation:

```python
def _select_responding_jurors(self, active_jurors: list[JurorPersona], current_round: int) -> list[JurorPersona]:
    """
    Select 2 of 3 active jurors to respond, ensuring each responds at least every 2 rounds.
    """
```

**Selection Logic:**
1. **Priority 1:** Jurors who haven't responded in 2+ rounds MUST respond
2. **Priority 2:** If only 1 juror must respond, pair them with the juror who responded least recently
3. **Priority 3:** If no jurors are forced to respond, select the 2 who responded least recently

This ensures:
- Fair rotation among all 3 jurors
- No juror is silent for more than 1 round
- More dynamic, varied deliberation patterns

### 3. Added Tracking Infrastructure

Added `juror_last_response_round` dictionary to `__init__`:
```python
self.juror_last_response_round: dict[str, int] = {}
```

Tracks the last round number each juror responded in, enabling the rotation logic.

### 4. Inter-Juror Reactions

**No code change needed** - The existing implementation already supports jurors reacting to each other:
- `_generate_juror_response()` includes `recent_statements` (last 5 turns) in the prompt
- This context includes statements from other jurors, enabling natural back-and-forth debate

## Requirements Validated

- **Requirement 8.2:** Juror Personas - Active AI jurors engage in back-and-forth debate
- **Requirement 8.3:** Lightweight AI jurors contribute brief statements  
- **Requirement 9.3:** Active AI jurors respond within 15 seconds when user makes a statement

## Testing

### New Tests (`tests/unit/test_juror_rotation.py`)

1. **test_two_of_three_jurors_respond_per_round** - Verifies only 2 jurors respond per round
2. **test_juror_rotation_ensures_all_respond_every_two_rounds** - Validates rotation logic
3. **test_lightweight_juror_responds_every_fourth_round** - Confirms lightweight timing change
4. **test_juror_last_response_tracking** - Verifies tracking infrastructure
5. **test_select_responding_jurors_rotation_logic** - Tests selection method directly

### Updated Tests

- **test_different_jurors_track_separately** in `tests/unit/test_evidence_aware_deliberation.py`
  - Updated to expect 2 of 3 jurors responding instead of all 3

### Test Results

All tests pass:
- ✅ 7/7 evidence-aware deliberation tests
- ✅ 5/5 juror rotation tests
- ✅ 8/8 jury-related unit tests
- ✅ 1/1 deliberation dynamics integration test

## Benefits

1. **More Realistic Debate:** Not all jurors speak at once, mimicking real jury deliberations
2. **Varied Perspectives:** Different combinations of jurors create diverse discussion dynamics
3. **Better Pacing:** Fewer responses per round makes deliberation feel less overwhelming
4. **Fairness:** Rotation ensures all juror personas get equal representation over time
5. **Performance:** Fewer LLM calls per round (2 instead of 3) improves response time

## Example Deliberation Flow

**Round 1:** User speaks → Juror 1 (Evidence Purist) + Juror 2 (Sympathetic Doubter) respond

**Round 2:** User speaks → Juror 3 (Moral Absolutist) + Juror 1 (Evidence Purist) respond

**Round 3:** User speaks → Juror 2 (Sympathetic Doubter) + Juror 3 (Moral Absolutist) respond

**Round 4:** User speaks → Juror 1 + Juror 2 respond + Lightweight Juror 4 chimes in (every 4th round)

This creates natural debate patterns where different juror combinations interact, rather than the same 3 voices responding in unison every time.

## Implementation Notes

- The rotation logic is deterministic based on response history, ensuring consistent behavior
- Lightweight jurors still respond independently based on total statement count
- The 15-second response timeout per juror is maintained
- Evidence-aware prompts continue to work with the new rotation system
