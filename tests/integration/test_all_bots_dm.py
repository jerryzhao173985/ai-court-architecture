"""Test all 5 bots sending DMs using SDK."""

import asyncio
import logging
from src.config import load_config
from src.multi_bot_client_sdk import MultiBotSDKClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("veritas")

YOUR_USER_ID = "WYspi9HYaHH"


async def test_all_bots():
    """Test all bots sending DMs."""
    print("\n" + "="*60)
    print("🤖 Testing All 5 Bots with SDK")
    print("="*60 + "\n")
    
    config = load_config()
    multi_bot = MultiBotSDKClient(config.luffa)
    
    bot_messages = {
        "clerk": "👋 Clerk here! I orchestrate the trial. My UID: ORQAZCejHdZELLD",
        "prosecution": "👋 Prosecution here! I present the Crown's case. My UID: MZIXVYXwSwRx6Vd",
        "defence": "👋 Defence here! I defend the accused. My UID: NGKIEJGGRlKKnAqC",
        "fact_checker": "👋 Fact Checker here! I verify facts. My UID: GKUPDBfLv23WktAS",
        "judge": "👋 Judge here! I provide legal guidance. My UID: YNLJHNCCsRmLBcvU"
    }
    
    for role, message in bot_messages.items():
        print(f"📤 {role.upper()} sending DM...")
        
        success = await multi_bot.send_as_agent(
            agent_role=role,
            group_id=YOUR_USER_ID,
            message=message,
            is_dm=True
        )
        
        if success:
            print(f"   ✅ Success")
        else:
            print(f"   ❌ Failed")
        
        await asyncio.sleep(1)
    
    print()
    print("="*60)
    print("📱 CHECK YOUR LUFFA DMs")
    print("="*60)
    print()
    print("You should have 5 new DMs with bot UIDs.")
    print()
    print("To add bots:")
    print("1. Open each DM in Luffa")
    print("2. Click on bot profile")
    print("3. Add as friend")
    print("4. Invite to Courtroom group (Hqvqnvzh4mq)")
    print()


if __name__ == "__main__":
    asyncio.run(test_all_bots())
