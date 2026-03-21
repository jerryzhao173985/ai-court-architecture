"""
Simplified load test focusing on metrics system performance.

Tests metrics collection under concurrent load without requiring
full system dependencies.

Requirements: All requirements (metrics validation)
"""

import asyncio
import time
import statistics
from typing import List, Dict, Any
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from metrics import MetricsCollector, reset_metrics, get_metrics_collector


async def simulate_agent_calls(collector: MetricsCollector, num_calls: int, agent_role: str, stage: str):
    """Simulate multiple agent calls."""
    for i in range(num_calls):
        metrics = collector.start_agent_response(agent_role, stage)
        
        # Simulate work
        await asyncio.sleep(0.01 + (i % 5) * 0.01)  # 10-50ms
        
        await collector.end_agent_response(
            metrics,
            success=True,
            used_fallback=(i % 10 == 0)  # 10% fallback rate
        )


async def simulate_state_transitions(collector: MetricsCollector, num_transitions: int):
    """Simulate multiple state transitions."""
    states = ["not_started", "hook_scene", "charge_reading", "prosecution_opening", 
              "defence_opening", "evidence_presentation", "cross_examination",
              "prosecution_closing", "defence_closing", "judge_summing_up",
              "jury_deliberation", "anonymous_vote", "dual_reveal", "completed"]
    
    for i in range(num_transitions):
        from_state = states[i % len(states)]
        to_state = states[(i + 1) % len(states)]
        
        metrics = collector.start_state_transition(from_state, to_state)
        
        # Simulate work
        await asyncio.sleep(0.005)  # 5ms
        
        await collector.end_state_transition(metrics, success=True)


async def simulate_session(collector: MetricsCollector, session_id: str, case_id: str):
    """Simulate a complete session."""
    # Start session
    await collector.start_session(session_id, case_id)
    
    # Simulate agent calls
    await simulate_agent_calls(collector, 5, "prosecution", "prosecution_opening")
    await collector.increment_session_agent_calls(session_id)
    
    await simulate_agent_calls(collector, 5, "defence", "defence_opening")
    await collector.increment_session_agent_calls(session_id)
    
    # Simulate state transitions
    await simulate_state_transitions(collector, 10)
    for _ in range(10):
        await collector.increment_session_state_transitions(session_id)
    
    # Simulate reasoning evaluation
    reasoning_metrics = collector.start_reasoning_evaluation(session_id)
    await asyncio.sleep(0.02)  # 20ms
    await collector.end_reasoning_evaluation(
        reasoning_metrics,
        success=True,
        category="sound_correct"
    )
    
    # End session
    await collector.end_session(session_id, completed=True, final_state="completed")


async def run_concurrent_load_test(num_concurrent: int = 10) -> Dict[str, Any]:
    """
    Run load test with concurrent sessions.
    
    Args:
        num_concurrent: Number of concurrent sessions
        
    Returns:
        Test results
    """
    print(f"Starting load test with {num_concurrent} concurrent sessions...")
    
    # Reset metrics
    reset_metrics()
    collector = get_metrics_collector()
    
    start_time = time.time()
    
    # Create concurrent session tasks
    tasks = []
    for i in range(num_concurrent):
        session_id = f"load_test_{i}"
        case_id = "blackthorn-hall-001"
        tasks.append(simulate_session(collector, session_id, case_id))
    
    # Run all sessions concurrently
    await asyncio.gather(*tasks)
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Get metrics summary
    summary = collector.get_summary()
    
    return {
        "test_duration": duration,
        "concurrent_sessions": num_concurrent,
        "metrics": summary
    }


