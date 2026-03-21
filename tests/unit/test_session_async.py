"""Unit tests for async session management."""

import pytest
import tempfile
import shutil
import asyncio
from datetime import datetime, timedelta
from pathlib import Path

from src.session_async import (
    UserSession,
    AsyncSessionStore,
    FileBackend,
    SessionProgress,
    SessionMetadata,
    DeliberationTurn,
    ReasoningAssessment,
)
from src.state_machine import ExperienceState, StateTiming


class TestUserSession:
    """Test UserSession model (same as sync version)."""

    def test_session_creation(self):
        """Test creating a user session."""
        session = UserSession(
            sessionId="test-session",
            userId="test-user",
            caseId="test-case",
            currentState=ExperienceState.NOT_STARTED,
            startTime=datetime.now(),
            lastActivityTime=datetime.now(),
        )
        
        assert session.session_id == "test-session"
        assert session.user_id == "test-user"
        assert session.case_id == "test-case"
        assert session.current_state == ExperienceState.NOT_STARTED

    def test_session_serialization_round_trip(self):
        """Test session can be serialized and deserialized."""
        original = UserSession(
            sessionId="test-session",
            userId="test-user",
            caseId="test-case",
            currentState=ExperienceState.HOOK_SCENE,
            startTime=datetime.now(),
            lastActivityTime=datetime.now(),
        )
        
        # Serialize
        json_str = original.serialize()
        
        # Deserialize
        restored = UserSession.deserialize(json_str)
        
        assert restored.session_id == original.session_id
        assert restored.user_id == original.user_id
        assert restored.case_id == original.case_id
        assert restored.current_state == original.current_state


class TestFileBackend:
    """Test FileBackend with async I/O."""

    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.mark.asyncio
    async def test_save_and_load(self, temp_storage):
        """Test saving and loading session with async I/O."""
        backend = FileBackend(storage_dir=temp_storage)
        
        session = UserSession(
            sessionId="test-session",
            userId="test-user",
            caseId="test-case",
            currentState=ExperienceState.HOOK_SCENE,
            startTime=datetime.now(),
            lastActivityTime=datetime.now(),
        )
        
        # Save
        await backend.save(session)
        
        # Load
        restored = await backend.load("test-session")
        
        assert restored is not None
        assert restored.session_id == session.session_id
        assert restored.current_state == session.current_state

    @pytest.mark.asyncio
    async def test_load_nonexistent_session(self, temp_storage):
        """Test loading a session that doesn't exist."""
        backend = FileBackend(storage_dir=temp_storage)
        
        restored = await backend.load("nonexistent-session")
        assert restored is None

    @pytest.mark.asyncio
    async def test_load_expired_session(self, temp_storage):
        """Test loading an expired session returns None."""
        backend = FileBackend(storage_dir=temp_storage)
        
        session = UserSession(
            sessionId="test-session",
            userId="test-user",
            caseId="test-case",
            currentState=ExperienceState.HOOK_SCENE,
            startTime=datetime.now() - timedelta(hours=25),
            lastActivityTime=datetime.now() - timedelta(hours=25),
        )
        
        # Save
        await backend.save(session)
        
        # Try to load (should be expired)
        restored = await backend.load("test-session")
        assert restored is None
        
        # Session file should be deleted
        session_path = Path(temp_storage) / "test-session.json"
        assert not session_path.exists()

    @pytest.mark.asyncio
    async def test_delete_session(self, temp_storage):
        """Test deleting a session."""
        backend = FileBackend(storage_dir=temp_storage)
        
        session = UserSession(
            sessionId="test-session",
            userId="test-user",
            caseId="test-case",
            currentState=ExperienceState.HOOK_SCENE,
            startTime=datetime.now(),
            lastActivityTime=datetime.now(),
        )
        
        # Save
        await backend.save(session)
        
        # Delete
        await backend.delete("test-session")
        
        # Should not be able to load
        restored = await backend.load("test-session")
        assert restored is None

    @pytest.mark.asyncio
    async def test_cleanup_expired_sessions(self, temp_storage):
        """Test cleaning up expired sessions."""
        backend = FileBackend(storage_dir=temp_storage)
        
        # Create one expired and one active session
        expired_session = UserSession(
            sessionId="expired-session",
            userId="test-user",
            caseId="test-case",
            currentState=ExperienceState.HOOK_SCENE,
            startTime=datetime.now() - timedelta(hours=25),
            lastActivityTime=datetime.now() - timedelta(hours=25),
        )
        
        active_session = UserSession(
            sessionId="active-session",
            userId="test-user",
            caseId="test-case",
            currentState=ExperienceState.HOOK_SCENE,
            startTime=datetime.now(),
            lastActivityTime=datetime.now(),
        )
        
        await backend.save(expired_session)
        await backend.save(active_session)
        
        # Cleanup
        cleaned = await backend.cleanup_expired(retention_hours=24)
        
        assert cleaned == 1
        
        # Expired should be gone
        assert await backend.load("expired-session") is None
        
        # Active should still exist
        assert await backend.load("active-session") is not None


