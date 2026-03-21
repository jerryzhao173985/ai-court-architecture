"""Trial stage content and progression management."""

from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

from models import CaseContent
from state_machine import ExperienceState


class StageContent(BaseModel):
    """Content for a trial stage."""
    model_config = ConfigDict(populate_by_name=True)
    
    stage: ExperienceState
    content: str
    duration_seconds: int = Field(alias="durationSeconds")
    requires_superbox: bool = Field(default=False, alias="requiresSuperbox")


class StageTiming(BaseModel):
    """Timing configuration for trial stages."""
    model_config = ConfigDict(populate_by_name=True)
    
    stage: ExperienceState
    min_duration: int = Field(alias="minDuration")  # seconds
    max_duration: int = Field(alias="maxDuration")  # seconds
    target_duration: int = Field(alias="targetDuration")  # seconds


class PauseState(BaseModel):
    """State of a pause between stages."""
    model_config = ConfigDict(populate_by_name=True)
    
    is_paused: bool = Field(alias="isPaused")
    pause_start: Optional[datetime] = Field(default=None, alias="pauseStart")
    max_pause_seconds: int = Field(default=120, alias="maxPauseSeconds")  # 2 minutes

    def get_pause_duration(self) -> float:
        """Get current pause duration in seconds."""
        if not self.pause_start:
            return 0.0
        return (datetime.now() - self.pause_start).total_seconds()

    def is_pause_expired(self) -> bool:
        """Check if pause has exceeded maximum duration."""
        return self.get_pause_duration() >= self.max_pause_seconds


