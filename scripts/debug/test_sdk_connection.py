"""Test Luffa Bot connection using official SDK."""

import asyncio
import logging
from src.config import load_config
from src.multi_bot_client_sdk import MultiBotSDKClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("veritas")

# Your information
YOUR_USER_ID = "WYspi9HYaHH"
COURTROOM_GROUP_ID = "Hqvqnvzh4mq"


async def test_sdk():
    """Test SDK connection with all bots."""
    print("\n" + "="*60)
    print("🧪 Testing Luffa Bot SDK Connection")
    print("="*60 + "\n")
    
    config = load_config()
    multi_bot = MultiBotSDKClient(config.luffa)
    
    roles = multi_bot.get_configured_roles()
    print(f"✅ Configured {len(roles)} bots: {', '.join(roles)}\n")
    
    # Test 1: Send DM from each bot
    print("📤 Test 1: Sending DMs to you...\n")
    
    for role in roles:
        message = f"👋 Hello from {role.upper()} bot! SDK test successful."
        
        success = await multi_bot.send_as_agent(
            agent_role=role,
            group_id=YOUR_USER_ID,
            message=message,
            is_dm=True
        )
        
        if success:
            print(f"   ✅ {role.upper()}: DM sent")
        else:
            print(f"   ❌ {role.upper()}: DM failed")
        
        await asyncio.sleep(1)
    
    print()
    
    # Test 2: Send group message from Clerk
    print("📤 Test 2: Sending group message from Clerk...\n")
    
    success = await multi_bot.send_as_agent(
        agent_role="clerk",
        group_id=COURTROOM_GROUP_ID,
        message="🎭 VERITAS Courtroom is ready! Type /start to begin.",
        is_dm=False
    )
    
    if success:
        print("   ✅ Clerk: Group message sent")
    else:
        print("   ❌ Clerk: Group message failed (bot may not be in group)")
    
    print()
    
    # Test 3: Poll for messages from Clerk
    print("📥 Test 3: Polling for messages from Clerk...\n")
    
    messages = await multi_bot.poll_messages("clerk")
    
    if messages:
        print(f"   📬 Received {len(messages)} message(s):")
        for msg in messages:
            print(f"      • From: {msg.get('sender_uid')}")
            print(f"        Type: {'Group' if msg.get('type') == 1 else 'DM'}")
            print(f"        Text: {msg.get('text', 'N/A')[:50]}")
    else:
        print("   📭 No messages")
    
    print()
    print("="*60)
    print("✅ SDK Test Complete")
    print("="*60)
    print()
    print("Check your Luffa app:")
    print(f"  • DMs: You should have {len(roles)} new messages")
    print("  • Group: Check if Clerk message appeared in Courtroom")
    print()
    print("If DMs arrived but group message didn't:")
    print("  → Bots need to be added to the group first")
    print("  → Search for bot UIDs in Luffa and add them")
    print()


if __name__ == "__main__":
    asyncio.run(test_sdk())
