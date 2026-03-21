"""Simulate what happens when user types /start in the Courtroom group."""

import asyncio
import logging
from src.multi_bot_service import MultiBotService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("veritas")

# Your group and a test user
COURTROOM_GROUP_ID = "Hqvqnvzh4mq"
TEST_USER_UID = "test_user_001"


async def simulate_start():
    """Simulate /start command in Courtroom group."""
    print("\n" + "="*60)
    print("🎭 VERITAS Trial Start Simulation")
    print("="*60 + "\n")
    
    print(f"Group: Courtroom ({COURTROOM_GROUP_ID})")
    print(f"User: {TEST_USER_UID}")
    print()
    
    # Initialize service
    service = MultiBotService()
    
    print("✅ Service initialized")
    print(f"   Configured bots: {', '.join(service.multi_bot.get_configured_roles())}")
    print()
    
    # Simulate /start command
    print("📥 Simulating: User types '/start'")
    print()
    
    # Create mock message
    mock_message = {
        "text": "/start",
        "gid": COURTROOM_GROUP_ID,
        "uid": TEST_USER_UID,
        "sender_uid": TEST_USER_UID,
        "type": 1,  # Group message
        "msgId": "test_msg_001"
    }
    
    print("🔄 Processing command...")
    print()
    
    # Handle the message
    await service.handle_message(mock_message)
    
    print()
    print("="*60)
    print("What You Should See in Courtroom Group:")
    print("="*60)
    print()
    print("1. Clerk: Greeting message explaining VERITAS")
    print("2. Clerk: Hook scene (atmospheric opening)")
    print("3. [Continue] button appears")
    print()
    print("If you see these messages, the system is working!")
    print()
    print("="*60)
    print("Next: Check your Courtroom group in Luffa")
    print("="*60)
    print()


if __name__ == "__main__":
    asyncio.run(simulate_start())