class TrialStageManager:
    """
    Manages trial stage content, timing, and progression.
    
    Handles hook scene presentation, stage duration tracking,
    pause functionality, and progress indicators.
    """

    # Stage timing configurations (in seconds)
    STAGE_TIMINGS = {
        ExperienceState.HOOK_SCENE: StageTiming(
            stage=ExperienceState.HOOK_SCENE,
            minDuration=60,
            maxDuration=90,
            targetDuration=75
        ),
        ExperienceState.CHARGE_READING: StageTiming(
            stage=ExperienceState.CHARGE_READING,
            minDuration=20,
            maxDuration=40,
            targetDuration=30
        ),
        ExperienceState.PROSECUTION_OPENING: StageTiming(
            stage=ExperienceState.PROSECUTION_OPENING,
            minDuration=45,
            maxDuration=75,
            targetDuration=60
        ),
        ExperienceState.DEFENCE_OPENING: StageTiming(
            stage=ExperienceState.DEFENCE_OPENING,
            minDuration=45,
            maxDuration=75,
            targetDuration=60
        ),
        ExperienceState.EVIDENCE_PRESENTATION: StageTiming(
            stage=ExperienceState.EVIDENCE_PRESENTATION,
            minDuration=90,
            maxDuration=150,
            targetDuration=120
        ),
        ExperienceState.CROSS_EXAMINATION: StageTiming(
            stage=ExperienceState.CROSS_EXAMINATION,
            minDuration=60,
            maxDuration=120,
            targetDuration=90
        ),
        ExperienceState.PROSECUTION_CLOSING: StageTiming(
            stage=ExperienceState.PROSECUTION_CLOSING,
            minDuration=45,
            maxDuration=75,
            targetDuration=60
        ),
        ExperienceState.DEFENCE_CLOSING: StageTiming(
            stage=ExperienceState.DEFENCE_CLOSING,
            minDuration=45,
            maxDuration=75,
            targetDuration=60
        ),
        ExperienceState.JUDGE_SUMMING_UP: StageTiming(
            stage=ExperienceState.JUDGE_SUMMING_UP,
            minDuration=90,
            maxDuration=120,
            targetDuration=105
        ),
        ExperienceState.JURY_DELIBERATION: StageTiming(
            stage=ExperienceState.JURY_DELIBERATION,
            minDuration=240,
            maxDuration=360,
            targetDuration=300
        ),
        ExperienceState.ANONYMOUS_VOTE: StageTiming(
            stage=ExperienceState.ANONYMOUS_VOTE,
            minDuration=20,
            maxDuration=60,
            targetDuration=30
        ),
        ExperienceState.DUAL_REVEAL: StageTiming(
            stage=ExperienceState.DUAL_REVEAL,
            minDuration=60,
            maxDuration=120,
            targetDuration=90
        )
    }

    def __init__(self, case_content: CaseContent):
        """
        Initialize trial stage manager.
        
        Args:
            case_content: The case content for stage generation
        """
        self.case_content = case_content
        self.pause_state = PauseState(isPaused=False)

    def present_hook_scene(self) -> StageContent:
        """
        Present the atmospheric opening hook scene.
        
        Returns:
            Hook scene content
        """
        hook_text = self.case_content.narrative.hook_scene
        
        # Ensure hook scene introduces victim, defendant, and mystery
        if not self._validates_hook_content(hook_text):
            # Fallback if hook scene is incomplete
            hook_text = self._generate_fallback_hook()
        
        timing = self.STAGE_TIMINGS[ExperienceState.HOOK_SCENE]
        
        return StageContent(
            stage=ExperienceState.HOOK_SCENE,
            content=hook_text,
            durationSeconds=timing.target_duration,
            requiresSuperbox=True
        )

    def _validates_hook_content(self, hook_text: str) -> bool:
        """
        Validate that hook scene includes required elements.
        
        Args:
            hook_text: The hook scene text
            
        Returns:
            True if valid, False otherwise
        """
        hook_lower = hook_text.lower()
        
        # Check for victim mention
        victim_name = self.case_content.narrative.victim_profile.name.lower()
        has_victim = victim_name in hook_lower or "victim" in hook_lower
        
        # Check for defendant mention
        defendant_name = self.case_content.narrative.defendant_profile.name.lower()
        has_defendant = defendant_name in hook_lower or "defendant" in hook_lower or "accused" in hook_lower
        
        # Check for mystery/crime mention
        has_mystery = any(word in hook_lower for word in ["murder", "death", "killed", "found dead", "mystery"])
        
        return has_victim and has_defendant and has_mystery

    def _generate_fallback_hook(self) -> str:
        """Generate fallback hook scene if case content is incomplete."""
        victim = self.case_content.narrative.victim_profile.name
        defendant = self.case_content.narrative.defendant_profile.name
        
        return f"""The courtroom falls silent as the case begins.

{victim} was found dead under mysterious circumstances. The prosecution claims {defendant} is responsible for this heinous crime.

But is the evidence as clear as it seems? Or does reasonable doubt lurk in the shadows?

The trial is about to begin. Justice awaits."""

    def get_stage_timing(self, stage: ExperienceState) -> Optional[StageTiming]:
        """
        Get timing configuration for a stage.
        
        Args:
            stage: The experience state
            
        Returns:
            Stage timing or None if not configured
        """
        return self.STAGE_TIMINGS.get(stage)

    def is_stage_duration_valid(self, stage: ExperienceState, duration_seconds: float) -> bool:
        """
        Check if stage duration is within valid range.
        
        Args:
            stage: The experience state
            duration_seconds: Duration in seconds
            
        Returns:
            True if valid, False otherwise
        """
        timing = self.get_stage_timing(stage)
        if not timing:
            return True  # No timing constraints
        
        return timing.min_duration <= duration_seconds <= timing.max_duration

    def start_pause(self) -> None:
        """Start a pause between stages."""
        self.pause_state.is_paused = True
        self.pause_state.pause_start = datetime.now()

    def end_pause(self) -> None:
        """End the current pause."""
        self.pause_state.is_paused = False
        self.pause_state.pause_start = None

    def check_pause_status(self) -> dict:
        """
        Check current pause status.
        
        Returns:
            Dictionary with pause information
        """
        if not self.pause_state.is_paused:
            return {"is_paused": False}
        
        duration = self.pause_state.get_pause_duration()
        is_expired = self.pause_state.is_pause_expired()
        
        return {
            "is_paused": True,
            "duration_seconds": duration,
            "max_duration_seconds": self.pause_state.max_pause_seconds,
            "is_expired": is_expired,
            "remaining_seconds": max(0, self.pause_state.max_pause_seconds - duration)
        }

    def get_progress_indicator(self, current_stage: ExperienceState, 
                              completed_stages: list[ExperienceState]) -> dict:
        """
        Get progress indicator for current position in experience.
        
        Args:
            current_stage: Current experience state
            completed_stages: List of completed stages
            
        Returns:
            Progress indicator data
        """
        # Define all trial stages in order
        all_stages = [
            ExperienceState.HOOK_SCENE,
            ExperienceState.CHARGE_READING,
            ExperienceState.PROSECUTION_OPENING,
            ExperienceState.DEFENCE_OPENING,
            ExperienceState.EVIDENCE_PRESENTATION,
            ExperienceState.CROSS_EXAMINATION,
            ExperienceState.PROSECUTION_CLOSING,
            ExperienceState.DEFENCE_CLOSING,
            ExperienceState.JUDGE_SUMMING_UP,
            ExperienceState.JURY_DELIBERATION,
            ExperienceState.ANONYMOUS_VOTE,
            ExperienceState.DUAL_REVEAL,
            ExperienceState.COMPLETED
        ]
        
        # Calculate progress
        total_stages = len(all_stages)  # NOT_STARTED is already excluded from list
        current_index = all_stages.index(current_stage) if current_stage in all_stages else 0
        completed_count = len(completed_stages)

        if current_stage == ExperienceState.COMPLETED:
            progress_percentage = 100.0
        else:
            progress_percentage = (current_index / total_stages) * 100
        
        return {
            "current_stage": current_stage.value,
            "current_stage_name": self._get_stage_display_name(current_stage),
            "completed_stages": [s.value for s in completed_stages],
            "total_stages": total_stages,
            "completed_count": completed_count,
            "progress_percentage": round(progress_percentage, 1),
            "is_complete": current_stage == ExperienceState.COMPLETED
        }

    def _get_stage_display_name(self, stage: ExperienceState) -> str:
        """Get human-readable stage name."""
        display_names = {
            ExperienceState.HOOK_SCENE: "Opening Scene",
            ExperienceState.CHARGE_READING: "Charge Reading",
            ExperienceState.PROSECUTION_OPENING: "Prosecution Opening",
            ExperienceState.DEFENCE_OPENING: "Defence Opening",
            ExperienceState.EVIDENCE_PRESENTATION: "Evidence Presentation",
            ExperienceState.CROSS_EXAMINATION: "Cross-Examination",
            ExperienceState.PROSECUTION_CLOSING: "Prosecution Closing",
            ExperienceState.DEFENCE_CLOSING: "Defence Closing",
            ExperienceState.JUDGE_SUMMING_UP: "Judge's Summing Up",
            ExperienceState.JURY_DELIBERATION: "Jury Deliberation",
            ExperienceState.ANONYMOUS_VOTE: "Voting",
            ExperienceState.DUAL_REVEAL: "Verdict Reveal",
            ExperienceState.COMPLETED: "Complete"
        }
        return display_names.get(stage, stage.value)

    def calculate_total_target_duration(self) -> int:
        """
        Calculate total target duration for complete experience.
        
        Returns:
            Total duration in seconds (target: ~900 seconds / 15 minutes)
        """
        return sum(timing.target_duration for timing in self.STAGE_TIMINGS.values())
