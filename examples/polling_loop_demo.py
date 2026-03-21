"""
Demonstration of the message polling loop in the orchestrator.

This example shows how to use the orchestrator's built-in message polling
functionality to handle incoming Luffa Bot messages.

Task 22.1: Implement message polling loop in orchestrator
- Polls /receive endpoint every 1 second
- Parses incoming messages and routes to appropriate handlers
- Implements message deduplication by msgId
"""

import asyncio
import logging
from src.orchestrator import ExperienceOrchestrator
from src.config import load_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Demonstrate the polling loop functionality."""
    
    # Load configuration from environment
    config = load_config()
    
    # Create orchestrator instance
    orchestrator = ExperienceOrchestrator(
        session_id="demo-session-001",
        user_id="demo-user",
        case_id="blackthorn-hall-001",
        config=config
    )
    
    logger.info("Initializing orchestrator...")
    init_result = await orchestrator.initialize()
    
    if not init_result["success"]:
        logger.error(f"Failed to initialize: {init_result.get('error')}")
        return
    
    logger.info("✓ Orchestrator initialized successfully")
    
    # Start the message polling loop
    logger.info("Starting message polling loop...")
    await orchestrator.start_message_polling()
    
    logger.info("✓ Polling loop started - listening for messages every 1 second")
    logger.info("  - Messages are automatically deduplicated by msgId")
    logger.info("  - Commands (starting with /) are routed to command handlers")
    logger.info("  - Regular messages are treated as deliberation statements")
    logger.info("")
    logger.info("Available commands:")
    logger.info("  /start - Begin a new trial")
    logger.info("  /continue - Advance to next stage")
    logger.info("  /vote guilty|not_guilty - Cast your vote")
    logger.info("  /evidence - View evidence board")
    logger.info("  /status - Check trial progress")
    logger.info("  /help - Show help message")
    logger.info("")
    logger.info("Press Ctrl+C to stop...")
    
    try:
        # Keep running until interrupted
        while True:
            await asyncio.sleep(1)
    
    except KeyboardInterrupt:
        logger.info("\nReceived shutdown signal")
    
    finally:
        # Stop the polling loop
        logger.info("Stopping message polling loop...")
        await orchestrator.stop_message_polling()
        logger.info("✓ Polling loop stopped")


async def demo_custom_handler():
    """Demonstrate custom message handler registration."""
    
    config = load_config()
    
    orchestrator = ExperienceOrchestrator(
        session_id="demo-session-002",
        user_id="demo-user",
        case_id="blackthorn-hall-001",
        config=config
    )
    
    await orchestrator.initialize()
    
    # Define a custom message handler
    async def custom_handler(msg: dict):
        """Custom handler that logs all messages from a specific group."""
        logger.info(f"Custom handler received message: {msg.get('text')}")
        # You can add custom logic here
    
    # Register the custom handler for a specific group
    group_id = "custom-group-123"
    orchestrator.register_message_handler(group_id, custom_handler)
    
    logger.info(f"Registered custom handler for group: {group_id}")
    
    # Start polling
    await orchestrator.start_message_polling()
    
    try:
        await asyncio.sleep(10)  # Run for 10 seconds
    finally:
        # Unregister handler
        orchestrator.unregister_message_handler(group_id)
        await orchestrator.stop_message_polling()
        logger.info("Custom handler demo complete")


if __name__ == "__main__":
    # Run the main demo
    asyncio.run(main())
    
    # Uncomment to run the custom handler demo instead:
    # asyncio.run(demo_custom_handler())
