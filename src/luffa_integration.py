"""Luffa platform integration components (Bot, SuperBox, Channel)."""

from datetime import datetime
from typing import Optional, Literal
import logging
from pydantic import BaseModel, Field, ConfigDict

from state_machine import ExperienceState
from models import CaseContent
from luffa_client import LuffaAPIClient

logger = logging.getLogger("veritas")


# ============================================================================
# LUFFA BOT INTEGRATION
# ============================================================================

class LuffaBotMessage(BaseModel):
    """Message from Luffa Bot (courtroom clerk)."""
    model_config = ConfigDict(populate_by_name=True)
    
    type: Literal["greeting", "stage_announcement", "prompt", "response"]
    content: str
    metadata: dict = Field(default_factory=dict)


class LuffaBot:
    """
    Luffa Bot interface serving as courtroom clerk and user guide.
    
    Provides greetings, stage announcements, SuperBox prompts,
    and procedural guidance.
    """

    def __init__(self, case_content: CaseContent, api_client: Optional[LuffaAPIClient] = None):
        """
        Initialize Luffa Bot.
        
        Args:
            case_content: The case content for context
            api_client: Luffa API client for sending messages (optional for testing)
        """
        self.case_content = case_content
        self.api_client = api_client

    def get_greeting(self) -> LuffaBotMessage:
        """
        Get initial greeting message.
        
        Returns:
            Greeting message
        """
        content = f"""Welcome to VERITAS - an interactive courtroom experience.

You are about to witness the trial of {self.case_content.title}. You will serve as a juror, observing the proceedings and ultimately deliberating with fellow jurors to reach a verdict.

This experience will take approximately 15 minutes. Your reasoning will be evaluated alongside your verdict.

Are you ready to begin?"""
        
        message = LuffaBotMessage(
            type="greeting",
            content=content,
            metadata={"case_id": self.case_content.case_id}
        )
        
        return message
    
    async def send_greeting(self, session_id: str) -> LuffaBotMessage:
        """
        Send greeting message via API.
        
        Args:
            session_id: User session ID
            
        Returns:
            Greeting message
        """
        message = self.get_greeting()
        
        if self.api_client:
            try:
                await self.api_client.send_bot_message(
                    session_id=session_id,
                    message_type=message.type,
                    content=message.content,
                    metadata=message.metadata
                )
            except Exception as e:
                logger.warning(f"Failed to send greeting via API: {e}")
        
        return message

    def announce_stage(self, stage: ExperienceState) -> LuffaBotMessage:
        """
        Announce transition to a new trial stage.
        
        Args:
            stage: The new stage being entered
            
        Returns:
            Stage announcement message with visual formatting
        """
        announcements = {
            ExperienceState.HOOK_SCENE: "🎭 THE TRIAL BEGINS\n\nThe trial is about to begin. Please observe carefully.",
            
            ExperienceState.CHARGE_READING: "⚖️ CHARGE READING\n\nThe Clerk will now read the formal charges against the defendant.",
            
            ExperienceState.PROSECUTION_OPENING: "👔 PROSECUTION OPENING\n\nThe Crown Prosecution will present their opening statement.",
            
            ExperienceState.DEFENCE_OPENING: "🛡️ DEFENCE OPENING\n\nThe Defence will now present their opening statement.",
            
            ExperienceState.EVIDENCE_PRESENTATION: "📋 EVIDENCE PRESENTATION\n\nWe will now hear the evidence. The Evidence Board is now available for your reference.",
            
            ExperienceState.CROSS_EXAMINATION: "❓ CROSS-EXAMINATION\n\nCross-examination will now proceed.",
            
            ExperienceState.PROSECUTION_CLOSING: "👔 PROSECUTION CLOSING\n\nThe Crown Prosecution will deliver their closing speech.",
            
            ExperienceState.DEFENCE_CLOSING: "🛡️ DEFENCE CLOSING\n\nThe Defence will deliver their closing speech.",
            
            ExperienceState.JUDGE_SUMMING_UP: "⚖️ JUDGE'S SUMMING UP\n\nThe Judge will now sum up the case and provide legal instructions to the jury.",
            
            ExperienceState.JURY_DELIBERATION: "🗣️ JURY DELIBERATION\n\nYou may now retire to the jury chamber to deliberate with your fellow jurors.\n\nShare your thoughts on the evidence and discuss the case.",
            
            ExperienceState.ANONYMOUS_VOTE: "🗳️ TIME TO VOTE\n\nIt is time to cast your verdict. Your vote will remain anonymous until the final reveal.",
            
            ExperienceState.DUAL_REVEAL: "📊 VERDICT REVEAL\n\nThe verdict will now be revealed, along with the truth of the case.",
            
            ExperienceState.COMPLETED: "✅ TRIAL COMPLETE\n\nThe trial is complete. Thank you for your service as a juror."
        }
        
        content = announcements.get(stage, f"Proceeding to {stage.value}")
        
        return LuffaBotMessage(
            type="stage_announcement",
            content=content,
            metadata={"stage": stage.value}
        )
    
    async def send_stage_announcement(self, session_id: str, stage: ExperienceState) -> LuffaBotMessage:
        """
        Send stage announcement via API.
        
        Args:
            session_id: User session ID
            stage: The new stage
            
        Returns:
            Stage announcement message
        """
        message = self.announce_stage(stage)
        
        if self.api_client:
            try:
                await self.api_client.send_bot_message(
                    session_id=session_id,
                    message_type=message.type,
                    content=message.content,
                    metadata=message.metadata
                )
            except Exception as e:
                logger.warning(f"Failed to send stage announcement via API: {e}")
        
        return message
    
    async def broadcast_stage_to_group(self, group_id: str, stage: ExperienceState) -> dict:
        """
        Broadcast stage announcement to group with visual formatting and buttons.
        
        Args:
            group_id: Group ID to broadcast to
            stage: The new stage being entered
            
        Returns:
            Broadcast result
        """
        if not self.api_client:
            logger.warning("Cannot broadcast to group - API client not initialized")
            return {"success": False, "error": "API client not initialized"}
        
        # Get formatted announcement
        message = self.announce_stage(stage)
        
        # Determine if buttons are needed for this stage
        buttons = None
        
        # Add continue button for stages that need user progression
        if stage in [
            ExperienceState.HOOK_SCENE,
            ExperienceState.CHARGE_READING,
            ExperienceState.PROSECUTION_OPENING,
            ExperienceState.DEFENCE_OPENING,
            ExperienceState.EVIDENCE_PRESENTATION,
            ExperienceState.CROSS_EXAMINATION,
            ExperienceState.PROSECUTION_CLOSING,
            ExperienceState.DEFENCE_CLOSING,
            ExperienceState.JUDGE_SUMMING_UP
        ]:
            buttons = [
                {
                    "name": "▶️ Continue",
                    "selector": "/continue",
                    "isHidden": "0"  # Visible to all
                }
            ]
        
        # Add vote buttons for voting stage
        elif stage == ExperienceState.ANONYMOUS_VOTE:
            buttons = [
                {
                    "name": "✅ GUILTY",
                    "selector": "/vote guilty",
                    "isHidden": "1"  # Hidden from others
                },
                {
                    "name": "❌ NOT GUILTY",
                    "selector": "/vote not_guilty",
                    "isHidden": "1"  # Hidden from others
                }
            ]
        
        # Add evidence button for deliberation
        elif stage == ExperienceState.JURY_DELIBERATION:
            buttons = [
                {
                    "name": "📋 View Evidence",
                    "selector": "/evidence",
                    "isHidden": "0"  # Visible to all
                }
            ]
        
        try:
            # Send to group with buttons
            result = await self.api_client.send_group_message(
                group_id=group_id,
                text=message.content,
                buttons=buttons,
                dismiss_type="select" if buttons else None  # Persist buttons
            )
            
            return {
                "success": True,
                "stage": stage.value,
                "message": message.content,
                "buttons_sent": buttons is not None,
                "api_response": result
            }
        
        except Exception as e:
            logger.error(f"Failed to broadcast stage to group: {e}")
            return {
                "success": False,
                "error": str(e),
                "stage": stage.value
            }

    def prompt_superbox_launch(self, stage: ExperienceState) -> LuffaBotMessage:
        """
        Prompt user to launch SuperBox for visual content.
        
        Args:
            stage: The stage requiring SuperBox
            
        Returns:
            SuperBox launch prompt
        """
        prompts = {
            ExperienceState.HOOK_SCENE: "Please launch SuperBox to view the opening scene.",
            ExperienceState.EVIDENCE_PRESENTATION: "Launch SuperBox to view the Evidence Board.",
            ExperienceState.JURY_DELIBERATION: "Launch SuperBox to enter the jury chamber.",
            ExperienceState.DUAL_REVEAL: "Launch SuperBox to view the verdict reveal."
        }
        
        content = prompts.get(stage, "Launch SuperBox for visual content.")
        
        return LuffaBotMessage(
            type="prompt",
            content=content,
            metadata={
                "stage": stage.value,
                "requires_superbox": True
            }
        )

    def respond_to_question(self, question: str) -> LuffaBotMessage:
        """
        Respond to user's procedural question.
        
        Args:
            question: User's question
            
        Returns:
            Response message
        """
        # Simple keyword-based responses
        question_lower = question.lower()
        
        if "evidence" in question_lower:
            content = "The Evidence Board displays all evidence presented during the trial. You can reference it during deliberation."
        elif "vote" in question_lower or "verdict" in question_lower:
            content = "You will vote after deliberation. Your vote will be anonymous until the final reveal."
        elif "deliberation" in question_lower:
            content = "During deliberation, you will discuss the case with fellow jurors. Share your thoughts and listen to others."
        elif "time" in question_lower or "long" in question_lower:
            content = "The complete experience takes approximately 15 minutes."
        else:
            content = "I'm here to guide you through the trial. If you have specific questions about procedure, please ask."
        
        return LuffaBotMessage(
            type="response",
            content=content,
            metadata={"question": question}
        )


