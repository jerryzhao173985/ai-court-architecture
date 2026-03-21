#!/usr/bin/env python3
"""
Demonstration of the LLM-based fact checker for VERITAS.

This script shows how the fact checker detects contradictions in agent statements
by comparing them against case evidence using LLM analysis.
"""

import asyncio
from src.trial_orchestrator import TrialOrchestrator
from src.case_manager import CaseManager
from src.state_machine import ExperienceState
from src.llm_service import LLMService
from src.config import get_config


async def demo_fact_checker():
    """Demonstrate fact checker functionality."""
    print("=" * 80)
    print("VERITAS Fact Checker Demonstration")
    print("=" * 80)
    print()
    
    # Load the Blackthorn Hall case
    print("Loading Blackthorn Hall case...")
    case_manager = CaseManager()
    case_content = case_manager.load_case("blackthorn-hall-001")
    print(f"✓ Loaded case: {case_content.title}")
    print()
    
    # Initialize LLM service
    config = get_config()
    llm_service = LLMService(config.llm)
    print(f"✓ Initialized LLM service (provider: {config.llm.provider})")
    print()
    
    # Initialize trial orchestrator
    orchestrator = TrialOrchestrator(llm_service=llm_service)
    orchestrator.initialize_agents(case_content)
    print("✓ Initialized trial orchestrator with 5 agents")
    print()
    
    # Display evidence summary
    print("Case Evidence Summary:")
    print("-" * 80)
    for i, evidence in enumerate(case_content.evidence, 1):
        print(f"{i}. {evidence.title}")
        print(f"   {evidence.description}")
        print()
    
    # Test statements
    test_cases = [
        {
            "statement": "The security log shows Marcus Ashford left the estate at 8:20 PM",
            "speaker": "defence",
            "expected": "No contradiction (accurate statement)",
        },
        {
            "statement": "Marcus Ashford left the estate at 9:00 PM according to the security log",
            "speaker": "prosecution",
            "expected": "Contradiction detected (wrong time)",
        },
        {
            "statement": "The victim died from natural causes",
            "speaker": "defence",
            "expected": "Contradiction detected (toxicology shows poisoning)",
        },
        {
            "statement": "The housekeeper witnessed the confrontation at 8:00 PM",
            "speaker": "prosecution",
            "expected": "No contradiction (accurate statement)",
        },
    ]
    
    print("=" * 80)
    print("Testing Fact Checker with Various Statements")
    print("=" * 80)
    print()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['expected']}")
        print("-" * 80)
        print(f"Speaker: {test_case['speaker'].upper()}")
        print(f"Statement: \"{test_case['statement']}\"")
        print()
        
        # Check fact accuracy
        result = await orchestrator.check_fact_accuracy(
            statement=test_case["statement"],
            speaker=test_case["speaker"],
            stage=ExperienceState.EVIDENCE_PRESENTATION
        )
        
        if result and result.is_contradiction:
            print("✗ CONTRADICTION DETECTED")
            print(f"  Contradicting Evidence: {result.contradicting_evidence}")
            print(f"  Correction: {result.correction}")
            
            # Trigger intervention
            intervention = orchestrator.trigger_fact_check_intervention(result)
            print()
            print("  Fact Checker Intervention:")
            print(f"  \"{intervention.content}\"")
        else:
            print("✓ No contradiction detected")
        
        print()
        print()
    
    # Show intervention count
    print("=" * 80)
    print(f"Total Interventions: {orchestrator.fact_check_count} / {orchestrator.max_fact_checks}")
    print("=" * 80)
    print()
    
    print("Demonstration complete!")


if __name__ == "__main__":
    try:
        asyncio.run(demo_fact_checker())
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
