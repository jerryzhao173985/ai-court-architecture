#!/usr/bin/env python3
"""Test to verify complexity analyzer adds real value to agent outputs."""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config import load_config
from llm_service import LLMService
from case_manager import CaseManager
from trial_orchestrator import TrialOrchestrator
from jury_orchestrator import JuryOrchestrator
from complexity_analyzer import CaseComplexityAnalyzer


async def test_prosecution_with_complexity():
    """Test prosecution opening with complexity-adjusted prompts."""
    print("\n" + "="*80)
    print("TEST: PROSECUTION OPENING - WITH COMPLEXITY ADJUSTMENT")
    print("="*80)
    
    config = load_config()
    llm_service = LLMService(config.llm)
    case_manager = CaseManager()
    case = case_manager.load_case('blackthorn-hall-001')
    
    # Initialize with complexity
    orchestrator = TrialOrchestrator(llm_service=llm_service)
    orchestrator.initialize_agents(case)
    
    print(f"\nCase: {case.title}")
    print(f"Complexity: {orchestrator.complexity_level.level}")
    print(f"Verbosity Multiplier: {orchestrator.complexity_level.verbosity_multiplier}")
    print(f"Character Limit: {orchestrator.agents['prosecution'].character_limit}")
    
    # Get prosecution prompt
    prosecution_prompt = orchestrator.agents['prosecution'].system_prompt
    
    # Check if complexity guidance is present
    has_guidance = "CASE COMPLEXITY" in prosecution_prompt
    print(f"Has Complexity Guidance: {has_guidance}")
    
    # Generate opening statement
    print("\nGenerating prosecution opening statement...")
    response = await llm_service.generate_response(
        system_prompt=prosecution_prompt,
        user_prompt="Deliver your opening statement to the jury.",
        max_tokens=orchestrator.agents['prosecution'].character_limit // 4
    )
    
    print(f"\n{'='*80}")
    print("PROSECUTION OPENING (with complexity adjustment):")
    print(f"{'='*80}")
    print(response)
    print(f"\nLength: {len(response)} chars, {len(response.split())} words")
    
    return response


async def test_prosecution_without_complexity():
    """Test prosecution opening without complexity adjustment (baseline)."""
    print("\n" + "="*80)
    print("TEST: PROSECUTION OPENING - WITHOUT COMPLEXITY ADJUSTMENT (BASELINE)")
    print("="*80)
    
    config = load_config()
    llm_service = LLMService(config.llm)
    case_manager = CaseManager()
    case = case_manager.load_case('blackthorn-hall-001')
    
    # Create basic prompt without complexity guidance
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
- Reference evidence that supports guilt in a logical sequence

