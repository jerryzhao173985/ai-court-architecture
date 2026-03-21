"""Demo script showing metrics collection in action."""

import asyncio
import sys
import os
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.metrics import get_metrics_collector, reset_metrics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)


async def simulate_agent_responses():
    """Simulate agent responses with metrics tracking."""
    print("=== Simulating Agent Responses ===\n")
    
    metrics_collector = get_metrics_collector()
    
    # Simulate prosecution opening
    print("Prosecution opening statement...")
    metrics = metrics_collector.start_agent_response("prosecution", "opening")
    await asyncio.sleep(1.2)  # Simulate LLM call
    await metrics_collector.end_agent_response(metrics, success=True, used_fallback=False)
    print(f"  Duration: {metrics.duration_ms:.0f}ms\n")
    
    # Simulate defence opening
    print("Defence opening statement...")
    metrics = metrics_collector.start_agent_response("defence", "opening")
    await asyncio.sleep(1.5)  # Simulate LLM call
    await metrics_collector.end_agent_response(metrics, success=True, used_fallback=False)
    print(f"  Duration: {metrics.duration_ms:.0f}ms\n")
    
    # Simulate judge summing up
    print("Judge summing up...")
    metrics = metrics_collector.start_agent_response("judge", "summing_up")
    await asyncio.sleep(2.0)  # Simulate LLM call
    await metrics_collector.end_agent_response(metrics, success=True, used_fallback=False)
    print(f"  Duration: {metrics.duration_ms:.0f}ms\n")
    
    # Simulate failed agent response with fallback
    print("Fact checker (with fallback)...")
    metrics = metrics_collector.start_agent_response("fact_checker", "evidence")
    await asyncio.sleep(0.5)
    await metrics_collector.end_agent_response(metrics, success=True, used_fallback=True)
    print(f"  Duration: {metrics.duration_ms:.0f}ms (used fallback)\n")


async def simulate_state_transitions():
    """Simulate state transitions with metrics tracking."""
    print("=== Simulating State Transitions ===\n")
    
    metrics_collector = get_metrics_collector()
    
    transitions = [
        ("not_started", "hook_scene"),
        ("hook_scene", "charge_reading"),
        ("charge_reading", "prosecution_opening"),
        ("prosecution_opening", "defence_opening"),
        ("defence_opening", "evidence_presentation")
    ]
    
    for from_state, to_state in transitions:
        print(f"Transitioning: {from_state} -> {to_state}")
        metrics = metrics_collector.start_state_transition(from_state, to_state)
        await asyncio.sleep(0.1)  # Simulate transition work
        await metrics_collector.end_state_transition(metrics, success=True)
        print(f"  Duration: {metrics.duration_ms:.0f}ms\n")


async def simulate_reasoning_evaluation():
    """Simulate reasoning evaluation with metrics tracking."""
    print("=== Simulating Reasoning Evaluation ===\n")
    
    metrics_collector = get_metrics_collector()
    
    print("Evaluating user reasoning...")
    metrics = metrics_collector.start_reasoning_evaluation("demo_session_001")
    await asyncio.sleep(2.5)  # Simulate evaluation work
    await metrics_collector.end_reasoning_evaluation(
        metrics,
        success=True,
        category="sound_correct"
    )
    print(f"  Duration: {metrics.duration_ms:.0f}ms")
    print(f"  Category: {metrics.category}\n")


async def simulate_session():
    """Simulate a complete session with metrics tracking."""
    print("=== Simulating Complete Session ===\n")
    
    metrics_collector = get_metrics_collector()
    session_id = "demo_session_001"
    case_id = "blackthorn-hall-001"
    
    # Start session
    print(f"Starting session: {session_id}")
    await metrics_collector.start_session(session_id, case_id)
    
    # Simulate activity
    print("  Agent call 1...")
    await metrics_collector.increment_session_agent_calls(session_id)
    await asyncio.sleep(0.5)
    
    print("  Agent call 2...")
    await metrics_collector.increment_session_agent_calls(session_id)
    await asyncio.sleep(0.5)
    
    print("  State transition 1...")
    await metrics_collector.increment_session_state_transitions(session_id)
    await asyncio.sleep(0.2)
    
    print("  State transition 2...")
    await metrics_collector.increment_session_state_transitions(session_id)
    await asyncio.sleep(0.2)
    
    # End session
    print("Completing session...")
    await metrics_collector.end_session(session_id, completed=True, final_state="completed")
    print(f"  Session completed\n")


async def show_metrics_summary():
    """Display metrics summary."""
    print("=== Metrics Summary ===\n")
    
    metrics_collector = get_metrics_collector()
    
    # Get summary
    summary = metrics_collector.get_summary()
    
    # Agent responses
    agent_stats = summary["agent_responses"]["overall"]
    print(f"Agent Responses:")
    print(f"  Total calls: {agent_stats['count']}")
    print(f"  Avg duration: {agent_stats['avg_duration_ms']:.0f}ms")
    print(f"  P95 duration: {agent_stats['p95_duration_ms']:.0f}ms")
    print(f"  Success rate: {agent_stats['success_rate']:.1%}")
    print(f"  Fallback rate: {agent_stats['fallback_rate']:.1%}")
    print()
    
    # By role
    print("By Role:")
    for role, stats in summary["agent_responses"]["by_role"].items():
        print(f"  {role}: {stats['count']} calls, avg {stats['avg_duration_ms']:.0f}ms")
    print()
    
    # State transitions
    state_stats = summary["state_transitions"]
    print(f"State Transitions:")
    print(f"  Total: {state_stats['count']}")
    print(f"  Avg duration: {state_stats['avg_duration_ms']:.0f}ms")
    print(f"  P95 duration: {state_stats['p95_duration_ms']:.0f}ms")
    print()
    
    # Reasoning evaluation
    reasoning_stats = summary["reasoning_evaluation"]
    print(f"Reasoning Evaluations:")
    print(f"  Total: {reasoning_stats['count']}")
    print(f"  Avg duration: {reasoning_stats['avg_duration_ms']:.0f}ms")
    if reasoning_stats["category_distribution"]:
        print(f"  Categories: {reasoning_stats['category_distribution']}")
    print()
    
    # Sessions
    session_stats = summary["sessions"]
    print(f"Sessions:")
    print(f"  Total: {session_stats['total_sessions']}")
    print(f"  Completed: {session_stats['completed_sessions']}")
    print(f"  Completion rate: {session_stats['completion_rate']:.1%}")
    print(f"  Avg duration: {session_stats['avg_duration_ms'] / 1000:.1f}s")
    print(f"  Avg agent calls: {session_stats['avg_agent_calls']:.1f}")
    print(f"  Avg state transitions: {session_stats['avg_state_transitions']:.1f}")
    print()


async def main():
    """Run the metrics demo."""
    print("\n" + "=" * 60)
    print("VERITAS Performance Metrics Demo")
    print("=" * 60 + "\n")
    
    # Reset metrics for clean demo
    reset_metrics()
    
    # Run simulations
    await simulate_agent_responses()
    await simulate_state_transitions()
    await simulate_reasoning_evaluation()
    await simulate_session()
    
    # Show summary
    await show_metrics_summary()
    
    # Log formatted summary
    print("=== Formatted Log Output ===\n")
    metrics_collector = get_metrics_collector()
    
    # Force logger level
    import logging
    logging.getLogger("veritas").setLevel(logging.INFO)
    
    metrics_collector.log_summary()
    
    print("\n" + "=" * 60)
    print("Demo Complete!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
