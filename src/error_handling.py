"""Error handling and recovery infrastructure for VERITAS."""

import logging
from datetime import datetime
from typing import Optional, Literal, Any
from pydantic import BaseModel, Field, ConfigDict

from state_machine import ExperienceState


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('veritas')


class ErrorLog(BaseModel):
    """Structured error log entry."""
    model_config = ConfigDict(populate_by_name=True)
    
    timestamp: datetime
    session_id: str = Field(alias="sessionId")
    user_id: str = Field(alias="userId")  # Anonymized
    error_type: str = Field(alias="errorType")
    component: str
    severity: Literal["low", "medium", "high", "critical"]
    context: dict = Field(default_factory=dict)
    message: str
    stack_trace: Optional[str] = Field(default=None, alias="stackTrace")


class FallbackResponse(BaseModel):
    """Fallback response for component failures."""
    model_config = ConfigDict(populate_by_name=True)
    
    component: str
    fallback_type: str = Field(alias="fallbackType")
    content: Any
    is_fallback: bool = Field(default=True, alias="isFallback")


class ErrorHandler:
    """
    Central error handling and recovery system.
    
    Provides error logging, fallback responses, graceful degradation,
    and recovery strategies.
    """

    def __init__(self, session_id: str, user_id: str):
        """
        Initialize error handler.
        
        Args:
            session_id: Current session ID
            user_id: Anonymized user ID
        """
        self.session_id = session_id
        self.user_id = user_id
        self.error_count = 0
        self.critical_error_count = 0
        self.degraded_mode = False

    def log_error(self, error_type: str, component: str, severity: str,
                  message: str, context: dict = None, stack_trace: str = None) -> None:
        """
        Log error without interrupting user experience.
        
        Args:
            error_type: Type of error
            component: Component where error occurred
            severity: Error severity level
            message: Error message
            context: Additional context
            stack_trace: Stack trace if available
        """
        error_log = ErrorLog(
            timestamp=datetime.now(),
            sessionId=self.session_id,
            userId=self.user_id,
            errorType=error_type,
            component=component,
            severity=severity,
            context=context or {},
            message=message,
            stackTrace=stack_trace
        )
        
        # Log to system logger
        log_message = f"[{severity.upper()}] {component}: {message}"
        
        if severity == "critical":
            logger.critical(log_message, extra={"error_log": error_log.model_dump()})
            self.critical_error_count += 1
        elif severity == "high":
            logger.error(log_message, extra={"error_log": error_log.model_dump()})
        elif severity == "medium":
            logger.warning(log_message, extra={"error_log": error_log.model_dump()})
        else:
            logger.info(log_message, extra={"error_log": error_log.model_dump()})
        
        self.error_count += 1

    def handle_agent_timeout(self, agent_role: str, stage: ExperienceState) -> FallbackResponse:
        """
        Handle AI agent timeout with fallback response.
        
        Args:
            agent_role: Role of the timed-out agent
            stage: Current trial stage
            
        Returns:
            Fallback response
        """
        self.log_error(
            error_type="agent_timeout",
            component=f"trial_agent_{agent_role}",
            severity="medium",
            message=f"Agent {agent_role} timed out during {stage.value}",
            context={"agent_role": agent_role, "stage": stage.value}
        )
        
        # Return generic fallback based on role and stage
        fallback_content = self._get_agent_fallback(agent_role, stage)
        
        return FallbackResponse(
            component=f"trial_agent_{agent_role}",
            fallbackType="agent_timeout",
            content=fallback_content
        )

    def _get_agent_fallback(self, agent_role: str, stage: ExperienceState) -> str:
        """Get fallback content for agent."""
        fallbacks = {
            "prosecution": "The prosecution presents their case based on the evidence.",
            "defence": "The defence challenges the prosecution's interpretation of the evidence.",
            "judge": "The judge provides legal guidance to the jury.",
            "clerk": "The clerk reads the formal charges.",
            "fact_checker": "A factual clarification is noted."
        }
        return fallbacks.get(agent_role, f"[{agent_role} statement]")

    def handle_superbox_failure(self) -> FallbackResponse:
        """
        Handle SuperBox loading failure with text-only mode.
        
        Returns:
            Fallback response with text alternatives
        """
        self.log_error(
            error_type="superbox_failure",
            component="superbox",
            severity="medium",
            message="SuperBox failed to load, switching to text-only mode",
            context={"degraded_mode": True}
        )
        
        self.degraded_mode = True
        
        return FallbackResponse(
            component="superbox",
            fallbackType="text_only_mode",
            content={
                "mode": "text_only",
                "message": "Visual content unavailable. Proceeding with text descriptions."
            }
        )

    def handle_reasoning_evaluation_failure(self) -> FallbackResponse:
        """
        Handle reasoning evaluation failure by isolating it.
        
        Returns:
            Fallback response indicating evaluation unavailable
        """
        self.log_error(
            error_type="reasoning_evaluation_failure",
            component="reasoning_evaluator",
            severity="medium",
            message="Reasoning evaluation failed, proceeding without assessment",
            context={"isolated": True}
        )
        
        return FallbackResponse(
            component="reasoning_evaluator",
            fallbackType="evaluation_unavailable",
            content={
                "message": "Reasoning assessment unavailable. Verdict and truth reveal will still be shown.",
                "show_verdict": True,
                "show_reasoning": False
            }
        )

    def handle_state_persistence_failure(self) -> FallbackResponse:
        """
        Handle state persistence failure.
        
        Returns:
            Fallback response with warning
        """
        self.log_error(
            error_type="state_persistence_failure",
            component="session_store",
            severity="high",
            message="Failed to persist session state",
            context={"in_memory_only": True}
        )
        
        return FallbackResponse(
            component="session_store",
            fallbackType="in_memory_only",
            content={
                "warning": "Progress may not be saved if you disconnect.",
                "continue_in_memory": True
            }
        )

    def handle_invalid_state_transition(self, from_state: ExperienceState, 
                                       to_state: ExperienceState) -> FallbackResponse:
        """
        Handle invalid state transition attempt.
        
        Args:
            from_state: Current state
            to_state: Attempted target state
            
        Returns:
            Fallback response rejecting transition
        """
        self.log_error(
            error_type="invalid_state_transition",
            component="state_machine",
            severity="medium",
            message=f"Invalid transition from {from_state.value} to {to_state.value}",
            context={"from_state": from_state.value, "to_state": to_state.value}
        )
        
        return FallbackResponse(
            component="state_machine",
            fallbackType="transition_rejected",
            content={
                "message": "Invalid stage transition. Remaining in current stage.",
                "current_state": from_state.value
            }
        )

    def handle_critical_failure(self, component: str, error_message: str,
                               last_completed_stage: Optional[ExperienceState] = None) -> dict:
        """
        Handle critical failure with restart offer.
        
        Args:
            component: Component that failed
            error_message: Error description
            last_completed_stage: Last successfully completed stage
            
        Returns:
            Recovery options for user
        """
        self.log_error(
            error_type="critical_failure",
            component=component,
            severity="critical",
            message=error_message,
            context={"last_completed_stage": last_completed_stage.value if last_completed_stage else None}
        )
        
        return {
            "critical_failure": True,
            "component": component,
            "message": "A critical error occurred. We apologize for the interruption.",
            "options": {
                "restart_from_checkpoint": {
                    "available": last_completed_stage is not None,
                    "stage": last_completed_stage.value if last_completed_stage else None,
                    "description": f"Restart from {last_completed_stage.value if last_completed_stage else 'beginning'}"
                },
                "restart_from_beginning": {
                    "available": True,
                    "description": "Start the experience from the beginning"
                },
                "exit": {
                    "available": True,
                    "description": "Exit the experience"
                }
            }
        }

    def should_trigger_alert(self) -> bool:
        """
        Check if error thresholds warrant alerting.
        
        Returns:
            True if alert should be triggered
        """
        # Alert on critical errors
        if self.critical_error_count >= 3:
            return True
        
        # Alert on high error rate
        if self.error_count >= 10:
            return True
        
        return False

    def get_error_summary(self) -> dict:
        """
        Get summary of errors for this session.
        
        Returns:
            Error summary data
        """
        return {
            "session_id": self.session_id,
            "total_errors": self.error_count,
            "critical_errors": self.critical_error_count,
            "degraded_mode": self.degraded_mode,
            "alert_triggered": self.should_trigger_alert()
        }


