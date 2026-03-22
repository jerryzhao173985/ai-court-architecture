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
from metrics import get_metrics_collector

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
        self.cleanup_task: Optional[asyncio.Task] = None
        
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

        # Start session cleanup task (Task 27.1)
        self.cleanup_task = asyncio.create_task(self._session_cleanup_task())
        logger.info("Started session cleanup task (checks every 5 minutes)")

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
        parts = command.split()
        cmd = parts[0].lower()
        
        if cmd == "/start":
            # Parse optional case_id argument: /start [case_id]
            case_id = parts[1] if len(parts) > 1 else None
            await self.start_trial(group_id, sender_uid, case_id)
        
        elif cmd == "/continue":
            await self.continue_trial(group_id, sender_uid)
        
        elif cmd == "/vote":
            vote = command.split()[1] if len(command.split()) > 1 else None
            await self.handle_vote(group_id, sender_uid, vote)
        
        elif cmd == "/evidence":
            await self.show_evidence(group_id, sender_uid)
        
        elif cmd == "/status":
            await self.show_status(group_id, sender_uid)
        
        elif cmd == "/cases":
            await self.show_cases(group_id)
        
        elif cmd == "/help":
            await self.show_help(group_id)

        elif cmd == "/stop":
            await self.stop_trial(group_id, sender_uid)
        
        elif cmd == "/metrics":
            await self.show_metrics(group_id, sender_uid)
        
        elif cmd == "/sessions":
            await self.show_sessions(group_id, sender_uid)

        else:
            await self.multi_bot.send_as_agent(
                "clerk",
                group_id,
                "Unknown command. Type /help for available commands."
            )

    async def start_trial(self, group_id: str, sender_uid: str, case_id: Optional[str] = None):
        """Start a new trial.
        
        Args:
            group_id: Group ID
            sender_uid: User who initiated the trial
            case_id: Optional case ID to use. If not provided, randomly selects from available cases.
        """
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
        
        # Select case: resolve query, or randomly select
        from case_manager import CaseManager
        import random

        case_manager = CaseManager()

        if case_id is not None:
            # User provided a query — resolve it (number, partial, or full ID)
            result = case_manager.resolve_case_id(case_id)
            if result is None:
                await self.multi_bot.send_as_agent(
                    "clerk", group_id,
                    f"❌ No case matching \"{case_id}\". Type /cases to see available cases."
                )
                return
            case_id, _ = result
        else:
            # No query — random selection
            available_cases = case_manager.list_available_cases()
            if not available_cases:
                await self.multi_bot.send_as_agent(
                    "clerk", group_id,
                    "❌ No cases available."
                )
                return
            case_id, _ = random.choice(available_cases)
            logger.info(f"Randomly selected case: {case_id}")
        
        # Create new session
        session_id = self._create_session_id(sender_uid, group_id)
        orchestrator = ExperienceOrchestrator(
            session_id=session_id,
            user_id=sender_uid,
            case_id=case_id
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
        metadata = response.get("metadata", {})
        
        # Check for rate limit warning
        if metadata.get("rate_limit_warning"):
            await self.multi_bot.send_as_agent(
                "clerk",
                group_id,
                "⏳ The court needs a moment..."
            )
            await asyncio.sleep(1)
        
        # Check for timeout
        if metadata.get("timeout"):
            role_display = agent_role.replace("_", " ").title()
            await self.multi_bot.send_as_agent(
                "clerk",
                group_id,
                f"⚠️ {role_display} is composing their response..."
            )
            await asyncio.sleep(1)
        
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
            # Send AI juror responses with persona identity
            # Note: If juror bots configured, could send from those bots
            # For now, send from clerk bot
            for turn in result["turns"][1:]:  # Skip user's own turn
                juror_id = turn["jurorId"]
                juror_statement = turn["statement"]
                
                # Get juror display info (emoji and name)
                emoji, name = orchestrator.jury_orchestrator.get_juror_display_info(juror_id)
                
                # Extract juror number from juror_id (e.g., "juror_1" -> "1")
                juror_num = juror_id.replace("juror_", "")
                
                # Format: "{emoji} {name} (Juror {n}): {statement}"
                formatted_message = f"{emoji} {name} (Juror {juror_num}): {juror_statement}"
                
                await self.multi_bot.send_as_agent(
                    "clerk",
                    group_id,
                    formatted_message
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

                    juror_text += f"• **{juror['jurorId']}**: {persona or 'Juror'} — Voted {vote_text}\n"

                    # Show vote reasoning if available
                    key_statements = juror.get("keyStatements", [])
                    for stmt in key_statements:
                        if stmt.startswith("Vote reasoning:"):
                            juror_text += f"  _{stmt[len('Vote reasoning: '):]}_\n"

            await self.multi_bot.send_as_agent("clerk", group_id, juror_text)
            await asyncio.sleep(2)
            
            # 5. Case statistics (Task 26.4)
            orchestrator = self._get_user_orchestrator(sender_uid)
            if orchestrator:
                from metrics import get_metrics_collector
                
                metrics_collector = get_metrics_collector()
                case_stats = metrics_collector.get_case_verdict_stats(orchestrator.case_id)
                
                if case_stats["total"] > 0:
                    stats_text = f"""📊 **CASE STATISTICS**

{case_stats['total']} users have tried this case.
• {case_stats['guilty_pct']}% voted guilty
• {case_stats['not_guilty_pct']}% voted not guilty"""
                    
                    await self.multi_bot.send_as_agent("clerk", group_id, stats_text)
                    await asyncio.sleep(2)

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

    async def show_cases(self, group_id: str):
        """Show available cases with complexity levels."""
        from case_manager import CaseManager
        from complexity_analyzer import CaseComplexityAnalyzer
        
        case_manager = CaseManager()
        available_cases = case_manager.list_available_cases()
        
        if not available_cases:
            await self.multi_bot.send_as_agent(
                "clerk",
                group_id,
                "❌ No cases available."
            )
            return
        
        # Build case list with complexity
        cases_text = "📋 AVAILABLE CASES\n\n"
        
        for idx, (case_id, title) in enumerate(available_cases, 1):
            try:
                # Load case and analyze complexity
                case_content = case_manager.load_case(case_id)
                analyzer = CaseComplexityAnalyzer()
                complexity = analyzer.analyze_complexity(case_content)
                complexity_level = complexity.level.title()
                
                cases_text += f"{idx}. {title}\n"
                cases_text += f"   Case ID: {case_id}\n"
                cases_text += f"   Complexity: {complexity_level}\n\n"
            except Exception as e:
                logger.warning(f"Failed to load case {case_id}: {e}")
                cases_text += f"{idx}. {title}\n"
                cases_text += f"   Case ID: {case_id}\n\n"
        
        cases_text += "Type /start <number or name> to begin, or /start for random."
        
        await self.multi_bot.send_as_agent("clerk", group_id, cases_text)

    async def show_help(self, group_id: str):
        """Show help message."""
        help_text = """🎭 VERITAS COURTROOM EXPERIENCE

Commands:
• /start [1|name] - Begin trial (by number, name, or random)
• /cases - List all available cases
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

    async def show_metrics(self, group_id: str, sender_uid: str):
        """Show performance metrics (admin only)."""
        # Check if sender is admin
        if sender_uid not in self.config.admin_uids:
            await self.multi_bot.send_as_agent(
                "clerk",
                group_id,
                "⚠️ This command is only available to administrators."
            )
            return
        
        # Get metrics summary
        metrics_collector = get_metrics_collector()
        summary = metrics_collector.get_summary()
        
        # Format as readable text
        metrics_text = "📊 VERITAS PERFORMANCE METRICS\n\n"
        
        # Agent responses
        agent_overall = summary["agent_responses"]["overall"]
        metrics_text += f"**Agent Responses:**\n"
        metrics_text += f"• Total calls: {agent_overall['count']}\n"
        metrics_text += f"• Avg duration: {agent_overall.get('avg_duration_ms', 0):.0f}ms\n"
        metrics_text += f"• P95 duration: {agent_overall.get('p95_duration_ms', 0):.0f}ms\n"
        metrics_text += f"• Success rate: {agent_overall.get('success_rate', 0):.1%}\n"
        metrics_text += f"• Fallback rate: {agent_overall.get('fallback_rate', 0):.1%}\n\n"
        
        # By role
        if summary["agent_responses"]["by_role"]:
            metrics_text += "**By Role:**\n"
            for role, stats in summary["agent_responses"]["by_role"].items():
                metrics_text += f"• {role}: {stats['count']} calls, avg {stats.get('avg_duration_ms', 0):.0f}ms\n"
            metrics_text += "\n"
        
        # State transitions
        state_stats = summary["state_transitions"]
        metrics_text += f"**State Transitions:**\n"
        metrics_text += f"• Total: {state_stats['count']}\n"
        metrics_text += f"• Avg duration: {state_stats.get('avg_duration_ms', 0):.0f}ms\n"
        metrics_text += f"• P95 duration: {state_stats.get('p95_duration_ms', 0):.0f}ms\n"
        metrics_text += f"• Success rate: {state_stats.get('success_rate', 0):.1%}\n\n"
        
        # Reasoning evaluation
        reasoning_stats = summary["reasoning_evaluation"]
        metrics_text += f"**Reasoning Evaluations:**\n"
        metrics_text += f"• Total: {reasoning_stats['count']}\n"
        metrics_text += f"• Avg duration: {reasoning_stats.get('avg_duration_ms', 0):.0f}ms\n"
        metrics_text += f"• Success rate: {reasoning_stats.get('success_rate', 0):.1%}\n"
        if reasoning_stats.get("category_distribution"):
            metrics_text += f"• Categories: {reasoning_stats['category_distribution']}\n"
        metrics_text += "\n"
        
        # Sessions
        session_stats = summary["sessions"]
        metrics_text += f"**Sessions:**\n"
        metrics_text += f"• Total: {session_stats['total_sessions']}\n"
        metrics_text += f"• Completed: {session_stats['completed_sessions']}\n"
        metrics_text += f"• Completion rate: {session_stats.get('completion_rate', 0):.1%}\n"
        metrics_text += f"• Avg duration: {session_stats.get('avg_duration_ms', 0) / 1000:.1f}s\n"
        metrics_text += f"• Avg agent calls: {session_stats.get('avg_agent_calls', 0):.1f}\n"
        metrics_text += f"• Avg state transitions: {session_stats.get('avg_state_transitions', 0):.1f}\n"
        
        await self.multi_bot.send_as_agent("clerk", group_id, metrics_text)

    async def show_sessions(self, group_id: str, sender_uid: str):
        """Show active sessions (admin only)."""
        # Check if sender is admin
        if sender_uid not in self.config.admin_uids:
            await self.multi_bot.send_as_agent(
                "clerk",
                group_id,
                "⚠️ This command is only available to administrators."
            )
            return
        
        # Get active sessions
        if not self.active_sessions:
            await self.multi_bot.send_as_agent(
                "clerk",
                group_id,
                "📋 No active sessions."
            )
            return
        
        sessions_text = f"📋 ACTIVE SESSIONS ({len(self.active_sessions)})\n\n"
        
        for session_id, orchestrator in self.active_sessions.items():
            # Get session state and duration
            current_state = orchestrator.user_session.current_state
            start_time = orchestrator.user_session.start_time
            duration_seconds = (datetime.now() - start_time).total_seconds()
            duration_minutes = int(duration_seconds / 60)
            
            # Format session info
            sessions_text += f"**Session:** {session_id}\n"
            sessions_text += f"• State: {current_state}\n"
            sessions_text += f"• Duration: {duration_minutes} minutes\n"
            sessions_text += f"• Case: {orchestrator.user_session.case_id}\n\n"
        
        await self.multi_bot.send_as_agent("clerk", group_id, sessions_text)

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

    async def _session_cleanup_task(self):
        """
        Background task that checks for inactive sessions and cleans them up.
        
        Runs every 5 minutes and:
        - Sends warning at 30 min inactive via clerk bot
        - Cleans up at 60 min inactive with timeout message
        
        Task 27.1: Session timeout and auto-cleanup
        """
        logger.info("Session cleanup task started")
        
        try:
            while self.running:
                await asyncio.sleep(300)  # 5 minutes
                
                if not self.running:
                    break
                
                now = datetime.now()
                sessions_to_cleanup = []
                
                for session_id, orchestrator in list(self.active_sessions.items()):
                    if not orchestrator.user_session:
                        continue
                    
                    last_activity = orchestrator.user_session.last_activity_time
                    inactive_duration = (now - last_activity).total_seconds() / 60  # minutes
                    
                    # Get user_id and group_id for this session
                    user_id = orchestrator.user_session.user_id
                    
                    # Extract group_id from session_id (format: luffa_{group_id}_{uid}_{timestamp})
                    parts = session_id.split("_")
                    if len(parts) >= 3:
                        group_id = parts[1]
                    else:
                        logger.warning(f"Cannot parse group_id from session_id: {session_id}")
                        continue
                    
                    # Check for 60 min timeout (cleanup)
                    if inactive_duration >= 60:
                        logger.info(f"Session {session_id} inactive for {inactive_duration:.1f} min - timing out")
                        sessions_to_cleanup.append((user_id, group_id, session_id))
                    
                    # Check for 30 min warning
                    elif inactive_duration >= 30:
                        # Check if we've already sent a warning (use metadata to track)
                        # For simplicity, we'll send warning each time we check (every 5 min)
                        # In production, you might want to track "warning_sent" flag
                        logger.info(f"Session {session_id} inactive for {inactive_duration:.1f} min - sending warning")
                        try:
                            await self.multi_bot.send_as_agent(
                                "clerk",
                                group_id,
                                f"⚠️ Your trial has been inactive for {int(inactive_duration)} minutes. "
                                f"The session will timeout after 60 minutes of inactivity.\n\n"
                                f"Type /continue or /status to keep your session active."
                            )
                        except Exception as e:
                            logger.error(f"Failed to send warning for session {session_id}: {e}")
                
                # Cleanup timed-out sessions
                for user_id, group_id, session_id in sessions_to_cleanup:
                    try:
                        await self.multi_bot.send_as_agent(
                            "clerk",
                            group_id,
                            "⏰ Trial timed out due to inactivity."
                        )
                        await self._cleanup_user_session(user_id, group_id)
                        logger.info(f"Cleaned up inactive session {session_id}")
                    except Exception as e:
                        logger.error(f"Failed to cleanup session {session_id}: {e}")
        
        except asyncio.CancelledError:
            logger.info("Session cleanup task cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in session cleanup task: {e}")

    async def shutdown(self):
        """Gracefully shut down the service, cleaning up all active sessions."""
        logger.info("Shutting down Multi-Bot service...")
        self.running = False

        # Cancel cleanup task (Task 27.1)
        if self.cleanup_task and not self.cleanup_task.done():
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                logger.info("Session cleanup task cancelled")

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
