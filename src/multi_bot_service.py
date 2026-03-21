"""Multi-bot Luffa service for realistic courtroom group chat experience."""

import asyncio
import logging
from typing import Optional, Dict
from datetime import datetime

from multi_bot_client_sdk import MultiBotSDKClient as MultiBotClient
from orchestrator import ExperienceOrchestrator
from state_machine import ExperienceState
from config import load_config
from trial_orchestrator import AgentResponse

logger = logging.getLogger("veritas")


class MultiBotService:
    """
    Service that runs VERITAS with multiple Luffa bots in group chat.
    
    Each trial agent (Clerk, Prosecution, Defence, Fact Checker, Judge)
    is a separate bot, creating a realistic multi-participant courtroom.
    
    Architecture:
    - Bot 1 (Clerk): Orchestrates flow, procedural announcements
    - Bot 2 (Prosecution): Prosecution barrister arguments
    - Bot 3 (Defence): Defence barrister arguments
    - Bot 4 (Fact Checker): Intervenes on contradictions
    - Bot 5 (Judge): Summing up and legal instructions
    - Optional: Additional bots for AI jurors
    """

    def __init__(self):
        """Initialize multi-bot service."""
        self.config = load_config()
        self.multi_bot = MultiBotClient(self.config.luffa)
        
        # Session management
        self.uid_to_session: Dict[str, str] = {}
        self.active_sessions: Dict[str, ExperienceOrchestrator] = {}
        self.group_users: Dict[str, set] = {}
        
        self.running = False
        
        # Log configured bots
        configured_roles = self.multi_bot.get_configured_roles()
        logger.info(f"Configured bots: {', '.join(configured_roles)}")

    async def start(self):
        """Start the multi-bot service with polling loop."""
        if not self.config.luffa.bot_enabled:
            logger.error("Luffa Bot is disabled. Set LUFFA_BOT_ENABLED=true in .env")
            return

        # Check if we have at least the clerk bot
        if not self.multi_bot.has_bot_for_role("clerk"):
            logger.error("Clerk bot not configured. Set LUFFA_BOT_CLERK_UID and LUFFA_BOT_CLERK_SECRET")
            return

        logger.info("Starting VERITAS Multi-Bot service...")
        logger.info(f"API endpoint: {self.multi_bot.base_url}")
        logger.info(f"Configured roles: {self.multi_bot.get_configured_roles()}")

        # Verify bot authentication before starting
        logger.info("Verifying bot credentials...")
        auth_results = await self.multi_bot.verify_all_bots()

        failed_bots = [role for role, ok in auth_results.items() if not ok]
        passed_bots = [role for role, ok in auth_results.items() if ok]

        if failed_bots:
            logger.error(f"AUTH FAILED for: {', '.join(failed_bots)}")
            logger.error("Bot secrets may be expired. Regenerate at https://robot.luffa.im")
            if "clerk" in failed_bots:
                logger.error("Clerk bot auth failed — cannot start service without it.")
                return
            logger.warning(f"Continuing with working bots: {', '.join(passed_bots)}")
        else:
            logger.info(f"All {len(passed_bots)} bots authenticated successfully")

        self.running = True
        logger.info("Polling for messages every 1 second...")

        # Poll ALL bots — Luffa delivers group messages to each bot independently
        while self.running:
            try:
                for role in self.multi_bot.get_configured_roles():
                    messages = await self.multi_bot.poll_messages(role)
                    for msg in messages:
                        await self.handle_message(msg)

                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Error in polling loop: {e}")
                await asyncio.sleep(5)

    async def handle_message(self, msg: dict):
        """Handle incoming message."""
        text = msg.get("text", "").strip()
        group_id = msg.get("gid")  # Group ID
        sender_uid = msg.get("sender_uid") or msg.get("uid")  # Actual sender, not group ID
        msg_type = msg.get("type", 1)  # 1=Group

        if not text or not group_id:
            return

        # Ignore messages from our own bots (they appear in other bots' polls)
        if sender_uid in self.multi_bot.bot_uids:
            return
        
        # Handle commands
        if text.startswith("/"):
            await self.handle_command(text, group_id, sender_uid, msg_type)
        else:
            # Handle deliberation statements
            await self.handle_deliberation(text, group_id, sender_uid)

    async def handle_command(self, command: str, group_id: str, sender_uid: str, msg_type: int):
        """Handle bot commands."""
        cmd = command.lower().split()[0]
        
        if cmd == "/start":
            await self.start_trial(group_id, sender_uid)
        
        elif cmd == "/continue":
            await self.continue_trial(group_id, sender_uid)
        
        elif cmd == "/vote":
            vote = command.split()[1] if len(command.split()) > 1 else None
            await self.handle_vote(group_id, sender_uid, vote)
        
        elif cmd == "/evidence":
            await self.show_evidence(group_id, sender_uid)
        
        elif cmd == "/status":
            await self.show_status(group_id, sender_uid)
        
        elif cmd == "/help":
            await self.show_help(group_id)

        elif cmd == "/stop":
            await self.stop_trial(group_id, sender_uid)

        else:
            await self.multi_bot.send_as_agent(
                "clerk",
                group_id,
                "Unknown command. Type /help for available commands."
            )

    async def start_trial(self, group_id: str, sender_uid: str):
        """Start a new trial."""
        if not sender_uid:
            await self.multi_bot.send_as_agent(
                "clerk",
                group_id,
                "⚠️ Could not identify user."
            )
            return
        
        # Check if user already has active session
        existing = self._get_user_orchestrator(sender_uid)
        if existing:
            await self.multi_bot.send_as_agent(
                "clerk",
                group_id,
                "⚠️ You already have a trial in progress. Use /continue or /status."
            )
            return
        
        # Create new session
        session_id = self._create_session_id(sender_uid, group_id)
        orchestrator = ExperienceOrchestrator(
            session_id=session_id,
            user_id=sender_uid,
            case_id="blackthorn-hall-001"
        )
        
        # Initialize
        init_result = await orchestrator.initialize()

        if not init_result["success"]:
            # Clean up the uid mapping created by _create_session_id
            self.uid_to_session.pop(sender_uid, None)
            if group_id in self.group_users:
                self.group_users[group_id].discard(sender_uid)
            await self.multi_bot.send_as_agent(
                "clerk",
                group_id,
                f"❌ Failed to start trial: {init_result.get('error')}"
            )
            return

        self.active_sessions[session_id] = orchestrator

        # Send greeting from Clerk
        greeting = init_result["greeting"]["content"]
        await self.multi_bot.send_as_agent("clerk", group_id, greeting)

        # Start hook scene
        start_result = await orchestrator.start_experience()

        if start_result["success"]:
            hook_content = start_result["hook_content"]["content"]
            await self.multi_bot.send_as_agent(
                "clerk",
                group_id,
                f"🎭 THE TRIAL BEGINS\n\n{hook_content}",
                buttons=[{"name": "Continue", "selector": "/continue", "isHidden": "0"}]
            )
        else:
            await self.multi_bot.send_as_agent(
                "clerk",
                group_id,
                f"❌ Failed to start trial: {start_result.get('error')}\n\nType /start to try again."
            )
            await self._cleanup_user_session(sender_uid, group_id)

    async def continue_trial(self, group_id: str, sender_uid: str):
        """Continue to next trial stage."""
        orchestrator = self._get_user_orchestrator(sender_uid)
        
        if not orchestrator:
            await self.multi_bot.send_as_agent(
                "clerk",
                group_id,
                "⚠️ No active trial. Use /start to begin."
            )
            return
        
        current_state = orchestrator.state_machine.current_state
        
        # Handle deliberation — guide user clearly
        if current_state == ExperienceState.JURY_DELIBERATION:
            await self.multi_bot.send_as_agent(
                "clerk",
                group_id,
                "⚖️ DELIBERATION IN PROGRESS\n\n"
                "The jury is deliberating. Share your thoughts on the evidence — the AI jurors will respond.\n\n"
                "Type /evidence to review the evidence board.\n"
                "When ready, type /vote guilty OR /vote not_guilty",
                buttons=[
                    {"name": "View Evidence", "selector": "/evidence", "isHidden": "0"},
                    {"name": "Vote Guilty", "selector": "/vote guilty", "isHidden": "1"},
                    {"name": "Vote Not Guilty", "selector": "/vote not_guilty", "isHidden": "1"}
                ],
                dismiss_type="dismiss"
            )
            return

        # Handle voting
        if current_state == ExperienceState.ANONYMOUS_VOTE:
            await self.multi_bot.send_as_agent(
                "clerk",
                group_id,
                "⚖️ TIME TO VOTE\n\nType: /vote guilty OR /vote not_guilty",
                buttons=[
                    {"name": "Vote Guilty", "selector": "/vote guilty", "isHidden": "1"},
                    {"name": "Vote Not Guilty", "selector": "/vote not_guilty", "isHidden": "1"}
                ],
                dismiss_type="dismiss"
            )
            return
        
        # Advance stage
        result = await orchestrator.advance_trial_stage()
        
        if not result["success"]:
            await self.multi_bot.send_as_agent(
                "clerk",
                group_id,
                f"❌ Error: {result.get('error')}"
            )
            return
        
        # Send stage announcement from Clerk
        announcement = result["announcement"]["content"]
        await self.multi_bot.send_as_agent("clerk", group_id, f"📢 {announcement}")
        await asyncio.sleep(1)
        
        # Send agent responses from their respective bots
        if "agent_responses" in result:
            for response in result["agent_responses"]:
                await self.send_agent_response(group_id, response)
        
        # Handle deliberation start
        if "deliberation_prompt" in result:
            prompt = result["deliberation_prompt"]
            await self.multi_bot.send_as_agent(
                "clerk",
                group_id,
                f"🗣️ JURY DELIBERATION\n\n{prompt}\n\n"
                f"You are now in the jury chamber with 7 AI jurors.\n"
                f"Share your thoughts on the case — the AI jurors will respond.\n\n"
                f"Type /evidence to review the evidence board.\n"
                f"When ready: /vote guilty OR /vote not_guilty",
                buttons=[
                    {"name": "View Evidence", "selector": "/evidence", "isHidden": "0"},
                    {"name": "Vote Guilty", "selector": "/vote guilty", "isHidden": "1"},
                    {"name": "Vote Not Guilty", "selector": "/vote not_guilty", "isHidden": "1"}
                ]
            )
            return

        # Prompt to continue
        next_state = orchestrator.state_machine.get_next_state()
        if next_state:
            await self.multi_bot.send_as_agent(
                "clerk",
                group_id,
                "Type /continue to proceed.",
                buttons=[{"name": "Continue", "selector": "/continue", "isHidden": "0"}]
            )

    async def send_agent_response(self, group_id: str, response: dict):
        """
        Send agent response from appropriate bot.
        
        Args:
            group_id: Group ID
            response: Agent response dict with agentRole and content
        """
        agent_role = response["agentRole"]
        content = response["content"]
        
        # Map agent role to bot role
        role_mapping = {
            "clerk": "clerk",
            "prosecution": "prosecution",
            "defence": "defence",
            "fact_checker": "fact_checker",
            "judge": "judge"
        }
        
        bot_role = role_mapping.get(agent_role, "clerk")
        
        # Add role emoji
        role_emoji = {
            "clerk": "📋",
            "prosecution": "👔",
            "defence": "🛡️",
            "fact_checker": "🔍",
            "judge": "⚖️"
        }
        
        emoji = role_emoji.get(agent_role, "🎭")
        formatted_message = f"{emoji} **{agent_role.upper()}**\n\n{content}"
        
        # Send from appropriate bot
        success = await self.multi_bot.send_as_agent(bot_role, group_id, formatted_message)
        
        if success:
            await asyncio.sleep(2)  # Pace messages for readability

    async def handle_deliberation(self, statement: str, group_id: str, sender_uid: str):
        """Handle user deliberation statement."""
        orchestrator = self._get_user_orchestrator(sender_uid)
        
        if not orchestrator:
            return
        
        if orchestrator.state_machine.current_state != ExperienceState.JURY_DELIBERATION:
            return
        
        # Process statement
        result = await orchestrator.submit_deliberation_statement(statement)
        
        if result["success"]:
            # Send AI juror responses
            # Note: If juror bots configured, could send from those bots
            # For now, send from clerk bot
            for turn in result["turns"][1:]:
                juror_statement = turn["statement"]
                
                await self.multi_bot.send_as_agent(
                    "clerk",
                    group_id,
                    f"👤 AI Juror: {juror_statement}"
                )
                await asyncio.sleep(1)
            
            # Check if deliberation ended
            if result.get("deliberation_ended"):
                await self.multi_bot.send_as_agent(
                    "clerk",
                    group_id,
                    "⏰ Deliberation time is up!\n\nType: /vote guilty OR /vote not_guilty",
                    buttons=[
                        {"name": "Vote Guilty", "selector": "/vote guilty", "isHidden": "1"},
                        {"name": "Vote Not Guilty", "selector": "/vote not_guilty", "isHidden": "1"}
                    ],
                    dismiss_type="dismiss"
                )

    async def handle_vote(self, group_id: str, sender_uid: str, vote: Optional[str]):
        """Handle user vote."""
        orchestrator = self._get_user_orchestrator(sender_uid)
        
        if not orchestrator:
            await self.multi_bot.send_as_agent(
                "clerk",
                group_id,
                "⚠️ No active trial. Use /start to begin."
            )
            return
        
        if not vote or vote not in ["guilty", "not_guilty"]:
            await self.multi_bot.send_as_agent(
                "clerk",
                group_id,
                "⚠️ Invalid vote. Use: /vote guilty OR /vote not_guilty"
            )
            return
        
        # Submit vote
        await self.multi_bot.send_as_agent("clerk", group_id, "🗳️ Collecting votes from all jurors...")
        
        vote_result = await orchestrator.submit_vote(vote)
        
        if vote_result["success"]:
            if "dual_reveal" in vote_result:
                await self.send_dual_reveal(group_id, vote_result["dual_reveal"], sender_uid)
            else:
                # Fallback when reasoning evaluation fails
                verdict_data = vote_result.get("verdict", {})
                v = verdict_data.get("verdict", "unknown").replace("_", " ").upper()
                await self.multi_bot.send_as_agent(
                    "clerk", group_id,
                    f"⚖️ **THE VERDICT**\n\nThe jury finds the defendant: **{v}**\n\n"
                    f"(Detailed reasoning assessment is temporarily unavailable.)\n\n"
                    f"Type /start to begin a new trial.",
                    buttons=[{"name": "Start New Trial", "selector": "/start", "isHidden": "0"}]
                )
                await self._cleanup_user_session(sender_uid, group_id)
        else:
            await self.multi_bot.send_as_agent(
                "clerk", group_id,
                f"❌ Vote processing failed: {vote_result.get('error', 'Unknown error')}\n\n"
                f"Type /vote guilty or /vote not_guilty to try again."
            )

    async def send_dual_reveal(self, group_id: str, dual_reveal: dict, sender_uid: str):
        """Send dual reveal sequence from appropriate bots."""
        try:
            # 1. Verdict announcement from Clerk
            verdict = dual_reveal["verdict"]
            verdict_text = verdict["verdict"].replace("_", " ").upper()

            await self.multi_bot.send_as_agent(
                "clerk",
                group_id,
                f"⚖️ **THE VERDICT**\n\nThe jury finds the defendant: **{verdict_text}**\n\n📊 Vote: {verdict['guiltyCount']} guilty, {verdict['notGuiltyCount']} not guilty"
            )
            await asyncio.sleep(3)

            # 2. Ground truth from Judge
            truth = dual_reveal["groundTruth"]
            actual = truth["actualVerdict"].replace("_", " ").upper()

            await self.multi_bot.send_as_agent(
                "judge",
                group_id,
                f"🔍 **THE TRUTH**\n\nActual verdict: **{actual}**\n\n{truth['explanation']}"
            )
            await asyncio.sleep(3)

            # 3. Reasoning assessment from Clerk
            assessment = dual_reveal["reasoningAssessment"]
            category = assessment["category"].replace("_", " ").title()

            feedback_text = f"""📊 **REASONING ASSESSMENT**

**Category**: {category}
**Evidence Score**: {assessment['evidenceScore']:.2f}/1.0
**Coherence Score**: {assessment['coherenceScore']:.2f}/1.0

{assessment['feedback']}"""

            await self.multi_bot.send_as_agent("clerk", group_id, feedback_text)
            await asyncio.sleep(3)

            # 4. Juror reveal from Clerk
            juror_text = "🎭 **AI JUROR IDENTITIES**\n\n"

            for juror in dual_reveal["jurorReveal"]:
                if juror["type"] != "human":
                    persona = (juror.get("persona") or "").replace("_", " ").title()
                    vote_text = juror["vote"].replace("_", " ").title()

                    juror_text += f"• **{juror['jurorId']}**: {persona or 'Juror'} - Voted {vote_text}\n"

            await self.multi_bot.send_as_agent("clerk", group_id, juror_text)

            # Complete
            await self.multi_bot.send_as_agent(
                "clerk",
                group_id,
                "✅ **Trial complete!** Thank you for participating.\n\nType /start to begin a new trial.",
                buttons=[{"name": "Start New Trial", "selector": "/start", "isHidden": "0"}]
            )
        except Exception as e:
            logger.error(f"Error during dual reveal for {sender_uid}: {e}")
            try:
                await self.multi_bot.send_as_agent(
                    "clerk", group_id,
                    "⚠️ An error occurred during the reveal. The trial is now complete.\n\nType /start to begin a new trial."
                )
            except Exception:
                pass  # Best effort — don't let notification failure prevent cleanup
        finally:
            await self._cleanup_user_session(sender_uid, group_id)

    async def show_evidence(self, group_id: str, sender_uid: str):
        """Show evidence board with full item details."""
        orchestrator = self._get_user_orchestrator(sender_uid)

        if not orchestrator:
            await self.multi_bot.send_as_agent(
                "clerk",
                group_id,
                "⚠️ No active trial."
            )
            return

        evidence_board = orchestrator.get_evidence_board()

        if "error" in evidence_board:
            await self.multi_bot.send_as_agent("clerk", group_id, "⚠️ Evidence board not available yet.")
            return

        # Use "items" (full EvidenceItem data), not "timeline" (which lacks description)
        items = evidence_board.get("items", [])

        if not items:
            await self.multi_bot.send_as_agent("clerk", group_id, "📋 No evidence items available.")
            return

        # Split by side — mirrors how evidence is presented in a real courtroom
        prosecution_items = [i for i in items if i.get("presentedBy") == "prosecution"]
        defence_items = [i for i in items if i.get("presentedBy") == "defence"]

        type_label = {"physical": "Physical", "testimonial": "Testimony", "documentary": "Document"}

        # Send prosecution evidence
        if prosecution_items:
            text = "📋 EVIDENCE BOARD\n\n👔 PROSECUTION EVIDENCE\n"
            for item in prosecution_items:
                text += f"\n• {item['title']} ({type_label.get(item.get('type', ''), item.get('type', ''))})\n"
                text += f"  {item.get('description', '')}\n"
                text += f"  Significance: {item.get('significance', '')}\n"
            await self.multi_bot.send_as_agent("clerk", group_id, text)
            await asyncio.sleep(1)

        # Send defence evidence
        if defence_items:
            text = "🛡️ DEFENCE EVIDENCE\n"
            for item in defence_items:
                text += f"\n• {item['title']} ({type_label.get(item.get('type', ''), item.get('type', ''))})\n"
                text += f"  {item.get('description', '')}\n"
                text += f"  Significance: {item.get('significance', '')}\n"
            await self.multi_bot.send_as_agent("clerk", group_id, text)

    async def show_status(self, group_id: str, sender_uid: str):
        """Show trial status."""
        orchestrator = self._get_user_orchestrator(sender_uid)

        if not orchestrator:
            await self.multi_bot.send_as_agent(
                "clerk",
                group_id,
                "⚠️ No active trial. Use /start to begin."
            )
            return

        progress = orchestrator.get_progress()

        if "error" in progress:
            await self.multi_bot.send_as_agent("clerk", group_id, "⚠️ Status unavailable.")
            return

        # Keys from trial_stages.py: current_stage, current_stage_name, completed_count, total_stages, progress_percentage
        stage_name = progress.get("current_stage_name", progress.get("current_stage", "Unknown"))
        completed = progress.get("completed_count", 0)
        total = progress.get("total_stages", 13)
        pct = progress.get("progress_percentage", 0)

        text = f"📊 TRIAL STATUS\n\nCurrent Stage: {stage_name}\nProgress: {completed}/{total} stages ({pct}%)"

        await self.multi_bot.send_as_agent("clerk", group_id, text)

    async def stop_trial(self, group_id: str, sender_uid: str):
        """Stop and clear current trial."""
        orchestrator = self._get_user_orchestrator(sender_uid)

        if not orchestrator:
            await self.multi_bot.send_as_agent(
                "clerk",
                group_id,
                "No active trial to stop."
            )
            return

        await self._cleanup_user_session(sender_uid, group_id)
        await self.multi_bot.send_as_agent(
            "clerk",
            group_id,
            "⚖️ Trial stopped and session cleared.\n\nType /start to begin a new trial."
        )

    async def show_help(self, group_id: str):
        """Show help message."""
        help_text = """🎭 VERITAS COURTROOM EXPERIENCE

Commands:
• /start - Begin a new trial
• /stop - Stop current trial
• /continue - Advance to next stage
• /vote guilty - Vote guilty
• /vote not_guilty - Vote not guilty
• /evidence - View evidence board
• /status - Check trial progress
• /help - Show this help

**How it works:**
1. Start a trial in this group chat
2. AI agents (Prosecution, Defence, Judge) play courtroom roles
3. Watch the trial unfold through 8 stages
4. Deliberate with AI jurors
5. Cast your vote
6. See the dual reveal (verdict + truth + reasoning assessment)

Each agent is a separate bot for a realistic courtroom experience!"""
        
        await self.multi_bot.send_as_agent("clerk", group_id, help_text)

    def _create_session_id(self, uid: str, group_id: str) -> str:
        """Create session ID for user."""
        session_id = f"luffa_{group_id}_{uid}_{int(datetime.now().timestamp())}"
        self.uid_to_session[uid] = session_id
        
        if group_id not in self.group_users:
            self.group_users[group_id] = set()
        self.group_users[group_id].add(uid)
        
        return session_id

    def _get_user_orchestrator(self, uid: str) -> Optional[ExperienceOrchestrator]:
        """Get orchestrator for user."""
        session_id = self.uid_to_session.get(uid)
        if session_id:
            return self.active_sessions.get(session_id)
        return None

    async def _cleanup_user_session(self, uid: str, group_id: str):
        """Clean up user session."""
        session_id = self.uid_to_session.get(uid)
        
        if session_id:
            # Cleanup orchestrator if exists
            if session_id in self.active_sessions:
                orchestrator = self.active_sessions[session_id]
                try:
                    # Determine if session was completed — bot services end at DUAL_REVEAL
                    # (complete_experience() which transitions to COMPLETED is only used by API/demo)
                    completed = (orchestrator.user_session and
                               orchestrator.user_session.current_state in (
                                   ExperienceState.DUAL_REVEAL,
                                   ExperienceState.COMPLETED
                               ))
                    await orchestrator.cleanup(completed=completed)
                except Exception as e:
                    logger.error(f"Failed to cleanup orchestrator for session {session_id}: {e}")
                
                del self.active_sessions[session_id]
            del self.uid_to_session[uid]
        
        if group_id in self.group_users:
            self.group_users[group_id].discard(uid)
            if not self.group_users[group_id]:
                del self.group_users[group_id]

    async def shutdown(self):
        """Gracefully shut down the service, cleaning up all active sessions."""
        logger.info("Shutting down Multi-Bot service...")
        self.running = False

        # Cleanup all active sessions
        for session_id, orchestrator in list(self.active_sessions.items()):
            try:
                await orchestrator.cleanup(completed=False)
            except Exception as e:
                logger.error(f"Failed to cleanup session {session_id} during shutdown: {e}")

        self.active_sessions.clear()
        self.uid_to_session.clear()
        self.group_users.clear()

    def stop(self):
        """Stop the service (sets running flag — use shutdown() for graceful cleanup)."""
        self.running = False


async def main():
    """Main entry point."""
    service = MultiBotService()

    try:
        await service.start()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Service error: {e}")
        raise
    finally:
        await service.shutdown()
        await service.multi_bot.close()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    asyncio.run(main())
