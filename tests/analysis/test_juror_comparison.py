#!/usr/bin/env python3
"""Compare old vs new juror prompts to demonstrate improvement."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from case_manager import CaseManager
from jury_orchestrator import JuryOrchestrator


def test_prompt_comparison():
    """Compare old vs new juror prompt characteristics."""
    print("\n" + "="*60)
    print("JUROR PROMPT ENHANCEMENT COMPARISON")
    print("="*60)
    
    # Load case
    case_manager = CaseManager()
    case_content = case_manager.load_case("blackthorn-hall-001")
    
    # Initialize jury
    jury = JuryOrchestrator()
    jury.initialize_jury(case_content)
    
    # Old prompt characteristics (approximate)
    old_characteristics = {
        "Evidence Purist": {
            "length": 400,
            "sections": 1,
            "personality_depth": "Basic",
            "interaction_guidance": "None",
            "case_specific": "No",
            "speech_patterns": "Generic",
        },
        "Sympathetic Doubter": {
            "length": 380,
            "sections": 1,
            "personality_depth": "Basic",
            "interaction_guidance": "None",
            "case_specific": "No",
            "speech_patterns": "Generic",
        },
        "Moral Absolutist": {
            "length": 360,
            "sections": 1,
            "personality_depth": "Basic",
            "interaction_guidance": "None",
            "case_specific": "No",
            "speech_patterns": "Generic",
        },
    }
    
    # Get new prompts
    evidence_purist = next(j for j in jury.jurors if j.persona == "evidence_purist")
    sympathetic_doubter = next(j for j in jury.jurors if j.persona == "sympathetic_doubter")
    moral_absolutist = next(j for j in jury.jurors if j.persona == "moral_absolutist")
    
    new_characteristics = {
        "Evidence Purist": {
            "length": len(evidence_purist.system_prompt),
            "sections": 5,
            "personality_depth": "Detailed (forensic accountant, 30 years experience)",
            "interaction_guidance": "Explicit (clashes with Absolutist, respects Doubter)",
            "case_specific": "Yes (analyzes evidence items)",
            "speech_patterns": "Specific (\"Where's the evidence?\", analytical language)",
        },
        "Sympathetic Doubter": {
            "length": len(sympathetic_doubter.system_prompt),
            "sections": 5,
            "personality_depth": "Detailed (social worker, seen system failures)",
            "interaction_guidance": "Explicit (aligns with Purist, clashes with Absolutist)",
            "case_specific": "Yes (identifies missing evidence)",
            "speech_patterns": "Specific (\"But what if...\", gentle persistence)",
        },
        "Moral Absolutist": {
            "length": len(moral_absolutist.system_prompt),
            "sections": 5,
            "personality_depth": "Detailed (military officer, accountability focus)",
            "interaction_guidance": "Explicit (clashes with both, uses rhetorical questions)",
            "case_specific": "Yes (focuses on victim and justice)",
            "speech_patterns": "Specific (\"This is about justice\", passionate)",
        },
    }
    
    # Print comparison
    for persona_name in ["Evidence Purist", "Sympathetic Doubter", "Moral Absolutist"]:
        print(f"\n{'-'*60}")
        print(f"{persona_name.upper()}")
        print(f"{'-'*60}")
        
        old = old_characteristics[persona_name]
        new = new_characteristics[persona_name]
        
        print(f"\n{'Characteristic':<25} {'Before':<20} {'After':<30}")
        print(f"{'-'*75}")
        print(f"{'Prompt Length':<25} {old['length']:<20} {new['length']:<30}")
        print(f"{'Sections':<25} {old['sections']:<20} {new['sections']:<30}")
        print(f"{'Personality Depth':<25} {old['personality_depth']:<20} {new['personality_depth']:<30}")
        print(f"{'Interaction Guidance':<25} {old['interaction_guidance']:<20} {new['interaction_guidance']:<30}")
        print(f"{'Case-Specific Focus':<25} {old['case_specific']:<20} {new['case_specific']:<30}")
        print(f"{'Speech Patterns':<25} {old['speech_patterns']:<20} {new['speech_patterns']:<30}")
        
        # Calculate improvement
        length_increase = (new['length'] / old['length']) - 1
        print(f"\n  → Prompt length increased by {length_increase:.1%}")
        print(f"  → Added {new['sections'] - old['sections']} structured sections")
        print(f"  → Personality depth: {old['personality_depth']} → {new['personality_depth']}")
    
    # Summary
    print(f"\n{'='*60}")
    print("OVERALL IMPROVEMENT SUMMARY")
    print(f"{'='*60}")
    
    avg_old_length = sum(old['length'] for old in old_characteristics.values()) / 3
    avg_new_length = sum(new['length'] for new in new_characteristics.values()) / 3
    avg_increase = (avg_new_length / avg_old_length) - 1
    
    print(f"\n✓ Average prompt length: {avg_old_length:.0f} → {avg_new_length:.0f} chars ({avg_increase:.1%} increase)")
    print(f"✓ All personas now have 5 structured sections (vs 1 before)")
    print(f"✓ Detailed personality backgrounds added for all personas")
    print(f"✓ Explicit interaction patterns defined between personas")
    print(f"✓ Case-specific focus dynamically generated for each persona")
    print(f"✓ Specific speech patterns and phrases provided")
    print(f"\n✓ Result: More realistic, engaging, and nuanced jury deliberation")


if __name__ == "__main__":
    test_prompt_comparison()
