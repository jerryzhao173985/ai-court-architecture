"""Main entry point for VERITAS courtroom experience."""

import asyncio
from orchestrator import ExperienceOrchestrator


async def run_demo_experience():
    """
    Run a demonstration of the complete VERITAS experience flow.
    
    This demonstrates the end-to-end integration of all components.
    """
    print("=" * 60)
    print("VERITAS COURTROOM EXPERIENCE - DEMO")
    print("=" * 60)
    print()
    
    # Initialize orchestrator
    orchestrator = ExperienceOrchestrator(
        session_id="demo_session_001",
        user_id="demo_user",
        case_id="blackthorn-hall-001"
    )
    
    # Initialize experience
    print("Initializing experience...")
    init_result = await orchestrator.initialize()
    
    if not init_result["success"]:
        print(f"Initialization failed: {init_result.get('error')}")
        return
    
    print(f"✓ Initialized: {init_result['case_title']}")
    print()
    print("Greeting:")
    print(init_result['greeting']['content'])
    print()
    
    # Start experience (hook scene)
    print("-" * 60)
    print("Starting experience...")
    start_result = await orchestrator.start_experience()
    
    if start_result["success"]:
        print(f"✓ Stage: {start_result['stage']}")
        print(f"Hook Scene Duration: {start_result['hook_content']['durationSeconds']}s")
        print()
    
    # Advance through trial stages
    trial_stages = [
        "CHARGE_READING",
        "PROSECUTION_OPENING",
        "DEFENCE_OPENING",
        "EVIDENCE_PRESENTATION",
        "CROSS_EXAMINATION",
        "PROSECUTION_CLOSING",
        "DEFENCE_CLOSING",
        "JUDGE_SUMMING_UP"
    ]
    
    for stage_name in trial_stages:
        print("-" * 60)
        print(f"Advancing to {stage_name}...")
        stage_result = await orchestrator.advance_trial_stage()
        
        if stage_result["success"]:
            print(f"✓ Stage: {stage_result['stage']}")
            
            # Show agent responses
            if "agent_responses" in stage_result:
                for response in stage_result["agent_responses"]:
                    print(f"  [{response['agentRole']}]: {response['content'][:100]}...")
            print()
    
    # Enter jury deliberation
    print("-" * 60)
    print("Entering jury deliberation...")
    delib_result = await orchestrator.advance_trial_stage()
    
    if delib_result["success"]:
        print(f"✓ Stage: {delib_result['stage']}")
        print(f"Prompt: {delib_result['deliberation_prompt']}")
        print()
    
    # Submit deliberation statements
    print("-" * 60)
    print("Submitting deliberation statements...")
    
    statements = [
        "I think the evidence shows clear motive and opportunity.",
        "However, the timing inconsistencies create reasonable doubt.",
        "We must consider all the evidence carefully before deciding."
    ]
    
    for statement in statements:
        stmt_result = await orchestrator.submit_deliberation_statement(statement)
        if stmt_result["success"]:
            print(f"✓ User: {statement[:60]}...")
            for turn in stmt_result["turns"][1:]:  # Skip user turn
                print(f"  AI Juror: {turn['statement'][:60]}...")
        print()
    
    # Get evidence board
    print("-" * 60)
    print("Evidence Board:")
    evidence_board = orchestrator.get_evidence_board()
    print(f"✓ {len(evidence_board['items'])} evidence items available")
    for item in evidence_board['timeline'][:3]:
        print(f"  - {item['title']} ({item['type']})")
    print()
    
    # Advance to voting
    print("-" * 60)
    print("Advancing to voting...")
    vote_stage_result = await orchestrator.advance_trial_stage()
    
    if vote_stage_result["success"]:
        print(f"✓ Stage: {vote_stage_result['stage']}")
        print()
    
    # Submit vote
    print("-" * 60)
    print("Submitting vote...")
    vote_result = await orchestrator.submit_vote("not_guilty")
    
    if vote_result["success"]:
        print("✓ Vote submitted and verdict calculated")
        print()
        
        # Show dual reveal
        dual_reveal = vote_result["dual_reveal"]
        print("DUAL REVEAL:")
        print(f"  Verdict: {dual_reveal['verdict']['verdict']}")
        print(f"  Vote Count: {dual_reveal['verdict']['guiltyCount']} guilty, {dual_reveal['verdict']['notGuiltyCount']} not guilty")
        print(f"  Ground Truth: {dual_reveal['groundTruth']['actualVerdict']}")
        print(f"  Reasoning Category: {dual_reveal['reasoningAssessment']['category']}")
        print(f"  Evidence Score: {dual_reveal['reasoningAssessment']['evidenceScore']:.2f}")
        print(f"  Coherence Score: {dual_reveal['reasoningAssessment']['coherenceScore']:.2f}")
        print()
        print(f"Feedback: {dual_reveal['reasoningAssessment']['feedback'][:200]}...")
        print()
    
    # Complete experience
    print("-" * 60)
    print("Completing experience...")
    complete_result = await orchestrator.complete_experience(share_verdict=True)
    
    if complete_result["success"]:
        print("✓ Experience completed")
        print(f"  Verdict shared: {complete_result['verdict_shared']}")
        print(f"  Community statistics: {complete_result['statistics']}")
        print()
    
    # Show progress
    print("-" * 60)
    print("Final Progress:")
    progress = orchestrator.get_progress()
    print(f"  Completed: {progress['completed_count']}/{progress['total_stages']} stages")
    print(f"  Progress: {progress['progress_percentage']}%")
    print(f"  Status: {progress['current_stage_name']}")
    print()
    
    print("=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)


def main():
    """Main entry point."""
    asyncio.run(run_demo_experience())


if __name__ == "__main__":
    main()
