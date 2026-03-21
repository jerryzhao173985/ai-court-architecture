"""Async user session management with high-concurrency optimizations."""

import json
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Literal, Dict, Any
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field, ConfigDict
import aiofiles

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


class SessionBackend(ABC):
    """Abstract base class for session storage backends."""
    
    @abstractmethod
    async def save(self, session: UserSession) -> None:
        """Save a session."""
        pass
    
    @abstractmethod
    async def load(self, session_id: str) -> Optional[UserSession]:
        """Load a session by ID."""
        pass
    
    @abstractmethod
    async def delete(self, session_id: str) -> None:
        """Delete a session by ID."""
        pass
    
    @abstractmethod
    async def cleanup_expired(self, retention_hours: int = 24) -> int:
        """Clean up expired sessions. Returns count of cleaned sessions."""
        pass


class FileBackend(SessionBackend):
    """File-based session storage with async I/O."""
    
    def __init__(self, storage_dir: str = "data/sessions"):
        """
        Initialize file backend.
        
        Args:
            storage_dir: Directory path for storing session files
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._write_lock = asyncio.Lock()
    
    def _get_session_path(self, session_id: str) -> Path:
        """Get file path for a session."""
        return self.storage_dir / f"{session_id}.json"
    
    async def save(self, session: UserSession) -> None:
        """
        Save session to file using async I/O.
        
        Args:
            session: The user session to save
        """
        session_path = self._get_session_path(session.session_id)
        
        async with self._write_lock:
            async with aiofiles.open(session_path, "w") as f:
                await f.write(session.serialize())
    
    async def load(self, session_id: str) -> Optional[UserSession]:
        """
        Load session from file using async I/O.
        
        Args:
            session_id: The session ID to load
            
        Returns:
            UserSession if found and not expired, None otherwise
        """
        session_path = self._get_session_path(session_id)
        
        if not session_path.exists():
            return None
        
        try:
            async with aiofiles.open(session_path, "r") as f:
                json_str = await f.read()
            
            session = UserSession.deserialize(json_str)
            
            # Check if session is expired (24-hour retention)
            if session.is_expired(retention_hours=24):
                # Clean up expired session
                await self.delete(session_id)
                return None
            
            return session
        except Exception:
            # If we can't read/parse the session, delete it
            await self.delete(session_id)
            return None
    
    async def delete(self, session_id: str) -> None:
        """
        Delete a session file.
        
        Args:
            session_id: The session ID to delete
        """
        session_path = self._get_session_path(session_id)
        if session_path.exists():
            session_path.unlink()
    
    async def cleanup_expired(self, retention_hours: int = 24) -> int:
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
                async with aiofiles.open(session_path, "r") as f:
                    json_str = await f.read()
                session = UserSession.deserialize(json_str)
                
                if session.is_expired(retention_hours):
                    session_path.unlink()
                    cleaned += 1
            except Exception:
                # If we can't read/parse the session, delete it
                session_path.unlink()
                cleaned += 1
        
        return cleaned


class AsyncSessionStore:
    """
    High-concurrency session store with async I/O and batching.
    
    Manages saving and restoring session state with 24-hour retention
    for disconnected sessions. Supports multiple backend implementations.
    """
    
    def __init__(
        self,
        backend: Optional[SessionBackend] = None,
        batch_size: int = 10,
        batch_interval: float = 1.0
    ):
        """
        Initialize async session store.
        
        Args:
            backend: Storage backend (defaults to FileBackend)
            batch_size: Number of writes to batch before flushing
            batch_interval: Time in seconds between batch flushes
        """
        self.backend = backend or FileBackend()
        self.batch_size = batch_size
        self.batch_interval = batch_interval
        
        # Batch write queue
        self._write_queue: Dict[str, UserSession] = {}
        self._queue_lock = asyncio.Lock()
        self._batch_task: Optional[asyncio.Task] = None
    
    async def start_batch_processor(self) -> None:
        """Start the background batch processor."""
        if self._batch_task is None or self._batch_task.done():
            self._batch_task = asyncio.create_task(self._batch_processor())
    
    async def stop_batch_processor(self) -> None:
        """Stop the background batch processor and flush pending writes."""
        if self._batch_task and not self._batch_task.done():
            self._batch_task.cancel()
            try:
                await self._batch_task
            except asyncio.CancelledError:
                pass
        
        # Flush any remaining writes
        await self._flush_batch()
    
    async def _batch_processor(self) -> None:
        """Background task that periodically flushes the write queue."""
        while True:
            try:
                await asyncio.sleep(self.batch_interval)
                await self._flush_batch()
            except asyncio.CancelledError:
                break
            except Exception:
                # Log error but continue processing
                pass
    
    async def _flush_batch(self) -> None:
        """Flush all pending writes to the backend."""
        async with self._queue_lock:
            if not self._write_queue:
                return
            
            # Get all pending sessions
            sessions_to_write = list(self._write_queue.values())
            self._write_queue.clear()
        
        # Write all sessions concurrently
        await asyncio.gather(
            *[self.backend.save(session) for session in sessions_to_write],
            return_exceptions=True
        )
    
    async def save_progress(self, session: UserSession, immediate: bool = False) -> None:
        """
        Save session progress to persistent storage.

        Args:
            session: The user session to save
            immediate: If True, bypass batching and write immediately
        """
        if immediate:
            await self.backend.save(session)
        else:
            should_flush = False
            async with self._queue_lock:
                self._write_queue[session.session_id] = session
                should_flush = len(self._write_queue) >= self.batch_size

            # Flush outside the lock to avoid deadlock (_flush_batch also acquires _queue_lock)
            if should_flush:
                await self._flush_batch()
    
    async def restore_progress(self, session_id: str) -> Optional[UserSession]:
        """
        Restore session progress from persistent storage.
        
        Args:
            session_id: The session ID to restore
            
        Returns:
            UserSession if found and not expired, None otherwise
        """
        # Check if session is in write queue (not yet flushed)
        async with self._queue_lock:
            if session_id in self._write_queue:
                return self._write_queue[session_id]
        
        # Load from backend
        return await self.backend.load(session_id)
    
    async def delete_session(self, session_id: str) -> None:
        """
        Delete a session from storage.
        
        Args:
            session_id: The session ID to delete
        """
        # Remove from write queue if present
        async with self._queue_lock:
            self._write_queue.pop(session_id, None)
        
        # Delete from backend
        await self.backend.delete(session_id)
    
    async def cleanup_expired_sessions(self, retention_hours: int = 24) -> int:
        """
        Remove all expired sessions from storage.
        
        Args:
            retention_hours: Number of hours to retain sessions
            
        Returns:
            Number of sessions cleaned up
        """
        return await self.backend.cleanup_expired(retention_hours)