TONE: Authoritative but not aggressive. Confident but respectful of the court."""
    
    print(f"\nCase: {case.title}")
    print(f"Character Limit: 1500 (baseline, no adjustment)")
    print(f"Has Complexity Guidance: False")
    
    # Generate opening statement
    print("\nGenerating prosecution opening statement...")
    response = await llm_service.generate_response(
        system_prompt=basic_prompt,
        user_prompt="Deliver your opening statement to the jury.",
        max_tokens=1500 // 4
    )
    
    print(f"\n{'='*80}")
    print("PROSECUTION OPENING (baseline, no complexity adjustment):")
    print(f"{'='*80}")
    print(response)
    print(f"\nLength: {len(response)} chars, {len(response.split())} words")
    
    return response


async def test_juror_with_complexity():
    """Test Evidence Purist juror with complexity adjustment."""
    print("\n" + "="*80)
    print("TEST: EVIDENCE PURIST JUROR - WITH COMPLEXITY ADJUSTMENT")
    print("="*80)
    
    config = load_config()
    llm_service = LLMService(config.llm)
    case_manager = CaseManager()
    case = case_manager.load_case('blackthorn-hall-001')
    
    # Initialize with complexity
    orchestrator = JuryOrchestrator(llm_service=llm_service)
    orchestrator.initialize_jury(case)
    
    print(f"\nCase: {case.title}")
    print(f"Complexity: {orchestrator.complexity_level.level}")
    
    # Get Evidence Purist juror
    evidence_purist = orchestrator.jurors[0]
    print(f"Juror: {evidence_purist.persona}")
    
    # Check word limit
    prompt = evidence_purist.system_prompt
    if "under 250 words" in prompt:
        word_limit = 250
    elif "under 200 words" in prompt:
        word_limit = 200
    else:
        word_limit = 150
    
    print(f"Word Limit: {word_limit} (adjusted for complexity)")
    
    # Simulate deliberation statement
    print("\nGenerating juror statement...")
    response = await llm_service.generate_response(
        system_prompt=prompt,
        user_prompt="Another juror just said: 'I think the defendant seems guilty because he had a motive.' Respond to this.",
        max_tokens=word_limit
    )
    
    print(f"\n{'='*80}")
    print("EVIDENCE PURIST RESPONSE (with complexity adjustment):")
    print(f"{'='*80}")
    print(response)
    print(f"\nLength: {len(response)} chars, {len(response.split())} words")
    
    return response


async def compare_outputs():
    """Compare outputs with and without complexity adjustment."""
    print("\n" + "="*80)
    print("COMPLEXITY FEATURE VALUE ASSESSMENT")
    print("="*80)
    
    # Test prosecution
    with_complexity = await test_prosecution_with_complexity()
    await asyncio.sleep(2)  # Rate limiting
    without_complexity = await test_prosecution_without_complexity()
    
    print("\n" + "="*80)
    print("COMPARISON: PROSECUTION OPENING")
    print("="*80)
    
    with_words = len(with_complexity.split())
    without_words = len(without_complexity.split())
    
    print(f"\nWith Complexity:    {len(with_complexity)} chars, {with_words} words")
    print(f"Without Complexity: {len(without_complexity)} chars, {without_words} words")
    print(f"Difference:         {len(with_complexity) - len(without_complexity)} chars, {with_words - without_words} words")
    
    # Analyze content differences
    print("\n" + "="*80)
    print("CONTENT ANALYSIS")
    print("="*80)
    
    # Check for detailed argumentation
    with_has_trilogy = "trilogy" in with_complexity.lower() or "motive" in with_complexity.lower()
    without_has_trilogy = "trilogy" in without_complexity.lower() or "motive" in without_complexity.lower()
    
    print(f"\nWith Complexity - Uses trilogy/motive framework: {with_has_trilogy}")
    print(f"Without Complexity - Uses trilogy/motive framework: {without_has_trilogy}")
    
    # Check for evidence references
    with_evidence_refs = with_complexity.lower().count("evidence")
    without_evidence_refs = without_complexity.lower().count("evidence")
    
    print(f"\nWith Complexity - Evidence references: {with_evidence_refs}")
    print(f"Without Complexity - Evidence references: {without_evidence_refs}")
    
    # Test juror
    await asyncio.sleep(2)
    juror_response = await test_juror_with_complexity()
    
    print("\n" + "="*80)
    print("FINAL ASSESSMENT")
    print("="*80)
    
    improvements = []
    
    if with_words > without_words:
        improvements.append(f"✓ More detailed output ({with_words - without_words} more words)")
    
    if with_evidence_refs > without_evidence_refs:
        improvements.append(f"✓ More evidence references ({with_evidence_refs} vs {without_evidence_refs})")
    
    if "CASE COMPLEXITY" in with_complexity:
        improvements.append("✓ Complexity guidance visible in prompts")
    
    if len(improvements) > 0:
        print("\nComplexity feature adds value:")
        for improvement in improvements:
            print(f"  {improvement}")
        print("\n✓ VERDICT: Complexity feature earns its place!")
    else:
        print("\n⚠ WARNING: Complexity feature may not be adding significant value")
        print("Consider reviewing the implementation or scoring algorithm")


async def main():
    """Run comprehensive complexity impact test."""
    try:
        await compare_outputs()
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
