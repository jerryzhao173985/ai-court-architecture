"""Test multi-bot configuration and basic functionality."""

import asyncio
import logging
from src.config import load_config
from src.multi_bot_client import MultiBotClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("veritas")


async def test_multi_bot_setup():
    """Test that all bots are configured and can be initialized."""
    print("\n" + "="*60)
    print("VERITAS Multi-Bot Configuration Test")
    print("="*60 + "\n")
    
    # Load configuration
    config = load_config()
    
    print("📋 Configuration loaded:")
    print(f"  API URL: {config.luffa.api_base_url}")
    print(f"  Bot enabled: {config.luffa.bot_enabled}")
    print()
    
    # Initialize multi-bot client
    multi_bot = MultiBotClient(config.luffa)
    
    # Check configured roles
    roles = multi_bot.get_configured_roles()
    print(f"✅ Configured {len(roles)} bots:")
    for role in roles:
        print(f"  • {role.upper()}")
    print()
    
    # Verify each required role
    required_roles = ["clerk", "prosecution", "defence", "fact_checker", "judge"]
    missing_roles = []
    
    for role in required_roles:
        if multi_bot.has_bot_for_role(role):
            print(f"✅ {role.upper()} bot: Ready")
        else:
            print(f"❌ {role.upper()} bot: Missing")
            missing_roles.append(role)
    
    print()
    
    if missing_roles:
        print(f"⚠️  Missing {len(missing_roles)} required bots: {', '.join(missing_roles)}")
        print("   The system will fall back to single-bot mode for missing roles.")
    else:
        print("🎉 All 5 trial agent bots are configured!")
        print("   Your courtroom will have realistic multi-participant chat.")
    
    print()
    print("="*60)
    print("Next Steps:")
    print("="*60)
    print()
    print("1. Add all 5 bots to your Luffa group chat")
    print("2. Run: python src/multi_bot_service.py")
    print("3. In the group, type: /start")
    print("4. Watch the trial unfold with each agent as a separate bot!")
    print()
    print("Bot UIDs to add to your group:")
    for role in required_roles:
        client = multi_bot.get_client(role)
        if client and hasattr(config.luffa, f"{role}_bot"):
            bot_cfg = getattr(config.luffa, f"{role}_bot")
            if bot_cfg:
                print(f"  • {role.upper()}: {bot_cfg.uid}")
    print()


if __name__ == "__main__":
    asyncio.run(test_multi_bot_setup())
