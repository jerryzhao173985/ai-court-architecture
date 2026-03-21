"""Test VERITAS in the Courtroom group."""

import asyncio
import logging
from src.config import load_config
from src.multi_bot_client import MultiBotClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("veritas")

# Your Courtroom group ID
COURTROOM_GROUP_ID = "Hqvqnvzh4mq"


async def test_courtroom_group():
    """Test sending a message to the Courtroom group."""
    print("\n" + "="*60)
    print("VERITAS Courtroom Group Test")
    print("="*60 + "\n")
    
    config = load_config()
    multi_bot = MultiBotClient(config.luffa)
    
    print(f"📍 Target Group: {COURTROOM_GROUP_ID}")
    print(f"🤖 Configured Bots: {', '.join(multi_bot.get_configured_roles())}")
    print()
    
    # Test sending a welcome message from Clerk
    print("📤 Sending test message from Clerk bot...")
    
    test_message = """🎭 **VERITAS COURTROOM EXPERIENCE**

Welcome to the interactive trial system!

The courtroom is now in session. All 5 trial agents are present:
• 📋 Clerk (me) - Your guide
• 👔 Prosecution - Crown barrister
• 🛡️ Defence - Defence barrister
• 🔍 Fact Checker - Truth guardian
• ⚖️ Judge - Legal authority

Type /help to see available commands.
Type /start to begin your first trial!"""
    
    success = await multi_bot.send_as_agent(
        agent_role="clerk",
        group_id=COURTROOM_GROUP_ID,
        message=test_message,
        button=[
            {"name": "📚 Help", "selector": "/help", "isHidden": "0"},
            {"name": "🎬 Start Trial", "selector": "/start", "isHidden": "0"}
        ]
    )
    
    if success:
        print("✅ Message sent successfully!")
        print()
        print("Check your Courtroom group - you should see a message from the Clerk bot.")
    else:
        print("❌ Failed to send message")
        print()
        print("Possible issues:")
        print("  • Clerk bot not added to group")
        print("  • Bot credentials incorrect")
        print("  • API endpoint wrong")
    
    print()
    print("="*60)
    print("Next Steps:")
    print("="*60)
    print()
    
    if success:
        print("1. ✅ Clerk bot can send messages to your group")
        print("2. Ensure all 5 bots are added to the group")
        print("3. Run: python src/multi_bot_service.py")
        print("4. In the Courtroom group, type: /start")
        print("5. Experience the trial!")
    else:
        print("1. Add Clerk bot (ORQAZCejHdZELLD) to group Hqvqnvzh4mq")
        print("2. Verify bot credentials in .env")
        print("3. Run this test again")
    
    print()


if __name__ == "__main__":
    asyncio.run(test_courtroom_group())
