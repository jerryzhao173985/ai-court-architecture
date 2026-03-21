"""Have all 5 bots send DMs to user so they can be added as friends."""

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


async def send_friend_requests():
    """Have each bot send you a DM so you can add them as friends."""
    print("\n" + "="*60)
    print("🤖 VERITAS Bot Friend Request System")
    print("="*60 + "\n")
    
    print(f"📱 Your Luffa ID: {YOUR_USER_ID}")
    print()
    
    config = load_config()
    multi_bot = MultiBotClient(config.luffa)
    
    roles = multi_bot.get_configured_roles()
    print(f"Sending DMs from {len(roles)} bots...\n")
    
    # Messages for each bot
    bot_messages = {
        "clerk": """👋 Hello! I'm the Clerk bot for VERITAS Courtroom Experience.

I orchestrate the trial and guide you through the experience.

Please add me as a friend, then invite me to your Courtroom group!""",
        
        "prosecution": """👋 Hello! I'm the Prosecution bot for VERITAS.

I play the Crown barrister presenting the case against the defendant.

Please add me as a friend, then invite me to your Courtroom group!""",
        
        "defence": """👋 Hello! I'm the Defence bot for VERITAS.

I play the defence barrister representing the accused.

Please add me as a friend, then invite me to your Courtroom group!""",
        
        "fact_checker": """👋 Hello! I'm the Fact Checker bot for VERITAS.

I intervene when factual errors are made during the trial.

Please add me as a friend, then invite me to your Courtroom group!""",
        
        "judge": """👋 Hello! I'm the Judge bot for VERITAS.

I provide legal instructions and reveal the truth at the end.

Please add me as a friend, then invite me to your Courtroom group!"""
    }
    
    # Send DM from each bot
    for role in roles:
        if role in bot_messages:
            print(f"📤 Sending DM from {role.upper()} bot...")
            
            success = await multi_bot.send_as_agent(
                agent_role=role,
                group_id=YOUR_USER_ID,
                message=bot_messages[role],
                is_dm=True  # Send as DM
            )
            
            if success:
                print(f"   ✅ {role.upper()} sent DM")
            else:
                print(f"   ❌ {role.upper()} failed to send DM")
            
            await asyncio.sleep(1)  # Pace the messages
    
    print()
    print("="*60)
    print("Next Steps:")
    print("="*60)
    print()
    print("1. Check your Luffa DMs - you should have 5 messages")
    print("2. Add each bot as a friend (accept friend requests)")
    print("3. Open your Courtroom group")
    print("4. Invite all 5 bots to the group:")
    print("   • Clerk")
    print("   • Prosecution")
    print("   • Defence")
    print("   • Fact Checker")
    print("   • Judge")
    print("5. Run: ./run_courtroom.sh")
    print("6. Type in group: /start")
    print()


if __name__ == "__main__":
    asyncio.run(send_friend_requests())
