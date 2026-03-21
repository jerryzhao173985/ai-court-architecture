"""Trial layer agent orchestration for VERITAS courtroom experience."""

from datetime import datetime
from typing import Optional, Literal
import logging
from pydantic import BaseModel, Field, ConfigDict

from models import CaseContent, EvidenceItem
from state_machine import ExperienceState
from llm_service import LLMService

logger = logging.getLogger("veritas")


class TrialAgent(BaseModel):
    """Configuration for a trial layer AI agent."""
    model_config = ConfigDict(populate_by_name=True)
    
    role: Literal["clerk", "prosecution", "defence", "fact_checker", "judge"]
    system_prompt: str = Field(alias="systemPrompt")
    character_limit: int = Field(alias="characterLimit")
    response_timeout: int = Field(alias="responseTimeout")  # milliseconds


class AgentResponse(BaseModel):
    """Response from a trial agent."""
    model_config = ConfigDict(populate_by_name=True)
    
    agent_role: str = Field(alias="agentRole")
    content: str
    timestamp: datetime
    metadata: dict = Field(default_factory=dict)


class FactCheckResult(BaseModel):
    """Result of fact checking a statement."""
    model_config = ConfigDict(populate_by_name=True)
    
    is_contradiction: bool = Field(alias="isContradiction")
    contradicting_evidence: Optional[str] = Field(default=None, alias="contradictingEvidence")
    correction: Optional[str] = None


