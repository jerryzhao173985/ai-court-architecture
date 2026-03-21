#!/usr/bin/env python3
"""Final comprehensive assessment of complexity feature value."""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config import load_config
from llm_service import LLMService
from case_manager import CaseManager
from trial_orchestrator import TrialOrchestrator
from jury_orchestrator import JuryOrchestrator


async def test_without_complexity_feature():
    """Test by manually removing complexity guidance to see the difference."""
    print("\n" + "="*80)
    print("TEST A: WITHOUT COMPLEXITY FEATURE (Manual Override)")
    print("="*80)
    
    config = load_config()
    llm_service = LLMService(config.llm)
    case_manager = CaseManager()
    case = case_manager.load_case('blackthorn-hall-001')
    
    # Create basic prosecution prompt without complexity
    evidence_summary = "\n".join([f"- {e.title}: {e.description}" for e in case.evidence])
    
    basic_prompt = f"""You are the Crown Prosecution barrister in a British Crown Court murder trial.

Case: {case.title}
Defendant: {case.narrative.defendant_profile.name}
Victim: {case.narrative.victim_profile.name}

Evidence available:
{evidence_summary}

Your role is to:
- Present the case for the Crown with conviction and clarity
- Build a compelling narrative connecting motive, means, and opportunity
- Argue that the defendant is guilty beyond reasonable doubt
- Use the "trilogy of proof" approach: establish motive, demonstrate means, prove opportunity
- Reference evidence that supports guilt in a logical sequence

TONE: Authoritative but not aggressive. Confident but respectful of the court."""
    
    print(f"Character limit: 1500 (no adjustment)")
    print(f"Has complexity guidance: NO\n")
    
    response = await llm_service.generate_response(
        system_prompt=basic_prompt,
        user_prompt="Deliver your opening statement to the jury.",
        max_tokens=375
    )
    
    print("PROSECUTION OPENING:")
    print("-" * 80)
    print(response)
    print("-" * 80)
    
    return {
        'response': response,
        'word_count': len(response.split()),
        'char_count': len(response)
    }


async def test_with_complexity_feature():
    """Test with full complexity feature enabled."""
    print("\n" + "="*80)
    print("TEST B: WITH COMPLEXITY FEATURE (Full Implementation)")
    print("="*80)
    
    config = load_config()
    llm_service = LLMService(config.llm)
    case_manager = CaseManager()
    case = case_manager.load_case('blackthorn-hall-001')
    
    orchestrator = TrialOrchestrator(llm_service=llm_service)
    orchestrator.initialize_agents(case)
    
    print(f"Complexity: {orchestrator.complexity_level.level}")
    print(f"Character limit: {orchestrator.agents['prosecution'].character_limit} (adjusted)")
    print(f"Has complexity guidance: YES\n")
    
    prosecution_prompt = orchestrator.agents['prosecution'].system_prompt
    response = await llm_service.generate_response(
        system_prompt=prosecution_prompt,
        user_prompt="Deliver your opening statement to the jury.",
        max_tokens=450
    )
    
    print("PROSECUTION OPENING:")
    print("-" * 80)
    print(response)
    print("-" * 80)
    
    return {
        'response': response,
        'word_count': len(response.split()),
        'char_count': len(response)
    }


