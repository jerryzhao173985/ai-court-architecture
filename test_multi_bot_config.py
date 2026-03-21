#!/usr/bin/env python3
"""Test script to verify multi-bot configuration."""

import sys
from config import load_config
from multi_bot_client import MultiBotClient


def test_config():
    """Test configuration loading."""
    print("=" * 80)
    print("VERITAS MULTI-BOT CONFIGURATION TEST")
    print("=" * 80)
    print()
    
    try:
        config = load_config()
        print("✓ Configuration loaded successfully")
        print()
        
        # Check LLM config
        print(f"LLM Provider: {config.llm.provider}")
        print(f"LLM Model: {config.llm.model}")
        print(f"API Key: {'*' * 20}{config.llm.api_key[-4:] if len(config.llm.api_key) > 4 else '****'}")
        print()
        
        # Check Luffa config
        print(f"Luffa API: {config.luffa.api_base_url}")
        print(f"Bot Enabled: {config.luffa.bot_enabled}")
        print()
        
        # Check individual bots
        print("Configured Bots:")
        print("-" * 80)
        
        bot_count = 0
        
        if config.luffa.clerk_bot:
            print(f"✓ Clerk Bot: {config.luffa.clerk_bot.uid} (enabled: {config.luffa.clerk_bot.enabled})")
            bot_count += 1
        else:
            print("✗ Clerk Bot: NOT CONFIGURED")
        
        if config.luffa.prosecution_bot:
            print(f"✓ Prosecution Bot: {config.luffa.prosecution_bot.uid} (enabled: {config.luffa.prosecution_bot.enabled})")
            bot_count += 1
        else:
            print("✗ Prosecution Bot: NOT CONFIGURED")
        
        if config.luffa.defence_bot:
            print(f"✓ Defence Bot: {config.luffa.defence_bot.uid} (enabled: {config.luffa.defence_bot.enabled})")
            bot_count += 1
        else:
            print("✗ Defence Bot: NOT CONFIGURED")
        
        if config.luffa.fact_checker_bot:
            print(f"✓ Fact Checker Bot: {config.luffa.fact_checker_bot.uid} (enabled: {config.luffa.fact_checker_bot.enabled})")
            bot_count += 1
        else:
            print("✗ Fact Checker Bot: NOT CONFIGURED")
        
        if config.luffa.judge_bot:
            print(f"✓ Judge Bot: {config.luffa.judge_bot.uid} (enabled: {config.luffa.judge_bot.enabled})")
            bot_count += 1
        else:
            print("✗ Judge Bot: NOT CONFIGURED")
        
        print()
        
        if config.luffa.juror_bots:
            print(f"✓ Juror Bots: {len(config.luffa.juror_bots)} configured")
            for juror_id, bot in config.luffa.juror_bots.items():
                print(f"  - {juror_id}: {bot.uid} (enabled: {bot.enabled})")
        else:
            print("ℹ️  Juror Bots: None configured (optional)")
        
        print()
        print("-" * 80)
        print()
        
        # Test multi-bot client
        print("Testing Multi-Bot Client...")
        multi_bot = MultiBotClient(config.luffa)
        
        configured_roles = multi_bot.get_configured_roles()
        print(f"✓ Multi-bot client initialized with {len(configured_roles)} roles")
        print(f"  Roles: {', '.join(configured_roles)}")
        print()
        
        # Summary
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print()
        print(f"Total Bots Configured: {bot_count}/5 required")
        print()
        
        if bot_count >= 5:
            print("✅ READY TO RUN")
            print()
            print("Next steps:")
            print("  1. Add all 5 bots to a Luffa group chat")
            print("  2. Run: python src/multi_bot_service.py")
            print("  3. In group chat, send: /start")
            print()
            return 0
        else:
            print("⚠️  INCOMPLETE CONFIGURATION")
            print()
            print("Missing bots. Please configure all 5 required bots in .env")
            print("Run: python setup_bots.py for guided setup")
            print()
            return 1
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        print()
        print("Please check your .env file and ensure all required variables are set.")
        return 1


if __name__ == "__main__":
    sys.exit(test_config())
