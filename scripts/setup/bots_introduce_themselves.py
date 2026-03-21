"""Have each bot introduce itself with its UID so user can add them."""

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


async def bots_introduce():
    """Have each bot send introduction with its UID."""
    print("\n" + "="*60)
    print("🤖 VERITAS Bots Self-Introduction")
    print("="*60 + "\n")
    
    config = load_config()
    multi_bot = MultiBotClient(config.luffa)
    
    # Bot introductions with their UIDs
    introductions = {
        "clerk": {
            "uid": config.luffa.clerk_bot.uid if config.luffa.clerk_bot else None,
            "message": """👋 Hello! I'm the CLERK bot.

🆔 My UID: ORQAZCejHdZELLD

I orchestrate the trial and guide you through the courtroom experience.

📱 TO ADD ME:
1. Search for my UID in Luffa: ORQAZCejHdZELLD
2. Add me as a friend
3. Invite me to your Courtroom group (Hqvqnvzh4mq)

Looking forward to serving justice with you! ⚖️"""
        },
        "prosecution": {
            "uid": config.luffa.prosecution_bot.uid if config.luffa.prosecution_bot else None,
            "message": """👋 Hello! I'm the PROSECUTION bot.

🆔 My UID: MZIXVYXwSwRx6Vd

I present the Crown's case against the defendant.

📱 TO ADD ME:
1. Search for my UID in Luffa: MZIXVYXwSwRx6Vd
2. Add me as a friend
3. Invite me to your Courtroom group (Hqvqnvzh4mq)

Justice must be served! ⚖️"""
        },
        "defence": {
            "uid": config.luffa.defence_bot.uid if config.luffa.defence_bot else None,
            "message": """👋 Hello! I'm the DEFENCE bot.

🆔 My UID: NGKIEJGGRlKKnAqC

I defend the accused and create reasonable doubt.

📱 TO ADD ME:
1. Search for my UID in Luffa: NGKIEJGGRlKKnAqC
2. Add me as a friend
3. Invite me to your Courtroom group (Hqvqnvzh4mq)

Everyone deserves a fair defence! ⚖️"""
        },
        "fact_checker": {
            "uid": config.luffa.fact_checker_bot.uid if config.luffa.fact_checker_bot else None,
            "message": """👋 Hello! I'm the FACT CHECKER bot.

🆔 My UID: GKUPDBfLv23WktAS

I intervene when factual errors are made during trial.

📱 TO ADD ME:
1. Search for my UID in Luffa: GKUPDBfLv23WktAS
2. Add me as a friend
3. Invite me to your Courtroom group (Hqvqnvzh4mq)

Truth matters! ⚖️"""
        },
        "judge": {
            "uid": config.luffa.judge_bot.uid if config.luffa.judge_bot else None,
            "message": """👋 Hello! I'm the JUDGE bot.

🆔 My UID: YNLJHNCCsRmLBcvU

I provide legal instructions and reveal the truth.

📱 TO ADD ME:
1. Search for my UID in Luffa: YNLJHNCCsRmLBcvU
2. Add me as a friend
3. Invite me to your Courtroom group (Hqvqnvzh4mq)

Order in the court! ⚖️"""
        }
    }
    
    # Send introduction from each bot
    for role, info in introductions.items():
        if info["uid"]:
            print(f"📤 {role.upper()} bot introducing itself...")
            
            success = await multi_bot.send_as_agent(
                agent_role=role,
                group_id=YOUR_USER_ID,
                message=info["message"],
                is_dm=True
            )
            
            if success:
                print(f"   ✅ {role.upper()} sent introduction")
            else:
                print(f"   ❌ {role.upper()} failed")
            
            await asyncio.sleep(2)  # Pace the messages
    
    print()
    print("="*60)
    print("📱 CHECK YOUR LUFFA DMs")
    print("="*60)
    print()
    print("You should receive 5 DMs with bot UIDs.")
    print()
    print("For each bot:")
    print("1. Open the DM in Luffa")
    print("2. Click on the bot's profile")
    print("3. Add as friend")
    print("4. Go to Courtroom group")
    print("5. Add bot to group")
    print()
    print("Once all 5 bots are in the group, run:")
    print("  ./run_courtroom.sh")
    print()


if __name__ == "__main__":
    asyncio.run(bots_introduce())
