"""Unit tests for performance metrics system."""

import pytest
import asyncio
from src.metrics import (
    MetricsCollector,
    get_metrics_collector,
    reset_metrics,
    AgentMetrics,
    StateTransitionMetrics,
    ReasoningEvaluationMetrics
)


@pytest.fixture
def metrics_collector():
    """Create a fresh metrics collector for each test."""
    reset_metrics()
    return get_metrics_collector()


@pytest.mark.asyncio
async def test_agent_response_tracking(metrics_collector):
    """Test tracking agent response times."""
    # Start tracking
    metrics = metrics_collector.start_agent_response("prosecution", "opening")
    
    # Simulate some work
    await asyncio.sleep(0.1)
    
    # End tracking
    await metrics_collector.end_agent_response(metrics, success=True, used_fallback=False)
    
    # Verify metrics
    assert metrics.duration_ms is not None
    assert metrics.duration_ms >= 100  # At least 100ms
    assert metrics.success is True
    assert metrics.used_fallback is False
    
    # Get stats
    stats = metrics_collector.get_agent_stats()
    assert stats["count"] == 1
    assert stats["avg_duration_ms"] >= 100
    assert stats["success_rate"] == 1.0
    assert stats["fallback_rate"] == 0.0


@pytest.mark.asyncio
async def test_agent_response_with_fallback(metrics_collector):
    """Test tracking agent response with fallback."""
    metrics = metrics_collector.start_agent_response("defence", "closing")
    await asyncio.sleep(0.05)
    await metrics_collector.end_agent_response(metrics, success=True, used_fallback=True)
    
    stats = metrics_collector.get_agent_stats()
    assert stats["count"] == 1
    assert stats["fallback_rate"] == 1.0


@pytest.mark.asyncio
async def test_agent_response_failure(metrics_collector):
    """Test tracking failed agent response."""
    metrics = metrics_collector.start_agent_response("judge", "summing_up")
    await asyncio.sleep(0.05)
    await metrics_collector.end_agent_response(
        metrics,
        success=False,
        error="Timeout"
    )
    
    stats = metrics_collector.get_agent_stats()
    assert stats["count"] == 1
    assert stats["success_rate"] == 0.0


@pytest.mark.asyncio
async def test_agent_stats_by_role(metrics_collector):
    """Test agent statistics grouped by role."""
    # Track multiple agents
    for role in ["prosecution", "defence", "judge"]:
        metrics = metrics_collector.start_agent_response(role, "test_stage")
        await asyncio.sleep(0.01)
        await metrics_collector.end_agent_response(metrics, success=True)
    
    # Get stats by role
    stats_by_role = metrics_collector.get_agent_stats_by_role()
    assert len(stats_by_role) == 3
    assert "prosecution" in stats_by_role
    assert "defence" in stats_by_role
    assert "judge" in stats_by_role
    
    for role, stats in stats_by_role.items():
        assert stats["count"] == 1


@pytest.mark.asyncio
async def test_agent_stats_by_stage(metrics_collector):
    """Test agent statistics grouped by stage."""
    # Track multiple stages
    for stage in ["opening", "closing", "evidence"]:
        metrics = metrics_collector.start_agent_response("prosecution", stage)
        await asyncio.sleep(0.01)
        await metrics_collector.end_agent_response(metrics, success=True)
    
    # Get stats by stage
    stats_by_stage = metrics_collector.get_agent_stats_by_stage()
    assert len(stats_by_stage) == 3
    
    for stage, stats in stats_by_stage.items():
        assert stats["count"] == 1


@pytest.mark.asyncio
async def test_state_transition_tracking(metrics_collector):
    """Test tracking state transitions."""
    # Start tracking
    metrics = metrics_collector.start_state_transition("hook_scene", "charge_reading")
    
    # Simulate transition work
    await asyncio.sleep(0.05)
    
    # End tracking
    await metrics_collector.end_state_transition(metrics, success=True)
    
    # Verify metrics
    assert metrics.duration_ms is not None
    assert metrics.duration_ms >= 50
    assert metrics.success is True
    
    # Get stats
    stats = metrics_collector.get_state_transition_stats()
    assert stats["count"] == 1
    assert stats["avg_duration_ms"] >= 50
    assert stats["success_rate"] == 1.0


@pytest.mark.asyncio
async def test_state_transition_failure(metrics_collector):
    """Test tracking failed state transition."""
    metrics = metrics_collector.start_state_transition("deliberation", "completed")
    await asyncio.sleep(0.01)
    await metrics_collector.end_state_transition(
        metrics,
        success=False,
        error="Invalid transition"
    )
    
    stats = metrics_collector.get_state_transition_stats()
    assert stats["count"] == 1
    assert stats["success_rate"] == 0.0


