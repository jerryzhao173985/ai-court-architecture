"""User session management with progress tracking and persistence."""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Literal
from pydantic import BaseModel, Field, ConfigDict

from state_machine import ExperienceState, StateTiming


class DeliberationTurn(BaseModel):
    """A single turn in jury deliberation."""
    model_config = ConfigDict(populate_by_name=True)
    
    juror_id: str = Field(alias="jurorId")
    statement: str
    timestamp: datetime
    evidence_references: list[str] = Field(default_factory=list, alias="evidenceReferences")


class ReasoningAssessment(BaseModel):
    """Assessment of user's reasoning quality."""
    model_config = ConfigDict(populate_by_name=True)
    
    category: Literal["sound_correct", "sound_incorrect", "weak_correct", "weak_incorrect"]
    evidence_score: float = Field(alias="evidenceScore")  # 0-1
    coherence_score: float = Field(alias="coherenceScore")  # 0-1
    fallacies_detected: list[str] = Field(default_factory=list, alias="fallaciesDetected")
    feedback: str


class SessionProgress(BaseModel):
    """Progress tracking for a user session."""
    model_config = ConfigDict(populate_by_name=True)
    
    completed_stages: list[ExperienceState] = Field(default_factory=list, alias="completedStages")
    deliberation_statements: list[DeliberationTurn] = Field(default_factory=list, alias="deliberationStatements")
    vote: Optional[Literal["guilty", "not_guilty"]] = None
    reasoning_assessment: Optional[ReasoningAssessment] = Field(default=None, alias="reasoningAssessment")


class SessionMetadata(BaseModel):
    """Metadata about session activity."""
    model_config = ConfigDict(populate_by_name=True)
    
    pause_count: int = Field(default=0, alias="pauseCount")
    total_pause_duration: float = Field(default=0.0, alias="totalPauseDuration")  # seconds
    agent_failures: int = Field(default=0, alias="agentFailures")


class UserSession(BaseModel):
    """
    Complete user session state.
    
    Tracks current state, progress, timing, and metadata for a user's
    experience through the VERITAS courtroom trial.
    """
    model_config = ConfigDict(populate_by_name=True)
    
    session_id: str = Field(alias="sessionId")
    user_id: str = Field(alias="userId")
    case_id: str = Field(alias="caseId")
    current_state: ExperienceState = Field(alias="currentState")
    start_time: datetime = Field(alias="startTime")
    last_activity_time: datetime = Field(alias="lastActivityTime")
    state_history: list[StateTiming] = Field(default_factory=list, alias="stateHistory")
    progress: SessionProgress = Field(default_factory=SessionProgress)
    metadata: SessionMetadata = Field(default_factory=SessionMetadata)

    def serialize(self) -> str:
        """Serialize session to JSON string."""
        return self.model_dump_json(by_alias=True, indent=2)

    @classmethod
    def deserialize(cls, json_str: str) -> "UserSession":
        """Deserialize session from JSON string."""
        return cls.model_validate_json(json_str)

    def is_expired(self, retention_hours: int = 24) -> bool:
        """
        Check if session has exceeded retention period.
        
        Args:
            retention_hours: Number of hours to retain disconnected sessions
            
        Returns:
            True if session is expired, False otherwise
        """
        expiry_time = self.last_activity_time + timedelta(hours=retention_hours)
        return datetime.now() > expiry_time

    def update_activity(self) -> None:
        """Update last activity timestamp to current time."""
        self.last_activity_time = datetime.now()


class SessionStore:
    """
    Persistent storage for user sessions.
    
    Manages saving and restoring session state with 24-hour retention
    for disconnected sessions.
    """

    def __init__(self, storage_dir: str = "data/sessions"):
        """
        Initialize session store.
        
        Args:
            storage_dir: Directory path for storing session files
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _get_session_path(self, session_id: str) -> Path:
        """Get file path for a session."""
        return self.storage_dir / f"{session_id}.json"

    def save_progress(self, session: UserSession) -> None:
        """
        Save session progress to persistent storage.
        
        Args:
            session: The user session to save
        """
        # Note: We don't call update_activity() here to preserve the actual last_activity_time
        session_path = self._get_session_path(session.session_id)
        
        with open(session_path, "w") as f:
            f.write(session.serialize())

    def restore_progress(self, session_id: str) -> Optional[UserSession]:
        """
        Restore session progress from persistent storage.
        
        Args:
            session_id: The session ID to restore
            
        Returns:
            UserSession if found and not expired, None otherwise
        """
        session_path = self._get_session_path(session_id)
        
        if not session_path.exists():
            return None
        
        with open(session_path, "r") as f:
            json_str = f.read()
        
        session = UserSession.deserialize(json_str)
        
        # Check if session is expired (24-hour retention)
        if session.is_expired(retention_hours=24):
            # Clean up expired session
            session_path.unlink()
            return None
        
        return session

    def delete_session(self, session_id: str) -> None:
        """
        Delete a session from storage.
        
        Args:
            session_id: The session ID to delete
        """
        session_path = self._get_session_path(session_id)
        if session_path.exists():
            session_path.unlink()

    def cleanup_expired_sessions(self, retention_hours: int = 24) -> int:
        """
        Remove all expired sessions from storage.
        
        Args:
            retention_hours: Number of hours to retain sessions
            
        Returns:
            Number of sessions cleaned up
        """
        cleaned = 0
        for session_path in self.storage_dir.glob("*.json"):
            try:
                with open(session_path, "r") as f:
                    json_str = f.read()
                session = UserSession.deserialize(json_str)
                
                if session.is_expired(retention_hours):
                    session_path.unlink()
                    cleaned += 1
            except Exception:
                # If we can't read/parse the session, delete it
                session_path.unlink()
                cleaned += 1
        
        return cleaned
