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
    
    Session Management (Task 22.4):
    - Maps Luffa user IDs (uid) to session IDs
    - Supports multiple concurrent users in the same group
    - Handles session recovery for disconnected users
    """

    def __init__(self):
        """Initialize Luffa Bot service."""
        self.config = load_config()
        self.client = LuffaBotAPIClient(self.config.luffa)
        
        # Session management (Task 22.4)
        # Map: uid -> session_id
        self.uid_to_session: Dict[str, str] = {}
        # Map: session_id -> ExperienceOrchestrator
        self.active_sessions: Dict[str, ExperienceOrchestrator] = {}
        # Map: group_id -> set of uids (users in that group)
        self.group_users: Dict[str, set] = {}
        
        self.running = False
        self.cleanup_task: Optional[asyncio.Task] = None

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
            
            # Start session cleanup task (Task 27.1)
            self.cleanup_task = asyncio.create_task(self._session_cleanup_task())
            logger.info("Started session cleanup task (checks every 5 minutes)")
            
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
        parts = command.split()
        cmd = parts[0].lower()
        sender_uid = msg.get("sender_uid") or uid  # Get actual user ID
        
        if cmd == "/start":
            # Parse optional case_id argument: /start [case_id]
            case_id = parts[1] if len(parts) > 1 else None
            await self.start_trial(uid, msg_type, sender_uid, case_id)
        
        elif cmd == "/continue":
            await self.continue_trial(uid, sender_uid)
        
        elif cmd == "/vote":
            vote = command.split()[1] if len(command.split()) > 1 else None
            await self.handle_vote(uid, vote, sender_uid)
        
        elif cmd == "/evidence":
            await self.show_evidence(uid, sender_uid)
        
        elif cmd == "/status":
            await self.show_status(uid, sender_uid)
        
        elif cmd == "/cases":
            await self.show_cases(uid, msg_type)
        
        elif cmd == "/help":
            await self.show_help(uid, msg_type)
        
        else:
            if msg_type == 1:  # Group
                await self.client.send_group_message(uid, "Unknown command. Type /help for available commands.")
            else:  # DM
                await self.client.send_dm(uid, "Unknown command. Type /help for available commands.")

    async def start_trial(self, group_id: str, msg_type: int, sender_uid: str, case_id: Optional[str] = None):
        """
        Start a new trial for a user in a group.

        Supports multiple concurrent users in the same group (Task 22.4).

        Args:
            group_id: Group ID
            msg_type: Message type
            sender_uid: User who initiated the trial
            case_id: Optional case ID. If None, randomly selects from available cases.
        """
        if msg_type != 1:  # Must be group
            await self.client.send_dm(group_id, "Trials can only be started in group chats.")
            return
        
        if not sender_uid:
            await self.client.send_group_message(group_id, "⚠️ Could not identify user. Please try again.")
            return
        
        # Check if user already has an active session
        existing_orchestrator = self._get_user_orchestrator(sender_uid)
        if existing_orchestrator:
            await self.client.send_group_message(
                group_id,
                f"⚠️ You already have a trial in progress. Use /continue to proceed or /status to check progress."
            )
            return
        
        # Try to restore session for disconnected user
        orchestrator = await self._get_or_restore_orchestrator(sender_uid, group_id)
        
        if orchestrator:
            # Session restored
            await self.client.send_group_message(
                group_id,
                f"✅ Welcome back! Your session has been restored.\n\nUse /status to see your progress, or /continue to proceed."
            )
            return
        
        # Select case: use provided case_id or randomly select
        if case_id is None:
            from case_manager import CaseManager
            import random

            case_manager = CaseManager()
            available_cases = case_manager.list_available_cases()

            if not available_cases:
                await self.client.send_group_message(group_id, "❌ No cases available.")
                return

            case_id, _ = random.choice(available_cases)
            logger.info(f"Randomly selected case: {case_id}")

        # Create new session
        session_id = self._get_or_create_session_id(sender_uid, group_id)
        orchestrator = ExperienceOrchestrator(
            session_id=session_id,
            user_id=sender_uid,
            case_id=case_id  # Already selected above (provided or random)
        )
        
        # Initialize
        init_result = await orchestrator.initialize()
        
        if not init_result["success"]:
            # Clean up orphaned session mapping
            self.uid_to_session.pop(sender_uid, None)
            if group_id in self.group_users:
                self.group_users[group_id].discard(sender_uid)
            await self.client.send_group_message(
                group_id,
                f"❌ Failed to start trial: {init_result.get('error')}"
            )
            return
        
        self.active_sessions[session_id] = orchestrator
        
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

    async def continue_trial(self, group_id: str, sender_uid: str):
        """
        Continue to next trial stage for a specific user.
        
        Args:
            group_id: Group ID
            sender_uid: User who sent the command
        """
        if not sender_uid:
            await self.client.send_group_message(group_id, "⚠️ Could not identify user.")
            return
        
        orchestrator = self._get_user_orchestrator(sender_uid)
        
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
                metadata = response.get("metadata", {})

                # Check for rate limit warning (Task 27.4)
                if metadata.get("rate_limit_warning"):
                    await self.client.send_group_message(group_id, "⏳ The court needs a moment...")
                    await asyncio.sleep(1)

                # Check for timeout (Task 27.4)
                if metadata.get("timeout"):
                    role_display = response["agentRole"].replace("_", " ").title()
                    await self.client.send_group_message(group_id, f"⚠️ {role_display} is composing their response...")
                    await asyncio.sleep(1)

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
        sender_uid = msg.get("sender_uid") or msg.get("uid")
        if not sender_uid:
            return
        
        orchestrator = self._get_user_orchestrator(sender_uid)
        
        if not orchestrator:
            return
        
        # Only process during deliberation
        if orchestrator.state_machine.current_state != ExperienceState.JURY_DELIBERATION:
            return
        
        # Process statement
        result = await orchestrator.submit_deliberation_statement(statement)
        
        if result["success"]:
            # Send AI juror responses with persona identity
            for turn in result["turns"][1:]:  # Skip user turn
                juror_id = turn["jurorId"]
                juror_statement = turn["statement"]
                
                # Get juror display info (emoji and name)
                emoji, name = orchestrator.jury_orchestrator.get_juror_display_info(juror_id)
                
                # Extract juror number from juror_id (e.g., "juror_1" -> "1")
                juror_num = juror_id.replace("juror_", "")
                
                # Format: "{emoji} {name} (Juror {n}): {statement}"
                formatted_message = f"{emoji} {name} (Juror {juror_num}): {juror_statement}"
                
                await self.client.send_group_message(
                    group_id,
                    formatted_message
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
        if not sender_uid:
            await self.client.send_group_message(group_id, "⚠️ Could not identify user.")
            return
        
        orchestrator = self._get_user_orchestrator(sender_uid)
        
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
            if "dual_reveal" in vote_result:
                await self.send_dual_reveal(group_id, vote_result["dual_reveal"], sender_uid)
            else:
                # Fallback when reasoning evaluation fails
                verdict_data = vote_result.get("verdict", {})
                v = verdict_data.get("verdict", "unknown").replace("_", " ").upper()
                await self.client.send_group_message(
                    group_id,
                    f"⚖️ THE VERDICT\n\nThe jury finds the defendant: {v}\n\n"
                    f"(Detailed reasoning assessment is temporarily unavailable.)\n\n"
                    f"Type /start to begin a new trial."
                )
                await self._cleanup_user_session(sender_uid, group_id)
        else:
            await self.client.send_group_message(
                group_id,
                f"❌ Vote processing failed: {vote_result.get('error', 'Unknown error')}\n\n"
                f"Type /vote guilty or /vote not_guilty to try again."
            )

    async def send_dual_reveal(self, group_id: str, dual_reveal: dict, sender_uid: str):
        """
        Send dual reveal in sequence.

        Args:
            group_id: Group ID
            dual_reveal: Dual reveal data
            sender_uid: User who completed the trial
        """
        try:
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
                    persona = (juror.get("persona") or "").replace("_", " ").title()
                    vote_text = juror["vote"].replace("_", " ").title()

                    juror_text += f"• {juror['jurorId']}: {persona or 'Juror'} — Voted {vote_text}\n"

                    # Show vote reasoning if available
                    key_statements = juror.get("keyStatements", [])
                    for stmt in key_statements:
                        if stmt.startswith("Vote reasoning:"):
                            juror_text += f"  {stmt[len('Vote reasoning: '):]}\n"

            await self.client.send_group_message(group_id, juror_text)
            await asyncio.sleep(2)
            
            # 5. Case statistics (Task 26.4)
            orchestrator = self._get_user_orchestrator(sender_uid)
            if orchestrator:
                from metrics import get_metrics_collector
                
                metrics_collector = get_metrics_collector()
                case_stats = metrics_collector.get_case_verdict_stats(orchestrator.case_id)
                
                if case_stats["total"] > 0:
                    stats_text = f"""📊 CASE STATISTICS

