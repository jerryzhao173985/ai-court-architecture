"""Send bot UIDs to user so they can manually add bots in Luffa app."""

import asyncio
import logging
from src.config import load_config
from src.multi_bot_client import MultiBotClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("veritas")

# Your Luffa user ID
YOUR_USER_ID = "WYspi9HYaHH"


async def send_bot_info():
    """Send comprehensive bot information to user."""
    print("\n" + "="*60)
    print("🤖 VERITAS Bot UID Sender")
    print("="*60 + "\n")
    
    config = load_config()
    
    # Bot UIDs from config
    bot_info = {
        "clerk": config.luffa.clerk_bot.uid if config.luffa.clerk_bot else None,
        "prosecution": config.luffa.prosecution_bot.uid if config.luffa.prosecution_bot else None,
        "defence": config.luffa.defence_bot.uid if config.luffa.defence_bot else None,
        "fact_checker": config.luffa.fact_checker_bot.uid if config.luffa.fact_checker_bot else None,
        "judge": config.luffa.judge_bot.uid if config.luffa.judge_bot else None
    }
    
    # Create comprehensive message with all bot UIDs
    message = """🎭 VERITAS COURTROOM BOTS - ADD INSTRUCTIONS

To add these bots to your Courtroom group, follow these steps:

📋 BOT UIDs (Search for these in Luffa):

1️⃣ Clerk: ORQAZCejHdZELLD
2️⃣ Prosecution: MZIXVYXwSwRx6Vd
3️⃣ Defence: NGKIEJGGRlKKnAqC
4️⃣ Fact Checker: GKUPDBfLv23WktAS
5️⃣ Judge: YNLJHNCCsRmLBcvU

📱 HOW TO ADD BOTS:

Option A - Search by UID:
• Open Luffa app
• Go to Contacts or Add Friend
• Search for each UID above
• Send friend request
• Once accepted, invite to Courtroom group

Option B - If bots can send you messages:
• Check your DMs for messages from these bots
• Click on each bot profile
• Add as friend
• Invite to Courtroom group (Hqvqnvzh4mq)

🎯 Your Group: Courtroom (Hqvqnvzh4mq)

Once all 5 bots are in the group, type /start to begin!"""
    
    multi_bot = MultiBotClient(config.luffa)
    
    # Try sending from Clerk bot (most likely to work)
    print("📤 Sending bot UID list from Clerk bot...\n")
    
    success = await multi_bot.send_as_agent(
        agent_role="clerk",
        group_id=YOUR_USER_ID,
        message=message,
        is_dm=True
    )
    
    if success:
        print("✅ Message sent successfully!")
        print()
        print("Check your Luffa DMs for the bot UID list.")
    else:
        print("❌ Failed to send message")
        print()
        print("Manual approach:")
        print("="*60)
        print(message)
        print("="*60)
    
    print()


if __name__ == "__main__":
    asyncio.run(send_bot_info())
