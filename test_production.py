#!/usr/bin/env python3
"""Production mode test - verifies OpenAI integration and all components."""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config import load_config
from llm_service import LLMService
from orchestrator import ExperienceOrchestrator


async def test_llm_service():
    """Test LLM service with real OpenAI API."""
    print("\n" + "="*60)
    print("TEST 1: LLM Service (OpenAI GPT-4o)")
    print("="*60)
    
    try:
        config = load_config()
        print(f"✓ Config loaded: {config.llm.provider} / {config.llm.model}")
        
        llm_service = LLMService(config.llm)
        print(f"✓ LLM service initialized")
        
        # Test simple generation
        response = await llm_service.generate_response(
            system_prompt="You are a British judge. Respond formally and briefly.",
            user_prompt="What is the role of a judge in a criminal trial?",
            max_tokens=100
        )
        
        print(f"✓ LLM response received ({len(response)} chars)")
        print(f"\nSample response:\n{response[:200]}...")
        
        return True
    
    except Exception as e:
        print(f"✗ LLM service test failed: {e}")
        return False


async def test_orchestrator_initialization():
    """Test orchestrator initialization with all components."""
    print("\n" + "="*60)
    print("TEST 2: Orchestrator Initialization")
    print("="*60)
    
    try:
        orchestrator = ExperienceOrchestrator(
            session_id="test_prod_001",
            user_id="test_user",
            case_id="blackthorn-hall-001"
        )
        print("✓ Orchestrator created")
        
        result = await orchestrator.initialize()
        
        if result["success"]:
            print(f"✓ Orchestrator initialized")
            print(f"  Case: {result['case_title']}")
            print(f"  Session: {result['session_id']}")
            print(f"  Greeting: {result['greeting']['content'][:100]}...")
            return True
        else:
            print(f"✗ Initialization failed: {result.get('error')}")
            return False
    
    except Exception as e:
        print(f"✗ Orchestrator test failed: {e}")
        return False


async def test_trial_agent_generation():
    """Test trial agent with real LLM."""
    print("\n" + "="*60)
    print("TEST 3: Trial Agent Generation (Judge)")
    print("="*60)
    
    try:
        orchestrator = ExperienceOrchestrator(
            session_id="test_prod_002",
            user_id="test_user",
            case_id="blackthorn-hall-001"
        )
        
        await orchestrator.initialize()
        print("✓ Orchestrator initialized")
        
        # Start experience and advance to charge reading
        await orchestrator.start_experience()
        print("✓ Experience started (Hook Scene)")
        
        # Advance to charge reading
        result = await orchestrator.advance_trial_stage()
        
        if result["success"] and result.get("agent_responses"):
            print(f"✓ Trial stage executed: {result['stage']}")
            
            for response in result["agent_responses"]:
                agent_role = response["agentRole"]
                content = response["content"]
                print(f"\n  {agent_role}:")
                print(f"  {content[:150]}...")
            
            return True
        else:
            print(f"✗ Trial stage failed: {result.get('error')}")
            return False
    
    except Exception as e:
        print(f"✗ Trial agent test failed: {e}")
        return False


async def test_jury_generation():
    """Test jury orchestrator with real LLM."""
    print("\n" + "="*60)
    print("TEST 4: Jury Generation (GPT-4o + GPT-4o-mini)")
    print("="*60)
    
    try:
        orchestrator = ExperienceOrchestrator(
            session_id="test_prod_003",
            user_id="test_user",
            case_id="blackthorn-hall-001"
        )
        
        await orchestrator.initialize()
        print("✓ Orchestrator initialized")
        
        # Check jury configuration
        jury = orchestrator.jury_orchestrator
        print(f"✓ Jury initialized: {len(jury.jurors)} jurors")
        
        # Count types
        active_count = sum(1 for j in jury.jurors if j.type == "active_ai")
        lightweight_count = sum(1 for j in jury.jurors if j.type == "lightweight_ai")
        human_count = sum(1 for j in jury.jurors if j.type == "human")
        
        print(f"  - Active AI (GPT-4o): {active_count} jurors")
        print(f"  - Lightweight AI (GPT-4o-mini): {lightweight_count} jurors")
        print(f"  - Human: {human_count} juror")
        
        # Test deliberation start
        prompt = jury.start_deliberation()
        print(f"✓ Deliberation prompt generated ({len(prompt)} chars)")
        
        return True
    
    except Exception as e:
        print(f"✗ Jury test failed: {e}")
        return False


async def main():
    """Run all production tests."""
    print("\n" + "="*60)
    print("VERITAS PRODUCTION MODE TEST")
    print("="*60)
    print("\nThis will test the system with real OpenAI API calls.")
    print("Estimated cost: < $0.10")
    
    results = []
    
    # Test 1: LLM Service
    results.append(await test_llm_service())
    
    # Test 2: Orchestrator
    results.append(await test_orchestrator_initialization())
    
    # Test 3: Trial Agents
    results.append(await test_trial_agent_generation())
    
    # Test 4: Jury
    results.append(await test_jury_generation())
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    passed = sum(results)
    total = len(results)
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ ALL TESTS PASSED - System is working perfectly!")
        print("\nThe system is ready for:")
        print("  1. Interactive demo (./play.sh)")
        print("  2. API server (./run_server.sh)")
        print("  3. Luffa Bot integration (set LUFFA_BOT_SECRET in .env)")
    else:
        print("\n✗ Some tests failed - please review errors above")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
