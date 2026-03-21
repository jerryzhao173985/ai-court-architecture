"""Check if bots have any pending friend requests or group invitations."""

import asyncio
import logging
import json
from src.config import load_config
from src.multi_bot_client import MultiBotClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("veritas")


async def check_notifications():
    """Poll each bot to see if they have pending notifications."""
    print("\n" + "="*60)
    print("🔔 Checking Bot Notifications")
    print("="*60 + "\n")
    
    config = load_config()
    multi_bot = MultiBotClient(config.luffa)
    
    roles = multi_bot.get_configured_roles()
    
    for role in roles:
        print(f"📥 Checking {role.upper()} bot...")
        
        messages = await multi_bot.poll_messages(role)
        
        if messages:
            print(f"   📬 {len(messages)} message(s) found:")
            for msg in messages:
                print(f"      • Type: {msg.get('type')} (0=DM, 1=Group)")
                print(f"        From: {msg.get('uid')}")
                print(f"        Text: {msg.get('text', 'N/A')[:50]}")
                print(f"        Full: {json.dumps(msg, indent=2)}")
                print()
        else:
            print(f"   📭 No messages")
        
        print()
        await asyncio.sleep(1)
    
    print("="*60)
    print("Analysis:")
    print("="*60)
    print()
    print("If you see messages from your UID (WYspi9HYaHH):")
    print("  → These might be friend requests or group invitations")
    print("  → Check the message type and content")
    print()
    print("If no messages:")
    print("  → Bots haven't received any notifications yet")
    print("  → You may need to manually search for bots by UID in Luffa")
    print()


if __name__ == "__main__":
    asyncio.run(check_notifications())
