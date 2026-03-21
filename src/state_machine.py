"""State machine for managing VERITAS experience flow."""

from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Callable, Awaitable, TYPE_CHECKING
from pydantic import BaseModel, Field, ConfigDict

if TYPE_CHECKING:
    from src.session import UserSession, SessionStore


class ExperienceState(str, Enum):
    """States in the VERITAS courtroom experience."""
    NOT_STARTED = "not_started"
    HOOK_SCENE = "hook_scene"
    CHARGE_READING = "charge_reading"
    PROSECUTION_OPENING = "prosecution_opening"
    DEFENCE_OPENING = "defence_opening"
    EVIDENCE_PRESENTATION = "evidence_presentation"
    CROSS_EXAMINATION = "cross_examination"
    PROSECUTION_CLOSING = "prosecution_closing"
    DEFENCE_CLOSING = "defence_closing"
    JUDGE_SUMMING_UP = "judge_summing_up"
    JURY_DELIBERATION = "jury_deliberation"
    ANONYMOUS_VOTE = "anonymous_vote"
    DUAL_REVEAL = "dual_reveal"
    COMPLETED = "completed"


# Define the valid state transitions in Crown Court procedure order
STATE_TRANSITIONS = {
    ExperienceState.NOT_STARTED: ExperienceState.HOOK_SCENE,
    ExperienceState.HOOK_SCENE: ExperienceState.CHARGE_READING,
    ExperienceState.CHARGE_READING: ExperienceState.PROSECUTION_OPENING,
    ExperienceState.PROSECUTION_OPENING: ExperienceState.DEFENCE_OPENING,
    ExperienceState.DEFENCE_OPENING: ExperienceState.EVIDENCE_PRESENTATION,
    ExperienceState.EVIDENCE_PRESENTATION: ExperienceState.CROSS_EXAMINATION,
    ExperienceState.CROSS_EXAMINATION: ExperienceState.PROSECUTION_CLOSING,
    ExperienceState.PROSECUTION_CLOSING: ExperienceState.DEFENCE_CLOSING,
    ExperienceState.DEFENCE_CLOSING: ExperienceState.JUDGE_SUMMING_UP,
    ExperienceState.JUDGE_SUMMING_UP: ExperienceState.JURY_DELIBERATION,
    ExperienceState.JURY_DELIBERATION: ExperienceState.ANONYMOUS_VOTE,
    ExperienceState.ANONYMOUS_VOTE: ExperienceState.DUAL_REVEAL,
    ExperienceState.DUAL_REVEAL: ExperienceState.COMPLETED,
    ExperienceState.COMPLETED: None,  # No next state
}


class StateTransition(BaseModel):
    """Configuration for a state transition."""
    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True)
    
    from_state: ExperienceState = Field(alias="fromState")
    to_state: ExperienceState = Field(alias="toState")
    condition: Optional[Callable[[], bool]] = None
    on_enter: Optional[Callable[[], Awaitable[None]]] = None
    on_exit: Optional[Callable[[], Awaitable[None]]] = None


class StateTiming(BaseModel):
    """Timing information for a state."""
    model_config = ConfigDict(populate_by_name=True)
    
    state: ExperienceState
    entered_at: datetime = Field(alias="enteredAt")
    exited_at: Optional[datetime] = Field(default=None, alias="exitedAt")
    duration_seconds: Optional[float] = Field(default=None, alias="durationSeconds")

    def calculate_duration(self) -> float:
        """Calculate duration in seconds."""
        if self.exited_at:
            return (self.exited_at - self.entered_at).total_seconds()
        return (datetime.now() - self.entered_at).total_seconds()


