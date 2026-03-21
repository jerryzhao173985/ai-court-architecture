"""Unit tests for session management."""

import pytest
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path

from src.session import (
    UserSession,
    SessionStore,
    SessionProgress,
    SessionMetadata,
    DeliberationTurn,
    ReasoningAssessment,
)
from src.state_machine import ExperienceState, StateTiming


class TestUserSession:
    """Test UserSession model."""

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

    def test_session_expiry_check(self):
        """Test session expiry detection."""
        session = UserSession(
            sessionId="test-session",
            userId="test-user",
            caseId="test-case",
            currentState=ExperienceState.NOT_STARTED,
            startTime=datetime.now(),
            lastActivityTime=datetime.now() - timedelta(hours=25),
        )
        
        assert session.is_expired(retention_hours=24)

    def test_session_not_expired(self):
        """Test session not expired within retention period."""
        session = UserSession(
            sessionId="test-session",
            userId="test-user",
            caseId="test-case",
            currentState=ExperienceState.NOT_STARTED,
            startTime=datetime.now(),
            lastActivityTime=datetime.now() - timedelta(hours=23),
        )
        
        assert not session.is_expired(retention_hours=24)

    def test_update_activity(self):
        """Test updating last activity time."""
        session = UserSession(
            sessionId="test-session",
            userId="test-user",
            caseId="test-case",
            currentState=ExperienceState.NOT_STARTED,
            startTime=datetime.now(),
            lastActivityTime=datetime.now() - timedelta(hours=1),
        )
        
        old_time = session.last_activity_time
        session.update_activity()
        
        assert session.last_activity_time > old_time


class TestSessionStore:
    """Test SessionStore functionality."""

    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_save_and_restore_progress(self, temp_storage):
        """Test saving and restoring session progress."""
        store = SessionStore(storage_dir=temp_storage)
        
        session = UserSession(
            sessionId="test-session",
            userId="test-user",
            caseId="test-case",
            currentState=ExperienceState.HOOK_SCENE,
            startTime=datetime.now(),
            lastActivityTime=datetime.now(),
        )
        
        # Save
        store.save_progress(session)
        
        # Restore
        restored = store.restore_progress("test-session")
        
        assert restored is not None
        assert restored.session_id == session.session_id
        assert restored.current_state == session.current_state

    def test_restore_nonexistent_session(self, temp_storage):
        """Test restoring a session that doesn't exist."""
        store = SessionStore(storage_dir=temp_storage)
        
        restored = store.restore_progress("nonexistent-session")
        assert restored is None

    def test_restore_expired_session(self, temp_storage):
        """Test restoring an expired session returns None."""
        store = SessionStore(storage_dir=temp_storage)
        
        session = UserSession(
            sessionId="test-session",
            userId="test-user",
            caseId="test-case",
            currentState=ExperienceState.HOOK_SCENE,
            startTime=datetime.now() - timedelta(hours=25),
            lastActivityTime=datetime.now() - timedelta(hours=25),
        )
        
        # Save
        store.save_progress(session)
        
        # Try to restore (should be expired)
        restored = store.restore_progress("test-session")
        assert restored is None
        
        # Session file should be deleted
        session_path = Path(temp_storage) / "test-session.json"
        assert not session_path.exists()

    def test_delete_session(self, temp_storage):
        """Test deleting a session."""
        store = SessionStore(storage_dir=temp_storage)
        
        session = UserSession(
            sessionId="test-session",
            userId="test-user",
            caseId="test-case",
            currentState=ExperienceState.HOOK_SCENE,
            startTime=datetime.now(),
            lastActivityTime=datetime.now(),
        )
        
        # Save
        store.save_progress(session)
        
        # Delete
        store.delete_session("test-session")
        
        # Should not be able to restore
        restored = store.restore_progress("test-session")
        assert restored is None

    def test_cleanup_expired_sessions(self, temp_storage):
        """Test cleaning up expired sessions."""
        store = SessionStore(storage_dir=temp_storage)
        
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
        
        store.save_progress(expired_session)
        store.save_progress(active_session)
        
        # Cleanup
        cleaned = store.cleanup_expired_sessions(retention_hours=24)
        
        assert cleaned == 1
        
        # Expired should be gone
        assert store.restore_progress("expired-session") is None
        
        # Active should still exist
        assert store.restore_progress("active-session") is not None


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


class TestReasoningAssessment:
    """Test ReasoningAssessment model."""

    def test_assessment_creation(self):
        """Test creating reasoning assessment."""
        assessment = ReasoningAssessment(
            category="sound_correct",
            evidenceScore=0.8,
            coherenceScore=0.9,
            fallaciesDetected=["ad_hominem"],
            feedback="Good reasoning with minor fallacy.",
        )
        
        assert assessment.category == "sound_correct"
        assert assessment.evidence_score == 0.8
        assert len(assessment.fallacies_detected) == 1