# ============================================================================
# SUPERBOX INTEGRATION
# ============================================================================

class SceneElement(BaseModel):
    """Element in a SuperBox scene."""
    model_config = ConfigDict(populate_by_name=True)
    
    type: Literal["background", "character", "evidence", "ui_component"]
    id: str
    properties: dict = Field(default_factory=dict)


class SuperBoxScene(BaseModel):
    """SuperBox scene configuration."""
    model_config = ConfigDict(populate_by_name=True)
    
    scene_type: Literal["courtroom", "jury_chamber", "evidence_board", "reveal"] = Field(alias="sceneType")
    elements: list[SceneElement] = Field(default_factory=list)
    active_agent: Optional[str] = Field(default=None, alias="activeAgent")


class SuperBox:
    """
    SuperBox visual interface integration.
    
    Provides rich visual presentation of courtroom environments,
    evidence boards, and trial participants.
    """

    def __init__(self, case_content: CaseContent, api_client: Optional[LuffaAPIClient] = None):
        """
        Initialize SuperBox.
        
        Args:
            case_content: The case content for visual rendering
            api_client: Luffa API client for rendering scenes (optional for testing)
        """
        self.case_content = case_content
        self.current_scene: Optional[SuperBoxScene] = None
        self.api_client = api_client

    def render_courtroom_scene(self, active_agent: Optional[str] = None) -> SuperBoxScene:
        """
        Render courtroom environment.
        
        Args:
            active_agent: Currently speaking agent
            
        Returns:
            Courtroom scene configuration
        """
        elements = [
            SceneElement(
                type="background",
                id="courtroom_bg",
                properties={"style": "british_crown_court"}
            ),
            SceneElement(
                type="character",
                id="judge",
                properties={"position": "bench", "visible": True}
            ),
            SceneElement(
                type="character",
                id="prosecution",
                properties={"position": "left", "visible": True}
            ),
            SceneElement(
                type="character",
                id="defence",
                properties={"position": "right", "visible": True}
            )
        ]
        
        scene = SuperBoxScene(
            sceneType="courtroom",
            elements=elements,
            activeAgent=active_agent
        )
        
        self.current_scene = scene
        return scene
    
    async def render_courtroom_scene_async(self, session_id: str, active_agent: Optional[str] = None) -> SuperBoxScene:
        """
        Render courtroom scene and send to API.
        
        Args:
            session_id: User session ID
            active_agent: Currently speaking agent
            
        Returns:
            Courtroom scene configuration
        """
        scene = self.render_courtroom_scene(active_agent)
        
        if self.api_client:
            try:
                await self.api_client.render_superbox_scene(
                    session_id=session_id,
                    scene_data={
                        "scene_type": scene.scene_type,
                        "elements": [e.model_dump(by_alias=True) for e in scene.elements],
                        "active_agent": active_agent
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to render courtroom scene via API: {e}")
        
        return scene

    def render_evidence_board(self, highlighted_item_id: Optional[str] = None) -> SuperBoxScene:
        """
        Render evidence board with timeline.
        
        Args:
            highlighted_item_id: ID of evidence item to highlight
            
        Returns:
            Evidence board scene configuration
        """
        elements = [
            SceneElement(
                type="background",
                id="evidence_board_bg",
                properties={"style": "timeline"}
            )
        ]
        
        # Add evidence items
        for evidence in self.case_content.evidence:
            elements.append(SceneElement(
                type="evidence",
                id=evidence.id,
                properties={
                    "title": evidence.title,
                    "timestamp": evidence.timestamp,
                    "highlighted": evidence.id == highlighted_item_id
                }
            ))
        
        scene = SuperBoxScene(
            sceneType="evidence_board",
            elements=elements
        )
        
        self.current_scene = scene
        return scene

    def render_jury_chamber(self, active_juror: Optional[str] = None) -> SuperBoxScene:
        """
        Render jury chamber for deliberation.
        
        Args:
            active_juror: Currently speaking juror
            
        Returns:
            Jury chamber scene configuration
        """
        elements = [
            SceneElement(
                type="background",
                id="jury_chamber_bg",
                properties={"style": "deliberation_room"}
            ),
            SceneElement(
                type="ui_component",
                id="deliberation_interface",
                properties={"type": "chat", "active_speaker": active_juror}
            )
        ]
        
        scene = SuperBoxScene(
            sceneType="jury_chamber",
            elements=elements,
            activeAgent=active_juror
        )
        
        self.current_scene = scene
        return scene

    def render_reveal_scene(self, verdict: str, reasoning_category: str) -> SuperBoxScene:
        """
        Render dual reveal scene.
        
        Args:
            verdict: The jury verdict
            reasoning_category: User's reasoning category
            
        Returns:
            Reveal scene configuration
        """
        elements = [
            SceneElement(
                type="background",
                id="reveal_bg",
                properties={"style": "dramatic"}
            ),
            SceneElement(
                type="ui_component",
                id="verdict_display",
                properties={"verdict": verdict, "type": "verdict"}
            ),
            SceneElement(
                type="ui_component",
                id="reasoning_display",
                properties={"category": reasoning_category, "type": "reasoning"}
            )
        ]
        
        scene = SuperBoxScene(
            sceneType="reveal",
            elements=elements
        )
        
        self.current_scene = scene
        return scene

    def get_text_fallback(self, scene_type: str) -> str:
        """
        Get text-based fallback when SuperBox fails to load.
        
        Args:
            scene_type: Type of scene
            
        Returns:
            Text description
        """
        fallbacks = {
            "courtroom": "You are in a British Crown Court. The judge presides from the bench, with prosecution on the left and defence on the right.",
            "jury_chamber": "You are in the jury deliberation room. Discuss the case with your fellow jurors.",
            "evidence_board": f"Evidence Board: {len(self.case_content.evidence)} items available. Reference them by name during deliberation.",
            "reveal": "The verdict and reasoning assessment will be displayed here."
        }
        
        return fallbacks.get(scene_type, "Visual content unavailable. Proceeding with text-only mode.")


# ============================================================================
# LUFFA CHANNEL INTEGRATION
# ============================================================================

class ChannelAnnouncement(BaseModel):
    """Announcement on Luffa Channel."""
    model_config = ConfigDict(populate_by_name=True)
    
    type: Literal["new_case", "verdict_share", "statistics"]
    case_id: str = Field(alias="caseId")
    content: str
    metadata: dict = Field(default_factory=dict)


class VerdictShare(BaseModel):
    """Shared verdict on Luffa Channel."""
    model_config = ConfigDict(populate_by_name=True)
    
    case_id: str = Field(alias="caseId")
    verdict: Literal["guilty", "not_guilty"]
    anonymous: bool
    timestamp: datetime


class LuffaChannel:
    """
    Luffa Channel integration for case distribution and verdict sharing.
    
    Handles new case announcements, verdict sharing, and aggregate statistics.
    """

    def __init__(self, api_client: Optional[LuffaAPIClient] = None):
        """Initialize Luffa Channel.
        
        Args:
            api_client: Luffa API client for channel operations (optional for testing)
        """
        self.verdict_shares: list[VerdictShare] = []
        self.api_client = api_client

    def announce_new_case(self, case_content: CaseContent) -> ChannelAnnouncement:
        """
        Announce new case availability.
        
        Args:
            case_content: The new case
            
        Returns:
            Channel announcement
        """
        content = f"New case available: {case_content.title}. Experience this compelling courtroom drama now."
        
        return ChannelAnnouncement(
            type="new_case",
            caseId=case_content.case_id,
            content=content,
            metadata={"title": case_content.title}
        )

    def offer_verdict_share(self, case_id: str, verdict: str) -> dict:
        """
        Offer user option to share their verdict.
        
        Args:
            case_id: The case ID
            verdict: User's verdict
            
        Returns:
            Share offer data
        """
        return {
            "message": "Would you like to share your verdict with the VERITAS community?",
            "case_id": case_id,
            "verdict": verdict,
            "anonymous": True,
            "note": "Your reasoning assessment will remain private."
        }

    async def share_verdict(self, case_id: str, verdict: Literal["guilty", "not_guilty"], 
                     user_opted_in: bool) -> Optional[VerdictShare]:
        """
        Share verdict to channel if user opted in.
        
        Args:
            case_id: The case ID
            verdict: The verdict
            user_opted_in: Whether user consented to sharing
            
        Returns:
            VerdictShare if shared, None otherwise
        """
        if not user_opted_in:
            return None
        
        share = VerdictShare(
            caseId=case_id,
            verdict=verdict,
            anonymous=True,
            timestamp=datetime.now()
        )
        
        self.verdict_shares.append(share)
        
        # Send to API if available
        if self.api_client:
            try:
                await self.api_client.share_verdict(
                    case_id=case_id,
                    verdict=verdict,
                    anonymous=True
                )
            except Exception as e:
                logger.warning(f"Failed to share verdict via API: {e}")
        
        return share

    async def get_aggregate_statistics(self, case_id: str) -> dict:
        """
        Get aggregate verdict statistics for a case.
        
        Args:
            case_id: The case ID
            
        Returns:
            Statistics dictionary
        """
        # Try to get from API first
        if self.api_client:
            try:
                return await self.api_client.get_verdict_statistics(case_id)
            except Exception as e:
                logger.warning(f"Failed to get statistics from API: {e}")
        
        # Fallback to local statistics
        case_shares = [s for s in self.verdict_shares if s.case_id == case_id]
        
        if not case_shares:
            return {
                "case_id": case_id,
                "total_verdicts": 0,
                "guilty_percentage": 0,
                "not_guilty_percentage": 0
            }
        
        guilty_count = sum(1 for s in case_shares if s.verdict == "guilty")
        total = len(case_shares)
        
        return {
            "case_id": case_id,
            "total_verdicts": total,
            "guilty_percentage": round((guilty_count / total) * 100, 1),
            "not_guilty_percentage": round(((total - guilty_count) / total) * 100, 1)
        }
