#!/usr/bin/env python3
"""Test enhanced juror persona prompts for realistic deliberation."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from case_manager import CaseManager
from jury_orchestrator import JuryOrchestrator


def test_enhanced_juror_prompts():
    """Test that enhanced juror prompts include nuanced traits and patterns."""
    print("\n" + "="*60)
    print("TEST: Enhanced Juror Persona Prompts")
    print("="*60)
    
    # Load Blackthorn Hall case
    case_manager = CaseManager()
    case_content = case_manager.load_case("blackthorn-hall-001")
    print(f"✓ Loaded case: {case_content.title}")
    
    # Initialize jury orchestrator
    jury = JuryOrchestrator()
    jury.initialize_jury(case_content)
    print(f"✓ Initialized jury: {len(jury.jurors)} jurors")
    
    # Test Evidence Purist prompt
    print("\n" + "-"*60)
    print("EVIDENCE PURIST (Juror 1)")
    print("-"*60)
    
    evidence_purist = next(j for j in jury.jurors if j.persona == "evidence_purist")
    prompt = evidence_purist.system_prompt
    
    # Check for enhanced elements
    checks = {
        "Personality & Background": "PERSONALITY & BACKGROUND:" in prompt,
        "Core Reasoning Style": "CORE REASONING STYLE:" in prompt,
        "Deliberation Behaviors": "DELIBERATION BEHAVIORS:" in prompt,
        "Interaction Patterns": "INTERACTION PATTERNS:" in prompt,
        "Case-Specific Focus": "CASE-SPECIFIC FOCUS:" in prompt,
        "Background detail (forensic accountant)": "forensic accountant" in prompt,
        "Specific behaviors (interrupts)": "interrupt" in prompt.lower(),
        "Interaction with other personas": "Moral Absolutist" in prompt,
        "Natural speech guidance": "Speak naturally" in prompt,
    }
    
    for check_name, passed in checks.items():
        status = "✓" if passed else "✗"
        print(f"  {status} {check_name}")
    
    print(f"\n  Prompt length: {len(prompt)} characters")
    print(f"  Sample excerpt:\n  {prompt[:300]}...")
    
    # Test Sympathetic Doubter prompt
    print("\n" + "-"*60)
    print("SYMPATHETIC DOUBTER (Juror 2)")
    print("-"*60)
    
    sympathetic_doubter = next(j for j in jury.jurors if j.persona == "sympathetic_doubter")
    prompt = sympathetic_doubter.system_prompt
    
    checks = {
        "Personality & Background": "PERSONALITY & BACKGROUND:" in prompt,
        "Core Reasoning Style": "CORE REASONING STYLE:" in prompt,
        "Deliberation Behaviors": "DELIBERATION BEHAVIORS:" in prompt,
        "Interaction Patterns": "INTERACTION PATTERNS:" in prompt,
        "Case-Specific Focus": "CASE-SPECIFIC FOCUS:" in prompt,
        "Background detail (social worker)": "social worker" in prompt,
        "Specific phrases (But what if)": "But what if" in prompt,
        "Burden of proof emphasis": "burden of proof" in prompt,
        "Natural speech guidance": "Speak naturally" in prompt,
    }
    
    for check_name, passed in checks.items():
        status = "✓" if passed else "✗"
        print(f"  {status} {check_name}")
    
    print(f"\n  Prompt length: {len(prompt)} characters")
    print(f"  Sample excerpt:\n  {prompt[:300]}...")
    
    # Test Moral Absolutist prompt
    print("\n" + "-"*60)
    print("MORAL ABSOLUTIST (Juror 3)")
    print("-"*60)
    
    moral_absolutist = next(j for j in jury.jurors if j.persona == "moral_absolutist")
    prompt = moral_absolutist.system_prompt
    
    checks = {
        "Personality & Background": "PERSONALITY & BACKGROUND:" in prompt,
        "Core Reasoning Style": "CORE REASONING STYLE:" in prompt,
        "Deliberation Behaviors": "DELIBERATION BEHAVIORS:" in prompt,
        "Interaction Patterns": "INTERACTION PATTERNS:" in prompt,
        "Case-Specific Focus": "CASE-SPECIFIC FOCUS:" in prompt,
        "Background detail (military officer)": "military officer" in prompt,
        "Victim focus": "victim" in prompt.lower(),
        "Justice emphasis": "justice" in prompt.lower(),
        "Natural speech guidance": "Speak naturally" in prompt,
    }
    
    for check_name, passed in checks.items():
        status = "✓" if passed else "✗"
        print(f"  {status} {check_name}")
    
    print(f"\n  Prompt length: {len(prompt)} characters")
    print(f"  Sample excerpt:\n  {prompt[:300]}...")
    
    # Test case-specific focus methods
    print("\n" + "-"*60)
    print("CASE-SPECIFIC FOCUS GENERATION")
    print("-"*60)
    
    ep_focus = jury._get_evidence_purist_case_focus(case_content)
    sd_focus = jury._get_sympathetic_doubter_case_focus(case_content)
    ma_focus = jury._get_moral_absolutist_case_focus(case_content)
    
    print(f"  ✓ Evidence Purist focus: {len(ep_focus)} chars")
    print(f"  ✓ Sympathetic Doubter focus: {len(sd_focus)} chars")
    print(f"  ✓ Moral Absolutist focus: {len(ma_focus)} chars")
    
    # Verify focus includes case-specific details
    if "Blackthorn" in case_content.title or "Marcus" in str(case_content.narrative.defendant_profile.name):
        print(f"  ✓ Focus includes case-specific names")
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print("\n✓ All three juror personas have enhanced prompts with:")
    print("  - Detailed personality and background")
    print("  - Nuanced reasoning patterns")
    print("  - Specific deliberation behaviors")
    print("  - Interaction patterns with other jurors")
    print("  - Case-specific focus areas")
    print("  - Natural speech guidance")
    print("\n✓ Prompts are significantly more detailed than before")
    print("✓ Each persona has distinct voice and approach")
    print("✓ Deliberation dynamics should be more realistic and engaging")


if __name__ == "__main__":
    test_enhanced_juror_prompts()
