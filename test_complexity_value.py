#!/usr/bin/env python3
"""Rigorous test to verify complexity analyzer adds measurable value."""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config import load_config
from llm_service import LLMService
from case_manager import CaseManager
from trial_orchestrator import TrialOrchestrator
from jury_orchestrator import JuryOrchestrator
from models import CaseContent, CaseNarrative, CharacterProfile, EvidenceItem, TimelineEvent, GroundTruth, ReasoningCriteria


def create_simple_case() -> CaseContent:
    """Create a simple test case with minimal complexity."""
    return CaseContent(
        case_id="simple-test",
        title="The Crown v. John Smith",
        narrative=CaseNarrative(
            hook_scene="A simple theft case.",
            charge_text="Theft of a bicycle",
            victim_profile=CharacterProfile(
                name="Jane Doe",
                role="victim",
                background="Bicycle owner",
                relevant_facts=["Owned a red bicycle"]
            ),
            defendant_profile=CharacterProfile(
                name="John Smith",
                role="defendant",
                background="Accused of theft",
                relevant_facts=["Seen near bicycle"]
            ),
            witness_profiles=[
                CharacterProfile(
                    name="Bob Jones",
                    role="witness",
                    background="Saw the incident",
                    relevant_facts=["Witnessed theft"]
                )
            ]
        ),
        evidence=[
            EvidenceItem(
                id="e1",
                type="physical",
                title="Bicycle",
                description="Red bicycle found in defendant's garage",
                timestamp="2024-01-01T10:00:00Z",
                presented_by="prosecution",
                significance="Critical"
            ),
            EvidenceItem(
                id="e2",
                type="testimonial",
                title="Witness Statement",
                description="Witness saw defendant take bicycle",
                timestamp="2024-01-01T10:05:00Z",
                presented_by="prosecution",
                significance="Critical"
            ),
            EvidenceItem(
                id="e3",
                type="physical",
                title="Receipt",
                description="Defendant claims he bought the bicycle",
                timestamp="2024-01-01T09:00:00Z",
                presented_by="defence",
                significance="Minor"
            ),
            EvidenceItem(
                id="e4",
                type="testimonial",
                title="Alibi",
                description="Friend says defendant was elsewhere",
                timestamp="2024-01-01T10:00:00Z",
                presented_by="defence",
                significance="Minor"
            ),
            EvidenceItem(
                id="e5",
                type="physical",
                title="CCTV",
                description="Grainy footage shows someone near bicycle",
                timestamp="2024-01-01T10:02:00Z",
                presented_by="prosecution",
                significance="Minor"
            )
        ],
        timeline=[
            TimelineEvent(
                timestamp="2024-01-01T09:00:00Z",
                description="Defendant allegedly bought bicycle",
                evidence_ids=["e3"]
            ),
            TimelineEvent(
                timestamp="2024-01-01T10:00:00Z",
                description="Bicycle stolen",
                evidence_ids=["e1", "e2"]
            )
        ],
        ground_truth=GroundTruth(
            actual_verdict="guilty",
            key_facts=["Bicycle found in garage", "Witness saw theft"],
            reasoning_criteria=ReasoningCriteria(
                required_evidence_references=["e1", "e2"],
                logical_fallacies=[],
                coherence_threshold=0.6
            )
        )
    )


async def test_with_simple_case():
    """Test prosecution with simple case."""
    print("\n" + "="*80)
    print("TEST 1: SIMPLE CASE (Bicycle Theft)")
    print("="*80)
    
    config = load_config()
    llm_service = LLMService(config.llm)
    
    simple_case = create_simple_case()
    
    orchestrator = TrialOrchestrator(llm_service=llm_service)
    orchestrator.initialize_agents(simple_case)
    
    print(f"\nCase: {simple_case.title}")
    print(f"Evidence Count: {len(simple_case.evidence)}")
    print(f"Witness Count: {len(simple_case.narrative.witness_profiles)}")
    print(f"Complexity: {orchestrator.complexity_level.level}")
    print(f"Verbosity Multiplier: {orchestrator.complexity_level.verbosity_multiplier}")
    print(f"Character Limit: {orchestrator.agents['prosecution'].character_limit}")
    
    # Generate opening
    prosecution_prompt = orchestrator.agents['prosecution'].system_prompt
    response = await llm_service.generate_response(
        system_prompt=prosecution_prompt,
        user_prompt="Deliver your opening statement to the jury.",
        max_tokens=orchestrator.agents['prosecution'].character_limit // 4
    )
    
    print(f"\nPROSECUTION OPENING:")
    print("-" * 80)
    print(response)
    print("-" * 80)
    print(f"Length: {len(response)} chars, {len(response.split())} words")
    
    return {
        'complexity': orchestrator.complexity_level.level,
        'char_limit': orchestrator.agents['prosecution'].character_limit,
        'response': response,
        'word_count': len(response.split()),
        'char_count': len(response)
    }