{case_stats['total']} users have tried this case.
• {case_stats['guilty_pct']}% voted guilty
• {case_stats['not_guilty_pct']}% voted not guilty"""
                    
                    await self.client.send_group_message(group_id, stats_text)
                    await asyncio.sleep(2)

            # Complete
            await self.client.send_group_message(
                group_id,
                "✅ Trial complete! Thank you for participating.\n\nType /start to begin a new trial."
            )
        except Exception as e:
            logger.error(f"Error during dual reveal for {sender_uid}: {e}")
            try:
                await self.client.send_group_message(
                    group_id,
                    "⚠️ An error occurred during the reveal. The trial is now complete.\n\nType /start to begin a new trial."
                )
            except Exception:
                pass
        finally:
            await self._cleanup_user_session(sender_uid, group_id)

    async def show_evidence(self, group_id: str, sender_uid: str):
        """
        Show evidence board.
        
        Args:
            group_id: Group ID
            sender_uid: User requesting evidence
        """
        if not sender_uid:
            await self.client.send_group_message(group_id, "⚠️ Could not identify user.")
            return
        
        orchestrator = self._get_user_orchestrator(sender_uid)
        
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

    async def show_status(self, group_id: str, sender_uid: str):
        """
        Show current trial status.
        
        Args:
            group_id: Group ID
            sender_uid: User requesting status
        """
        if not sender_uid:
            await self.client.send_group_message(group_id, "⚠️ Could not identify user.")
            return
        
        orchestrator = self._get_user_orchestrator(sender_uid)
        
        if not orchestrator:
            await self.client.send_group_message(
                group_id,
                "⚠️ No active trial. Use /start to begin."
            )
            return
        
        progress = orchestrator.get_progress()
        current = progress.get("current_stage_name", progress.get("current_stage", "Unknown"))
        
        text = f"📊 TRIAL STATUS\n\nCurrent Stage: {current}\nProgress: {progress.get('completed_count', 0)}/{progress.get('total_stages', 13)} stages"
        
        await self.client.send_group_message(group_id, text)

    async def show_cases(self, uid: str, msg_type: int):
        """Show available cases with complexity levels."""
        from case_manager import CaseManager
        from complexity_analyzer import CaseComplexityAnalyzer
        
        case_manager = CaseManager()
        available_cases = case_manager.list_available_cases()
        
        if not available_cases:
            message = "❌ No cases available."
            if msg_type == 1:
                await self.client.send_group_message(uid, message)
            else:
                await self.client.send_dm(uid, message)
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
        
        cases_text += "Type /start <case-id> to begin a specific case,\nor /start to randomly select one."
        
        if msg_type == 1:  # Group
            await self.client.send_group_message(uid, cases_text)
        else:  # DM
            await self.client.send_dm(uid, cases_text)

    async def show_help(self, uid: str, msg_type: int):
        """Show help message."""
        help_text = """🎭 VERITAS COURTROOM EXPERIENCE

