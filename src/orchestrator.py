"""Main application orchestrator wiring all VERITAS components together."""

from datetime import datetime
from typing import Optional, Literal
import asyncio
import logging

from models import CaseContent
from session import UserSession, SessionStore, DeliberationTurn
from state_machine import StateMachine, ExperienceState
from case_manager import CaseManager
from evidence_board import EvidenceBoard
from trial_orchestrator import TrialOrchestrator
from jury_orchestrator import JuryOrchestrator
from reasoning_evaluator import ReasoningEvaluator
from dual_reveal import DualRevealAssembler, DualReveal
from trial_stages import TrialStageManager
from luffa_integration import LuffaBot, SuperBox, LuffaChannel
from error_handling import ErrorHandler, StatePreservation
from llm_service import LLMService
from luffa_client import LuffaAPIClient
from config import AppConfig, load_config

logger = logging.getLogger("veritas")


class ExperienceOrchestrator:
    """
    Main orchestrator coordinating all VERITAS components.
    
    Manages the complete experience flow from start to completion,
    coordinating state machine, agents, jury, evaluation, and platform
    integrations.
    """

    def __init__(self, session_id: str, user_id: str, case_id: str, config: Optional[AppConfig] = None):
        """
        Initialize experience orchestrator.
        
        Args:
            session_id: Unique session identifier
            user_id: User identifier
            case_id: Case identifier
            config: Application configuration (loads from env if None)
        """
        self.session_id = session_id
        self.user_id = user_id
        self.case_id = case_id
        
        # Load configuration
        try:
            self.config = config or load_config()
            self.llm_service = LLMService(self.config.llm)
            self.luffa_client = LuffaAPIClient(self.config.luffa)
        except Exception as e:
            logger.warning(f"Failed to load config, using test mode: {e}")
            self.config = None
            self.llm_service = None
            self.luffa_client = None
        
        # Initialize components (use fixtures path relative to project root)
        self.case_manager = CaseManager(cases_directory="fixtures")
        self.session_store = SessionStore()
        self.error_handler = ErrorHandler(session_id, user_id)
        
        # Load case content
        self.case_content: Optional[CaseContent] = None
        self.user_session: Optional[UserSession] = None
        self.state_machine: Optional[StateMachine] = None
        
        # Component instances (initialized after case load)
        self.evidence_board: Optional[EvidenceBoard] = None
        self.trial_orchestrator: Optional[TrialOrchestrator] = None
        self.jury_orchestrator: Optional[JuryOrchestrator] = None
        self.reasoning_evaluator: Optional[ReasoningEvaluator] = None
        self.dual_reveal_assembler: Optional[DualRevealAssembler] = None
        self.trial_stage_manager: Optional[TrialStageManager] = None
        self.luffa_bot: Optional[LuffaBot] = None
        self.superbox: Optional[SuperBox] = None
        self.luffa_channel: Optional[LuffaChannel] = None
        self.state_preservation: Optional[StatePreservation] = None
        
        # Message polling state
        self._polling_task: Optional[asyncio.Task] = None
        self._polling_active = False
        self._message_handlers = {}

    async def initialize(self) -> dict:
        """
        Initialize the experience by loading case and setting up components.
        
        Returns:
            Initialization result with greeting
        """
        try:
            # Load case content
            self.case_content = self.case_manager.load_case(self.case_id)
            
            # Create user session
            self.user_session = UserSession(
                sessionId=self.session_id,
                userId=self.user_id,
                caseId=self.case_id,
                currentState=ExperienceState.NOT_STARTED,
                startTime=datetime.now(),
                lastActivityTime=datetime.now()
            )
            
            # Initialize state machine
            self.state_machine = StateMachine(
                session_id=self.session_id,
                case_id=self.case_id,
                session_store=self.session_store
            )
            
            # Initialize all components
            self.evidence_board = EvidenceBoard(self.case_content)
            self.trial_orchestrator = TrialOrchestrator(llm_service=self.llm_service)
            self.trial_orchestrator.initialize_agents(self.case_content)
            self.jury_orchestrator = JuryOrchestrator(llm_service=self.llm_service)
            self.jury_orchestrator.initialize_jury(self.case_content)
            self.reasoning_evaluator = ReasoningEvaluator(self.case_content)
            self.dual_reveal_assembler = DualRevealAssembler(self.case_content)
            self.trial_stage_manager = TrialStageManager(self.case_content)
            self.luffa_bot = LuffaBot(self.case_content, api_client=self.luffa_client)
            self.superbox = SuperBox(self.case_content, api_client=self.luffa_client)
            self.luffa_channel = LuffaChannel(api_client=self.luffa_client)
            self.state_preservation = StatePreservation(self.session_store)
            
            # Get greeting from Luffa Bot
            greeting = self.luffa_bot.get_greeting()
            
            return {
                "success": True,
                "session_id": self.session_id,
                "case_title": self.case_content.title,
                "greeting": greeting.model_dump(by_alias=True)
            }
        
        except Exception as e:
            self.error_handler.log_error(
                error_type="initialization_failure",
                component="orchestrator",
                severity="critical",
                message=f"Failed to initialize experience: {str(e)}"
            )
            return {
                "success": False,
                "error": str(e)
            }

    async def start_experience(self) -> dict:
        """
        Start the experience by transitioning to hook scene.
        
        Returns:
            Hook scene content and SuperBox prompt
        """
        try:
            # Transition to hook scene
            await self.state_machine.transition_to(ExperienceState.HOOK_SCENE)
            self.user_session.current_state = ExperienceState.HOOK_SCENE
            
            # Get hook scene content
            hook_content = self.trial_stage_manager.present_hook_scene()
            
            # Get stage announcement
            announcement = self.luffa_bot.announce_stage(ExperienceState.HOOK_SCENE)
            
            # Get SuperBox prompt
            superbox_prompt = self.luffa_bot.prompt_superbox_launch(ExperienceState.HOOK_SCENE)
            
            # Render SuperBox scene
            superbox_scene = self.superbox.render_courtroom_scene()
            
            # Save progress
            self._save_progress()
            
            return {
                "success": True,
                "stage": ExperienceState.HOOK_SCENE.value,
                "hook_content": hook_content.model_dump(by_alias=True),
                "announcement": announcement.model_dump(by_alias=True),
                "superbox_prompt": superbox_prompt.model_dump(by_alias=True),
                "superbox_scene": superbox_scene.model_dump(by_alias=True)
            }
        
        except Exception as e:
            return self._handle_error("start_experience", e)

    async def advance_trial_stage(self) -> dict:
        """
        Advance to the next trial stage.
        
        Returns:
            Stage content and agent responses
        """
        try:
            # Get next state
            next_state = self.state_machine.get_next_state()
            if not next_state:
                return {"success": False, "error": "No next stage available"}
            
            # Transition to next state
            await self.state_machine.transition_to(next_state)
            self.user_session.current_state = next_state
            
            # Get stage announcement
            announcement = self.luffa_bot.announce_stage(next_state)
            
            # Execute trial stage if in trial phase
            agent_responses = []
            if next_state in [
                ExperienceState.CHARGE_READING,
                ExperienceState.PROSECUTION_OPENING,
                ExperienceState.DEFENCE_OPENING,
                ExperienceState.EVIDENCE_PRESENTATION,
                ExperienceState.CROSS_EXAMINATION,
                ExperienceState.PROSECUTION_CLOSING,
                ExperienceState.DEFENCE_CLOSING,
                ExperienceState.JUDGE_SUMMING_UP
            ]:
                agent_responses = await self.trial_orchestrator.execute_stage(next_state)
                
                # Update evidence board highlighting during evidence presentation
                if next_state == ExperienceState.EVIDENCE_PRESENTATION:
                    if self.case_content.evidence:
                        self.evidence_board.highlight_item(self.case_content.evidence[0].id)
            
            # Start deliberation if entering jury deliberation
            if next_state == ExperienceState.JURY_DELIBERATION:
                deliberation_prompt = self.jury_orchestrator.start_deliberation()
                return {
                    "success": True,
                    "stage": next_state.value,
                    "announcement": announcement.model_dump(by_alias=True),
                    "deliberation_prompt": deliberation_prompt
                }
            
            # Save progress
            self._save_progress()
            
            return {
                "success": True,
                "stage": next_state.value,
                "announcement": announcement.model_dump(by_alias=True),
                "agent_responses": [r.model_dump(by_alias=True) for r in agent_responses]
            }
        
        except Exception as e:
            return self._handle_error("advance_trial_stage", e)
    
    async def broadcast_stage_to_group(self, group_id: str) -> dict:
        """
        Broadcast current stage announcement to group with formatting and buttons.
        
        Args:
            group_id: Group ID to broadcast to
            
        Returns:
            Broadcast result
        """
        if not self.state_machine or not self.luffa_bot:
            return {"success": False, "error": "Not initialized"}
        
        try:
            result = await self.luffa_bot.broadcast_stage_to_group(
                group_id=group_id,
                stage=self.state_machine.current_state
            )
            return result
        
        except Exception as e:
            return self._handle_error("broadcast_stage_to_group", e)

    async def submit_deliberation_statement(self, statement: str, 
                                           evidence_refs: list[str] = None) -> dict:
        """
        Submit user deliberation statement and get AI responses.
        
        Args:
            statement: User's statement
            evidence_refs: Evidence IDs referenced
            
        Returns:
            User turn and AI responses
        """
        try:
            # Process statement through jury orchestrator
            turns = await self.jury_orchestrator.process_user_statement(
                statement, 
                evidence_refs or []
            )
            
            # Store in session
            self.user_session.progress.deliberation_statements.extend(turns)
            
            # Check if deliberation should end
            if self.jury_orchestrator.should_end_deliberation():
                return {
                    "success": True,
                    "turns": [t.model_dump(by_alias=True) for t in turns],
                    "deliberation_ended": True,
                    "message": "Deliberation time has expired. Please proceed to voting."
                }
            
            # Save progress
            self._save_progress()
            
            return {
                "success": True,
                "turns": [t.model_dump(by_alias=True) for t in turns],
                "deliberation_ended": False
            }
        
        except Exception as e:
            return self._handle_error("submit_deliberation_statement", e)

    async def submit_vote(self, vote: Literal["guilty", "not_guilty"]) -> dict:
        """
        Submit user vote and calculate verdict.
        
        Args:
            vote: User's vote
            
        Returns:
            Vote result with verdict
        """
        vote_result = None
        try:
            # Collect votes from all jurors
            vote_result = await self.jury_orchestrator.collect_votes(vote)
            
            # Store in session
            self.user_session.progress.vote = vote
            
            # Evaluate reasoning
            reasoning_assessment = await self.reasoning_evaluator.analyze_statements(
                self.user_session.progress.deliberation_statements,
                vote
            )
            
            # Store reasoning assessment
            self.user_session.progress.reasoning_assessment = reasoning_assessment
            
            # Reveal jurors
            juror_reveals = self.jury_orchestrator.reveal_jurors(vote_result)
            
            # Assemble dual reveal
            dual_reveal = self.dual_reveal_assembler.assemble_dual_reveal(
                vote_result,
                reasoning_assessment,
                juror_reveals
            )
            
            # Transition to dual reveal state
            await self.state_machine.transition_to(ExperienceState.DUAL_REVEAL)
            self.user_session.current_state = ExperienceState.DUAL_REVEAL
            
            # Save progress
            self._save_progress()
            
            return {
                "success": True,
                "dual_reveal": dual_reveal.model_dump(by_alias=True),
                "sequential_reveal": self.dual_reveal_assembler.present_sequential_reveal(dual_reveal)
            }
        
        except Exception as e:
            # Handle reasoning evaluation failure gracefully
            if "reasoning" in str(e).lower() and vote_result is not None:
                fallback = self.error_handler.handle_reasoning_evaluation_failure()
                return {
                    "success": True,
                    "verdict": vote_result.model_dump(by_alias=True),
                    "reasoning_unavailable": True,
                    "fallback": fallback.model_dump(by_alias=True)
                }

            return self._handle_error("submit_vote", e)

    async def complete_experience(self, share_verdict: bool = False) -> dict:
        """
        Complete the experience and optionally share verdict.
        
        Args:
            share_verdict: Whether to share verdict to Luffa Channel
            
        Returns:
            Completion data
        """
        try:
            # Transition to completed state
            await self.state_machine.transition_to(ExperienceState.COMPLETED)
            self.user_session.current_state = ExperienceState.COMPLETED
            
            # Share verdict if opted in
            verdict_share = None
            if share_verdict and self.user_session.progress.vote:
                verdict_share = await self.luffa_channel.share_verdict(
                    self.case_id,
                    self.user_session.progress.vote,
                    user_opted_in=True
                )
            
            # Get aggregate statistics
            statistics = await self.luffa_channel.get_aggregate_statistics(self.case_id)
            
            # Save final progress
            self._save_progress()
            
            return {
                "success": True,
                "message": "Experience completed. Thank you for your participation.",
                "verdict_shared": verdict_share is not None,
                "statistics": statistics
            }
        
        except Exception as e:
            return self._handle_error("complete_experience", e)

    def get_evidence_board(self) -> dict:
        """
        Get evidence board data.
        
        Returns:
            Evidence board timeline and items
        """
        if not self.evidence_board:
            return {"error": "Evidence board not initialized"}
        
        return {
            "timeline": self.evidence_board.render_timeline(),
            "items": [item.model_dump(by_alias=True) for item in self.evidence_board.get_all_items()],
            "highlighted_item_id": self.evidence_board.highlighted_item_id
        }

    def get_progress(self) -> dict:
        """
        Get current progress indicator.
        
        Returns:
            Progress data
        """
        if not self.state_machine or not self.trial_stage_manager:
            return {"error": "Not initialized"}
        
        return self.trial_stage_manager.get_progress_indicator(
            self.state_machine.current_state,
            self.state_machine.get_completed_states()
        )

    def _save_progress(self) -> None:
        """Save current progress to persistent storage."""
        try:
            if self.state_preservation and self.state_machine and self.user_session:
                # Sync state machine data to session before saving
                self.user_session.current_state = self.state_machine.current_state
                self.user_session.state_history = self.state_machine.state_history
                self.user_session.progress.completed_stages = self.state_machine.get_completed_states()
                self.state_preservation.auto_save(self.user_session)
        except Exception as e:
            self.error_handler.log_error(
                error_type="save_progress_failure",
                component="orchestrator",
                severity="medium",
                message=f"Failed to save progress: {str(e)}"
            )

    def _handle_error(self, operation: str, error: Exception) -> dict:
        """
        Handle error and return error response.
        
        Args:
            operation: Operation that failed
            error: The exception
            
        Returns:
            Error response
        """
        self.error_handler.log_error(
            error_type=f"{operation}_failure",
            component="orchestrator",
            severity="high",
            message=str(error)
        )
        
        return {
            "success": False,
            "error": str(error),
            "operation": operation
        }

    # ========================================================================
    # Message Polling Loop (Task 22.1)
    # ========================================================================

    async def start_message_polling(self) -> None:
        """
        Start background task for polling Luffa Bot messages.
        
        Polls /receive endpoint every 1 second, parses incoming messages,
        routes to appropriate handlers, and implements message deduplication.
        
        Requirements: 13.1, 13.2, 13.4
        """
        if self._polling_active:
            logger.warning("Message polling already active")
            return
        
        if not self.luffa_client:
            logger.warning("Luffa client not initialized, cannot start polling")
            return
        
        self._polling_active = True
        self._polling_task = asyncio.create_task(self._polling_loop())
        logger.info("Started message polling loop")

    async def stop_message_polling(self) -> None:
        """Stop the message polling background task."""
        if not self._polling_active:
            return
        
        self._polling_active = False
        
        if self._polling_task:
            self._polling_task.cancel()
            try:
                await self._polling_task
            except asyncio.CancelledError:
                pass
            self._polling_task = None
        
        logger.info("Stopped message polling loop")

    async def _polling_loop(self) -> None:
        """
        Internal polling loop that runs every 1 second.
        
        Continuously polls for messages, parses them, and routes to handlers.
        Message deduplication is handled by the LuffaAPIClient.
        """
        logger.info("Polling loop started - checking for messages every 1 second")
        
        while self._polling_active:
            try:
                # Poll for new messages (deduplication handled in client)
                messages = await self.luffa_client.receive_messages()
                
                # Process each message
                for msg in messages:
                    await self._route_message(msg)
                
                # Wait 1 second before next poll
                await asyncio.sleep(1)
            
            except asyncio.CancelledError:
                logger.info("Polling loop cancelled")
                break
            
            except Exception as e:
                logger.error(f"Error in polling loop: {e}")
                # Back off on error to avoid tight error loops
                await asyncio.sleep(5)

    async def _route_message(self, msg: dict) -> None:
        """
        Route incoming message to appropriate handler.
        
        Args:
            msg: Parsed message object with fields:
                - uid: Sender or group ID
                - type: 0=DM, 1=Group
                - text: Message text
                - msgId: Message ID (already deduplicated)
                - sender_uid: Only in group messages
                - atList: List of mentioned users
                - urlLink: Optional URL link
        """
        text = msg.get("text", "").strip()
        uid = msg.get("uid")
        msg_type = msg.get("type")
        
        if not text or uid is None:
            return
        
        # Check if this is a command (starts with /)
        if text.startswith("/"):
            await self._handle_command_message(msg)
        else:
            # Regular message - check if we have a handler registered
            handler = self._message_handlers.get(uid)
            if handler:
                await handler(msg)
            else:
                # Default: treat as deliberation statement if in deliberation state
                if self.state_machine and self.state_machine.current_state == ExperienceState.JURY_DELIBERATION:
                    await self._handle_deliberation_message(msg)

    async def _handle_command_message(self, msg: dict) -> None:
        """
        Handle command messages (starting with /).
        
        Args:
            msg: Message object
        """
        text = msg.get("text", "").strip()
        uid = msg.get("uid")
        
        # Extract command and arguments
        parts = text.split()
        command = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        # Route to appropriate command handler
        if command == "/start":
            await self._handle_start_command(uid, msg)
        elif command == "/continue":
            await self._handle_continue_command(uid, msg)
        elif command == "/vote":
            vote = args[0] if args else None
            await self._handle_vote_command(uid, vote, msg)
        elif command == "/evidence":
            await self._handle_evidence_command(uid, msg)
        elif command == "/status":
            await self._handle_status_command(uid, msg)
        elif command == "/help":
            await self._handle_help_command(uid, msg)
        else:
            # Unknown command
            await self._send_message(uid, msg.get("type"), f"Unknown command: {command}. Type /help for available commands.")

    async def _handle_deliberation_message(self, msg: dict) -> None:
        """
        Handle deliberation statement from user.
        
        Args:
            msg: Message object
        """
        text = msg.get("text", "").strip()
        
        if not text:
            return
        
        # Submit deliberation statement
        result = await self.submit_deliberation_statement(text)
        
        if result["success"]:
            # Send AI juror responses back
            uid = msg.get("uid")
            msg_type = msg.get("type")
            
            for turn in result["turns"][1:]:  # Skip user's own turn
                juror_statement = turn["statement"]
                await self._send_message(uid, msg_type, f"🗣️ AI Juror: {juror_statement}")
            
            # Check if deliberation ended
            if result.get("deliberation_ended"):
                await self._send_message(uid, msg_type, "⏰ Deliberation time is up! Type /vote guilty or /vote not_guilty")

    async def _handle_start_command(self, uid: str, msg: dict) -> None:
        """Handle /start command."""
        # Initialize if not already done
        if not self.case_content:
            init_result = await self.initialize()
            if not init_result["success"]:
                await self._send_message(uid, msg.get("type"), f"❌ Failed to start: {init_result.get('error')}")
                return
        
        # Start experience
        start_result = await self.start_experience()
        
        if start_result["success"]:
            hook_content = start_result["hook_content"]["content"]
            
            # Broadcast to group if this is a group message
            if msg.get("type") == 1:  # Group message
                await self.broadcast_stage_to_group(uid)
                await self._send_message(uid, msg.get("type"), f"\n{hook_content}")
            else:
                # Send to DM
                await self._send_message(uid, msg.get("type"), f"🎭 THE TRIAL BEGINS\n\n{hook_content}")
                await self._send_message(uid, msg.get("type"), "Type /continue to proceed.")
        else:
            await self._send_message(uid, msg.get("type"), f"❌ Error: {start_result.get('error')}")

    async def _handle_continue_command(self, uid: str, msg: dict) -> None:
        """Handle /continue command."""
        if not self.state_machine:
            await self._send_message(uid, msg.get("type"), "⚠️ No active trial. Use /start to begin.")
            return
        
        # Advance to next stage
        result = await self.advance_trial_stage()
        
        if result["success"]:
            # Broadcast stage announcement to group if this is a group message
            if msg.get("type") == 1:  # Group message
                await self.broadcast_stage_to_group(uid)
            else:
                # Send announcement to DM
                announcement = result["announcement"]["content"]
                await self._send_message(uid, msg.get("type"), f"📢 {announcement}")
            
            # Send agent responses if any
            if "agent_responses" in result:
                for response in result["agent_responses"]:
                    role = response["agentRole"].upper()
                    content = response["content"]
                    await self._send_message(uid, msg.get("type"), f"🎭 [{role}]\n\n{content}")
                    await asyncio.sleep(1)  # Pace messages
            
            # Handle deliberation start
            if "deliberation_prompt" in result:
                prompt = result["deliberation_prompt"]
                await self._send_message(uid, msg.get("type"), f"⚖️ JURY DELIBERATION\n\n{prompt}\n\nShare your thoughts or type /evidence to view evidence.")
        else:
            await self._send_message(uid, msg.get("type"), f"❌ Error: {result.get('error')}")

    async def _handle_vote_command(self, uid: str, vote: Optional[str], msg: dict) -> None:
        """Handle /vote command."""
        if not vote or vote not in ["guilty", "not_guilty"]:
            await self._send_message(uid, msg.get("type"), "⚠️ Invalid vote. Use: /vote guilty OR /vote not_guilty")
            return
        
        # Submit vote
        await self._send_message(uid, msg.get("type"), "🗳️ Collecting votes from all jurors...")
        
        vote_result = await self.submit_vote(vote)
        
        if vote_result["success"]:
            # Send dual reveal
            dual_reveal = vote_result["dual_reveal"]
            
            # 1. Verdict
            verdict = dual_reveal["verdict"]
            verdict_text = verdict["verdict"].replace("_", " ").upper()
            await self._send_message(uid, msg.get("type"), 
                f"⚖️ THE VERDICT\n\nThe jury finds the defendant: {verdict_text}\n\nVote: {verdict['guiltyCount']} guilty, {verdict['notGuiltyCount']} not guilty")
            await asyncio.sleep(2)
            
            # 2. Ground truth
            truth = dual_reveal["groundTruth"]
            actual = truth["actualVerdict"].replace("_", " ").upper()
            await self._send_message(uid, msg.get("type"),
                f"🔍 THE TRUTH\n\nActual verdict: {actual}\n\n{truth['explanation']}")
            await asyncio.sleep(2)
            
            # 3. Reasoning assessment
            assessment = dual_reveal["reasoningAssessment"]
            category = assessment["category"].replace("_", " ").title()
            await self._send_message(uid, msg.get("type"),
                f"📊 REASONING ASSESSMENT\n\nCategory: {category}\nEvidence Score: {assessment['evidenceScore']:.2f}/1.0\nCoherence Score: {assessment['coherenceScore']:.2f}/1.0\n\n{assessment['feedback']}")
            
            await self._send_message(uid, msg.get("type"), "✅ Trial complete! Type /start to begin a new trial.")
        else:
            await self._send_message(uid, msg.get("type"), f"❌ Error: {vote_result.get('error')}")

    async def _handle_evidence_command(self, uid: str, msg: dict) -> None:
        """Handle /evidence command."""
        evidence_board = self.get_evidence_board()
        
        if "error" in evidence_board:
            await self._send_message(uid, msg.get("type"), "⚠️ Evidence board not available.")
            return
        
        text = "📋 EVIDENCE BOARD\n\n"
        for item in evidence_board["timeline"]:
            text += f"• {item['title']} ({item['type']})\n  {item['timestamp']}\n\n"
        
        await self._send_message(uid, msg.get("type"), text)

    async def _handle_status_command(self, uid: str, msg: dict) -> None:
        """Handle /status command."""
        progress = self.get_progress()
        
        if "error" in progress:
            await self._send_message(uid, msg.get("type"), "⚠️ No active trial.")
            return
        
        current = progress["currentStage"].replace("_", " ").title()
        text = f"📊 TRIAL STATUS\n\nCurrent Stage: {current}\nProgress: {progress['completedStages']}/{progress['totalStages']} stages"
        
        await self._send_message(uid, msg.get("type"), text)

    async def _handle_help_command(self, uid: str, msg: dict) -> None:
        """Handle /help command."""
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
1. Start a trial with /start
2. AI agents play courtroom roles
3. Watch the trial unfold
4. Deliberate with AI jurors
5. Cast your vote
6. See the dual reveal"""
        
        await self._send_message(uid, msg.get("type"), help_text)

    async def _send_message(self, uid: str, msg_type: int, text: str) -> None:
        """
        Send message via Luffa Bot.
        
        Args:
            uid: User or group ID
            msg_type: 0=DM, 1=Group
            text: Message text
        """
        if not self.luffa_client:
            logger.warning("Cannot send message - Luffa client not initialized")
            return
        
        try:
            if msg_type == 1:  # Group
                await self.luffa_client.send_group_message(uid, text)
            else:  # DM
                await self.luffa_client.send_dm(uid, text)
        except Exception as e:
            logger.error(f"Failed to send message: {e}")

    def register_message_handler(self, uid: str, handler) -> None:
        """
        Register a custom message handler for a specific user/group.
        
        Args:
            uid: User or group ID
            handler: Async function that takes a message dict
        """
        self._message_handlers[uid] = handler

    def unregister_message_handler(self, uid: str) -> None:
        """
        Unregister message handler for a user/group.
        
        Args:
            uid: User or group ID
        """
        if uid in self._message_handlers:
            del self._message_handlers[uid]
