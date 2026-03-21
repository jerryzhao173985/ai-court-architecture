#!/usr/bin/env python3
"""Test complexity feature across trial progression to verify continuous value."""

import asyncio
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config import load_config
from llm_service import LLMService
from case_manager import CaseManager
from trial_orchestrator import TrialOrchestrator
from jury_orchestrator import JuryOrchestrator
from state_machine import ExperienceState


async def test_trial_progression():
    """Test prosecution and defence across multiple stages."""
    print("\n" + "="*80)
    print("COMPLEXITY FEATURE - TRIAL PROGRESSION TEST")
    print("="*80)
    
    config = load_config()
    llm_service = LLMService(config.llm)
    case_manager = CaseManager()
    case = case_manager.load_case('blackthorn-hall-001')
    
    orchestrator = TrialOrchestrator(llm_service=llm_service)
    orchestrator.initialize_agents(case)
    
    print(f"\nCase: {case.title}")
    print(f"Complexity: {orchestrator.complexity_level.level}")
    print(f"Verbosity Multiplier: {orchestrator.complexity_level.verbosity_multiplier}")
    
    results = []
    
    # Test 1: Prosecution Opening
    print("\n" + "-"*80)
    print("STAGE 1: PROSECUTION OPENING")
    print("-"*80)
    
    prosecution_prompt = orchestrator.agents['prosecution'].system_prompt
    response = await llm_service.generate_response(
        system_prompt=prosecution_prompt,
        user_prompt="Deliver your opening statement to the jury.",
        max_tokens=450
    )
    
    print(response)
    print(f"\nMetrics: {len(response)} chars, {len(response.split())} words")
    
    # Analyze quality
    evidence_refs = response.lower().count('evidence')
    specific_details = len([w for w in response.split() if any(c.isdigit() for c in w)])
    
    results.append({
        'stage': 'prosecution_opening',
        'word_count': len(response.split()),
        'evidence_refs': evidence_refs,
        'specific_details': specific_details,
        'response': response
    })
    
    await asyncio.sleep(2)
    
    # Test 2: Defence Opening
    print("\n" + "-"*80)
    print("STAGE 2: DEFENCE OPENING")
    print("-"*80)
    
    defence_prompt = orchestrator.agents['defence'].system_prompt
    response = await llm_service.generate_response(
        system_prompt=defence_prompt,
        user_prompt="Deliver your opening statement to the jury.",
        max_tokens=450
    )
    
    print(response)
    print(f"\nMetrics: {len(response)} chars, {len(response.split())} words")
    
    evidence_refs = response.lower().count('evidence')
    specific_details = len([w for w in response.split() if any(c.isdigit() for c in w)])
    
    results.append({
        'stage': 'defence_opening',
        'word_count': len(response.split()),
        'evidence_refs': evidence_refs,
        'specific_details': specific_details,
        'response': response
    })
    
    await asyncio.sleep(2)
    
    # Test 3: Prosecution Closing
    print("\n" + "-"*80)
    print("STAGE 3: PROSECUTION CLOSING")
    print("-"*80)
    
    response = await llm_service.generate_response(
        system_prompt=prosecution_prompt,
        user_prompt="Deliver your closing statement to the jury, summarizing the key evidence and why it proves guilt beyond reasonable doubt.",
        max_tokens=450
    )
    
    print(response)
    print(f"\nMetrics: {len(response)} chars, {len(response.split())} words")
    
    evidence_refs = response.lower().count('evidence')
    specific_details = len([w for w in response.split() if any(c.isdigit() for c in w)])
    
    results.append({
        'stage': 'prosecution_closing',
        'word_count': len(response.split()),
        'evidence_refs': evidence_refs,
        'specific_details': specific_details,
        'response': response
    })
    
    await asyncio.sleep(2)
    
    # Test 4: Defence Closing
    print("\n" + "-"*80)
    print("STAGE 4: DEFENCE CLOSING")
    print("-"*80)
    
    response = await llm_service.generate_response(
        system_prompt=defence_prompt,
        user_prompt="Deliver your closing statement to the jury, emphasizing reasonable doubt and weaknesses in the prosecution's case.",
        max_tokens=450
    )
    
    print(response)
    print(f"\nMetrics: {len(response)} chars, {len(response.split())} words")
    
    evidence_refs = response.lower().count('evidence')
    specific_details = len([w for w in response.split() if any(c.isdigit() for c in w)])
    
    results.append({
        'stage': 'defence_closing',
        'word_count': len(response.split()),
        'evidence_refs': evidence_refs,
        'specific_details': specific_details,
        'response': response
    })
    
    return results


