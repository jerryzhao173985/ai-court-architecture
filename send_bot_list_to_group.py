"""Send bot UID list to the Courtroom group so user can add them."""

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


async def send_bot_list():
    """Send bot UID list to group."""
    print("\n" + "="*60)
    print("📋 Sending Bot List to Courtroom Group")
    print("="*60 + "\n")
    
    config = load_config()
    multi_bot = MultiBotClient(config.luffa)
    
    # Message with all bot UIDs
    message = """🎭 VERITAS COURTROOM BOTS

Please add these 5 bots to this group:

1️⃣ **Clerk**
   UID: ORQAZCejHdZELLD
   Role: Orchestrates the trial

2️⃣ **Prosecution**
   UID: MZIXVYXwSwRx6Vd
   Role: Crown barrister

3️⃣ **Defence**
   UID: NGKIEJGGRlKKnAqC
   Role: Defence barrister

4️⃣ **Fact Checker**
   UID: GKUPDBfLv23WktAS
   Role: Verifies facts

5️⃣ **Judge**
   UID: YNLJHNCCsRmLBcvU
   Role: Provides legal guidance

📱 TO ADD EACH BOT:
• Search for the UID in Luffa
• Add as friend
• Invite to this group

Once all 5 bots are here, type /start to begin the trial! ⚖️"""
    
    # Try sending from Clerk bot
    print("📤 Attempting to send from Clerk bot to group...\n")
    
    success = await multi_bot.send_as_agent(
        agent_role="clerk",
        group_id=COURTROOM_GROUP_ID,
        message=message,
        is_dm=False  # Group message
    )
    
    if success:
        print("✅ Message sent to group!")
        print()
        print("Check your Courtroom group in Luffa.")
        print("You should see a message with all bot UIDs.")
    else:
        print("❌ Failed to send to group")
        print()
        print("This is expected if Clerk bot is not in the group yet.")
        print()
        print("Manual steps:")
        print("="*60)
        print(message)
        print("="*60)
        print()
        print("Copy the UIDs above and search for them in Luffa app.")
    
    print()


if __name__ == "__main__":
    asyncio.run(send_bot_list())