def analyze_quality_difference(without, with_feature):
    """Detailed quality comparison."""
    print("\n" + "="*80)
    print("DETAILED QUALITY COMPARISON")
    print("="*80)
    
    print("\n1. LENGTH AND DETAIL:")
    print(f"   Without: {without['word_count']} words, {without['char_count']} chars")
    print(f"   With:    {with_feature['word_count']} words, {with_feature['char_count']} chars")
    print(f"   Gain:    +{with_feature['word_count'] - without['word_count']} words (+{((with_feature['word_count'] - without['word_count']) / without['word_count'] * 100):.1f}%)")
    
    # Specific evidence items mentioned
    evidence_items = [
        'forged will', 'toxicology', 'digoxin', 'fingerprint', 
        'security gate', 'pemberton', 'pathologist', '£500,000', '500,000'
    ]
    
    print("\n2. SPECIFIC EVIDENCE CITATIONS:")
    without_citations = sum(1 for item in evidence_items if item in without['response'].lower())
    with_citations = sum(1 for item in evidence_items if item in with_feature['response'].lower())
    
    print(f"   Without: {without_citations} specific evidence items cited")
    print(f"   With:    {with_citations} specific evidence items cited")
    
    if with_citations > without_citations:
        print(f"   ✓ Improvement: +{with_citations - without_citations} more citations")
    
    # Argumentation structure
    print("\n3. ARGUMENTATION STRUCTURE:")
    
    structure_words = [
        'firstly', 'secondly', 'thirdly', 'furthermore', 'moreover',
        'additionally', 'next', 'finally', 'consequently', 'therefore'
    ]
    
    without_structure = sum(1 for word in structure_words if word in without['response'].lower())
    with_structure = sum(1 for word in structure_words if word in with_feature['response'].lower())
    
    print(f"   Without: {without_structure} structural connectors")
    print(f"   With:    {with_structure} structural connectors")
    
    if with_structure > without_structure:
        print(f"   ✓ Improvement: +{with_structure - without_structure} more connectors")
    
    # Trilogy of proof usage
    print("\n4. TRILOGY OF PROOF (Motive, Means, Opportunity):")
    
    trilogy_terms = ['motive', 'means', 'opportunity']
    without_trilogy = sum(1 for term in trilogy_terms if term in without['response'].lower())
    with_trilogy = sum(1 for term in trilogy_terms if term in with_feature['response'].lower())
    
    print(f"   Without: {without_trilogy}/3 trilogy elements mentioned")
    print(f"   With:    {with_trilogy}/3 trilogy elements mentioned")
    
    # Specific details (times, amounts, names)
    import re
    without_times = len(re.findall(r'\d+:\d+', without['response']))
    with_times = len(re.findall(r'\d+:\d+', with_feature['response']))
    
    without_amounts = len(re.findall(r'£[\d,]+', without['response']))
    with_amounts = len(re.findall(r'£[\d,]+', with_feature['response']))
    
    print("\n5. SPECIFIC DETAILS:")
    print(f"   Without: {without_times} times, {without_amounts} amounts")
    print(f"   With:    {with_times} times, {with_amounts} amounts")
    
    # Calculate overall score
    print("\n" + "="*80)
    print("SCORING")
    print("="*80)
    
    score = 0
    max_score = 0
    
    # Length improvement (up to 2 points)
    max_score += 2
    word_gain_pct = ((with_feature['word_count'] - without['word_count']) / without['word_count']) * 100
    if word_gain_pct >= 20:
        score += 2
        print(f"✓ Length: +2 points (gained {word_gain_pct:.1f}%)")
    elif word_gain_pct >= 10:
        score += 1
        print(f"⚠ Length: +1 point (gained {word_gain_pct:.1f}%)")
    else:
        print(f"✗ Length: 0 points (gained {word_gain_pct:.1f}%)")
    
    # Evidence citations (up to 2 points)
    max_score += 2
    if with_citations > without_citations:
        citation_gain = with_citations - without_citations
        if citation_gain >= 2:
            score += 2
            print(f"✓ Citations: +2 points (+{citation_gain} citations)")
        else:
            score += 1
            print(f"⚠ Citations: +1 point (+{citation_gain} citation)")
    else:
        print(f"✗ Citations: 0 points (no improvement)")
    
    # Structure (up to 1 point)
    max_score += 1
    if with_structure > without_structure:
        score += 1
        print(f"✓ Structure: +1 point (+{with_structure - without_structure} connectors)")
    else:
        print(f"✗ Structure: 0 points (no improvement)")
    
    # Trilogy usage (up to 1 point)
    max_score += 1
    if with_trilogy >= 3:
        score += 1
        print(f"✓ Trilogy: +1 point (all 3 elements present)")
    else:
        print(f"✗ Trilogy: 0 points ({with_trilogy}/3 elements)")
    
    # Specific details (up to 2 points)
    max_score += 2
    detail_gain = (with_times - without_times) + (with_amounts - without_amounts)
    if detail_gain >= 2:
        score += 2
        print(f"✓ Details: +2 points (+{detail_gain} specific details)")
    elif detail_gain >= 1:
        score += 1
        print(f"⚠ Details: +1 point (+{detail_gain} specific detail)")
    else:
        print(f"✗ Details: 0 points (no improvement)")
    
    print(f"\nFINAL SCORE: {score}/{max_score} ({(score/max_score)*100:.0f}%)")
    
    return score, max_score


async def main():
    """Run final assessment."""
    print("\n" + "="*80)
    print("COMPLEXITY FEATURE - FINAL VALUE ASSESSMENT")
    print("="*80)
    print("\nThis test compares outputs WITH and WITHOUT complexity adjustments")
    print("to determine if the feature genuinely improves quality.\n")
    
    try:
        without = await test_without_complexity_feature()
        await asyncio.sleep(3)  # Rate limiting
        with_feature = await test_with_complexity_feature()
        
        score, max_score = analyze_quality_difference(without, with_feature)
        
        print("\n" + "="*80)
        print("FINAL VERDICT")
        print("="*80)
        
        percentage = (score / max_score) * 100
        
        if percentage >= 75:
            print(f"\n✓✓✓ COMPLEXITY FEATURE STRONGLY EARNS ITS PLACE! ({percentage:.0f}%)")
            print("\nThe feature provides substantial quality improvements:")
            print("  - More detailed and comprehensive arguments")
            print("  - Better evidence integration")
            print("  - Stronger structural organization")
            print("  - More specific details and citations")
        elif percentage >= 50:
            print(f"\n✓✓ COMPLEXITY FEATURE EARNS ITS PLACE ({percentage:.0f}%)")
            print("\nThe feature provides measurable quality improvements.")
        elif percentage >= 25:
            print(f"\n⚠ COMPLEXITY FEATURE SHOWS SOME VALUE ({percentage:.0f}%)")
            print("\nConsider refining the implementation for better impact.")
        else:
            print(f"\n✗ COMPLEXITY FEATURE NEEDS IMPROVEMENT ({percentage:.0f}%)")
            print("\nThe feature is not adding sufficient value.")
            sys.exit(1)
    
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
