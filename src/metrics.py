"""Performance monitoring and metrics for VERITAS system."""

import time
import logging
from typing import Optional, Literal, Dict, Any
from datetime import datetime
from collections import defaultdict
from dataclasses import dataclass, field
import asyncio

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("veritas")


@dataclass
class AgentMetrics:
    """Metrics for a single agent response."""
    agent_role: str
    stage: str
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    success: bool = True
    used_fallback: bool = False
    error: Optional[str] = None


@dataclass
class StateTransitionMetrics:
    """Metrics for a state transition."""
    from_state: str
    to_state: str
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    success: bool = True
    error: Optional[str] = None


@dataclass
class ReasoningEvaluationMetrics:
    """Metrics for reasoning evaluation."""
    session_id: str
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    success: bool = True
    category: Optional[str] = None
    error: Optional[str] = None


@dataclass
class SessionMetrics:
    """Metrics for a complete session."""
    session_id: str
    case_id: str
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    completed: bool = False
    final_state: Optional[str] = None
    agent_calls: int = 0
    state_transitions: int = 0
    verdict: Optional[str] = None  # Task 26.4: Track verdict for case statistics
    bot_failovers: int = 0  # Task 27.2: Track bot failover count


class MetricsCollector:
    """
    Collects and aggregates performance metrics for the VERITAS system.
    
    Tracks agent response times, state transitions, reasoning evaluation,
    and session completion rates.
    """
    
    def __init__(self):
        """Initialize metrics collector."""
        self._agent_metrics: list[AgentMetrics] = []
        self._state_transition_metrics: list[StateTransitionMetrics] = []
        self._reasoning_metrics: list[ReasoningEvaluationMetrics] = []
        self._session_metrics: Dict[str, SessionMetrics] = {}
        self._lock = asyncio.Lock()
    
    # ========================================================================
    # Agent Response Tracking
    # ========================================================================
    
    def start_agent_response(self, agent_role: str, stage: str) -> AgentMetrics:
        """
        Start tracking an agent response.
        
        Args:
            agent_role: The agent role (clerk, prosecution, defence, etc.)
            stage: The current stage
            
        Returns:
            AgentMetrics object to be completed later
        """
        metrics = AgentMetrics(
            agent_role=agent_role,
            stage=stage,
            start_time=time.time()
        )
        return metrics
    
    async def end_agent_response(
        self,
        metrics: AgentMetrics,
        success: bool = True,
        used_fallback: bool = False,
        error: Optional[str] = None
    ):
        """
        Complete tracking an agent response.
        
        Args:
            metrics: The AgentMetrics object from start_agent_response
            success: Whether the response succeeded
            used_fallback: Whether fallback was used
            error: Error message if failed
        """
        metrics.end_time = time.time()
        metrics.duration_ms = (metrics.end_time - metrics.start_time) * 1000
        metrics.success = success
        metrics.used_fallback = used_fallback
        metrics.error = error
        
        async with self._lock:
            self._agent_metrics.append(metrics)
        
        # Log slow responses
        if metrics.duration_ms > 10000:  # > 10 seconds (GPT-4o typically 5-9s)
            logger.warning(
                f"Slow agent response: {metrics.agent_role} at {metrics.stage} "
                f"took {metrics.duration_ms:.0f}ms"
            )
    
    def get_agent_stats(
        self,
        agent_role: Optional[str] = None,
        stage: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get aggregated agent response statistics.
        
        Args:
            agent_role: Filter by agent role (optional)
            stage: Filter by stage (optional)
            
        Returns:
            Dictionary with statistics
        """
        # Filter metrics
        filtered = self._agent_metrics
        if agent_role:
            filtered = [m for m in filtered if m.agent_role == agent_role]
        if stage:
            filtered = [m for m in filtered if m.stage == stage]
        
        if not filtered:
            return {
                "count": 0,
                "avg_duration_ms": 0,
                "min_duration_ms": 0,
                "max_duration_ms": 0,
                "success_rate": 0,
                "fallback_rate": 0
            }
        
        durations = [m.duration_ms for m in filtered if m.duration_ms is not None]
        successes = sum(1 for m in filtered if m.success)
        fallbacks = sum(1 for m in filtered if m.used_fallback)
        
        return {
            "count": len(filtered),
            "avg_duration_ms": sum(durations) / len(durations) if durations else 0,
            "min_duration_ms": min(durations) if durations else 0,
            "max_duration_ms": max(durations) if durations else 0,
            "p95_duration_ms": self._percentile(durations, 0.95) if durations else 0,
            "success_rate": successes / len(filtered) if filtered else 0,
            "fallback_rate": fallbacks / len(filtered) if filtered else 0
        }
    
    def get_agent_stats_by_role(self) -> Dict[str, Dict[str, Any]]:
        """
        Get agent statistics grouped by role.
        
        Returns:
            Dictionary mapping agent role to statistics
        """
        roles = set(m.agent_role for m in self._agent_metrics)
        return {
            role: self.get_agent_stats(agent_role=role)
            for role in roles
        }
    
    def get_agent_stats_by_stage(self) -> Dict[str, Dict[str, Any]]:
        """
        Get agent statistics grouped by stage.
        
        Returns:
            Dictionary mapping stage to statistics
        """
        stages = set(m.stage for m in self._agent_metrics)
        return {
            stage: self.get_agent_stats(stage=stage)
            for stage in stages
        }
    
    # ========================================================================
    # State Transition Tracking
    # ========================================================================
    
    def start_state_transition(self, from_state: str, to_state: str) -> StateTransitionMetrics:
        """
        Start tracking a state transition.
        
        Args:
            from_state: The current state
            to_state: The target state
            
        Returns:
            StateTransitionMetrics object to be completed later
        """
        metrics = StateTransitionMetrics(
            from_state=from_state,
            to_state=to_state,
            start_time=time.time()
        )
        return metrics
    
    async def end_state_transition(
        self,
        metrics: StateTransitionMetrics,
        success: bool = True,
        error: Optional[str] = None
    ):
        """
        Complete tracking a state transition.
        
        Args:
            metrics: The StateTransitionMetrics object from start_state_transition
            success: Whether the transition succeeded
            error: Error message if failed
        """
        metrics.end_time = time.time()
        metrics.duration_ms = (metrics.end_time - metrics.start_time) * 1000
        metrics.success = success
        metrics.error = error
        
        async with self._lock:
            self._state_transition_metrics.append(metrics)
        
        # Log slow transitions
        if metrics.duration_ms > 1000:  # > 1 second
            logger.warning(
                f"Slow state transition: {metrics.from_state} -> {metrics.to_state} "
                f"took {metrics.duration_ms:.0f}ms"
            )
    
    def get_state_transition_stats(
        self,
        from_state: Optional[str] = None,
        to_state: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get aggregated state transition statistics.
        
        Args:
            from_state: Filter by source state (optional)
            to_state: Filter by target state (optional)
            
        Returns:
            Dictionary with statistics
        """
        # Filter metrics
        filtered = self._state_transition_metrics
        if from_state:
            filtered = [m for m in filtered if m.from_state == from_state]
        if to_state:
            filtered = [m for m in filtered if m.to_state == to_state]
        
        if not filtered:
            return {
                "count": 0,
                "avg_duration_ms": 0,
                "min_duration_ms": 0,
                "max_duration_ms": 0,
                "success_rate": 0
            }
        
        durations = [m.duration_ms for m in filtered if m.duration_ms is not None]
        successes = sum(1 for m in filtered if m.success)
        
        return {
            "count": len(filtered),
            "avg_duration_ms": sum(durations) / len(durations) if durations else 0,
            "min_duration_ms": min(durations) if durations else 0,
            "max_duration_ms": max(durations) if durations else 0,
            "p95_duration_ms": self._percentile(durations, 0.95) if durations else 0,
            "success_rate": successes / len(filtered) if filtered else 0
        }
    
    # ========================================================================
    # Reasoning Evaluation Tracking
    # ========================================================================
    
    def start_reasoning_evaluation(self, session_id: str) -> ReasoningEvaluationMetrics:
        """
        Start tracking reasoning evaluation.
        
        Args:
            session_id: The session ID
            
        Returns:
            ReasoningEvaluationMetrics object to be completed later
        """
        metrics = ReasoningEvaluationMetrics(
            session_id=session_id,
            start_time=time.time()
        )
        return metrics
    
    async def end_reasoning_evaluation(
        self,
        metrics: ReasoningEvaluationMetrics,
        success: bool = True,
        category: Optional[str] = None,
        error: Optional[str] = None
    ):
        """
        Complete tracking reasoning evaluation.
        
        Args:
            metrics: The ReasoningEvaluationMetrics object from start_reasoning_evaluation
            success: Whether the evaluation succeeded
            category: The reasoning category (sound_correct, etc.)
            error: Error message if failed
        """
        metrics.end_time = time.time()
        metrics.duration_ms = (metrics.end_time - metrics.start_time) * 1000
        metrics.success = success
        metrics.category = category
        metrics.error = error
        
        async with self._lock:
            self._reasoning_metrics.append(metrics)
        
        # Log slow evaluations (should complete within 10 seconds)
        if metrics.duration_ms > 10000:
            logger.warning(
                f"Slow reasoning evaluation for session {metrics.session_id}: "
                f"{metrics.duration_ms:.0f}ms"
            )
    
    def get_reasoning_evaluation_stats(self) -> Dict[str, Any]:
        """
        Get aggregated reasoning evaluation statistics.
        
        Returns:
            Dictionary with statistics
        """
        if not self._reasoning_metrics:
            return {
                "count": 0,
                "avg_duration_ms": 0,
                "min_duration_ms": 0,
                "max_duration_ms": 0,
                "success_rate": 0,
                "category_distribution": {}
            }
        
        durations = [m.duration_ms for m in self._reasoning_metrics if m.duration_ms is not None]
        successes = sum(1 for m in self._reasoning_metrics if m.success)
        
        # Category distribution
        category_counts = defaultdict(int)
        for m in self._reasoning_metrics:
            if m.category:
                category_counts[m.category] += 1
        
        return {
            "count": len(self._reasoning_metrics),
            "avg_duration_ms": sum(durations) / len(durations) if durations else 0,
            "min_duration_ms": min(durations) if durations else 0,
            "max_duration_ms": max(durations) if durations else 0,
            "p95_duration_ms": self._percentile(durations, 0.95) if durations else 0,
            "success_rate": successes / len(self._reasoning_metrics),
            "category_distribution": dict(category_counts)
        }
    
    # ========================================================================
    # Session Tracking
    # ========================================================================
    
    async def start_session(self, session_id: str, case_id: str):
        """
        Start tracking a session.
        
        Args:
            session_id: The session ID
            case_id: The case ID
        """
        async with self._lock:
            self._session_metrics[session_id] = SessionMetrics(
                session_id=session_id,
                case_id=case_id,
                start_time=time.time()
            )
    
    async def end_session(
        self,
        session_id: str,
        completed: bool = True,
        final_state: Optional[str] = None,
        verdict: Optional[str] = None
    ):
        """
        Complete tracking a session.
        
        Args:
            session_id: The session ID
            completed: Whether the session completed successfully
            final_state: The final state reached
            verdict: The jury verdict (guilty/not_guilty) for case statistics
        """
        async with self._lock:
            if session_id in self._session_metrics:
                metrics = self._session_metrics[session_id]
                metrics.end_time = time.time()
                metrics.duration_ms = (metrics.end_time - metrics.start_time) * 1000
                metrics.completed = completed
                metrics.final_state = final_state
                metrics.verdict = verdict
    
    async def increment_session_agent_calls(self, session_id: str):
        """Increment agent call count for a session."""
        async with self._lock:
            if session_id in self._session_metrics:
                self._session_metrics[session_id].agent_calls += 1
    
    async def increment_session_state_transitions(self, session_id: str):
        """Increment state transition count for a session."""
        async with self._lock:
            if session_id in self._session_metrics:
                self._session_metrics[session_id].state_transitions += 1
    
    async def record_bot_failover(self, session_id: str):
        """
        Record a bot failover event for a session.
        
        Args:
            session_id: The session ID
        """
        async with self._lock:
            if session_id in self._session_metrics:
                self._session_metrics[session_id].bot_failovers += 1
    
    def get_session_completion_stats(self) -> Dict[str, Any]:
        """
        Get session completion statistics.
        
        Returns:
            Dictionary with statistics
        """
        if not self._session_metrics:
            return {
                "total_sessions": 0,
                "completed_sessions": 0,
                "completion_rate": 0,
                "avg_duration_ms": 0,
                "avg_agent_calls": 0,
                "avg_state_transitions": 0
            }
        
        sessions = list(self._session_metrics.values())
        completed = [s for s in sessions if s.completed]
        durations = [s.duration_ms for s in completed if s.duration_ms is not None]
        
        return {
            "total_sessions": len(sessions),
            "completed_sessions": len(completed),
            "completion_rate": len(completed) / len(sessions) if sessions else 0,
            "avg_duration_ms": sum(durations) / len(durations) if durations else 0,
            "avg_agent_calls": sum(s.agent_calls for s in sessions) / len(sessions) if sessions else 0,
            "avg_state_transitions": sum(s.state_transitions for s in sessions) / len(sessions) if sessions else 0
        }
    
    # ========================================================================
    # Utility Methods
    # ========================================================================
    
    def _percentile(self, values: list[float], percentile: float) -> float:
        """Calculate percentile of values."""
        if not values:
            return 0
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile)
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all metrics.
        
        Returns:
            Dictionary with all statistics
        """
        return {
            "agent_responses": {
                "overall": self.get_agent_stats(),
                "by_role": self.get_agent_stats_by_role(),
                "by_stage": self.get_agent_stats_by_stage()
            },
            "state_transitions": self.get_state_transition_stats(),
            "reasoning_evaluation": self.get_reasoning_evaluation_stats(),
            "sessions": self.get_session_completion_stats()
        }
    
    def get_case_verdict_stats(self, case_id: str) -> Dict[str, Any]:
        """
        Get verdict statistics for a specific case.
        
        Args:
            case_id: The case ID to get statistics for
            
        Returns:
            Dictionary with verdict statistics:
            - total: Total number of completed sessions for this case
            - guilty_count: Number of guilty verdicts
            - not_guilty_count: Number of not guilty verdicts
            - guilty_pct: Percentage of guilty verdicts
            - not_guilty_pct: Percentage of not guilty verdicts
        """
        # Filter completed sessions for this case with verdicts
        case_sessions = [
            m for m in self._session_metrics.values()
            if m.case_id == case_id and m.completed and m.verdict
        ]
        
        total = len(case_sessions)
        
        if total == 0:
            return {
                "total": 0,
                "guilty_count": 0,
                "not_guilty_count": 0,
                "guilty_pct": 0.0,
                "not_guilty_pct": 0.0
            }
        
        guilty_count = sum(1 for m in case_sessions if m.verdict == "guilty")
        not_guilty_count = total - guilty_count
        
        return {
            "total": total,
            "guilty_count": guilty_count,
            "not_guilty_count": not_guilty_count,
            "guilty_pct": round((guilty_count / total) * 100, 1),
            "not_guilty_pct": round((not_guilty_count / total) * 100, 1)
        }
    
    def log_summary(self):
        """Log a summary of all metrics."""
        summary = self.get_summary()
        
        print("INFO:veritas:=== VERITAS Performance Metrics Summary ===")
        
        # Agent responses
        agent_overall = summary["agent_responses"]["overall"]
        print(
            f"INFO:veritas:Agent Responses: {agent_overall['count']} calls, "
            f"avg {agent_overall['avg_duration_ms']:.0f}ms, "
            f"p95 {agent_overall['p95_duration_ms']:.0f}ms, "
            f"success rate {agent_overall['success_rate']:.1%}, "
            f"fallback rate {agent_overall['fallback_rate']:.1%}"
        )
        
        # By role
        for role, stats in summary["agent_responses"]["by_role"].items():
            print(
                f"INFO:veritas:  {role}: {stats['count']} calls, "
                f"avg {stats['avg_duration_ms']:.0f}ms, "
                f"p95 {stats['p95_duration_ms']:.0f}ms"
            )
        
        # State transitions
        state_stats = summary["state_transitions"]
        print(
            f"INFO:veritas:State Transitions: {state_stats['count']} transitions, "
            f"avg {state_stats['avg_duration_ms']:.0f}ms, "
            f"p95 {state_stats['p95_duration_ms']:.0f}ms"
        )
        
        # Reasoning evaluation
        reasoning_stats = summary["reasoning_evaluation"]
        print(
            f"INFO:veritas:Reasoning Evaluations: {reasoning_stats['count']} evaluations, "
            f"avg {reasoning_stats['avg_duration_ms']:.0f}ms, "
            f"p95 {reasoning_stats['p95_duration_ms']:.0f}ms"
        )
        if reasoning_stats["category_distribution"]:
            print(f"INFO:veritas:  Category distribution: {reasoning_stats['category_distribution']}")
        
        # Sessions
        session_stats = summary["sessions"]
        print(
            f"INFO:veritas:Sessions: {session_stats['total_sessions']} total, "
            f"{session_stats['completed_sessions']} completed, "
            f"completion rate {session_stats['completion_rate']:.1%}, "
            f"avg duration {session_stats['avg_duration_ms'] / 1000:.1f}s"
        )
        
        print("INFO:veritas:" + "=" * 50)


# Global metrics collector instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """
    Get the global metrics collector instance.
    
    Returns:
        MetricsCollector instance
    """
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


def reset_metrics():
    """Reset the global metrics collector."""
    global _metrics_collector
    _metrics_collector = MetricsCollector()