class TrialOrchestrator:
    """
    Coordinates the 5 trial layer AI agents through Crown Court procedure.
    
    Manages agent initialization, stage execution, fact checking, and
    fallback responses for agent failures.
    """

    def __init__(self, llm_service: Optional[LLMService] = None):
        """Initialize trial orchestrator.
        
        Args:
            llm_service: LLM service for generating agent responses (optional for testing)
        """
        self.agents: dict[str, TrialAgent] = {}
        self.case_content: Optional[CaseContent] = None
        self.fact_check_count = 0
        self.max_fact_checks = 3
        self.llm_service = llm_service

    def initialize_agents(self, case_content: CaseContent) -> None:
        """
        Initialize all trial agents with case context.
        
        Args:
            case_content: The case content to provide as context
        """
        self.case_content = case_content
        self.fact_check_count = 0
        
        # Create agent configurations with system prompts
        self.agents = {
            "clerk": TrialAgent(
                role="clerk",
                systemPrompt=self._get_clerk_prompt(case_content),
                characterLimit=500,
                responseTimeout=30000
            ),
            "prosecution": TrialAgent(
                role="prosecution",
                systemPrompt=self._get_prosecution_prompt(case_content),
                characterLimit=1500,
                responseTimeout=30000
            ),
            "defence": TrialAgent(
                role="defence",
                systemPrompt=self._get_defence_prompt(case_content),
                characterLimit=1500,
                responseTimeout=30000
            ),
            "fact_checker": TrialAgent(
                role="fact_checker",
                systemPrompt=self._get_fact_checker_prompt(case_content),
                characterLimit=300,
                responseTimeout=10000
            ),
            "judge": TrialAgent(
                role="judge",
                systemPrompt=self._get_judge_prompt(case_content),
                characterLimit=2000,
                responseTimeout=30000
            )
        }

    def _get_clerk_prompt(self, case_content: CaseContent) -> str:
        """Generate system prompt for clerk agent."""
        return f"""You are the Clerk of the Court in a British Crown Court trial.

Case: {case_content.title}
Charge: {case_content.narrative.charge_text}

Your role is to:
- Read formal charges and procedural announcements
- Maintain courtroom decorum
- Provide clear, formal guidance
- Use proper Crown Court terminology

Be concise, formal, and authoritative."""

    def _get_prosecution_prompt(self, case_content: CaseContent) -> str:
        """Generate system prompt for prosecution agent."""
        evidence_summary = "\n".join([f"- {e.title}: {e.description}" for e in case_content.evidence])
        
        return f"""You are the Crown Prosecution barrister in a British Crown Court murder trial.

Case: {case_content.title}
Defendant: {case_content.narrative.defendant_profile.name}
Victim: {case_content.narrative.victim_profile.name}

Evidence available:
{evidence_summary}

Your role is to:
- Present the case for the Crown
- Argue that the defendant is guilty beyond reasonable doubt
- Reference evidence that supports guilt
- Cross-examine defence witnesses
- Deliver compelling opening and closing speeches

Be persuasive, professional, and focused on proving guilt. Only reference evidence that has been presented."""

    def _get_defence_prompt(self, case_content: CaseContent) -> str:
        """Generate system prompt for defence agent."""
        evidence_summary = "\n".join([f"- {e.title}: {e.description}" for e in case_content.evidence])
        
        return f"""You are the Defence barrister in a British Crown Court murder trial.

Case: {case_content.title}
Defendant: {case_content.narrative.defendant_profile.name}
Victim: {case_content.narrative.victim_profile.name}

Evidence available:
{evidence_summary}

Your role is to:
- Defend your client vigorously
- Create reasonable doubt
- Challenge prosecution evidence
- Present alternative interpretations
- Deliver compelling opening and closing speeches

Be persuasive, professional, and focused on creating doubt. Only reference evidence that has been presented."""

    def _get_fact_checker_prompt(self, case_content: CaseContent) -> str:
        """Generate system prompt for fact checker agent."""
        return f"""You are the Fact Checker in a British Crown Court trial.

Your role is to:
- Monitor statements from prosecution and defence
- Identify factual contradictions with case evidence
- Intervene briefly and precisely when errors occur
- Cite the specific evidence that contradicts the misstatement

Be concise, neutral, and factual. Only intervene on clear factual errors, not opinions."""

    def _get_judge_prompt(self, case_content: CaseContent) -> str:
        """Generate system prompt for judge agent."""
        return f"""You are the presiding Judge in a British Crown Court murder trial.

Case: {case_content.title}

Your role is to:
- Maintain courtroom order
- Provide legal guidance to the jury
- Summarize key evidence from both sides fairly
- Explain burden of proof and reasonable doubt
- Remain impartial - do not express opinion on verdict

Be authoritative, fair, and clear in your instructions."""

    async def execute_stage(self, stage: ExperienceState) -> list[AgentResponse]:
        """
        Execute agents for the current trial stage.
        
        Args:
            stage: The current experience state/trial stage
            
        Returns:
            List of agent responses for this stage
        """
        responses = []
        
        # Determine which agents speak in this stage
        if stage == ExperienceState.CHARGE_READING:
            responses.append(await self._generate_agent_response("clerk", stage))
        
        elif stage == ExperienceState.PROSECUTION_OPENING:
            responses.append(await self._generate_agent_response("prosecution", stage))
        
        elif stage == ExperienceState.DEFENCE_OPENING:
            responses.append(await self._generate_agent_response("defence", stage))
        
        elif stage == ExperienceState.EVIDENCE_PRESENTATION:
            # Both sides present evidence
            responses.append(await self._generate_agent_response("prosecution", stage))
            responses.append(await self._generate_agent_response("defence", stage))
        
        elif stage == ExperienceState.CROSS_EXAMINATION:
            # Both sides cross-examine
            responses.append(await self._generate_agent_response("prosecution", stage))
            responses.append(await self._generate_agent_response("defence", stage))
        
        elif stage == ExperienceState.PROSECUTION_CLOSING:
            responses.append(await self._generate_agent_response("prosecution", stage))
        
        elif stage == ExperienceState.DEFENCE_CLOSING:
            responses.append(await self._generate_agent_response("defence", stage))
        
        elif stage == ExperienceState.JUDGE_SUMMING_UP:
            responses.append(await self._generate_judge_summary())
        
        return responses

    async def _generate_agent_response(self, agent_role: str, stage: ExperienceState) -> AgentResponse:
        """
        Generate response from an agent using LLM.
        
        Args:
            agent_role: The role of the agent
            stage: The current stage
            
        Returns:
            Agent response
        """
        agent = self.agents.get(agent_role)
        if not agent:
            return self.handle_agent_failure(agent_role, stage)
        
        # Generate user prompt based on stage
        user_prompt = self._get_stage_prompt(agent_role, stage)
        fallback = self._get_fallback_response(agent_role, stage)
        
        # Use LLM service if available, otherwise use fallback
        if self.llm_service:
            try:
                content, used_fallback = await self.llm_service.generate_with_fallback(
                    system_prompt=agent.system_prompt,
                    user_prompt=user_prompt,
                    fallback_text=fallback,
                    max_tokens=agent.character_limit,
                    timeout=agent.response_timeout // 1000  # Convert ms to seconds
                )
                
                return AgentResponse(
                    agent_role=agent_role,
                    content=content,
                    timestamp=datetime.now(),
                    metadata={"stage": stage.value, "used_fallback": used_fallback}
                )
            except Exception as e:
                logger.error(f"Agent response generation failed: {e}")
                return self.handle_agent_failure(agent_role, stage)
        else:
            # No LLM service, use fallback
            return AgentResponse(
                agent_role=agent_role,
                content=fallback,
                timestamp=datetime.now(),
                metadata={"stage": stage.value, "fallback": True}
            )
    
    def _get_stage_prompt(self, agent_role: str, stage: ExperienceState) -> str:
        """Get user prompt for agent based on stage."""
        prompts = {
            ("clerk", ExperienceState.CHARGE_READING): 
                "Read the formal charge to the court.",
            
            ("prosecution", ExperienceState.PROSECUTION_OPENING):
                "Deliver your opening statement to the jury. Outline the case you will prove.",
            
            ("defence", ExperienceState.DEFENCE_OPENING):
                "Deliver your opening statement to the jury. Outline your defence strategy.",
            
            ("prosecution", ExperienceState.EVIDENCE_PRESENTATION):
                "Present the key evidence that supports the prosecution's case.",
            
            ("defence", ExperienceState.EVIDENCE_PRESENTATION):
                "Present evidence and arguments that support the defence.",
            
            ("prosecution", ExperienceState.CROSS_EXAMINATION):
                "Cross-examine the defence's evidence and witnesses.",
            
            ("defence", ExperienceState.CROSS_EXAMINATION):
                "Cross-examine the prosecution's evidence and witnesses.",
            
            ("prosecution", ExperienceState.PROSECUTION_CLOSING):
                "Deliver your closing speech. Summarize why the jury should find the defendant guilty.",
            
            ("defence", ExperienceState.DEFENCE_CLOSING):
                "Deliver your closing speech. Summarize why the jury should find the defendant not guilty.",
            
            ("judge", ExperienceState.JUDGE_SUMMING_UP):
                "Sum up the case for the jury. Summarize evidence from both sides fairly and provide legal instructions on burden of proof and reasonable doubt. Do not express an opinion on the verdict."
        }
        
        return prompts.get((agent_role, stage), f"Provide your statement for {stage.value}.")

    async def _generate_judge_summary(self) -> AgentResponse:
        """Generate judge's summing up."""
        return await self._generate_agent_response("judge", ExperienceState.JUDGE_SUMMING_UP)

    def check_fact_accuracy(self, statement: str, speaker: str, stage: ExperienceState) -> Optional[FactCheckResult]:
        """
        Check if a statement contradicts case facts.
        
        Args:
            statement: The statement to check
            speaker: Who made the statement ("prosecution" or "defence")
            stage: Current trial stage
            
        Returns:
            FactCheckResult if contradiction found and intervention allowed, None otherwise
        """
        # Only check during evidence presentation and cross-examination
        if stage not in [ExperienceState.EVIDENCE_PRESENTATION, ExperienceState.CROSS_EXAMINATION]:
            return None
        
        # Check intervention limit
        if self.fact_check_count >= self.max_fact_checks:
            return None
        
        # TODO: Replace with actual fact checking logic using LLM
        # For now, return no contradiction
        return FactCheckResult(is_contradiction=False)

    def trigger_fact_check_intervention(self, result: FactCheckResult) -> AgentResponse:
        """
        Trigger fact checker intervention.
        
        Args:
            result: The fact check result with contradiction details
            
        Returns:
            Fact checker agent response
        """
        self.fact_check_count += 1
        
        content = f"I must intervene. {result.correction} The evidence shows: {result.contradicting_evidence}"
        
        return AgentResponse(
            agent_role="fact_checker",
            content=content,
            timestamp=datetime.now(),
            metadata={"intervention_number": self.fact_check_count}
        )

    def generate_judge_summary(self) -> str:
        """
        Generate judge's summing up with evidence summary and legal instructions.
        
        Returns:
            Judge's summing up text
        """
        if not self.case_content:
            return self._get_fallback_response("judge", ExperienceState.JUDGE_SUMMING_UP)
        
        # TODO: Replace with actual LLM generation
        # For now, return structured fallback
        summary = f"""Members of the jury, you have heard the evidence in the case of {self.case_content.title}.

The prosecution has presented evidence suggesting the defendant had motive, means, and opportunity. The defence has raised questions about the reliability and interpretation of this evidence.

I must remind you of the fundamental principles of British criminal law:

1. The burden of proof rests entirely with the prosecution. The defendant does not have to prove their innocence.

2. You must be satisfied of guilt beyond reasonable doubt. If you have a reasonable doubt, you must find the defendant not guilty.

3. You must consider only the evidence presented in this courtroom. Put aside any sympathy or prejudice.

Consider all the evidence carefully. You may now retire to deliberate."""
        
        return summary

    def handle_agent_failure(self, agent_role: str, stage: ExperienceState) -> AgentResponse:
        """
        Handle agent failure with fallback response.
        
        Args:
            agent_role: The role of the failed agent
            stage: The current stage
            
        Returns:
            Fallback agent response
        """
        content = self._get_fallback_response(agent_role, stage)
        
        return AgentResponse(
            agent_role=agent_role,
            content=content,
            timestamp=datetime.now(),
            metadata={"fallback": True, "stage": stage.value}
        )

    def _get_fallback_response(self, agent_role: str, stage: ExperienceState) -> str:
        """Get fallback response for an agent and stage."""
        fallbacks = {
            ("clerk", ExperienceState.CHARGE_READING): 
                "The defendant is charged with murder. How do you plead?",
            
            ("prosecution", ExperienceState.PROSECUTION_OPENING):
                "Members of the jury, the Crown will prove beyond reasonable doubt that the defendant committed this crime.",
            
            ("defence", ExperienceState.DEFENCE_OPENING):
                "Members of the jury, the defence will show that the prosecution's case is built on speculation, not facts.",
            
            ("prosecution", ExperienceState.PROSECUTION_CLOSING):
                "The evidence clearly demonstrates the defendant's guilt. We ask you to return a guilty verdict.",
            
            ("defence", ExperienceState.DEFENCE_CLOSING):
                "The prosecution has failed to prove guilt beyond reasonable doubt. You must find the defendant not guilty.",
            
            ("judge", ExperienceState.JUDGE_SUMMING_UP):
                "Members of the jury, you must consider all evidence and apply the law. The burden of proof rests with the prosecution."
        }
        
        return fallbacks.get((agent_role, stage), f"[{agent_role} statement for {stage.value}]")
