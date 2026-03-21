"""Main application orchestrator wiring all VERITAS components together."""

from datetime import datetime
from typing import Optional, Literal
import asyncio

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


class ExperienceOrchestrator:
    """
    Main orchestrator coordinating all VERITAS components.
    
    Manages the complete experience flow from start to completion,
    coordinating state machine, agents, jury, evaluation, and platform
    integrations.
    """

    def __init__(self, session_id: str, user_id: str, case_id: str):
        """
        Initialize experience orchestrator.
        
        Args:
            session_id: Unique session identifier
            user_id: User identifier
            case_id: Case identifier
        """
        self.session_id = session_id
        self.user_id = user_id
        self.case_id = case_id
        
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
            self.trial_orchestrator = TrialOrchestrator()
            self.trial_orchestrator.initialize_agents(self.case_content)
            self.jury_orchestrator = JuryOrchestrator()
            self.jury_orchestrator.initialize_jury(self.case_content)
            self.reasoning_evaluator = ReasoningEvaluator(self.case_content)
            self.dual_reveal_assembler = DualRevealAssembler(self.case_content)
            self.trial_stage_manager = TrialStageManager(self.case_content)
            self.luffa_bot = LuffaBot(self.case_content)
            self.superbox = SuperBox(self.case_content)
            self.luffa_channel = LuffaChannel()
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
            if "reasoning" in str(e).lower():
                fallback = self.error_handler.handle_reasoning_evaluation_failure()
                # Continue without reasoning assessment
                vote_result = await self.jury_orchestrator.collect_votes(vote)
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
                verdict_share = self.luffa_channel.share_verdict(
                    self.case_id,
                    self.user_session.progress.vote,
                    user_opted_in=True
                )
            
            # Get aggregate statistics
            statistics = self.luffa_channel.get_aggregate_statistics(self.case_id)
            
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
            if self.state_preservation:
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
