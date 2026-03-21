#!/usr/bin/env python3
"""Test that prosecution and defence prompts create balanced trial experience."""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from trial_orchestrator import TrialOrchestrator
from models import CaseContent
from state_machine import ExperienceState


def test_balanced_trial():
    """Test that both prosecution and defence have compelling arguments."""
    print("=" * 80)
    print("BALANCED TRIAL EXPERIENCE TEST")
    print("=" * 80)
    
    # Load Blackthorn Hall case
    with open("fixtures/blackthorn-hall-001.json", 'r') as f:
        data = json.load(f)
    case = CaseContent(**data)
    
    # Initialize orchestrator
    orchestrator = TrialOrchestrator()
    orchestrator.initialize_agents(case)
    
    # Get both agents
    prosecution = orchestrator.agents["prosecution"]
    defence = orchestrator.agents["defence"]
    
    print("\n1. PROSECUTION STRATEGIC FOCUS")
    print("-" * 80)
    pros_lines = prosecution.system_prompt.split('\n')
    in_strategic = False
    for line in pros_lines:
        if "STRATEGIC FOCUS" in line:
            in_strategic = True
            print(line)
        elif in_strategic and line.strip() and not line.startswith("Your role"):
            print(line)
        elif in_strategic and line.startswith("Your role"):
            break
    
    print("\n2. DEFENCE STRATEGIC FOCUS")
    print("-" * 80)
    def_lines = defence.system_prompt.split('\n')
    in_strategic = False
    for line in def_lines:
        if "STRATEGIC FOCUS" in line:
            in_strategic = True
            print(line)
        elif in_strategic and line.strip() and not line.startswith("Your role"):
            print(line)
        elif in_strategic and line.startswith("Your role"):
            break
    
    print("\n3. PROSECUTION CLOSING PROMPT")
    print("-" * 80)
    pros_closing = orchestrator._get_stage_prompt("prosecution", ExperienceState.PROSECUTION_CLOSING)
    print(pros_closing[:300] + "...")
    
    print("\n4. DEFENCE CLOSING PROMPT")
    print("-" * 80)
    def_closing = orchestrator._get_stage_prompt("defence", ExperienceState.DEFENCE_CLOSING)
    print(def_closing[:300] + "...")
    
    print("\n5. PROSECUTION CLOSING FALLBACK")
    print("-" * 80)
    pros_fallback = orchestrator._get_fallback_response("prosecution", ExperienceState.PROSECUTION_CLOSING)
    print(pros_fallback[:300] + "...")
    
    print("\n6. DEFENCE CLOSING FALLBACK")
    print("-" * 80)
    def_fallback = orchestrator._get_fallback_response("defence", ExperienceState.DEFENCE_CLOSING)
    print(def_fallback[:300] + "...")
    
    # Balance checks
    print("\n" + "=" * 80)
    print("BALANCE VERIFICATION")
    print("=" * 80)
    
    checks = [
        ("Both have STRATEGIC FOCUS", 
         "STRATEGIC FOCUS" in prosecution.system_prompt and "STRATEGIC FOCUS" in defence.system_prompt),
        ("Both have stage-specific strategies",
         "ARGUMENTATION STRATEGIES" in prosecution.system_prompt and "DEFENSIVE STRATEGIES" in defence.system_prompt),
        ("Both have specific techniques",
         "trilogy of proof" in prosecution.system_prompt.lower() and "REASONABLE DOUBT TECHNIQUES" in defence.system_prompt),
        ("Both have tone guidance",
         "TONE:" in prosecution.system_prompt and "TONE:" in defence.system_prompt),
        ("Prosecution emphasizes proof",
         "beyond reasonable doubt" in pros_closing and ("guilt" in pros_closing.lower() or "evidence" in pros_closing.lower())),
        ("Defence emphasizes doubt",
         "reasonable doubt" in def_closing.lower() and "doubt" in def_closing.lower()),
        ("Prosecution fallback is compelling",
         len(pros_fallback) > 200 and "motive" in pros_fallback.lower()),
        ("Defence fallback is compelling",
         len(def_fallback) > 200 and "doubt" in def_fallback.lower()),
        ("Both reference case specifics",
         "Marcus Ashford" in pros_fallback and "Marcus Ashford" in def_fallback),
        ("Prosecution builds case systematically",
         "evidence" in pros_closing.lower() and ("motive" in pros_closing.lower() or "means" in pros_closing.lower())),
        ("Defence challenges systematically",
         "gap" in def_closing.lower() or "missing" in def_closing.lower() or "hasn't proven" in def_closing.lower() or "failed to" in def_closing.lower()),
    ]
    
    all_passed = True
    for check_name, result in checks:
        status = "✓" if result else "✗"
        print(f"{status} {check_name}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 80)
    if all_passed:
        print("✓ TRIAL IS BALANCED")
        print("Both prosecution and defence have equally compelling arguments")
    else:
        print("✗ TRIAL IMBALANCE DETECTED")
    print("=" * 80)
    
    return all_passed


if __name__ == "__main__":
    success = test_balanced_trial()
    sys.exit(0 if success else 1)