class StateMachine:
    """
    State machine managing VERITAS experience flow.
    
    Enforces sequential progression through trial stages, tracks timing,
    and validates state transitions according to Crown Court procedure.
    """

    def __init__(self, session_id: str, case_id: str, session_store: Optional["SessionStore"] = None):
        """
        Initialize state machine.
        
        Args:
            session_id: Unique identifier for the user session
            case_id: Identifier for the case being experienced
            session_store: Optional session store for persistence
        """
        self.session_id = session_id
        self.case_id = case_id
        self.current_state = ExperienceState.NOT_STARTED
        self.state_history: list[StateTiming] = []
        self.start_time = datetime.now()
        self.max_duration_minutes = 20
        self.session_store = session_store

    def get_current_state(self) -> ExperienceState:
        """Get the current state."""
        return self.current_state

    def can_transition_to(self, target_state: ExperienceState) -> bool:
        """
        Check if transition to target state is valid.
        
        Args:
            target_state: The state to transition to
            
        Returns:
            True if transition is valid, False otherwise
        """
        # Check if we're at the end
        if self.current_state == ExperienceState.COMPLETED:
            return False
        
        # Get the expected next state
        expected_next = STATE_TRANSITIONS.get(self.current_state)
        
        # Can only transition to the immediate next state (no skipping)
        return target_state == expected_next

    async def transition_to(self, target_state: ExperienceState) -> None:
        """
        Transition to a new state.
        
        Args:
            target_state: The state to transition to
            
        Raises:
            ValueError: If the transition is not valid
        """
        if not self.can_transition_to(target_state):
            raise ValueError(
                f"Invalid transition from {self.current_state} to {target_state}. "
                f"Expected next state: {STATE_TRANSITIONS.get(self.current_state)}"
            )
        
        # Check maximum duration
        elapsed = self.get_elapsed_time_seconds()
        if elapsed > self.max_duration_minutes * 60:
            # Force completion if max duration exceeded
            target_state = ExperienceState.COMPLETED
        
        # Exit current state
        if self.state_history:
            self.state_history[-1].exited_at = datetime.now()
            self.state_history[-1].duration_seconds = self.state_history[-1].calculate_duration()
        
        # Enter new state
        self.current_state = target_state
        timing = StateTiming(
            state=target_state,
            entered_at=datetime.now()
        )
        self.state_history.append(timing)

    def get_next_state(self) -> Optional[ExperienceState]:
        """Get the next valid state from current state."""
        return STATE_TRANSITIONS.get(self.current_state)

    def get_elapsed_time_seconds(self) -> float:
        """Get total elapsed time since experience start in seconds."""
        return (datetime.now() - self.start_time).total_seconds()

    def get_current_state_duration_seconds(self) -> float:
        """Get duration of current state in seconds."""
        if not self.state_history:
            return 0.0
        return self.state_history[-1].calculate_duration()

    def get_completed_states(self) -> list[ExperienceState]:
        """Get list of completed states."""
        return [timing.state for timing in self.state_history if timing.exited_at is not None]

    def is_max_duration_exceeded(self) -> bool:
        """Check if maximum experience duration has been exceeded."""
        return self.get_elapsed_time_seconds() > self.max_duration_minutes * 60

    def save_progress(self, user_session: "UserSession") -> None:
        """
        Save current state machine progress to session.
        
        Args:
            user_session: The user session to update and save
        """
        if self.session_store is None:
            return
        
        # Update session with current state machine data
        user_session.current_state = self.current_state
        user_session.state_history = self.state_history
        user_session.progress.completed_stages = self.get_completed_states()
        
        # Save to persistent storage
        self.session_store.save_progress(user_session)

    @classmethod
    def restore_progress(cls, session_id: str, session_store: "SessionStore") -> Optional["StateMachine"]:
        """
        Restore state machine from saved session.
        
        Args:
            session_id: The session ID to restore
            session_store: The session store to load from
            
        Returns:
            StateMachine instance if session found and valid, None otherwise
        """
        user_session = session_store.restore_progress(session_id)
        
        if user_session is None:
            return None
        
        # Reconstruct state machine from session
        state_machine = cls(
            session_id=user_session.session_id,
            case_id=user_session.case_id,
            session_store=session_store
        )
        
        state_machine.current_state = user_session.current_state
        state_machine.state_history = user_session.state_history
        state_machine.start_time = user_session.start_time
        
        return state_machine
