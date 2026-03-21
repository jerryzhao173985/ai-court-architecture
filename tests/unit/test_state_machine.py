"""Unit tests for state machine."""

import pytest
from datetime import datetime, timedelta

from src.state_machine import (
    StateMachine,
    ExperienceState,
    STATE_TRANSITIONS,
    StateTiming,
)


class TestStateMachine:
    """Test state machine functionality."""

    def test_initial_state(self):
        """Test state machine starts in NOT_STARTED state."""
        sm = StateMachine(session_id="test-session", case_id="test-case")
        assert sm.get_current_state() == ExperienceState.NOT_STARTED

    def test_valid_transition(self):
        """Test valid state transition."""
        sm = StateMachine(session_id="test-session", case_id="test-case")
        
        # Should be able to transition from NOT_STARTED to HOOK_SCENE
        assert sm.can_transition_to(ExperienceState.HOOK_SCENE)

    def test_invalid_transition_skipping(self):
        """Test that skipping states is not allowed."""
        sm = StateMachine(session_id="test-session", case_id="test-case")
        
        # Cannot skip from NOT_STARTED to CHARGE_READING
        assert not sm.can_transition_to(ExperienceState.CHARGE_READING)

    @pytest.mark.asyncio
    async def test_transition_execution(self):
        """Test executing a state transition."""
        sm = StateMachine(session_id="test-session", case_id="test-case")
        
        await sm.transition_to(ExperienceState.HOOK_SCENE)
        assert sm.get_current_state() == ExperienceState.HOOK_SCENE
        assert len(sm.state_history) == 1
        assert sm.state_history[0].state == ExperienceState.HOOK_SCENE

    @pytest.mark.asyncio
    async def test_invalid_transition_raises_error(self):
        """Test that invalid transitions raise ValueError."""
        sm = StateMachine(session_id="test-session", case_id="test-case")
        
        with pytest.raises(ValueError, match="Invalid transition"):
            await sm.transition_to(ExperienceState.CHARGE_READING)

    @pytest.mark.asyncio
    async def test_sequential_progression(self):
        """Test state machine follows Crown Court order."""
        sm = StateMachine(session_id="test-session", case_id="test-case")
        
        # Progress through first few states
        await sm.transition_to(ExperienceState.HOOK_SCENE)
        await sm.transition_to(ExperienceState.CHARGE_READING)
        await sm.transition_to(ExperienceState.PROSECUTION_OPENING)
        
        assert sm.get_current_state() == ExperienceState.PROSECUTION_OPENING
        assert len(sm.state_history) == 3

    def test_get_next_state(self):
        """Test getting the next valid state."""
        sm = StateMachine(session_id="test-session", case_id="test-case")
        
        next_state = sm.get_next_state()
        assert next_state == ExperienceState.HOOK_SCENE

    def test_completed_state_has_no_next(self):
        """Test that COMPLETED state has no next state."""
        sm = StateMachine(session_id="test-session", case_id="test-case")
        sm.current_state = ExperienceState.COMPLETED
        
        next_state = sm.get_next_state()
        assert next_state is None
        assert not sm.can_transition_to(ExperienceState.HOOK_SCENE)

    def test_get_completed_states(self):
        """Test getting list of completed states."""
        sm = StateMachine(session_id="test-session", case_id="test-case")
        
        # Add some completed states
        timing1 = StateTiming(state=ExperienceState.HOOK_SCENE, entered_at=datetime.now())
        timing1.exited_at = datetime.now()
        timing2 = StateTiming(state=ExperienceState.CHARGE_READING, entered_at=datetime.now())
        timing2.exited_at = datetime.now()
        timing3 = StateTiming(state=ExperienceState.PROSECUTION_OPENING, entered_at=datetime.now())
        # timing3 has no exit (current state)
        
        sm.state_history = [timing1, timing2, timing3]
        
        completed = sm.get_completed_states()
        assert len(completed) == 2
        assert ExperienceState.HOOK_SCENE in completed
        assert ExperienceState.CHARGE_READING in completed
        assert ExperienceState.PROSECUTION_OPENING not in completed

    def test_elapsed_time_tracking(self):
        """Test elapsed time calculation."""
        sm = StateMachine(session_id="test-session", case_id="test-case")
        
        # Elapsed time should be very small (just created)
        elapsed = sm.get_elapsed_time_seconds()
        assert elapsed >= 0
        assert elapsed < 1  # Should be less than 1 second

    def test_max_duration_check(self):
        """Test maximum duration enforcement."""
        sm = StateMachine(session_id="test-session", case_id="test-case")
        
        # Set start time to 21 minutes ago
        sm.start_time = datetime.now() - timedelta(minutes=21)
        
        assert sm.is_max_duration_exceeded()

    def test_state_transitions_completeness(self):
        """Test that all states have defined transitions except COMPLETED."""
        for state in ExperienceState:
            if state == ExperienceState.COMPLETED:
                assert STATE_TRANSITIONS[state] is None
            else:
                assert state in STATE_TRANSITIONS
                assert STATE_TRANSITIONS[state] is not None
