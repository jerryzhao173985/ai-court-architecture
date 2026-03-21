#!/usr/bin/env python3
"""Test defence prompts with multiple case scenarios."""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from trial_orchestrator import TrialOrchestrator
from models import CaseContent, EvidenceItem, CaseNarrative, CharacterProfile, GroundTruth, ReasoningCriteria
from state_machine import ExperienceState


def create_fraud_case() -> CaseContent:
    """Create a corporate fraud case for testing."""
    return CaseContent(
        case_id="corporate-fraud-001",
        title="The Crown v. Sarah Mitchell",
        narrative=CaseNarrative(
            hook_scene="A whistleblower's mysterious death...",
            charge_text="Sarah Mitchell, you are charged with murder.",
            victim_profile=CharacterProfile(
                name="David Chen",
                role="Whistleblower",
                background="Accountant who discovered fraud",
                relevant_facts=["Discovered £2M fraud", "Planned to report to authorities"]
            ),
            defendant_profile=CharacterProfile(
                name="Sarah Mitchell",
                role="CFO",
                background="Chief Financial Officer",
                relevant_facts=["Had access to accounts", "Would lose job if fraud exposed"]
            ),
            witness_profiles=[]
        ),
        evidence=[
            EvidenceItem(
                id="evidence-001",
                type="documentary",
                title="Fraudulent Financial Records",
                description="Records showing £2M embezzlement",
                timestamp="2024-01-10T09:00:00Z",
                presented_by="prosecution",
                significance="Establishes motive - defendant would be exposed"
            ),
            EvidenceItem(
                id="evidence-002",
                type="testimonial",
                title="Security Camera Footage",
                description="Shows defendant entering victim's office at 11 PM",
                timestamp="2024-01-15T23:00:00Z",
                presented_by="prosecution",
                significance="Places defendant at scene"
            ),
            EvidenceItem(
                id="evidence-003",
                type="physical",
                title="Toxicology Report",
                description="Victim died from cyanide poisoning",
                timestamp="2024-01-16T08:00:00Z",
                presented_by="prosecution",
                significance="Cause of death established"
            ),
            EvidenceItem(
                id="evidence-004",
                type="testimonial",
                title="Defendant's Alibi",
                description="Defendant claims she was working late on legitimate business",
                timestamp="2024-01-15T23:00:00Z",
                presented_by="defence",
                significance="Provides alternative explanation for presence"
            ),
            EvidenceItem(
                id="evidence-005",
                type="physical",
                title="Missing Security Badge",
                description="Victim's security badge was missing, suggesting someone else had access",
                timestamp="2024-01-16T08:00:00Z",
                presented_by="defence",
                significance="Creates doubt about who had access to the office"
            )
        ],
        timeline=[],
        ground_truth=GroundTruth(
            actual_verdict="not_guilty",
            key_facts=["Badge was stolen", "Another employee had motive"],
            reasoning_criteria=ReasoningCriteria(
                required_evidence_references=["evidence-004", "evidence-005"],
                logical_fallacies=[],
                coherence_threshold=0.7
            )
        )
    )


def test_case(case: CaseContent, case_name: str) -> bool:
    """Test defence prompts for a specific case."""
    print("\n" + "=" * 80)
    print(f"TESTING: {case_name}")
    print("=" * 80)
    
    orchestrator = TrialOrchestrator()
    orchestrator.initialize_agents(case)
    
    defence_agent = orchestrator.agents["defence"]
    
    # Check system prompt
    print("\nDEFENCE SYSTEM PROMPT (excerpt):")
    print("-" * 80)
    lines = defence_agent.system_prompt.split('\n')
    for i, line in enumerate(lines[:15]):  # First 15 lines
        print(line)
    print("...")
    
    # Check strategic focus
    print("\nSTRATEGIC FOCUS:")
    print("-" * 80)
    in_strategic = False
    for line in lines:
        if "STRATEGIC FOCUS" in line:
            in_strategic = True
        elif in_strategic and line.strip() and not line.startswith("Your role"):
            print(line)
        elif in_strategic and line.startswith("Your role"):
            break
    
    # Check fallbacks
    opening_fallback = orchestrator._get_fallback_response("defence", ExperienceState.DEFENCE_OPENING)
    closing_fallback = orchestrator._get_fallback_response("defence", ExperienceState.DEFENCE_CLOSING)
    
    print("\nOPENING FALLBACK (excerpt):")
    print("-" * 80)
    print(opening_fallback[:200] + "...")
    
    print("\nCLOSING FALLBACK (excerpt):")
    print("-" * 80)
    print(closing_fallback[:200] + "...")
    
    # Verification
    checks = [
        ("System prompt includes STRATEGIC FOCUS", "STRATEGIC FOCUS" in defence_agent.system_prompt),
        ("System prompt includes DEFENSIVE STRATEGIES", "DEFENSIVE STRATEGIES" in defence_agent.system_prompt),
        ("System prompt includes REASONABLE DOUBT TECHNIQUES", "REASONABLE DOUBT TECHNIQUES" in defence_agent.system_prompt),
        ("System prompt includes defendant name", case.narrative.defendant_profile.name in defence_agent.system_prompt),
        ("Opening fallback challenges prosecution", "evidence" in opening_fallback.lower() or "proof" in opening_fallback.lower() or "burden of proof" in opening_fallback.lower()),
        ("Opening fallback mentions doubt or speculation", "doubt" in opening_fallback.lower() or "speculation" in opening_fallback.lower() or "assumptions" in opening_fallback.lower()),
        ("Closing fallback mentions reasonable doubt", "reasonable doubt" in closing_fallback.lower()),
        ("Closing fallback uses defendant name", case.narrative.defendant_profile.name in closing_fallback),
    ]
    
    print("\nVERIFICATION:")
    print("-" * 80)
    all_passed = True
    for check_name, result in checks:
        status = "✓" if result else "✗"
        print(f"{status} {check_name}")
        if not result:
            all_passed = False
    
    return all_passed


def main():
    """Run tests on multiple cases."""
    print("=" * 80)
    print("DEFENCE PROMPTS - MULTIPLE CASE SCENARIOS TEST")
    print("=" * 80)
    
    # Test Blackthorn Hall
    with open("fixtures/blackthorn-hall-001.json", 'r') as f:
        blackthorn_data = json.load(f)
    blackthorn_case = CaseContent(**blackthorn_data)
    
    result1 = test_case(blackthorn_case, "Blackthorn Hall Murder Case")
    
    # Test Corporate Fraud
    fraud_case = create_fraud_case()
    result2 = test_case(fraud_case, "Corporate Fraud Case")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Blackthorn Hall: {'✓ PASSED' if result1 else '✗ FAILED'}")
    print(f"Corporate Fraud: {'✓ PASSED' if result2 else '✗ FAILED'}")
    
    if result1 and result2:
        print("\n✓ ALL TESTS PASSED")
        print("Defence prompts adapt correctly to different case types")
        return 0
    else:
        print("\n✗ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
