"""Test bot connectivity to Luffa API."""

import asyncio
import logging
from src.config import load_config
from src.multi_bot_client import MultiBotClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("veritas")


async def test_bot_connectivity():
    """Test that bots can connect to Luffa API."""
    print("\n" + "="*60)
    print("VERITAS Bot Connectivity Test")
    print("="*60 + "\n")
    
    config = load_config()
    multi_bot = MultiBotClient(config.luffa)
    
    roles = multi_bot.get_configured_roles()
    print(f"Testing {len(roles)} bots...\n")
    
    # Test polling messages from Clerk (main orchestrator)
    print("📡 Testing Clerk bot message polling...")
    try:
        messages = await multi_bot.poll_messages("clerk")
        print(f"✅ Clerk bot connected successfully")
        print(f"   Received {len(messages)} messages")
        
        if messages:
            print("\n📬 Recent messages:")
            for msg in messages[:3]:  # Show first 3
                text = msg.get("text", "")[:50]
                print(f"   • {text}...")
    except Exception as e:
        print(f"❌ Clerk bot connection failed: {e}")
    
    print("\n" + "="*60)
    print("Status:")
    print("="*60)
    print()
    print("If you see '✅ Clerk bot connected successfully', your setup is working!")
    print()
    print("Next: Add all 5 bots to a Luffa group and run:")
    print("  python src/multi_bot_service.py")
    print()


if __name__ == "__main__":
    asyncio.run(test_bot_connectivity())