class StatePreservation:
    """
    State preservation and recovery system.
    
    Handles auto-save, checkpointing, and recovery windows.
    """

    def __init__(self, session_store):
        """
        Initialize state preservation.
        
        Args:
            session_store: SessionStore instance
        """
        self.session_store = session_store
        self.last_save_time: Optional[datetime] = None
        self.auto_save_interval_seconds = 30

    def should_auto_save(self) -> bool:
        """
        Check if auto-save should be triggered.
        
        Returns:
            True if auto-save is due
        """
        if self.last_save_time is None:
            return True
        
        elapsed = (datetime.now() - self.last_save_time).total_seconds()
        return elapsed >= self.auto_save_interval_seconds

    def auto_save(self, session) -> bool:
        """
        Perform auto-save if due.
        
        Args:
            session: UserSession to save
            
        Returns:
            True if saved, False if not due or failed
        """
        if not self.should_auto_save():
            return False
        
        try:
            self.session_store.save_progress(session)
            self.last_save_time = datetime.now()
            return True
        except Exception as e:
            logger.error(f"Auto-save failed: {e}")
            return False

    def create_checkpoint(self, session, checkpoint_name: str) -> bool:
        """
        Create a checkpoint before critical operations.
        
        Args:
            session: UserSession to checkpoint
            checkpoint_name: Name for the checkpoint
            
        Returns:
            True if successful
        """
        try:
            # Save with checkpoint metadata
            session.metadata.pause_count += 1  # Use as checkpoint counter
            self.session_store.save_progress(session)
            logger.info(f"Checkpoint created: {checkpoint_name}")
            return True
        except Exception as e:
            logger.error(f"Checkpoint creation failed: {e}")
            return False
