"""Luffa Bot service for group chat courtroom experience."""

import asyncio
import logging
from typing import Optional, Dict
from datetime import datetime

from luffa_client import LuffaBotAPIClient
from orchestrator import ExperienceOrchestrator
from state_machine import ExperienceState
from config import load_config

logger = logging.getLogger("veritas")


class LuffaBotService:
    """
    Service that runs VERITAS as a Luffa group chat experience.
    
    AI agents post as different characters in the group chat,
    users can interact and influence the story outcome.
    """

    def __init__(self):
        """Initialize Luffa Bot service."""
        self.config = load_config()
        self.client = LuffaBotAPIClient(self.config.luffa)
        self.active_sessions: Dict[str, ExperienceOrchestrator] = {}
        self.running = False

    async def start(self):
        """Start the bot service with polling loop."""
        if not self.config.luffa.bot_enabled:
            logger.error("Luffa Bot is disabled. Set LUFFA_BOT_ENABLED=true in .env")
            return
        
        if not self.config.luffa.api_key:
            logger.error("Luffa Bot secret not set. Get it from https://robot.luffa.im")
            return
        
        logger.info("Starting VERITAS Luffa Bot service...")
        self.running = True
        
        async with self.client:
            logger.info("✓ Connected to Luffa Bot API")
            logger.info("✓ Polling for messages every 1 second...")
            
            while self.running:
                try:
                    # Poll for messages
                    messages = await self.client.receive_messages()
                    
                    # Process each message
                    for msg in messages:
                        await self.handle_message(msg)
                    
                    # Wait 1 second before next poll
                    await asyncio.sleep(1)
                
                except Exception as e:
                    logger.error(f"Error in polling loop: {e}")
                    await asyncio.sleep(5)  # Back off on error

    async def handle_message(self, msg: dict):
        """
        Handle incoming message from Luffa.
        
        Args:
            msg: Parsed message object
        """
        text = msg.get("text", "").strip()
        uid = msg.get("uid")  # Group ID or user ID
        msg_type = msg.get("type")  # 0=DM, 1=Group
        
        if not text or not uid:
            return
        
        # Handle commands
        if text.startswith("/"):
            await self.handle_command(text, uid, msg_type, msg)
        else:
            # Handle deliberation statements if in active session
            await self.handle_deliberation(text, uid, msg)

    async def handle_command(self, command: str, uid: str, msg_type: int, msg: dict):
        """
        Handle bot commands.
        
        Args:
            command: Command text
            uid: User/group ID
            msg_type: 0=DM, 1=Group
            msg: Full message object
        """
        cmd = command.lower().split()[0]
        
        if cmd == "/start":
            await self.start_trial(uid, msg_type)
        
        elif cmd == "/continue":
            await self.continue_trial(uid)
        
        elif cmd == "/vote":
            vote = command.split()[1] if len(command.split()) > 1 else None
            await self.handle_vote(uid, vote, msg.get("sender_uid"))
        
        elif cmd == "/evidence":
            await self.show_evidence(uid)
        
        elif cmd == "/status":
            await self.show_status(uid)
        
        elif cmd == "/help":
            await self.show_help(uid, msg_type)
        
        else:
            if msg_type == 1:  # Group
                await self.client.send_group_message(uid, "Unknown command. Type /help for available commands.")
            else:  # DM
                await self.client.send_dm(uid, "Unknown command. Type /help for available commands.")

    async def start_trial(self, group_id: str, msg_type: int):
        """
        Start a new trial in a group.
        
        Args:
            group_id: Group ID
            msg_type: Message type
        """
        if msg_type != 1:  # Must be group
            await self.client.send_dm(group_id, "Trials can only be started in group chats.")
            return
        
        if group_id in self.active_sessions:
            await self.client.send_group_message(
                group_id,
                "⚠️ A trial is already in progress. Use /continue to proceed or /status to check progress."
            )
            return
        
        # Create new session
        session_id = f"luffa_{group_id}_{int(datetime.now().timestamp())}"
        orchestrator = ExperienceOrchestrator(
            session_id=session_id,
            user_id=group_id,
            case_id="blackthorn-hall-001"
        )
        
        # Initialize
        init_result = await orchestrator.initialize()
        
        if not init_result["success"]:
            await self.client.send_group_message(
                group_id,
                f"❌ Failed to start trial: {init_result.get('error')}"
            )
            return
        
        self.active_sessions[group_id] = orchestrator
        
        # Send greeting
        greeting = init_result["greeting"]["content"]
        await self.client.send_group_message(group_id, greeting)
        
        # Start hook scene
        start_result = await orchestrator.start_experience()
        
        if start_result["success"]:
            hook_content = start_result["hook_content"]["content"]
            await self.client.send_group_message(group_id, f"🎭 THE TRIAL BEGINS\n\n{hook_content}")
            
            # Prompt to continue
            await self.client.send_group_message(
                group_id,
                "Type /continue to proceed to the trial."
            )

    async def continue_trial(self, group_id: str):
        """
        Continue to next trial stage.
        
        Args:
            group_id: Group ID
        """
        orchestrator = self.active_sessions.get(group_id)
        
        if not orchestrator:
            await self.client.send_group_message(
                group_id,
                "⚠️ No active trial. Use /start to begin a new trial."
            )
            return
        
        current_state = orchestrator.state_machine.current_state
        
        # Check if in deliberation
        if current_state == ExperienceState.JURY_DELIBERATION:
            await self.client.send_group_message(
                group_id,
                "⚖️ You are currently deliberating. Share your thoughts or type /vote to cast your verdict."
            )
            return
        
        # Check if in voting
        if current_state == ExperienceState.ANONYMOUS_VOTE:
            await self.client.send_group_message(
                group_id,
                "⚖️ TIME TO VOTE\n\nType: /vote guilty OR /vote not_guilty"
            )
            return
        
        # Advance to next stage
        result = await orchestrator.advance_trial_stage()
        
        if not result["success"]:
            await self.client.send_group_message(
                group_id,
                f"❌ Error: {result.get('error')}"
            )
            return
        
        stage = result["stage"]
        announcement = result["announcement"]["content"]
        
        # Send stage announcement
        await self.client.send_group_message(group_id, f"📢 {announcement}")
        
        # Send agent responses
        if "agent_responses" in result:
            for response in result["agent_responses"]:
                role = response["agentRole"].upper()
                content = response["content"]
                
                # Format as character speaking
                await self.client.send_group_message(
                    group_id,
                    f"🎭 [{role}]\n\n{content}"
                )
                await asyncio.sleep(2)  # Pace the messages
        
        # Handle deliberation start
        if "deliberation_prompt" in result:
            prompt = result["deliberation_prompt"]
            await self.client.send_group_message(
                group_id,
                f"⚖️ JURY DELIBERATION\n\n{prompt}\n\nShare your thoughts in the chat. Type /evidence to view evidence board."
            )
            return
        
        # Prompt to continue
        next_state = orchestrator.state_machine.get_next_state()
        if next_state:
            await self.client.send_group_message(
                group_id,
                "Type /continue to proceed."
            )
        else:
            await self.client.send_group_message(
                group_id,
                "✓ Trial complete!"
            )

    async def handle_deliberation(self, statement: str, group_id: str, msg: dict):
        """
        Handle user deliberation statement.
        
        Args:
            statement: User's statement
            group_id: Group ID
            msg: Full message object
        """
        orchestrator = self.active_sessions.get(group_id)
        
        if not orchestrator:
            return
        
        # Only process during deliberation
        if orchestrator.state_machine.current_state != ExperienceState.JURY_DELIBERATION:
            return
        
        # Process statement
        result = await orchestrator.submit_deliberation_statement(statement)
        
        if result["success"]:
            # Send AI juror responses
            for turn in result["turns"][1:]:  # Skip user turn
                juror_statement = turn["statement"]
                
                await self.client.send_group_message(
                    group_id,
                    f"👤 AI Juror: {juror_statement}"
                )
                await asyncio.sleep(1)
            
            # Check if deliberation ended
            if result.get("deliberation_ended"):
                await self.client.send_group_message(
                    group_id,
                    "⏰ Deliberation time is up!\n\nType: /vote guilty OR /vote not_guilty"
                )

    async def handle_vote(self, group_id: str, vote: Optional[str], sender_uid: Optional[str]):
        """
        Handle user vote.
        
        Args:
            group_id: Group ID
            vote: Vote value (guilty/not_guilty)
            sender_uid: User who voted
        """
        orchestrator = self.active_sessions.get(group_id)
        
        if not orchestrator:
            await self.client.send_group_message(
                group_id,
                "⚠️ No active trial. Use /start to begin."
            )
            return
        
        if not vote or vote not in ["guilty", "not_guilty"]:
            await self.client.send_group_message(
                group_id,
                "⚠️ Invalid vote. Use: /vote guilty OR /vote not_guilty"
            )
            return
        
        # Submit vote
        await self.client.send_group_message(group_id, "🗳️ Collecting votes from all jurors...")
        
        vote_result = await orchestrator.submit_vote(vote)
        
        if vote_result["success"]:
            await self.send_dual_reveal(group_id, vote_result["dual_reveal"])

    async def send_dual_reveal(self, group_id: str, dual_reveal: dict):
        """
        Send dual reveal in sequence.
        
        Args:
            group_id: Group ID
            dual_reveal: Dual reveal data
        """
        # 1. Verdict
        verdict = dual_reveal["verdict"]
        verdict_text = verdict["verdict"].replace("_", " ").upper()
        
        await self.client.send_group_message(
            group_id,
            f"⚖️ THE VERDICT\n\nThe jury finds the defendant: {verdict_text}\n\nVote: {verdict['guiltyCount']} guilty, {verdict['notGuiltyCount']} not guilty"
        )
        await asyncio.sleep(3)
        
        # 2. Ground truth
        truth = dual_reveal["groundTruth"]
        actual = truth["actualVerdict"].replace("_", " ").upper()
        
        await self.client.send_group_message(
            group_id,
            f"🔍 THE TRUTH\n\nActual verdict: {actual}\n\n{truth['explanation']}"
        )
        await asyncio.sleep(3)
        
        # 3. Reasoning assessment
        assessment = dual_reveal["reasoningAssessment"]
        category = assessment["category"].replace("_", " ").title()
        
        feedback_text = f"""📊 REASONING ASSESSMENT

Category: {category}
Evidence Score: {assessment['evidenceScore']:.2f}/1.0
Coherence Score: {assessment['coherenceScore']:.2f}/1.0

{assessment['feedback']}"""
        
        await self.client.send_group_message(group_id, feedback_text)
        await asyncio.sleep(3)
        
        # 4. Juror reveal
        juror_text = "🎭 AI JUROR IDENTITIES\n\n"
        
        for juror in dual_reveal["jurorReveal"]:
            if juror["type"] != "human":
                persona = juror.get("persona", "").replace("_", " ").title()
                vote_text = juror["vote"].replace("_", " ").title()
                
                juror_text += f"• {juror['jurorId']}: {persona or 'Juror'} - Voted {vote_text}\n"
        
        await self.client.send_group_message(group_id, juror_text)
        
        # Complete
        await self.client.send_group_message(
            group_id,
            "✅ Trial complete! Thank you for participating.\n\nType /start to begin a new trial."
        )
        
        # Clean up session
        if group_id in self.active_sessions:
            del self.active_sessions[group_id]

    async def show_evidence(self, group_id: str):
        """Show evidence board."""
        orchestrator = self.active_sessions.get(group_id)
        
        if not orchestrator:
            await self.client.send_group_message(
                group_id,
                "⚠️ No active trial."
            )
            return
        
        evidence_board = orchestrator.get_evidence_board()
        
        text = "📋 EVIDENCE BOARD\n\n"
        for item in evidence_board["timeline"]:
            text += f"• {item['title']} ({item['type']})\n  {item['timestamp']}\n\n"
        
        await self.client.send_group_message(group_id, text)

    async def show_status(self, group_id: str):
        """Show current trial status."""
        orchestrator = self.active_sessions.get(group_id)
        
        if not orchestrator:
            await self.client.send_group_message(
                group_id,
                "⚠️ No active trial. Use /start to begin."
            )
            return
        
        progress = orchestrator.get_progress()
        current = progress["currentStage"].replace("_", " ").title()
        
        text = f"📊 TRIAL STATUS\n\nCurrent Stage: {current}\nProgress: {progress['completedStages']}/{progress['totalStages']} stages"
        
        await self.client.send_group_message(group_id, text)

    async def show_help(self, uid: str, msg_type: int):
        """Show help message."""
        help_text = """🎭 VERITAS COURTROOM EXPERIENCE

Commands:
/start - Begin a new trial
/continue - Advance to next stage
/vote guilty - Vote guilty
/vote not_guilty - Vote not guilty
/evidence - View evidence board
/status - Check trial progress
/help - Show this help

How it works:
1. Start a trial in a group chat
2. AI agents play different courtroom roles
3. Watch the trial unfold through 8 stages
4. Deliberate with AI jurors
5. Cast your vote
6. See the dual reveal (verdict + truth + your reasoning)

The story adapts based on your participation!"""
        
        if msg_type == 1:  # Group
            await self.client.send_group_message(uid, help_text)
        else:  # DM
            await self.client.send_dm(uid, help_text)

    def stop(self):
        """Stop the bot service."""
        logger.info("Stopping VERITAS Luffa Bot service...")
        self.running = False


async def main():
    """Main entry point for Luffa Bot service."""
    service = LuffaBotService()
    
    try:
        await service.start()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
        service.stop()
    except Exception as e:
        logger.error(f"Service error: {e}")
        raise


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    asyncio.run(main())