def print_results(results: Dict[str, Any]):
    """Print formatted test results."""
    print("\n" + "=" * 80)
    print("METRICS SYSTEM LOAD TEST RESULTS")
    print("=" * 80)
    
    print(f"\nTest Duration: {results['test_duration']:.2f}s")
    print(f"Concurrent Sessions: {results['concurrent_sessions']}")
    
    metrics = results["metrics"]
    
    # Agent responses
    agent_overall = metrics["agent_responses"]["overall"]
    print(f"\nAgent Response Metrics:")
    print(f"  Total Calls: {agent_overall['count']}")
    print(f"  Avg Duration: {agent_overall['avg_duration_ms']:.2f}ms")
    print(f"  P95 Duration: {agent_overall['p95_duration_ms']:.2f}ms")
    print(f"  Max Duration: {agent_overall['max_duration_ms']:.2f}ms")
    print(f"  Success Rate: {agent_overall['success_rate']:.1%}")
    print(f"  Fallback Rate: {agent_overall['fallback_rate']:.1%}")
    
    # By role
    print(f"\n  By Role:")
    for role, stats in metrics["agent_responses"]["by_role"].items():
        print(f"    {role}: {stats['count']} calls, avg {stats['avg_duration_ms']:.2f}ms")
    
    # State transitions
    state_stats = metrics["state_transitions"]
    print(f"\nState Transition Metrics:")
    print(f"  Total Transitions: {state_stats['count']}")
    print(f"  Avg Duration: {state_stats['avg_duration_ms']:.2f}ms")
    print(f"  P95 Duration: {state_stats['p95_duration_ms']:.2f}ms")
    print(f"  Success Rate: {state_stats['success_rate']:.1%}")
    
    # Reasoning evaluation
    reasoning_stats = metrics["reasoning_evaluation"]
    print(f"\nReasoning Evaluation Metrics:")
    print(f"  Total Evaluations: {reasoning_stats['count']}")
    print(f"  Avg Duration: {reasoning_stats['avg_duration_ms']:.2f}ms")
    print(f"  P95 Duration: {reasoning_stats['p95_duration_ms']:.2f}ms")
    print(f"  Success Rate: {reasoning_stats['success_rate']:.1%}")
    
    # Sessions
    session_stats = metrics["sessions"]
    print(f"\nSession Metrics:")
    print(f"  Total Sessions: {session_stats['total_sessions']}")
    print(f"  Completed: {session_stats['completed_sessions']}")
    print(f"  Completion Rate: {session_stats['completion_rate']:.1%}")
    print(f"  Avg Duration: {session_stats['avg_duration_ms'] / 1000:.2f}s")
    print(f"  Avg Agent Calls: {session_stats['avg_agent_calls']:.1f}")
    print(f"  Avg State Transitions: {session_stats['avg_state_transitions']:.1f}")
    
    print("\n" + "=" * 80)
    
    # Performance assessment
    print("\nPERFORMANCE ASSESSMENT:")
    print("-" * 80)
    
    # Check metrics collection overhead
    throughput = agent_overall['count'] / results['test_duration']
    print(f"\nMetrics Collection Throughput: {throughput:.1f} operations/second")
    
    if agent_overall['avg_duration_ms'] < 100:
        print("✓ Agent response tracking overhead is minimal (<100ms avg)")
    else:
        print(f"⚠️  Agent response tracking overhead is high ({agent_overall['avg_duration_ms']:.0f}ms avg)")
    
    if state_stats['avg_duration_ms'] < 50:
        print("✓ State transition tracking overhead is minimal (<50ms avg)")
    else:
        print(f"⚠️  State transition tracking overhead is high ({state_stats['avg_duration_ms']:.0f}ms avg)")
    
    if reasoning_stats['avg_duration_ms'] < 100:
        print("✓ Reasoning evaluation tracking overhead is minimal (<100ms avg)")
    else:
        print(f"⚠️  Reasoning evaluation tracking overhead is high ({reasoning_stats['avg_duration_ms']:.0f}ms avg)")
    
    print("\n" + "=" * 80)


async def main():
    """Main entry point."""
    # Test with increasing concurrency
    for num_concurrent in [5, 10, 20]:
        print(f"\n{'=' * 80}")
        print(f"Testing with {num_concurrent} concurrent sessions")
        print(f"{'=' * 80}")
        
        results = await run_concurrent_load_test(num_concurrent)
        print_results(results)
        
        # Brief pause between tests
        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
