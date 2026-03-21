"""Trial layer agent orchestration for VERITAS courtroom experience."""

from datetime import datetime
from typing import Optional, Literal
import logging
from pydantic import BaseModel, Field, ConfigDict

from models import CaseContent, EvidenceItem
from state_machine import ExperienceState
from llm_service import LLMService
from complexity_analyzer import CaseComplexityAnalyzer, ComplexityLevel

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
        self.complexity_analyzer = CaseComplexityAnalyzer()
        self.complexity_level: Optional[ComplexityLevel] = None

    def initialize_agents(self, case_content: CaseContent) -> None:
        """
        Initialize all trial agents with case context.
        
        Args:
            case_content: The case content to provide as context
        """
        self.case_content = case_content
        self.fact_check_count = 0
        
        # Analyze case complexity
        self.complexity_level = self.complexity_analyzer.analyze_complexity(case_content)
        logger.info(f"Case complexity: {self.complexity_level.level}")
        
        # Create agent configurations with system prompts adjusted for complexity
        self.agents = {
            "clerk": TrialAgent(
                role="clerk",
                systemPrompt=self._get_clerk_prompt(case_content),
                characterLimit=self._adjust_char_limit(500),
                responseTimeout=30000
            ),
            "prosecution": TrialAgent(
                role="prosecution",
                systemPrompt=self._get_prosecution_prompt(case_content),
                characterLimit=self._adjust_char_limit(1500),
                responseTimeout=30000
            ),
            "defence": TrialAgent(
                role="defence",
                systemPrompt=self._get_defence_prompt(case_content),
                characterLimit=self._adjust_char_limit(1500),
                responseTimeout=30000
            ),
            "fact_checker": TrialAgent(
                role="fact_checker",
                systemPrompt=self._get_fact_checker_prompt(case_content),
                characterLimit=self._adjust_char_limit(300),
                responseTimeout=10000
            ),
            "judge": TrialAgent(
                role="judge",
                systemPrompt=self._get_judge_prompt(case_content),
                characterLimit=self._adjust_char_limit(2000),
                responseTimeout=30000
            )
        }
    
    def _adjust_char_limit(self, base_limit: int) -> int:
        """Adjust character limit based on case complexity."""
        if self.complexity_level:
            return self.complexity_analyzer.adjust_character_limit(
                base_limit,
                self.complexity_level
            )
        return base_limit

    def _identify_prosecution_strengths(self, case_content: CaseContent) -> str:
        """Identify key prosecution strengths for strategic focus."""
        strengths = []
        
        # Look for motive evidence
        for evidence in case_content.evidence:
            if "motive" in evidence.significance.lower() or "benefit" in evidence.significance.lower():
                strengths.append(f"MOTIVE: {evidence.title} - {evidence.significance}")
        
        # Look for means/opportunity evidence
        for evidence in case_content.evidence:
            if "access" in evidence.significance.lower() or "opportunity" in evidence.significance.lower():
                strengths.append(f"MEANS/OPPORTUNITY: {evidence.title} - {evidence.significance}")
        
        # Look for timeline evidence
        for evidence in case_content.evidence:
            if "time" in evidence.significance.lower() or "scene" in evidence.significance.lower():
                strengths.append(f"PRESENCE: {evidence.title} - {evidence.significance}")
        
        if not strengths:
            strengths.append("Build a comprehensive case using all available evidence")
        
        return "\n".join(strengths)

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
        
        # Extract key prosecution evidence for strategic focus
        prosecution_evidence = [e for e in case_content.evidence if e.presented_by == "prosecution"]
        key_strengths = self._identify_prosecution_strengths(case_content)
        
        # Get complexity guidance
        complexity_guidance = ""
        if self.complexity_level:
            complexity_guidance = self.complexity_analyzer.get_complexity_guidance(self.complexity_level)
        
        return f"""You are the Crown Prosecution barrister in a British Crown Court murder trial.

Case: {case_content.title}
Defendant: {case_content.narrative.defendant_profile.name}
Victim: {case_content.narrative.victim_profile.name}

Evidence available:
{evidence_summary}

STRATEGIC FOCUS - Your strongest arguments:
{key_strengths}

Your role is to:
- Present the case for the Crown with conviction and clarity
- Build a compelling narrative connecting motive, means, and opportunity
- Argue that the defendant is guilty beyond reasonable doubt
- Use the "trilogy of proof" approach: establish motive, demonstrate means, prove opportunity
- Reference evidence that supports guilt in a logical sequence
- Anticipate and preemptively address defence arguments
- Cross-examine defence witnesses to expose inconsistencies
- Deliver compelling opening and closing speeches that tell a coherent story

ARGUMENTATION STRATEGIES:
- Opening: Frame the narrative - "This is a case about trust betrayed and greed that led to murder"
- Evidence presentation: Build your case piece by piece, showing how evidence interconnects
- Cross-examination: Focus on timeline inconsistencies and access to means
- Closing: Remind jury of the weight of evidence and that coincidences pile up to proof

TONE: Authoritative but not aggressive. Confident but respectful of the court. Let the evidence speak, but guide the jury to see the connections.
{complexity_guidance}

CRITICAL: Only reference evidence that has been presented in earlier stages. Do not reveal information prematurely."""

    def _identify_defence_strengths(self, case_content: CaseContent) -> str:
        """Identify key defence strengths for creating reasonable doubt."""
        strengths = []
        
        # Look for timeline inconsistencies
        for evidence in case_content.evidence:
            if "time" in evidence.significance.lower() or "alibi" in evidence.significance.lower():
                strengths.append(f"TIMELINE DOUBT: {evidence.title} - {evidence.significance}")
        
        # Look for missing evidence or gaps
        for evidence in case_content.evidence:
            if "missing" in evidence.significance.lower() or "absence" in evidence.significance.lower() or "no evidence" in evidence.significance.lower():
                strengths.append(f"MISSING EVIDENCE: {evidence.title} - {evidence.significance}")
        
        # Look for alternative explanations
        for evidence in case_content.evidence:
            if "alternative" in evidence.significance.lower() or "could" in evidence.significance.lower() or "other" in evidence.significance.lower():
                strengths.append(f"ALTERNATIVE EXPLANATION: {evidence.title} - {evidence.significance}")
        
        # Look for witness credibility issues
        for evidence in case_content.evidence:
            if "witness" in evidence.title.lower() or "testimony" in evidence.title.lower():
                strengths.append(f"WITNESS SCRUTINY: {evidence.title} - Question reliability and bias")
        
        if not strengths:
            strengths.append("Challenge prosecution's burden of proof and highlight gaps in their case")
        
        return "\n".join(strengths)

    def _get_defence_prompt(self, case_content: CaseContent) -> str:
        """Generate system prompt for defence agent."""
        evidence_summary = "\n".join([f"- {e.title}: {e.description}" for e in case_content.evidence])
        
        # Extract key defence evidence for strategic focus
        defence_evidence = [e for e in case_content.evidence if e.presented_by == "defence"]
        key_strengths = self._identify_defence_strengths(case_content)
        
        # Get complexity guidance
        complexity_guidance = ""
        if self.complexity_level:
            complexity_guidance = self.complexity_analyzer.get_complexity_guidance(self.complexity_level)
        
        return f"""You are the Defence barrister in a British Crown Court murder trial.

Case: {case_content.title}
Defendant: {case_content.narrative.defendant_profile.name}
Victim: {case_content.narrative.victim_profile.name}

Evidence available:
{evidence_summary}

STRATEGIC FOCUS - Your strongest defensive arguments:
{key_strengths}

Your role is to:
- Defend your client vigorously and create reasonable doubt
- Challenge the prosecution's narrative at every weak point
- Present alternative interpretations of the evidence
- Highlight gaps, inconsistencies, and missing evidence
- Emphasize that the burden of proof rests entirely with the prosecution
- Remind the jury that "possible" is not the same as "proven beyond reasonable doubt"
- Cross-examine prosecution witnesses to expose bias, uncertainty, or alternative explanations
- Deliver compelling opening and closing speeches that plant seeds of doubt

DEFENSIVE STRATEGIES:
- Opening: Frame the case as built on speculation, not facts - "The prosecution will ask you to fill gaps with assumptions"
- Evidence presentation: Highlight what's missing - "Where are the fingerprints? Where is the direct evidence?"
- Cross-examination: Attack timeline precision, question witness certainty, offer alternative scenarios
- Closing: Remind jury of reasonable doubt standard - "If you're not sure, you must acquit"

REASONABLE DOUBT TECHNIQUES:
1. **Timeline Challenges**: "The prosecution's timeline requires everything to happen in an impossibly tight window"
2. **Missing Evidence**: "If this really happened as they claim, where is the physical evidence?"
3. **Alternative Explanations**: "This evidence is equally consistent with [alternative scenario]"
4. **Witness Credibility**: "Can we really rely on testimony from someone who [bias/uncertainty]?"
5. **Burden of Proof**: "The prosecution must prove guilt beyond reasonable doubt - they haven't met that burden"
6. **Presumption of Innocence**: "My client doesn't have to prove innocence - the prosecution must prove guilt"

TONE: Confident but not dismissive. Respectful of the court but forceful in defending your client. Plant doubt without appearing desperate. Let the gaps in the prosecution's case speak for themselves.
{complexity_guidance}

CRITICAL: Only reference evidence that has been presented in earlier stages. Do not reveal information prematurely."""

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
        # Get complexity guidance
        complexity_guidance = ""
        if self.complexity_level:
            complexity_guidance = self.complexity_analyzer.get_complexity_guidance(self.complexity_level)
        
        return f"""You are the presiding Judge in a British Crown Court murder trial.

Case: {case_content.title}

Your role is to:
- Maintain courtroom order
- Provide legal guidance to the jury
- Summarize key evidence from both sides fairly
- Explain burden of proof and reasonable doubt
- Remain impartial - do not express opinion on verdict

Be authoritative, fair, and clear in your instructions.
{complexity_guidance}"""

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
            prosecution_response = await self._generate_agent_response("prosecution", stage)
            responses.append(prosecution_response)
            
            # Check prosecution statement for contradictions
            fact_check = await self.check_fact_accuracy(
                statement=prosecution_response.content,
                speaker="prosecution",
                stage=stage
            )
            if fact_check and fact_check.is_contradiction:
                intervention = self.trigger_fact_check_intervention(fact_check)
                responses.append(intervention)
            
            defence_response = await self._generate_agent_response("defence", stage)
            responses.append(defence_response)
            
            # Check defence statement for contradictions
            fact_check = await self.check_fact_accuracy(
                statement=defence_response.content,
                speaker="defence",
                stage=stage
            )
            if fact_check and fact_check.is_contradiction:
                intervention = self.trigger_fact_check_intervention(fact_check)
                responses.append(intervention)
        
        elif stage == ExperienceState.CROSS_EXAMINATION:
            # Both sides cross-examine
            prosecution_response = await self._generate_agent_response("prosecution", stage)
            responses.append(prosecution_response)
            
            # Check prosecution statement for contradictions
            fact_check = await self.check_fact_accuracy(
                statement=prosecution_response.content,
                speaker="prosecution",
                stage=stage
            )
            if fact_check and fact_check.is_contradiction:
                intervention = self.trigger_fact_check_intervention(fact_check)
                responses.append(intervention)
            
            defence_response = await self._generate_agent_response("defence", stage)
            responses.append(defence_response)
            
            # Check defence statement for contradictions
            fact_check = await self.check_fact_accuracy(
                statement=defence_response.content,
                speaker="defence",
                stage=stage
            )
            if fact_check and fact_check.is_contradiction:
                intervention = self.trigger_fact_check_intervention(fact_check)
                responses.append(intervention)
        
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
                "Deliver your opening statement to the jury. Paint a clear picture of what happened and why the defendant is guilty. Outline the key evidence you will present: motive, means, and opportunity. Make the jury understand the narrative of this case. Be compelling but measured - you're setting the stage for the evidence to come.",
            
            ("defence", ExperienceState.DEFENCE_OPENING):
                "Deliver your opening statement to the jury. Frame this case as built on speculation, not proof. Warn the jury that the prosecution will ask them to fill gaps with assumptions. Preview the weaknesses in their case: timeline inconsistencies, missing physical evidence, alternative explanations. Remind them that the burden of proof rests entirely with the prosecution. Plant the first seeds of reasonable doubt - be confident and clear that the evidence will not meet the standard of proof beyond reasonable doubt.",
            
            ("prosecution", ExperienceState.EVIDENCE_PRESENTATION):
                "Present the key evidence that supports the prosecution's case. Walk through each piece methodically: the forged will establishing motive, the testimony placing the defendant at the scene, the toxicology showing cause of death, and the defendant's access to the means. Connect the dots for the jury - show how these pieces form a complete picture of guilt.",
            
            ("defence", ExperienceState.EVIDENCE_PRESENTATION):
                "Present evidence and arguments that create reasonable doubt. Highlight what's missing: no fingerprints, no witnesses to the actual act, no direct evidence. Present the security log showing the tight timeline - is it really possible? Emphasize the absence of physical evidence linking your client to the crime. Offer alternative explanations: natural causes initially suspected, others with access to the estate, the victim's age and health. Make the jury see that the prosecution's case requires them to assume, not conclude.",
            
            ("prosecution", ExperienceState.CROSS_EXAMINATION):
                "Cross-examine the defence's evidence and witnesses. Challenge the timeline defence - if the security log shows he left at 8:20, how tight is that window really? Question the significance of missing fingerprints - could gloves explain this? Press on the defendant's account - why should we believe someone caught with a forged will? Be incisive but professional.",
            
            ("defence", ExperienceState.CROSS_EXAMINATION):
                "Cross-examine the prosecution's evidence and witnesses. Attack the timeline precision - can the housekeeper really be certain about exact times? Question the toxicology interpretation - couldn't digoxin levels be consistent with prescribed medication? Challenge the motive assumption - discovering a forgery doesn't automatically lead to murder. Expose the lack of direct evidence - no one saw the act, no fingerprints, no weapon. Ask the questions that create doubt: 'How can you be certain?' 'Isn't it possible that...?' 'Where is the proof?' Be methodical and relentless in exposing gaps.",
            
            ("prosecution", ExperienceState.PROSECUTION_CLOSING):
                "Deliver your closing speech. This is your final opportunity to convince the jury. Summarize the overwhelming evidence: the defendant had motive (£500,000 from the forged will), means (access to digoxin), and opportunity (alone with the victim during the critical window). Address the defence's timeline argument - the security log doesn't exonerate him, it places him at the scene. The absence of fingerprints suggests premeditation, not innocence. Remind the jury that when you have motive, means, opportunity, and presence at the scene, that's not coincidence - that's guilt beyond reasonable doubt.",
            
            ("defence", ExperienceState.DEFENCE_CLOSING):
                "Deliver your closing speech. This is your final opportunity to save your client. Remind the jury of the reasonable doubt standard - if they're not sure, they must acquit. Systematically dismantle the prosecution's case: the timeline is impossibly tight, the missing physical evidence is damning to their theory, the motive is speculative (discovering a forgery doesn't prove murder), and alternative explanations exist. Emphasize what the prosecution hasn't proven: no direct evidence, no witnesses, no physical connection to the crime. Ask the jury: 'Are you sure? Are you certain beyond reasonable doubt?' If there's any doubt - and there should be - they must find your client not guilty. The prosecution has failed to meet their burden.",
            
            ("judge", ExperienceState.JUDGE_SUMMING_UP):
                "Sum up the case for the jury. Summarize evidence from both sides fairly and provide legal instructions on burden of proof and reasonable doubt. Do not express an opinion on the verdict."
        }
        
        return prompts.get((agent_role, stage), f"Provide your statement for {stage.value}.")

    async def _generate_judge_summary(self) -> AgentResponse:
        """Generate judge's summing up."""
        return await self._generate_agent_response("judge", ExperienceState.JUDGE_SUMMING_UP)

    async def check_fact_accuracy(self, statement: str, speaker: str, stage: ExperienceState) -> Optional[FactCheckResult]:
        """
        Check if a statement contradicts case facts using LLM analysis.
        
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
        
        # If no LLM service available, cannot perform fact checking
        if not self.llm_service or not self.case_content:
            return FactCheckResult(is_contradiction=False)
        
        # Build evidence context for LLM
        evidence_context = self._build_evidence_context()
        
        # Create system prompt for fact checking
        system_prompt = f"""You are a fact checker in a British Crown Court trial. Your role is to identify factual contradictions between statements and case evidence.

