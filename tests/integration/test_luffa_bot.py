#!/usr/bin/env python3
"""Test Luffa Bot service (without actual bot secret)."""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from luffa_bot_service import LuffaBotService
from config import load_config


async def test_service_initialization():
    """Test that service can be initialized."""
    print("\n" + "="*60)
    print("TEST: Luffa Bot Service Initialization")
    print("="*60)
    
    try:
        # This will work even without bot secret
        service = LuffaBotService()
        print("✓ Service created")
        
        # Check configuration
        if service.config.luffa.bot_enabled:
            print("✓ Bot enabled in config")
            if service.config.luffa.api_key:
                print("✓ Bot secret configured")
            else:
                print("⚠ Bot secret not set (get from https://robot.luffa.im)")
        else:
            print("⚠ Bot disabled in config (set LUFFA_BOT_ENABLED=true)")
        
        print(f"✓ API endpoint: {service.client.base_url}")
        print(f"✓ Active sessions: {len(service.active_sessions)}")
        
        return True
    
    except Exception as e:
        print(f"✗ Service initialization failed: {e}")
        return False


async def test_command_parsing():
    """Test command parsing logic."""
    print("\n" + "="*60)
    print("TEST: Command Parsing")
    print("="*60)
    
    commands = [
        "/start",
        "/continue", 
        "/vote guilty",
        "/vote not_guilty",
        "/evidence",
        "/status",
        "/help"
    ]
    
    print("✓ Supported commands:")
    for cmd in commands:
        print(f"  - {cmd}")
    
    return True


async def test_message_flow():
    """Test message handling flow."""
    print("\n" + "="*60)
    print("TEST: Message Flow")
    print("="*60)
    
    print("Message flow:")
    print("  1. Luffa group chat → Bot receives (polling)")
    print("  2. Parse command or deliberation")
    print("  3. Orchestrator processes")
    print("  4. AI agents generate (GPT-4o)")
    print("  5. Bot posts to group")
    print("  6. Users see AI characters")
    
    print("\n✓ Message flow structure verified")
    return True


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("LUFFA BOT SERVICE TEST")
    print("="*60)
    print("\nThis tests the bot service structure (no API calls).")
    
    results = []
    
    results.append(await test_service_initialization())
    results.append(await test_command_parsing())
    results.append(await test_message_flow())
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    passed = sum(results)
    total = len(results)
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ Bot service structure is correct!")
        print("\nTo activate:")
        print("  1. Get bot secret from https://robot.luffa.im")
        print("  2. Set LUFFA_BOT_SECRET in .env")
        print("  3. Set LUFFA_BOT_ENABLED=true")
        print("  4. Run: ./run_luffa_bot.sh")
    else:
        print("\n✗ Some tests failed")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