@pytest.mark.asyncio
async def test_reasoning_evaluation_tracking(metrics_collector):
    """Test tracking reasoning evaluation."""
    # Start tracking
    metrics = metrics_collector.start_reasoning_evaluation("session_123")
    
    # Simulate evaluation work
    await asyncio.sleep(0.1)
    
    # End tracking
    await metrics_collector.end_reasoning_evaluation(
        metrics,
        success=True,
        category="sound_correct"
    )
    
    # Verify metrics
    assert metrics.duration_ms is not None
    assert metrics.duration_ms >= 100
    assert metrics.success is True
    assert metrics.category == "sound_correct"
    
    # Get stats
    stats = metrics_collector.get_reasoning_evaluation_stats()
    assert stats["count"] == 1
    assert stats["avg_duration_ms"] >= 100
    assert stats["success_rate"] == 1.0
    assert stats["category_distribution"]["sound_correct"] == 1


@pytest.mark.asyncio
async def test_reasoning_evaluation_categories(metrics_collector):
    """Test reasoning evaluation category distribution."""
    categories = ["sound_correct", "sound_incorrect", "weak_correct", "weak_incorrect"]
    
    for category in categories:
        metrics = metrics_collector.start_reasoning_evaluation(f"session_{category}")
        await asyncio.sleep(0.01)
        await metrics_collector.end_reasoning_evaluation(
            metrics,
            success=True,
            category=category
        )
    
    stats = metrics_collector.get_reasoning_evaluation_stats()
    assert stats["count"] == 4
    assert len(stats["category_distribution"]) == 4
    
    for category in categories:
        assert stats["category_distribution"][category] == 1


@pytest.mark.asyncio
async def test_session_tracking(metrics_collector):
    """Test session tracking."""
    session_id = "test_session_001"
    case_id = "blackthorn-hall-001"
    
    # Start session
    await metrics_collector.start_session(session_id, case_id)
    
    # Simulate some activity
    await metrics_collector.increment_session_agent_calls(session_id)
    await metrics_collector.increment_session_agent_calls(session_id)
    await metrics_collector.increment_session_state_transitions(session_id)
    
    await asyncio.sleep(0.1)
    
    # End session
    await metrics_collector.end_session(session_id, completed=True, final_state="completed")
    
    # Get stats
    stats = metrics_collector.get_session_completion_stats()
    assert stats["total_sessions"] == 1
    assert stats["completed_sessions"] == 1
    assert stats["completion_rate"] == 1.0
    assert stats["avg_agent_calls"] == 2.0
    assert stats["avg_state_transitions"] == 1.0


@pytest.mark.asyncio
async def test_session_incomplete(metrics_collector):
    """Test tracking incomplete session."""
    session_id = "test_session_002"
    case_id = "blackthorn-hall-001"
    
    # Start session
    await metrics_collector.start_session(session_id, case_id)
    
    await asyncio.sleep(0.05)
    
    # End session as incomplete
    await metrics_collector.end_session(session_id, completed=False, final_state="deliberation")
    
    # Get stats
    stats = metrics_collector.get_session_completion_stats()
    assert stats["total_sessions"] == 1
    assert stats["completed_sessions"] == 0
    assert stats["completion_rate"] == 0.0


@pytest.mark.asyncio
async def test_metrics_summary(metrics_collector):
    """Test getting complete metrics summary."""
    # Add some metrics
    agent_metrics = metrics_collector.start_agent_response("prosecution", "opening")
    await asyncio.sleep(0.01)
    await metrics_collector.end_agent_response(agent_metrics, success=True)
    
    state_metrics = metrics_collector.start_state_transition("hook", "charge")
    await asyncio.sleep(0.01)
    await metrics_collector.end_state_transition(state_metrics, success=True)
    
    reasoning_metrics = metrics_collector.start_reasoning_evaluation("session_001")
    await asyncio.sleep(0.01)
    await metrics_collector.end_reasoning_evaluation(
        reasoning_metrics,
        success=True,
        category="sound_correct"
    )
    
    await metrics_collector.start_session("session_001", "case_001")
    await metrics_collector.end_session("session_001", completed=True)
    
    # Get summary
    summary = metrics_collector.get_summary()
    
    assert "agent_responses" in summary
    assert "state_transitions" in summary
    assert "reasoning_evaluation" in summary
    assert "sessions" in summary
    
    assert summary["agent_responses"]["overall"]["count"] == 1
    assert summary["state_transitions"]["count"] == 1
    assert summary["reasoning_evaluation"]["count"] == 1
    assert summary["sessions"]["total_sessions"] == 1


@pytest.mark.asyncio
async def test_percentile_calculation(metrics_collector):
    """Test percentile calculation for response times."""
    # Add multiple agent responses with varying durations
    for i in range(10):
        metrics = metrics_collector.start_agent_response("test_agent", "test_stage")
        await asyncio.sleep(0.01 * (i + 1))  # Varying durations
        await metrics_collector.end_agent_response(metrics, success=True)
    
    stats = metrics_collector.get_agent_stats()
    assert stats["count"] == 10
    assert stats["p95_duration_ms"] > stats["avg_duration_ms"]
    assert stats["p95_duration_ms"] <= stats["max_duration_ms"]


def test_global_metrics_collector():
    """Test global metrics collector singleton."""
    collector1 = get_metrics_collector()
    collector2 = get_metrics_collector()
    
    # Should be the same instance
    assert collector1 is collector2
    
    # Reset and get new instance
    reset_metrics()
    collector3 = get_metrics_collector()
    
    # Should be a different instance
    assert collector3 is not collector1
