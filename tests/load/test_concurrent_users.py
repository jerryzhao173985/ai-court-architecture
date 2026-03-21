"""
Load test for VERITAS system with concurrent users.

Simulates 10+ concurrent sessions to measure response times,
identify bottlenecks, and verify error handling under stress.

Requirements: All requirements (comprehensive system test)
"""

import asyncio
import time
import statistics
from typing import List, Dict, Any
from datetime import datetime
import logging

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from orchestrator import ExperienceOrchestrator
from config import load_config
from metrics import get_metrics_collector, reset_metrics
from state_machine import ExperienceState

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("load_test")


class LoadTestMetrics:
    """Metrics collector for load testing."""
    
    def __init__(self):
        self.session_times: List[float] = []
        self.stage_times: Dict[str, List[float]] = {}
        self.errors: List[Dict[str, Any]] = []
        self.concurrent_sessions: int = 0
        self.start_time: float = 0
        self.end_time: float = 0
    
    def record_session_time(self, duration: float):
        """Record total session duration."""
        self.session_times.append(duration)
    
    def record_stage_time(self, stage: str, duration: float):
        """Record stage execution time."""
        if stage not in self.stage_times:
            self.stage_times[stage] = []
        self.stage_times[stage].append(duration)
    
    def record_error(self, session_id: str, operation: str, error: str):
        """Record an error."""
        self.errors.append({
            "session_id": session_id,
            "operation": operation,
            "error": error,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics."""
        total_duration = self.end_time - self.start_time
        
        summary = {
            "test_duration_seconds": total_duration,
            "concurrent_sessions": self.concurrent_sessions,
            "total_errors": len(self.errors),
            "error_rate": len(self.errors) / self.concurrent_sessions if self.concurrent_sessions > 0 else 0,
            "sessions": {
                "count": len(self.session_times),
                "avg_duration_seconds": statistics.mean(self.session_times) if self.session_times else 0,
                "min_duration_seconds": min(self.session_times) if self.session_times else 0,
                "max_duration_seconds": max(self.session_times) if self.session_times else 0,
                "median_duration_seconds": statistics.median(self.session_times) if self.session_times else 0,
                "p95_duration_seconds": self._percentile(self.session_times, 0.95) if self.session_times else 0,
                "p99_duration_seconds": self._percentile(self.session_times, 0.99) if self.session_times else 0
            },
            "stages": {}
        }
        
        # Add per-stage statistics
        for stage, times in self.stage_times.items():
            summary["stages"][stage] = {
                "count": len(times),
                "avg_duration_seconds": statistics.mean(times) if times else 0,
                "min_duration_seconds": min(times) if times else 0,
                "max_duration_seconds": max(times) if times else 0,
                "median_duration_seconds": statistics.median(times) if times else 0,
                "p95_duration_seconds": self._percentile(times, 0.95) if times else 0
            }
        
        return summary
    
    def _percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile of values."""
        if not values:
            return 0
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile)
        return sorted_values[min(index, len(sorted_values) - 1)]


async def simulate_user_session(
    session_id: str,
    user_id: str,
    case_id: str,
    metrics: LoadTestMetrics
) -> Dict[str, Any]:
    """
    Simulate a complete user session through the experience.
    
    Args:
        session_id: Unique session identifier
        user_id: User identifier
        case_id: Case identifier
        metrics: Metrics collector
        
    Returns:
        Session result with timing and status
    """
    session_start = time.time()
    result = {
        "session_id": session_id,
        "success": False,
        "stages_completed": [],
        "errors": []
    }
    
    orchestrator = None
    
    try:
        # Initialize orchestrator
        orchestrator = ExperienceOrchestrator(
            session_id=session_id,
            user_id=user_id,
            case_id=case_id
        )
        
        # Initialize experience
        stage_start = time.time()
        init_result = await orchestrator.initialize()
        stage_duration = time.time() - stage_start
        
        if not init_result["success"]:
            metrics.record_error(session_id, "initialize", init_result.get("error", "Unknown error"))
            result["errors"].append(f"Initialize failed: {init_result.get('error')}")
            return result
        
        metrics.record_stage_time("initialize", stage_duration)
        result["stages_completed"].append("initialize")
        
        # Start experience (hook scene)
        stage_start = time.time()
        start_result = await orchestrator.start_experience()
        stage_duration = time.time() - stage_start
        
        if not start_result["success"]:
            metrics.record_error(session_id, "start_experience", start_result.get("error", "Unknown error"))
            result["errors"].append(f"Start failed: {start_result.get('error')}")
            return result
        
        metrics.record_stage_time("hook_scene", stage_duration)
        result["stages_completed"].append("hook_scene")
        
        # Advance through trial stages
        trial_stages = [
            ExperienceState.CHARGE_READING,
            ExperienceState.PROSECUTION_OPENING,
            ExperienceState.DEFENCE_OPENING,
            ExperienceState.EVIDENCE_PRESENTATION,
            ExperienceState.CROSS_EXAMINATION,
            ExperienceState.PROSECUTION_CLOSING,
            ExperienceState.DEFENCE_CLOSING,
            ExperienceState.JUDGE_SUMMING_UP
        ]
        
        for expected_stage in trial_stages:
            stage_start = time.time()
            advance_result = await orchestrator.advance_trial_stage()
            stage_duration = time.time() - stage_start
            
            if not advance_result["success"]:
                metrics.record_error(session_id, f"advance_to_{expected_stage.value}", advance_result.get("error", "Unknown error"))
                result["errors"].append(f"Advance to {expected_stage.value} failed: {advance_result.get('error')}")
                return result
            
            metrics.record_stage_time(expected_stage.value, stage_duration)
            result["stages_completed"].append(expected_stage.value)
        
        # Start deliberation
        stage_start = time.time()
        delib_result = await orchestrator.advance_trial_stage()
        stage_duration = time.time() - stage_start
        
        if not delib_result["success"]:
            metrics.record_error(session_id, "start_deliberation", delib_result.get("error", "Unknown error"))
            result["errors"].append(f"Deliberation failed: {delib_result.get('error')}")
            return result
        
        metrics.record_stage_time("jury_deliberation", stage_duration)
        result["stages_completed"].append("jury_deliberation")
        
        # Submit deliberation statement
        stage_start = time.time()
        statement_result = await orchestrator.submit_deliberation_statement(
            "I believe the evidence shows reasonable doubt about the defendant's guilt.",
            evidence_refs=[]
        )
        stage_duration = time.time() - stage_start
        
        if not statement_result["success"]:
            metrics.record_error(session_id, "submit_statement", statement_result.get("error", "Unknown error"))
            result["errors"].append(f"Statement submission failed: {statement_result.get('error')}")
            return result
        
        metrics.record_stage_time("deliberation_statement", stage_duration)
        
        # Submit vote
        stage_start = time.time()
        vote_result = await orchestrator.submit_vote("not_guilty")
        stage_duration = time.time() - stage_start
        
        if not vote_result["success"]:
            metrics.record_error(session_id, "submit_vote", vote_result.get("error", "Unknown error"))
            result["errors"].append(f"Vote submission failed: {vote_result.get('error')}")
            return result
        
        metrics.record_stage_time("vote_and_reveal", stage_duration)
        result["stages_completed"].append("vote_and_reveal")
        
        # Complete experience
        stage_start = time.time()
        complete_result = await orchestrator.complete_experience(share_verdict=False)
        stage_duration = time.time() - stage_start
        
        if not complete_result["success"]:
            metrics.record_error(session_id, "complete_experience", complete_result.get("error", "Unknown error"))
            result["errors"].append(f"Completion failed: {complete_result.get('error')}")
            return result
        
        metrics.record_stage_time("complete", stage_duration)
        result["stages_completed"].append("complete")
        
        # Mark as successful
        result["success"] = True
        
    except Exception as e:
        logger.error(f"Session {session_id} failed with exception: {e}")
        metrics.record_error(session_id, "exception", str(e))
        result["errors"].append(f"Exception: {str(e)}")
    
    finally:
        # Cleanup orchestrator and end session tracking
        if orchestrator:
            try:
                await orchestrator.cleanup(completed=result["success"])
            except Exception as e:
                logger.error(f"Cleanup failed for session {session_id}: {e}")
        
        session_duration = time.time() - session_start
        metrics.record_session_time(session_duration)
        result["duration_seconds"] = session_duration
    
    return result


async def run_load_test(
    num_concurrent_users: int = 10,
    case_id: str = "blackthorn-hall-001"
) -> Dict[str, Any]:
    """
    Run load test with concurrent users.
    
    Args:
        num_concurrent_users: Number of concurrent sessions to simulate
        case_id: Case ID to use for all sessions
        
    Returns:
        Test results with metrics and summary
    """
    logger.info(f"Starting load test with {num_concurrent_users} concurrent users")
    
    # Reset metrics
    reset_metrics()
    
    # Initialize load test metrics
    load_metrics = LoadTestMetrics()
    load_metrics.concurrent_sessions = num_concurrent_users
    load_metrics.start_time = time.time()
    
    # Create tasks for all concurrent sessions
    tasks = []
    for i in range(num_concurrent_users):
        session_id = f"load_test_session_{i}_{int(time.time())}"
        user_id = f"load_test_user_{i}"
        
        task = simulate_user_session(
            session_id=session_id,
            user_id=user_id,
            case_id=case_id,
            metrics=load_metrics
        )
        tasks.append(task)
    
    # Run all sessions concurrently
    logger.info("Running concurrent sessions...")
    session_results = await asyncio.gather(*tasks, return_exceptions=True)
    
    load_metrics.end_time = time.time()
    
    # Process results
    successful_sessions = 0
    failed_sessions = 0
    
    for result in session_results:
        if isinstance(result, Exception):
            failed_sessions += 1
            logger.error(f"Session failed with exception: {result}")
        elif result.get("success"):
            successful_sessions += 1
        else:
            failed_sessions += 1
    
    # Get system metrics
    system_metrics = get_metrics_collector()
    system_summary = system_metrics.get_summary()
    
    # Compile final results
    test_results = {
        "load_test": load_metrics.get_summary(),
        "system_metrics": system_summary,
        "session_results": {
            "total": num_concurrent_users,
            "successful": successful_sessions,
            "failed": failed_sessions,
            "success_rate": successful_sessions / num_concurrent_users if num_concurrent_users > 0 else 0
        },
        "errors": load_metrics.errors
    }
    
    return test_results


def print_test_results(results: Dict[str, Any]):
    """Print formatted test results."""
    print("\n" + "=" * 80)
    print("VERITAS LOAD TEST RESULTS")
    print("=" * 80)
    
    # Load test summary
    load_test = results["load_test"]
    print(f"\nTest Duration: {load_test['test_duration_seconds']:.2f}s")
    print(f"Concurrent Sessions: {load_test['concurrent_sessions']}")
    print(f"Total Errors: {load_test['total_errors']}")
    print(f"Error Rate: {load_test['error_rate']:.1%}")
    
    # Session statistics
    sessions = load_test["sessions"]
    print(f"\nSession Statistics:")
    print(f"  Count: {sessions['count']}")
    print(f"  Avg Duration: {sessions['avg_duration_seconds']:.2f}s")
    print(f"  Min Duration: {sessions['min_duration_seconds']:.2f}s")
    print(f"  Max Duration: {sessions['max_duration_seconds']:.2f}s")
    print(f"  Median Duration: {sessions['median_duration_seconds']:.2f}s")
    print(f"  P95 Duration: {sessions['p95_duration_seconds']:.2f}s")
    print(f"  P99 Duration: {sessions['p99_duration_seconds']:.2f}s")
    
    # Stage statistics
    print(f"\nStage Performance:")
    for stage, stats in load_test["stages"].items():
        print(f"  {stage}:")
        print(f"    Count: {stats['count']}")
        print(f"    Avg: {stats['avg_duration_seconds']:.2f}s")
        print(f"    P95: {stats['p95_duration_seconds']:.2f}s")
    
    # System metrics
    system = results["system_metrics"]
    
    # Agent responses
    agent_overall = system["agent_responses"]["overall"]
    print(f"\nAgent Response Performance:")
    print(f"  Total Calls: {agent_overall['count']}")
    print(f"  Avg Duration: {agent_overall['avg_duration_ms']:.0f}ms")
    print(f"  P95 Duration: {agent_overall['p95_duration_ms']:.0f}ms")
    print(f"  Success Rate: {agent_overall['success_rate']:.1%}")
    print(f"  Fallback Rate: {agent_overall['fallback_rate']:.1%}")
    
    # By role
    print(f"\n  By Role:")
    for role, stats in system["agent_responses"]["by_role"].items():
        print(f"    {role}: {stats['count']} calls, avg {stats['avg_duration_ms']:.0f}ms, p95 {stats['p95_duration_ms']:.0f}ms")
    
    # State transitions
    state_stats = system["state_transitions"]
    print(f"\nState Transition Performance:")
    print(f"  Total Transitions: {state_stats['count']}")
    print(f"  Avg Duration: {state_stats['avg_duration_ms']:.0f}ms")
    print(f"  P95 Duration: {state_stats['p95_duration_ms']:.0f}ms")
    
    # Session completion
    session_stats = system["sessions"]
    print(f"\nSession Completion:")
    print(f"  Total Sessions: {session_stats['total_sessions']}")
    print(f"  Completed: {session_stats['completed_sessions']}")
    print(f"  Completion Rate: {session_stats['completion_rate']:.1%}")
    print(f"  Avg Duration: {session_stats['avg_duration_ms'] / 1000:.1f}s")
    
    # Session results
    session_results = results["session_results"]
    print(f"\nSession Results:")
    print(f"  Total: {session_results['total']}")
    print(f"  Successful: {session_results['successful']}")
    print(f"  Failed: {session_results['failed']}")
    print(f"  Success Rate: {session_results['success_rate']:.1%}")
    
    # Errors
    if results["errors"]:
        print(f"\nErrors ({len(results['errors'])}):")
        for error in results["errors"][:10]:  # Show first 10 errors
            print(f"  [{error['session_id']}] {error['operation']}: {error['error']}")
        if len(results["errors"]) > 10:
            print(f"  ... and {len(results['errors']) - 10} more errors")
    
    print("\n" + "=" * 80)


async def main():
    """Main entry point for load test."""
    # Run load test with 10 concurrent users
    results = await run_load_test(num_concurrent_users=10)
    
    # Print results
    print_test_results(results)
    
    # Identify bottlenecks
    print("\nBOTTLENECK ANALYSIS:")
    print("-" * 80)
    
    # Check for slow stages
    load_test = results["load_test"]
    slow_stages = []
    for stage, stats in load_test["stages"].items():
        if stats["p95_duration_seconds"] > 5.0:  # Stages taking >5s at P95
            slow_stages.append((stage, stats["p95_duration_seconds"]))
    
    if slow_stages:
        print("\nSlow Stages (P95 > 5s):")
        for stage, duration in sorted(slow_stages, key=lambda x: x[1], reverse=True):
            print(f"  {stage}: {duration:.2f}s")
    else:
        print("\nNo slow stages detected (all P95 < 5s)")
    
    # Check for high agent response times
    agent_stats = results["system_metrics"]["agent_responses"]["by_role"]
    slow_agents = []
    for role, stats in agent_stats.items():
        if stats["p95_duration_ms"] > 3000:  # Agents taking >3s at P95
            slow_agents.append((role, stats["p95_duration_ms"]))
    
    if slow_agents:
        print("\nSlow Agents (P95 > 3s):")
        for role, duration in sorted(slow_agents, key=lambda x: x[1], reverse=True):
            print(f"  {role}: {duration:.0f}ms")
    else:
        print("\nNo slow agents detected (all P95 < 3s)")
    
    # Check error rate
    error_rate = load_test["error_rate"]
    if error_rate > 0.05:  # >5% error rate
        print(f"\n⚠️  HIGH ERROR RATE: {error_rate:.1%}")
        print("   Review error logs for details")
    else:
        print(f"\n✓ Error rate acceptable: {error_rate:.1%}")
    
    # Check success rate
    success_rate = results["session_results"]["success_rate"]
    if success_rate < 0.95:  # <95% success rate
        print(f"\n⚠️  LOW SUCCESS RATE: {success_rate:.1%}")
        print("   Review failed sessions for details")
    else:
        print(f"\n✓ Success rate good: {success_rate:.1%}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
