"""Unit tests for post-trial case statistics (Task 26.4)."""

import pytest
from metrics import MetricsCollector


class TestCaseStatistics:
    """Test case verdict statistics tracking."""
    
    @pytest.mark.asyncio
    async def test_verdict_tracked_in_session_metrics(self):
        """Test that verdict is tracked when session ends."""
        collector = MetricsCollector()
        
        # Start session
        await collector.start_session("test_session_001", "blackthorn-hall-001")
        
        # End session with verdict
        await collector.end_session(
            "test_session_001",
            completed=True,
            final_state="COMPLETED",
            verdict="guilty"
        )
        
        # Verify verdict stored
        session = collector._session_metrics["test_session_001"]
        assert session.verdict == "guilty"
        assert session.completed is True
    
    @pytest.mark.asyncio
    async def test_get_case_verdict_stats_empty(self):
        """Test case stats when no sessions completed."""
        collector = MetricsCollector()
        
        stats = collector.get_case_verdict_stats("nonexistent-case")
        
        assert stats["total"] == 0
        assert stats["guilty_count"] == 0
        assert stats["not_guilty_count"] == 0
        assert stats["guilty_pct"] == 0.0
        assert stats["not_guilty_pct"] == 0.0
    
    @pytest.mark.asyncio
    async def test_get_case_verdict_stats_with_verdicts(self):
        """Test case stats calculation with multiple verdicts."""
        collector = MetricsCollector()
        case_id = "blackthorn-hall-001"
        
        # Simulate 5 sessions: 3 guilty, 2 not guilty
        verdicts = ["guilty", "guilty", "not_guilty", "guilty", "not_guilty"]
        
        for i, verdict in enumerate(verdicts):
            session_id = f"test_session_{i}"
            await collector.start_session(session_id, case_id)
            await collector.end_session(
                session_id,
                completed=True,
                final_state="COMPLETED",
                verdict=verdict
            )
        
        # Get stats
        stats = collector.get_case_verdict_stats(case_id)
        
        assert stats["total"] == 5
        assert stats["guilty_count"] == 3
        assert stats["not_guilty_count"] == 2
        assert stats["guilty_pct"] == 60.0
        assert stats["not_guilty_pct"] == 40.0
    
    @pytest.mark.asyncio
    async def test_case_stats_only_counts_completed_sessions(self):
        """Test that incomplete sessions are not counted in stats."""
        collector = MetricsCollector()
        case_id = "blackthorn-hall-001"
        
        # Complete session with verdict
        await collector.start_session("complete_session", case_id)
        await collector.end_session(
            "complete_session",
            completed=True,
            final_state="COMPLETED",
            verdict="guilty"
        )
        
        # Incomplete session
        await collector.start_session("incomplete_session", case_id)
        await collector.end_session(
            "incomplete_session",
            completed=False,
            final_state="ERROR"
        )
        
        # Get stats
        stats = collector.get_case_verdict_stats(case_id)
        
        # Should only count the completed session
        assert stats["total"] == 1
        assert stats["guilty_count"] == 1
    
    @pytest.mark.asyncio
    async def test_case_stats_filters_by_case_id(self):
        """Test that stats are filtered by case ID."""
        collector = MetricsCollector()
        
        # Session for case 1
        await collector.start_session("session_1", "blackthorn-hall-001")
        await collector.end_session(
            "session_1",
            completed=True,
            final_state="COMPLETED",
            verdict="guilty"
        )
        
        # Session for case 2
        await collector.start_session("session_2", "digital-deception-002")
        await collector.end_session(
            "session_2",
            completed=True,
            final_state="COMPLETED",
            verdict="not_guilty"
        )
        
        # Get stats for case 1
        stats_case1 = collector.get_case_verdict_stats("blackthorn-hall-001")
        assert stats_case1["total"] == 1
        assert stats_case1["guilty_count"] == 1
        
        # Get stats for case 2
        stats_case2 = collector.get_case_verdict_stats("digital-deception-002")
        assert stats_case2["total"] == 1
        assert stats_case2["not_guilty_count"] == 1