async def test_with_complex_case():
    """Test prosecution with complex case (Blackthorn Hall)."""
    print("\n" + "="*80)
    print("TEST 2: COMPLEX CASE (Blackthorn Hall Murder)")
    print("="*80)
    
    config = load_config()
    llm_service = LLMService(config.llm)
    case_manager = CaseManager()
    case = case_manager.load_case('blackthorn-hall-001')
    
    orchestrator = TrialOrchestrator(llm_service=llm_service)
    orchestrator.initialize_agents(case)
    
    print(f"\nCase: {case.title}")
    print(f"Evidence Count: {len(case.evidence)}")
    print(f"Witness Count: {len(case.narrative.witness_profiles)}")
    print(f"Complexity: {orchestrator.complexity_level.level}")
    print(f"Verbosity Multiplier: {orchestrator.complexity_level.verbosity_multiplier}")
    print(f"Character Limit: {orchestrator.agents['prosecution'].character_limit}")
    
    # Generate opening
    prosecution_prompt = orchestrator.agents['prosecution'].system_prompt
    response = await llm_service.generate_response(
        system_prompt=prosecution_prompt,
        user_prompt="Deliver your opening statement to the jury.",
        max_tokens=orchestrator.agents['prosecution'].character_limit // 4
    )
    
    print(f"\nPROSECUTION OPENING:")
    print("-" * 80)
    print(response)
    print("-" * 80)
    print(f"Length: {len(response)} chars, {len(response.split())} words")
    
    return {
        'complexity': orchestrator.complexity_level.level,
        'char_limit': orchestrator.agents['prosecution'].character_limit,
        'response': response,
        'word_count': len(response.split()),
        'char_count': len(response)
    }


def analyze_content_quality(simple_result, complex_result):
    """Analyze if complexity adjustment improves content quality."""
    print("\n" + "="*80)
    print("QUALITY ANALYSIS")
    print("="*80)
    
    metrics = []
    
    # 1. Length appropriateness
    print("\n1. LENGTH SCALING:")
    print(f"   Simple case:  {simple_result['word_count']} words (limit: {simple_result['char_limit']} chars)")
    print(f"   Complex case: {complex_result['word_count']} words (limit: {complex_result['char_limit']} chars)")
    
    if complex_result['word_count'] > simple_result['word_count']:
        diff = complex_result['word_count'] - simple_result['word_count']
        pct = (diff / simple_result['word_count']) * 100
        print(f"   ✓ Complex case is {diff} words longer ({pct:.1f}% increase)")
        metrics.append(('length_scaling', True))
    else:
        print(f"   ✗ Complex case is not longer")
        metrics.append(('length_scaling', False))
    
    # 2. Evidence references
    print("\n2. EVIDENCE DEPTH:")
    simple_evidence_refs = simple_result['response'].lower().count('evidence')
    complex_evidence_refs = complex_result['response'].lower().count('evidence')
    
    print(f"   Simple case:  {simple_evidence_refs} evidence mentions")
    print(f"   Complex case: {complex_evidence_refs} evidence mentions")
    
    if complex_evidence_refs >= simple_evidence_refs:
        print(f"   ✓ Complex case has more/equal evidence references")
        metrics.append(('evidence_depth', True))
    else:
        print(f"   ✗ Complex case has fewer evidence references")
        metrics.append(('evidence_depth', False))
    
    # 3. Argumentation structure
    print("\n3. ARGUMENTATION STRUCTURE:")
    
    # Check for connecting words indicating complex argumentation
    complex_connectors = ['furthermore', 'moreover', 'however', 'additionally', 'consequently', 'therefore']
    
    simple_connectors = sum(1 for word in complex_connectors if word in simple_result['response'].lower())
    complex_connectors_count = sum(1 for word in complex_connectors if word in complex_result['response'].lower())
    
    print(f"   Simple case:  {simple_connectors} logical connectors")
    print(f"   Complex case: {complex_connectors_count} logical connectors")
    
    if complex_connectors_count > simple_connectors:
        print(f"   ✓ Complex case uses more sophisticated argumentation")
        metrics.append(('argumentation', True))
    else:
        print(f"   ✗ No improvement in argumentation structure")
        metrics.append(('argumentation', False))
    
    # 4. Detail and nuance
    print("\n4. DETAIL AND NUANCE:")
    
    # Count specific details (numbers, dates, names)
    import re
    simple_numbers = len(re.findall(r'\d+', simple_result['response']))
    complex_numbers = len(re.findall(r'\d+', complex_result['response']))
    
    print(f"   Simple case:  {simple_numbers} specific details (numbers/dates)")
    print(f"   Complex case: {complex_numbers} specific details (numbers/dates)")
    
    if complex_numbers > simple_numbers:
        print(f"   ✓ Complex case includes more specific details")
        metrics.append(('detail', True))
    else:
        print(f"   ✗ No improvement in detail level")
        metrics.append(('detail', False))
    
    return metrics


async def main():
    """Run comprehensive value assessment."""
    print("\n" + "="*80)
    print("COMPLEXITY ANALYZER VALUE ASSESSMENT")
    print("Testing if complexity adjustment improves output quality")
    print("="*80)
    
    try:
        # Test both cases
        simple_result = await test_with_simple_case()
        await asyncio.sleep(2)  # Rate limiting
        complex_result = await test_with_complex_case()
        
        # Analyze quality
        metrics = analyze_content_quality(simple_result, complex_result)
        
        # Final verdict
        print("\n" + "="*80)
        print("FINAL VERDICT")
        print("="*80)
        
        passed = sum(1 for _, result in metrics if result)
        total = len(metrics)
        
        print(f"\nMetrics passed: {passed}/{total}")
        
        for metric_name, result in metrics:
            status = "✓" if result else "✗"
            print(f"  {status} {metric_name}")
        
        if passed >= 3:
            print("\n✓ COMPLEXITY FEATURE EARNS ITS PLACE!")
            print("  The feature demonstrably improves output quality for complex cases.")
        elif passed >= 2:
            print("\n⚠ COMPLEXITY FEATURE SHOWS SOME VALUE")
            print("  Consider refining the scoring algorithm or guidance text.")
        else:
            print("\n✗ COMPLEXITY FEATURE NEEDS IMPROVEMENT")
            print("  The feature is not adding sufficient value.")
            sys.exit(1)
    
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