class TestAsyncSessionStore:
    """Test AsyncSessionStore with batching."""

    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.mark.asyncio
    async def test_save_and_restore_progress(self, temp_storage):
        """Test saving and restoring session progress."""
        backend = FileBackend(storage_dir=temp_storage)
        store = AsyncSessionStore(backend=backend)
        
        session = UserSession(
            sessionId="test-session",
            userId="test-user",
            caseId="test-case",
            currentState=ExperienceState.HOOK_SCENE,
            startTime=datetime.now(),
            lastActivityTime=datetime.now(),
        )
        
        # Save with immediate flush
        await store.save_progress(session, immediate=True)
        
        # Restore
        restored = await store.restore_progress("test-session")
        
        assert restored is not None
        assert restored.session_id == session.session_id
        assert restored.current_state == session.current_state

    @pytest.mark.asyncio
    async def test_batched_writes(self, temp_storage):
        """Test that writes are batched."""
        backend = FileBackend(storage_dir=temp_storage)
        store = AsyncSessionStore(backend=backend, batch_size=3, batch_interval=10.0)
        
        # Create 3 sessions
        sessions = []
        for i in range(3):
            session = UserSession(
                sessionId=f"test-session-{i}",
                userId="test-user",
                caseId="test-case",
                currentState=ExperienceState.HOOK_SCENE,
                startTime=datetime.now(),
                lastActivityTime=datetime.now(),
            )
            sessions.append(session)
            await store.save_progress(session, immediate=False)
        
        # Sessions should be in queue, not yet written to disk
        # But we can still restore them from the queue
        restored = await store.restore_progress("test-session-0")
        assert restored is not None
        assert restored.session_id == "test-session-0"

    @pytest.mark.asyncio
    async def test_batch_processor(self, temp_storage):
        """Test automatic batch flushing."""
        backend = FileBackend(storage_dir=temp_storage)
        store = AsyncSessionStore(backend=backend, batch_size=10, batch_interval=0.5)
        
        # Start batch processor
        await store.start_batch_processor()
        
        session = UserSession(
            sessionId="test-session",
            userId="test-user",
            caseId="test-case",
            currentState=ExperienceState.HOOK_SCENE,
            startTime=datetime.now(),
            lastActivityTime=datetime.now(),
        )
        
        # Save without immediate flush
        await store.save_progress(session, immediate=False)
        
        # Wait for batch processor to flush
        await asyncio.sleep(1.0)
        
        # Stop batch processor
        await store.stop_batch_processor()
        
        # Session should be written to disk
        restored = await backend.load("test-session")
        assert restored is not None
        assert restored.session_id == "test-session"

    @pytest.mark.asyncio
    async def test_delete_session(self, temp_storage):
        """Test deleting a session removes it from queue and backend."""
        backend = FileBackend(storage_dir=temp_storage)
        store = AsyncSessionStore(backend=backend)
        
        session = UserSession(
            sessionId="test-session",
            userId="test-user",
            caseId="test-case",
            currentState=ExperienceState.HOOK_SCENE,
            startTime=datetime.now(),
            lastActivityTime=datetime.now(),
        )
        
        # Save
        await store.save_progress(session, immediate=True)
        
        # Delete
        await store.delete_session("test-session")
        
        # Should not be able to restore
        restored = await store.restore_progress("test-session")
        assert restored is None

    @pytest.mark.asyncio
    async def test_concurrent_writes(self, temp_storage):
        """Test handling concurrent write operations."""
        backend = FileBackend(storage_dir=temp_storage)
        store = AsyncSessionStore(backend=backend, batch_size=100)
        
        # Create many sessions concurrently
        async def create_and_save_session(i: int):
            session = UserSession(
                sessionId=f"test-session-{i}",
                userId=f"test-user-{i}",
                caseId="test-case",
                currentState=ExperienceState.HOOK_SCENE,
                startTime=datetime.now(),
                lastActivityTime=datetime.now(),
            )
            await store.save_progress(session, immediate=False)
        
        # Create 50 sessions concurrently
        await asyncio.gather(*[create_and_save_session(i) for i in range(50)])
        
        # Flush all writes
        await store.stop_batch_processor()
        
        # Verify all sessions can be loaded
        for i in range(50):
            restored = await backend.load(f"test-session-{i}")
            assert restored is not None
            assert restored.session_id == f"test-session-{i}"


class TestSessionProgress:
    """Test SessionProgress model."""

    def test_progress_creation(self):
        """Test creating session progress."""
        progress = SessionProgress(
            completedStages=[ExperienceState.HOOK_SCENE, ExperienceState.CHARGE_READING],
            deliberationStatements=[],
            vote="guilty",
        )
        
        assert len(progress.completed_stages) == 2
        assert progress.vote == "guilty"

    def test_progress_with_deliberation(self):
        """Test progress with deliberation statements."""
        turn = DeliberationTurn(
            jurorId="user",
            statement="I think the evidence is clear.",
            timestamp=datetime.now(),
            evidenceReferences=["evidence-001"],
        )
        
        progress = SessionProgress(
            completedStages=[],
            deliberationStatements=[turn],
        )
        
        assert len(progress.deliberation_statements) == 1
        assert progress.deliberation_statements[0].juror_id == "user"