Commands:
/start [case-id] - Begin a new trial (random case if no ID provided)
/cases - List all available cases
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

    async def shutdown(self):
        """Gracefully shut down the service, cleaning up all active sessions."""
        logger.info("Shutting down VERITAS Luffa Bot service...")
        self.running = False

        # Cancel cleanup task (Task 27.1)
        if self.cleanup_task and not self.cleanup_task.done():
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                logger.info("Session cleanup task cancelled")

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

    # ========================================================================
    # Session Management (Task 22.4)
    # ========================================================================

    def _get_or_create_session_id(self, uid: str, group_id: str) -> str:
        """
        Get existing session ID for user or create a new one.
        
        Maps Luffa user ID to session ID, supporting multiple concurrent
        users in the same group.
        
        Args:
            uid: Luffa user ID
            group_id: Group ID (for session naming)
            
        Returns:
            Session ID for this user
        """
        # Check if user already has a session
        if uid in self.uid_to_session:
            return self.uid_to_session[uid]
        
        # Create new session ID
        session_id = f"luffa_{group_id}_{uid}_{int(datetime.now().timestamp())}"
        self.uid_to_session[uid] = session_id
        
        # Track user in group
        if group_id not in self.group_users:
            self.group_users[group_id] = set()
        self.group_users[group_id].add(uid)
        
        return session_id

    async def _get_or_restore_orchestrator(
        self, 
        uid: str, 
        group_id: str
    ) -> Optional[ExperienceOrchestrator]:
        """
        Get existing orchestrator or restore from persistent storage.
        
        Handles session recovery for disconnected users (Requirement 2.4).
        
        Args:
            uid: Luffa user ID
            group_id: Group ID

        Returns:
            ExperienceOrchestrator if found/restored, None if needs creation
        """
        session_id = self._get_or_create_session_id(uid, group_id)
        
        # Check if already in memory
        if session_id in self.active_sessions:
            return self.active_sessions[session_id]
        
        # Try to restore from persistent storage
        from session import SessionStore
        session_store = SessionStore()
        
        # Look for any session for this user (may have different timestamp)
        # Search by uid pattern
        for stored_session_path in session_store.storage_dir.glob(f"luffa_{group_id}_{uid}_*.json"):
            try:
                stored_session_id = stored_session_path.stem
                user_session = session_store.restore_progress(stored_session_id)
                
                if user_session and not user_session.is_expired(retention_hours=24):
                    # Restore orchestrator
                    logger.info(f"Restoring session {stored_session_id} for user {uid}")
                    
                    orchestrator = ExperienceOrchestrator(
                        session_id=stored_session_id,
                        user_id=uid,
                        case_id=user_session.case_id
                    )
                    
                    # Initialize orchestrator
                    init_result = await orchestrator.initialize()
                    if not init_result["success"]:
                        logger.warning(f"Failed to restore session: {init_result.get('error')}")
                        continue
                    
                    # Restore state
                    orchestrator.user_session = user_session
                    orchestrator.state_machine.current_state = user_session.current_state
                    orchestrator.state_machine.state_history = user_session.state_history
                    
                    # Store in active sessions
                    self.active_sessions[stored_session_id] = orchestrator
                    self.uid_to_session[uid] = stored_session_id
                    
                    return orchestrator
                    
            except Exception as e:
                logger.warning(f"Failed to restore session from {stored_session_path}: {e}")
                continue
        
        # No session found
        return None

    async def _cleanup_user_session(self, uid: str, group_id: str) -> None:
        """
        Clean up user session after completion.
        
        Args:
            uid: Luffa user ID
            group_id: Group ID
        """
        session_id = self.uid_to_session.get(uid)
        
        if session_id:
            # Cleanup orchestrator if exists
            if session_id in self.active_sessions:
                orchestrator = self.active_sessions[session_id]
                try:
                    # Determine if session was completed — bot services end at DUAL_REVEAL
                    completed = (orchestrator.user_session and
                               orchestrator.user_session.current_state in (
                                   ExperienceState.DUAL_REVEAL,
                                   ExperienceState.COMPLETED
                               ))
                    await orchestrator.cleanup(completed=completed)
                except Exception as e:
                    logger.error(f"Failed to cleanup orchestrator for session {session_id}: {e}")
                
                del self.active_sessions[session_id]
            
            # Remove uid mapping
            del self.uid_to_session[uid]
        
        # Remove from group users
        if group_id in self.group_users:
            self.group_users[group_id].discard(uid)
            
            # Clean up empty group
            if not self.group_users[group_id]:
                del self.group_users[group_id]

    def _get_user_orchestrator(self, uid: str) -> Optional[ExperienceOrchestrator]:
        """
        Get orchestrator for a specific user.
        
        Args:
            uid: Luffa user ID
            
        Returns:
            ExperienceOrchestrator if user has active session, None otherwise
        """
        session_id = self.uid_to_session.get(uid)
        if session_id:
            return self.active_sessions.get(session_id)
        return None

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
                        # Send warning (every 5 min check if still inactive)
                        logger.info(f"Session {session_id} inactive for {inactive_duration:.1f} min - sending warning")
                        try:
                            await self.client.send_group_message(
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
                        await self.client.send_group_message(
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


async def main():
    """Main entry point for Luffa Bot service."""
    service = LuffaBotService()
    
    try:
        await service.start()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Service error: {e}")
        raise
    finally:
        await service.shutdown()


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    asyncio.run(main())