Case Evidence:
{evidence_context}

Analyze the statement and determine if it contradicts any of the case evidence. Only flag clear factual contradictions, not differences in interpretation or opinion.

You MUST respond with ONLY valid JSON in this exact format (no other text):
{{
  "is_contradiction": true,
  "confidence": 0.9,
  "contradicting_evidence": "Evidence Title",
  "correction": "Brief correction"
}}

OR if no contradiction:
{{
  "is_contradiction": false,
  "confidence": 0.95,
  "contradicting_evidence": null,
  "correction": null
}}"""

        user_prompt = f"""Statement by {speaker}: "{statement}"

Does this statement contain any factual contradictions with the case evidence? Consider:
1. Does it misstate facts from evidence items?
2. Does it claim something happened that contradicts the timeline?
3. Does it attribute statements or actions incorrectly?

Only flag clear factual errors, not interpretations or arguments."""

        try:
            # Call LLM with shorter timeout for fact checking
            response = await self.llm_service.generate_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=300,
                temperature=0.1,  # Low temperature for factual analysis
                timeout=10,  # 10 second timeout
                response_format={"type": "json_object"}  # Force JSON output
            )
            
            # Parse JSON response
            import json
            result_data = json.loads(response)
            
            # Apply confidence threshold (0.7 = 70% confidence required)
            confidence_threshold = 0.7
            if result_data.get("is_contradiction", False) and result_data.get("confidence", 0.0) >= confidence_threshold:
                return FactCheckResult(
                    is_contradiction=True,
                    contradicting_evidence=result_data.get("contradicting_evidence"),
                    correction=result_data.get("correction")
                )
            else:
                return FactCheckResult(is_contradiction=False)
                
        except Exception as e:
            logger.warning(f"Fact checking failed: {e}")
            # On error, don't intervene
            return FactCheckResult(is_contradiction=False)
    
    def _build_evidence_context(self) -> str:
        """Build a formatted string of all case evidence for fact checking."""
        if not self.case_content:
            return ""
        
        evidence_lines = []
        for item in self.case_content.evidence:
            evidence_lines.append(f"- {item.title}: {item.description}")
            evidence_lines.append(f"  Significance: {item.significance}")
            evidence_lines.append(f"  Timestamp: {item.timestamp}")
            evidence_lines.append("")
        
        return "\n".join(evidence_lines)

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
        # Get case-specific details if available
        case_title = self.case_content.title if self.case_content else "this case"
        defendant_name = self.case_content.narrative.defendant_profile.name if self.case_content else "the defendant"
        
        fallbacks = {
            ("clerk", ExperienceState.CHARGE_READING): 
                "The defendant is charged with murder. How do you plead?",
            
            ("prosecution", ExperienceState.PROSECUTION_OPENING):
                f"Members of the jury, the Crown will prove beyond reasonable doubt that {defendant_name} committed this crime. The evidence will show motive, means, and opportunity. We ask you to listen carefully to the facts and apply the law.",
            
            ("defence", ExperienceState.DEFENCE_OPENING):
                f"Members of the jury, the prosecution will present a case built on speculation and circumstantial evidence. They will ask you to fill gaps with assumptions. But assumptions are not proof. The burden of proof rests entirely with the prosecution, and they must prove guilt beyond reasonable doubt. As you listen to their case, ask yourself: where is the direct evidence? Where are the witnesses? Where is the proof? The defence will show you that the prosecution's case is built on a foundation of doubt, not certainty.",
            
            ("defence", ExperienceState.EVIDENCE_PRESENTATION):
                f"The prosecution wants you to believe their theory, but look at what's missing. No fingerprints. No witnesses to the actual act. No direct evidence linking {defendant_name} to this crime. The timeline they propose is impossibly tight. Alternative explanations exist that are equally consistent with the evidence. The absence of evidence is itself evidence - evidence that their theory doesn't hold up to scrutiny.",
            
            ("defence", ExperienceState.CROSS_EXAMINATION):
                "The prosecution's case relies on assumptions and speculation. Can the witnesses really be certain about exact times? Couldn't the evidence be interpreted differently? Where is the proof that connects these dots? The prosecution must prove guilt beyond reasonable doubt, and doubt is exactly what their case creates.",
            
            ("defence", ExperienceState.DEFENCE_CLOSING):
                f"Members of the jury, the prosecution has failed to meet their burden. They've presented theories and possibilities, but not proof beyond reasonable doubt. Ask yourselves: are you certain? Can you say with absolute confidence that {defendant_name} committed this crime? If you have any doubt - and the gaps in this case should create doubt - then you must find {defendant_name} not guilty. That is the law, and that is justice.",
            
            ("prosecution", ExperienceState.EVIDENCE_PRESENTATION):
                "The Crown presents evidence that establishes the defendant's guilt. Each piece of evidence connects to form a clear picture of what happened.",
            
            ("prosecution", ExperienceState.CROSS_EXAMINATION):
                "The defence would have you focus on minor details, but the fundamental facts remain: the defendant had motive, means, and opportunity. These are not coincidences.",
            
            ("prosecution", ExperienceState.PROSECUTION_CLOSING):
                f"Members of the jury, the evidence is clear. {defendant_name} had motive, means, and opportunity. When these elements align with the evidence presented, that is proof beyond reasonable doubt. The Crown asks you to return a verdict of guilty.",
            
            ("judge", ExperienceState.JUDGE_SUMMING_UP):
                "Members of the jury, you must consider all evidence and apply the law. The burden of proof rests with the prosecution. If you have reasonable doubt, you must acquit."
        }
        
        # For Blackthorn Hall specifically, use more detailed fallbacks
        if self.case_content and "blackthorn" in self.case_content.case_id.lower():
            fallbacks.update({
                ("defence", ExperienceState.DEFENCE_OPENING):
                    "Members of the jury, the prosecution will tell you a compelling story about greed and murder. But stories are not evidence. They will point to a forged will and claim it's a motive for murder. But discovering a forgery doesn't make someone a murderer. They will present a timeline that requires everything to happen in an impossibly tight window. They will ask you to ignore the absence of fingerprints, the lack of witnesses, the missing direct evidence. The defence will show you that this case is built on assumptions, not proof. And when the foundation is doubt, the verdict must be not guilty.",
                
                ("defence", ExperienceState.EVIDENCE_PRESENTATION):
                    "Look at what the prosecution hasn't shown you. No fingerprints on the medicine cabinet. No witnesses to the alleged poisoning. The security log shows Marcus Ashford left at 8:20 PM - giving him barely minutes to commit this elaborate crime. The toxicology report shows digoxin, but Lord Blackthorn was elderly with a heart condition - couldn't this be from prescribed medication? The prosecution wants you to see a murder, but the evidence is equally consistent with natural causes or another explanation entirely.",
                
                ("defence", ExperienceState.CROSS_EXAMINATION):
                    "The prosecution's timeline falls apart under scrutiny. The housekeeper claims the confrontation was at 8:00 PM, and the security log shows Marcus leaving at 8:20 PM. In twenty minutes, he supposedly administered poison, cleaned up all evidence, left no fingerprints, and departed calmly? That's not reasonable - it's impossible. And the forged will? Yes, it's a crime, but it's not murder. The prosecution wants you to leap from one crime to another without evidence. That's not how justice works.",
                
                ("defence", ExperienceState.DEFENCE_CLOSING):
                    "Members of the jury, let's be clear about what the prosecution has proven: Marcus Ashford forged a will. That's a crime, and it's wrong. But they haven't proven murder. They've shown you motive - but motive isn't murder. They've shown you opportunity - but a twenty-minute window to commit an elaborate poisoning with no physical evidence? That strains credibility. They've shown you means - but where's the proof he actually used those means? No fingerprints. No witnesses. No direct evidence. The prosecution's case requires you to assume, to speculate, to fill gaps. But the law requires proof beyond reasonable doubt. If you're not certain - and how can you be with all these gaps? - you must find Marcus Ashford not guilty.",
                
                ("prosecution", ExperienceState.PROSECUTION_OPENING):
                    "Members of the jury, this is a case about betrayal and greed. The defendant stood to gain £500,000 from a forged will - a will that Lord Blackthorn discovered just hours before his death. The Crown will prove that when confronted with exposure, the defendant chose murder over justice. We will show you the evidence of motive, means, and opportunity that points inexorably to guilt.",
                
                ("prosecution", ExperienceState.EVIDENCE_PRESENTATION):
                    "The evidence tells a clear story. First, the forged will - establishing a £500,000 motive. Second, the housekeeper's testimony - placing the defendant at the scene during the confrontation. Third, the toxicology report - showing digoxin poisoning, not natural causes. Fourth, the defendant's access to the estate medical supplies containing digoxin. Each piece connects to form an undeniable picture of guilt.",
                
                ("prosecution", ExperienceState.CROSS_EXAMINATION):
                    "The defence would have you focus on minor timeline details, but consider this: the defendant had motive, means, and opportunity. He was the last person to see the victim alive. He had access to the poison. And he stood to lose everything when the forgery was exposed. These are not coincidences.",
                
                ("prosecution", ExperienceState.PROSECUTION_CLOSING):
                    "Members of the jury, the evidence is overwhelming. Marcus Ashford had a powerful motive - £500,000 and exposure of his fraud. He had the means - access to digoxin in the estate medical cabinet. He had opportunity - alone with Lord Blackthorn during the critical time window. When motive, means, and opportunity align with presence at the scene, that is not reasonable doubt - that is proof beyond reasonable doubt. The Crown asks you to return a verdict of guilty.",
            })
        
        return fallbacks.get((agent_role, stage), f"[{agent_role} statement for {stage.value}]")