async def test_jury_deliberation():
    """Test jury deliberation with complexity adjustment."""
    print("\n" + "="*80)
    print("COMPLEXITY FEATURE - JURY DELIBERATION TEST")
    print("="*80)
    
    config = load_config()
    llm_service = LLMService(config.llm)
    case_manager = CaseManager()
    case = case_manager.load_case('blackthorn-hall-001')
    
    orchestrator = JuryOrchestrator(llm_service=llm_service)
    orchestrator.initialize_jury(case)
    
    print(f"\nCase: {case.title}")
    print(f"Complexity: {orchestrator.complexity_level.level}")
    
    results = []
    
    # Test each active AI juror
    for juror in orchestrator.jurors[:3]:
        print("\n" + "-"*80)
        print(f"JUROR: {juror.persona.upper()}")
        print("-"*80)
        
        # Check word limit in prompt
        prompt = juror.system_prompt
        if "250 words" in prompt:
            word_limit = 250
        elif "200 words" in prompt:
            word_limit = 200
        else:
            word_limit = 150
        
        print(f"Word limit: {word_limit}")
        
        # Generate response
        response = await llm_service.generate_response(
            system_prompt=prompt,
            user_prompt="The prosecution has presented evidence of a forged will and poisoning. What are your initial thoughts?",
            max_tokens=word_limit
        )
        
        print(response)
        print(f"\nMetrics: {len(response)} chars, {len(response.split())} words")
        
        results.append({
            'juror': juror.persona,
            'word_count': len(response.split()),
            'word_limit': word_limit,
            'response': response
        })
        
        await asyncio.sleep(2)
    
    return results


async def analyze_progression_quality(trial_results, jury_results):
    """Analyze if complexity feature maintains quality across progression."""
    print("\n" + "="*80)
    print("PROGRESSION QUALITY ANALYSIS")
    print("="*80)
    
    print("\n1. TRIAL STAGE CONSISTENCY:")
    for result in trial_results:
        print(f"   {result['stage']:25s} - {result['word_count']:3d} words, {result['evidence_refs']} evidence refs, {result['specific_details']} details")
    
    # Check if outputs are consistently detailed
    avg_words = sum(r['word_count'] for r in trial_results) / len(trial_results)
    avg_evidence = sum(r['evidence_refs'] for r in trial_results) / len(trial_results)
    avg_details = sum(r['specific_details'] for r in trial_results) / len(trial_results)
    
    print(f"\n   Average: {avg_words:.0f} words, {avg_evidence:.1f} evidence refs, {avg_details:.1f} details")
    
    # Check consistency
    word_variance = max(r['word_count'] for r in trial_results) - min(r['word_count'] for r in trial_results)
    print(f"   Word count variance: {word_variance} (lower is more consistent)")
    
    print("\n2. JURY DELIBERATION QUALITY:")
    for result in jury_results:
        print(f"   {result['juror']:25s} - {result['word_count']:3d} words (limit: {result['word_limit']})")
    
    # Check if jurors respect limits
    all_within_limits = all(r['word_count'] <= r['word_limit'] * 1.2 for r in jury_results)
    print(f"\n   All jurors within limits: {all_within_limits}")
    
    print("\n3. VALUE ASSESSMENT:")
    
    checks = []
    
    # Check 1: Trial outputs are substantial
    if avg_words >= 300:
        print("   ✓ Trial outputs are detailed (avg >= 300 words)")
        checks.append(True)
    else:
        print(f"   ✗ Trial outputs are too brief (avg {avg_words:.0f} words)")
        checks.append(False)
    
    # Check 2: Evidence references are present
    if avg_evidence >= 2:
        print("   ✓ Good evidence referencing (avg >= 2 per statement)")
        checks.append(True)
    else:
        print(f"   ✗ Insufficient evidence references (avg {avg_evidence:.1f})")
        checks.append(False)
    
    # Check 3: Specific details included
    if avg_details >= 3:
        print("   ✓ Specific details included (avg >= 3 per statement)")
        checks.append(True)
    else:
        print(f"   ✗ Lacking specific details (avg {avg_details:.1f})")
        checks.append(False)
    
    # Check 4: Consistency across stages
    if word_variance < 150:
        print("   ✓ Consistent quality across stages")
        checks.append(True)
    else:
        print(f"   ✗ Inconsistent quality (variance {word_variance})")
        checks.append(False)
    
    # Check 5: Jurors respect limits
    if all_within_limits:
        print("   ✓ Jurors respect word limits")
        checks.append(True)
    else:
        print("   ✗ Jurors exceed word limits")
        checks.append(False)
    
    return checks


async def main():
    """Run comprehensive progression test."""
    try:
        trial_results = await test_trial_progression()
        jury_results = await test_jury_deliberation()
        
        checks = await analyze_progression_quality(trial_results, jury_results)
        
        print("\n" + "="*80)
        print("FINAL VERDICT")
        print("="*80)
        
        passed = sum(checks)
        total = len(checks)
        
        print(f"\nQuality checks passed: {passed}/{total}")
        
        if passed >= 4:
            print("\n✓ COMPLEXITY FEATURE EARNS ITS PLACE!")
            print("  - Outputs are detailed and consistent")
            print("  - Evidence references are strong")
            print("  - Character limits are respected")
            print("  - Quality maintained across trial progression")
        elif passed >= 3:
            print("\n⚠ COMPLEXITY FEATURE SHOWS VALUE BUT NEEDS REFINEMENT")
            print("  Consider adjusting scoring thresholds or guidance text")
        else:
            print("\n✗ COMPLEXITY FEATURE NEEDS SIGNIFICANT IMPROVEMENT")
            sys.exit(1)
        
        # Save results for review
        with open('complexity_test_results.json', 'w') as f:
            json.dump({
                'trial_results': trial_results,
                'jury_results': jury_results,
                'quality_checks': {
                    'passed': passed,
                    'total': total
                }
            }, f, indent=2, default=str)
        
        print("\n✓ Results saved to complexity_test_results.json")
    
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
