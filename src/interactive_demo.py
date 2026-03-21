"""Interactive VERITAS experience for user participation."""

import asyncio
from orchestrator import ExperienceOrchestrator


async def run_interactive_experience():
    """Run an interactive VERITAS experience where the user participates."""
    print("=" * 70)
    print("VERITAS COURTROOM EXPERIENCE - INTERACTIVE MODE")
    print("=" * 70)
    print()
    print("Welcome! You are about to serve as a juror in a British Crown Court")
    print("murder trial. This experience will take approximately 15 minutes.")
    print()
    input("Press Enter to begin...")
    print()
    
    # Initialize orchestrator
    orchestrator = ExperienceOrchestrator(
        session_id="interactive_session_001",
        user_id="interactive_user",
        case_id="blackthorn-hall-001"
    )
    
    # Initialize experience
    print("Initializing experience...")
    init_result = await orchestrator.initialize()
    
    if not init_result["success"]:
        print(f"❌ Initialization failed: {init_result.get('error')}")
        return
    
    print(f"✓ Case loaded: {init_result['case_title']}")
    print()
    print("-" * 70)
    print(init_result['greeting']['content'])
    print("-" * 70)
    print()
    input("Press Enter when ready to begin...")
    print()
    
    # Start experience (hook scene)
    print("=" * 70)
    print("THE TRIAL BEGINS")
    print("=" * 70)
    print()
    start_result = await orchestrator.start_experience()
    
    if start_result["success"]:
        hook_content = start_result['hook_content']
        print(hook_content['content'])
        print()
        print(f"[Duration: {hook_content['durationSeconds']} seconds]")
        print()
        input("Press Enter to continue to the trial...")
        print()
    
    # Trial stages
    trial_stages = [
        ("CHARGE_READING", "Charge Reading"),
        ("PROSECUTION_OPENING", "Prosecution Opening Statement"),
        ("DEFENCE_OPENING", "Defence Opening Statement"),
        ("EVIDENCE_PRESENTATION", "Evidence Presentation"),
        ("CROSS_EXAMINATION", "Cross-Examination"),
        ("PROSECUTION_CLOSING", "Prosecution Closing Speech"),
        ("DEFENCE_CLOSING", "Defence Closing Speech"),
        ("JUDGE_SUMMING_UP", "Judge's Summing Up")
    ]
    
    for stage_name, stage_title in trial_stages:
        print("=" * 70)
        print(f"{stage_title.upper()}")
        print("=" * 70)
        print()
        
        stage_result = await orchestrator.advance_trial_stage()
        
        if stage_result["success"]:
            # Show agent responses
            if "agent_responses" in stage_result:
                for response in stage_result["agent_responses"]:
                    role = response['agentRole'].upper()
                    content = response['content']
                    print(f"[{role}]")
                    print(content)
                    print()
        
        input("Press Enter to continue...")
        print()
    
    # Jury deliberation
    print("=" * 70)
    print("JURY DELIBERATION")
    print("=" * 70)
    print()
    print("You are now in the jury chamber with 7 other jurors (AI).")
    print("You will discuss the case together before voting.")
    print()
    
    delib_result = await orchestrator.advance_trial_stage()
    
    if delib_result["success"]:
        print(delib_result['deliberation_prompt'])
        print()
        print("You can view the evidence board at any time.")
        print()
        
        # Show evidence board
        evidence_board = orchestrator.get_evidence_board()
        print("-" * 70)
        print("EVIDENCE BOARD")
        print("-" * 70)
        for item in evidence_board['timeline']:
            print(f"• {item['title']} ({item['type']}) - {item['timestamp']}")
        print("-" * 70)
        print()
        
        # Deliberation rounds
        print("Let's deliberate. You can make up to 3 statements.")
        print()
        
        for round_num in range(1, 4):
            statement = input(f"Your statement #{round_num}: ")
            
            if not statement.strip():
                print("(Skipping this round)")
                print()
                continue
            
            print()
            print("Submitting your statement...")
            stmt_result = await orchestrator.submit_deliberation_statement(statement)
            
            if stmt_result["success"]:
                print()
                print("AI Jurors respond:")
                print("-" * 70)
                for turn in stmt_result["turns"][1:]:  # Skip user turn
                    print(f"Juror: {turn['statement']}")
                    print()
                print("-" * 70)
            
            print()
        
        print("Deliberation time is up. Time to vote.")
        print()
    
    # Voting
    print("=" * 70)
    print("VOTING")
    print("=" * 70)
    print()
    
    await orchestrator.advance_trial_stage()
    
    while True:
        vote = input("Your verdict (guilty/not guilty): ").strip().lower()
        
        if vote in ["guilty", "not guilty", "not_guilty"]:
            if vote == "not guilty":
                vote = "not_guilty"
            break
        else:
            print("Please enter 'guilty' or 'not guilty'")
    
    print()
    print("Collecting votes from all jurors...")
    print()
    
    vote_result = await orchestrator.submit_vote(vote)
    
    if vote_result["success"]:
        # Dual reveal
        print("=" * 70)
        print("DUAL REVEAL")
        print("=" * 70)
        print()
        
        dual_reveal = vote_result["dual_reveal"]
        
        # 1. Verdict
        print("THE VERDICT")
        print("-" * 70)
        verdict_text = dual_reveal['verdict']['verdict'].replace('_', ' ').upper()
        print(f"The jury finds the defendant: {verdict_text}")
        print(f"Vote: {dual_reveal['verdict']['guiltyCount']} guilty, {dual_reveal['verdict']['notGuiltyCount']} not guilty")
        print()
        input("Press Enter to reveal the truth...")
        print()
        
        # 2. Ground truth
        print("THE TRUTH")
        print("-" * 70)
        truth = dual_reveal['groundTruth']
        actual_verdict = truth['actualVerdict'].replace('_', ' ').upper()
        print(f"The actual truth: {actual_verdict}")
        print()
        print(truth['explanation'])
        print()
        input("Press Enter to see your reasoning assessment...")
        print()
        
        # 3. Reasoning assessment
        print("YOUR REASONING ASSESSMENT")
        print("-" * 70)
        assessment = dual_reveal['reasoningAssessment']
        category = assessment['category'].replace('_', ' ').title()
        print(f"Category: {category}")
        print(f"Evidence Score: {assessment['evidenceScore']:.2f}/1.0")
        print(f"Coherence Score: {assessment['coherenceScore']:.2f}/1.0")
        print()
        print("Feedback:")
        print(assessment['feedback'])
        print()
        
        if assessment['fallaciesDetected']:
            print("Logical fallacies detected:")
            for fallacy in assessment['fallaciesDetected']:
                print(f"  • {fallacy}")
            print()
        
        input("Press Enter to reveal the AI jurors...")
        print()
        
        # 4. Juror reveal
        print("AI JUROR IDENTITIES")
        print("-" * 70)
        for juror in dual_reveal['jurorReveal']:
            if juror['type'] != 'human':
                juror_type = juror['type'].replace('_', ' ').title()
                persona = juror.get('persona', 'N/A')
                if persona:
                    persona = persona.replace('_', ' ').title()
                vote_text = juror['vote'].replace('_', ' ').title()
                
                print(f"{juror['jurorId']}: {juror_type}")
                if persona != 'N/A':
                    print(f"  Persona: {persona}")
                print(f"  Vote: {vote_text}")
                
                if juror.get('keyStatements'):
                    print(f"  Key statements:")
                    for stmt in juror['keyStatements'][:2]:
                        print(f"    - {stmt[:80]}...")
                print()
        print("-" * 70)
        print()
    
    # Complete experience
    print("=" * 70)
    print("EXPERIENCE COMPLETE")
    print("=" * 70)
    print()
    
    share = input("Would you like to share your verdict with the community? (yes/no): ").strip().lower()
    share_verdict = share in ['yes', 'y']
    
    complete_result = await orchestrator.complete_experience(share_verdict=share_verdict)
    
    if complete_result["success"]:
        print()
        if complete_result['verdict_shared']:
            print("✓ Your verdict has been shared anonymously")
        
        stats = complete_result['statistics']
        if stats['total_verdicts'] > 0:
            print()
            print("Community Statistics:")
            print(f"  Total verdicts: {stats['total_verdicts']}")
            print(f"  Guilty: {stats['guilty_percentage']}%")
            print(f"  Not Guilty: {stats['not_guilty_percentage']}%")
    
    print()
    print("=" * 70)
    print("Thank you for participating in VERITAS!")
    print("=" * 70)


def main():
    """Main entry point."""
    try:
        asyncio.run(run_interactive_experience())
    except KeyboardInterrupt:
        print("\n\nExperience interrupted. Goodbye!")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")


if __name__ == "__main__":
    main()
