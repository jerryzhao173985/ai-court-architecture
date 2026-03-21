#!/usr/bin/env python3
"""Test script for enhanced defence agent prompts."""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from trial_orchestrator import TrialOrchestrator
from models import CaseContent
from state_machine import ExperienceState


def load_case(case_file: str) -> CaseContent:
    """Load case content from JSON file."""
    with open(case_file, 'r') as f:
        data = json.load(f)
    return CaseContent(**data)


def test_blackthorn_hall_defence():
    """Test defence prompts for Blackthorn Hall case."""
    print("=" * 80)
    print("TESTING DEFENCE PROMPTS - BLACKTHORN HALL MURDER CASE")
    print("=" * 80)
    
    # Load case
    case = load_case("fixtures/blackthorn-hall-001.json")
    
    # Initialize orchestrator
    orchestrator = TrialOrchestrator()
    orchestrator.initialize_agents(case)
    
    # Test defence agent system prompt
    print("\n1. DEFENCE SYSTEM PROMPT")
    print("-" * 80)
    defence_agent = orchestrator.agents["defence"]
    print(defence_agent.system_prompt)
    
    # Test stage-specific prompts
    print("\n2. DEFENCE OPENING STATEMENT PROMPT")
    print("-" * 80)
    opening_prompt = orchestrator._get_stage_prompt("defence", ExperienceState.DEFENCE_OPENING)
    print(opening_prompt)
    
    print("\n3. DEFENCE EVIDENCE PRESENTATION PROMPT")
    print("-" * 80)
    evidence_prompt = orchestrator._get_stage_prompt("defence", ExperienceState.EVIDENCE_PRESENTATION)
    print(evidence_prompt)
    
    print("\n4. DEFENCE CROSS-EXAMINATION PROMPT")
    print("-" * 80)
    cross_prompt = orchestrator._get_stage_prompt("defence", ExperienceState.CROSS_EXAMINATION)
    print(cross_prompt)
    
    print("\n5. DEFENCE CLOSING SPEECH PROMPT")
    print("-" * 80)
    closing_prompt = orchestrator._get_stage_prompt("defence", ExperienceState.DEFENCE_CLOSING)
    print(closing_prompt)
    
    # Test fallback responses
    print("\n6. DEFENCE OPENING FALLBACK")
    print("-" * 80)
    opening_fallback = orchestrator._get_fallback_response("defence", ExperienceState.DEFENCE_OPENING)
    print(opening_fallback)
    
    print("\n7. DEFENCE EVIDENCE PRESENTATION FALLBACK")
    print("-" * 80)
    evidence_fallback = orchestrator._get_fallback_response("defence", ExperienceState.EVIDENCE_PRESENTATION)
    print(evidence_fallback)
    
    print("\n8. DEFENCE CROSS-EXAMINATION FALLBACK")
    print("-" * 80)
    cross_fallback = orchestrator._get_fallback_response("defence", ExperienceState.CROSS_EXAMINATION)
    print(cross_fallback)
    
    print("\n9. DEFENCE CLOSING FALLBACK")
    print("-" * 80)
    closing_fallback = orchestrator._get_fallback_response("defence", ExperienceState.DEFENCE_CLOSING)
    print(closing_fallback)
    
    # Verify key elements
    print("\n" + "=" * 80)
    print("VERIFICATION CHECKS")
    print("=" * 80)
    
    checks = [
        ("System prompt includes STRATEGIC FOCUS", "STRATEGIC FOCUS" in defence_agent.system_prompt),
        ("System prompt includes DEFENSIVE STRATEGIES", "DEFENSIVE STRATEGIES" in defence_agent.system_prompt),
        ("System prompt includes REASONABLE DOUBT TECHNIQUES", "REASONABLE DOUBT TECHNIQUES" in defence_agent.system_prompt),
        ("Opening prompt mentions speculation", "speculation" in opening_prompt.lower()),
        ("Opening prompt mentions burden of proof", "burden of proof" in opening_prompt.lower()),
        ("Evidence prompt mentions missing evidence", "missing" in evidence_prompt.lower()),
        ("Cross-exam prompt attacks timeline", "timeline" in cross_prompt.lower()),
        ("Closing prompt emphasizes reasonable doubt", "reasonable doubt" in closing_prompt.lower()),
        ("Opening fallback challenges prosecution narrative", "evidence" in opening_fallback.lower() or "assumptions" in opening_fallback.lower() or "proof" in opening_fallback.lower()),
        ("Opening fallback mentions doubt", "doubt" in opening_fallback.lower() or "not guilty" in opening_fallback.lower()),
        ("Evidence fallback mentions missing evidence", "fingerprints" in evidence_fallback.lower() or "witnesses" in evidence_fallback.lower()),
        ("Evidence fallback is case-aware", "Marcus Ashford" in evidence_fallback or "defendant" in evidence_fallback.lower()),
        ("Cross-exam fallback challenges prosecution", "timeline" in cross_fallback.lower() or "impossible" in cross_fallback.lower() or "twenty minutes" in cross_fallback.lower()),
        ("Closing fallback emphasizes doubt", "doubt" in closing_fallback.lower()),
        ("Closing fallback is case-aware", "Marcus Ashford" in closing_fallback or "defendant" in closing_fallback.lower()),
    ]
    
    all_passed = True
    for check_name, result in checks:
        status = "✓" if result else "✗"
        print(f"{status} {check_name}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 80)
    if all_passed:
        print("✓ ALL CHECKS PASSED")
    else:
        print("✗ SOME CHECKS FAILED")
    print("=" * 80)
    
    return all_passed


if __name__ == "__main__":
    success = test_blackthorn_hall_defence()
    sys.exit(0 if success else 1)
