"""Jury layer orchestration for VERITAS courtroom experience."""

from datetime import datetime
from typing import Optional, Literal
import hashlib
import logging
from pydantic import BaseModel, Field, ConfigDict

from models import CaseContent
from session import DeliberationTurn
from llm_service import LLMService
from complexity_analyzer import CaseComplexityAnalyzer, ComplexityLevel

logger = logging.getLogger("veritas")


class JurorPersona(BaseModel):
    """Configuration for a juror with persona."""
    model_config = ConfigDict(populate_by_name=True)
    
    id: str
    type: Literal["active_ai", "lightweight_ai", "human"]
    persona: Optional[Literal["evidence_purist", "sympathetic_doubter", "moral_absolutist"]] = None
    system_prompt: Optional[str] = Field(default=None, alias="systemPrompt")


class VoteCollection(BaseModel):
    """Collection of votes from all jurors."""
    model_config = ConfigDict(populate_by_name=True)
    
    session_id: str = Field(alias="sessionId")
    votes: list["JurorVote"] = Field(default_factory=list)
    collection_start_time: datetime = Field(alias="collectionStartTime")
    collection_end_time: Optional[datetime] = Field(default=None, alias="collectionEndTime")
    result: Optional["VoteResult"] = None


class JurorVote(BaseModel):
    """A single juror's vote."""
    model_config = ConfigDict(populate_by_name=True)
    
    juror_id: str = Field(alias="jurorId")
    vote: Literal["guilty", "not_guilty"]
    timestamp: datetime


class VoteResult(BaseModel):
    """Result of jury voting."""
    model_config = ConfigDict(populate_by_name=True)
    
    verdict: Literal["guilty", "not_guilty"]
    guilty_count: int = Field(alias="guiltyCount")
    not_guilty_count: int = Field(alias="notGuiltyCount")
    juror_breakdown: list["JurorBreakdown"] = Field(alias="jurorBreakdown")


class JurorBreakdown(BaseModel):
    """Breakdown of a juror's vote."""
    model_config = ConfigDict(populate_by_name=True)
    
    juror_id: str = Field(alias="jurorId")
    type: Literal["active_ai", "lightweight_ai", "human"]
    vote: Literal["guilty", "not_guilty"]


class JurorReveal(BaseModel):
    """Revealed information about a juror."""
    model_config = ConfigDict(populate_by_name=True)
    
    juror_id: str = Field(alias="jurorId")
    type: Literal["active_ai", "lightweight_ai", "human"]
    persona: Optional[str] = None
    vote: Literal["guilty", "not_guilty"]
    key_statements: list[str] = Field(default_factory=list, alias="keyStatements")


class JuryOrchestrator:
    """
    Manages 8-juror deliberation system with AI and human jurors.
    
    Coordinates deliberation, manages turn-taking, collects votes,
    and reveals juror identities.
    """

    def __init__(self, llm_service: Optional[LLMService] = None):
        """Initialize jury orchestrator.
        
        Args:
            llm_service: LLM service for generating juror responses (optional for testing)
        """
        self.jurors: list[JurorPersona] = []
        self.case_content: Optional[CaseContent] = None
        self.deliberation_start_time: Optional[datetime] = None
        self.deliberation_statements: list[DeliberationTurn] = []
        self.max_deliberation_seconds = 360  # 6 minutes hard limit
        self.min_deliberation_seconds = 240  # 4 minutes minimum
        self.llm_service = llm_service
        self.complexity_analyzer = CaseComplexityAnalyzer()
        self.complexity_level: Optional[ComplexityLevel] = None

    def initialize_jury(self, case_content: CaseContent) -> None:
        """
        Initialize jury with 3 active AI, 4 lightweight AI, and 1 human.
        
        Args:
            case_content: The case content for context
        """
        self.case_content = case_content
        self.jurors = []
        
        # Analyze case complexity
        self.complexity_level = self.complexity_analyzer.analyze_complexity(case_content)
        logger.info(f"Case complexity for jury: {self.complexity_level.level}")
        
        # Create 3 active AI jurors with distinct personas
        self.jurors.append(JurorPersona(
            id="juror_1",
            type="active_ai",
            persona="evidence_purist",
            systemPrompt=self._get_evidence_purist_prompt(case_content)
        ))
        
        self.jurors.append(JurorPersona(
            id="juror_2",
            type="active_ai",
            persona="sympathetic_doubter",
            systemPrompt=self._get_sympathetic_doubter_prompt(case_content)
        ))
        
        self.jurors.append(JurorPersona(
            id="juror_3",
            type="active_ai",
            persona="moral_absolutist",
            systemPrompt=self._get_moral_absolutist_prompt(case_content)
        ))
        
        # Create 4 lightweight AI jurors
        for i in range(4, 8):
            self.jurors.append(JurorPersona(
                id=f"juror_{i}",
                type="lightweight_ai",
                persona=None,
                systemPrompt=self._get_lightweight_prompt(case_content, i)
            ))
        
        # Human juror (added during deliberation)
        self.jurors.append(JurorPersona(
            id="juror_human",
            type="human",
            persona=None,
            systemPrompt=None
        ))

    def _get_evidence_purist_prompt(self, case_content: CaseContent) -> str:
        """Generate prompt for Evidence Purist persona."""
        # Get complexity guidance
        complexity_guidance = ""
        if self.complexity_level:
            complexity_guidance = self.complexity_analyzer.get_complexity_guidance(self.complexity_level)
        
        # Adjust response length based on complexity
        max_words = 200
        if self.complexity_level:
            if self.complexity_level.level == "simple":
                max_words = 150
            elif self.complexity_level.level == "complex":
                max_words = 250
        
        return f"""You are Juror 1, an Evidence Purist in a murder trial.

Case: {case_content.title}

PERSONALITY & BACKGROUND:
You are a retired forensic accountant with 30 years of experience analyzing documents and data. You have a scientific mindset and believe that truth emerges from facts, not feelings. You're respected but can come across as cold or dismissive of emotional appeals. You take notes meticulously during trial.

CORE REASONING STYLE:
- You rely EXCLUSIVELY on physical evidence, documents, and verifiable testimony
- You are deeply skeptical of circumstantial evidence unless it forms a clear pattern
- You demand concrete proof with clear chain of custody for every claim
- You frequently cite specific evidence items by name/number
- You are analytical, methodical, and sometimes pedantic about details
- You distrust "gut feelings" and "common sense" arguments

DELIBERATION BEHAVIORS:
- You interrupt when others make unsupported claims: "Where's the evidence for that?"
- You reference specific trial moments: "The prosecution said X, but the document showed Y"
- You create mental timelines and check them against evidence
- You're willing to change your mind, but ONLY when shown compelling physical evidence
- You sometimes frustrate other jurors with your insistence on proof
- You speak in measured, precise language with occasional technical terms

INTERACTION PATTERNS:
- You clash with the Moral Absolutist when they prioritize justice over evidence
- You respect the Sympathetic Doubter's logical approach but push back on speculation
- You ask pointed questions: "What physical evidence supports that theory?"
- You summarize evidence lists to ground the discussion
- You become more forceful when you sense the group drifting into emotion

CASE-SPECIFIC FOCUS:
{self._get_evidence_purist_case_focus(case_content)}
{complexity_guidance}

Keep responses under {max_words} words. Speak naturally as this character would - be direct, evidence-focused, and occasionally impatient with speculation."""

    def _get_sympathetic_doubter_prompt(self, case_content: CaseContent) -> str:
        """Generate prompt for Sympathetic Doubter persona."""
        # Get complexity guidance
        complexity_guidance = ""
        if self.complexity_level:
            complexity_guidance = self.complexity_analyzer.get_complexity_guidance(self.complexity_level)
        
        # Adjust response length based on complexity
        max_words = 200
        if self.complexity_level:
            if self.complexity_level.level == "simple":
                max_words = 150
            elif self.complexity_level.level == "complex":
                max_words = 250
        
        return f"""You are Juror 2, a Sympathetic Doubter in a murder trial.

Case: {case_content.title}

PERSONALITY & BACKGROUND:
You are a social worker who has seen how the justice system can fail vulnerable people. You believe in the presumption of innocence deeply - not as a legal technicality, but as a moral imperative. You're empathetic and thoughtful, sometimes to a fault. You've served on a jury once before and voted not guilty despite group pressure.

CORE REASONING STYLE:
- You are fundamentally inclined to give the defendant the benefit of the doubt
- You actively search for alternative explanations that could exonerate
- You emphasize "beyond reasonable doubt" as a HIGH bar, not just "probably guilty"
- You are compassionate but not irrational - you need logical alternatives, not just hope
- You question whether the prosecution has truly PROVEN their case or just suggested it
- You're sensitive to circumstantial evidence being presented as conclusive

DELIBERATION BEHAVIORS:
- You often start with: "But what if..." or "Couldn't it also mean..."
- You reframe prosecution evidence: "That shows X, but it doesn't prove Y"
- You remind others of the burden of proof when they seem too certain
- You speak gently but persistently, not backing down easily
- You sometimes play devil's advocate even when you're leaning guilty
- You ask "what are we missing?" to highlight gaps in the prosecution's case

INTERACTION PATTERNS:
- You align with the Evidence Purist on demanding proof, but differ on what constitutes doubt
- You clash with the Moral Absolutist when they prioritize punishment over proof
- You validate others' concerns while introducing alternative perspectives
- You use phrases like: "I understand, but..." or "That's fair, however..."
- You become more vocal when you sense the group rushing to judgment

CASE-SPECIFIC FOCUS:
{self._get_sympathetic_doubter_case_focus(case_content)}
{complexity_guidance}

Keep responses under {max_words} words. Speak naturally as this character would - be thoughtful, questioning, and gently persistent in raising doubts."""

    def _get_moral_absolutist_prompt(self, case_content: CaseContent) -> str:
        """Generate prompt for Moral Absolutist persona."""
        # Get complexity guidance
        complexity_guidance = ""
        if self.complexity_level:
            complexity_guidance = self.complexity_analyzer.get_complexity_guidance(self.complexity_level)
        
        # Adjust response length based on complexity
        max_words = 200
        if self.complexity_level:
            if self.complexity_level.level == "simple":
                max_words = 150
            elif self.complexity_level.level == "complex":
                max_words = 250
        
        return f"""You are Juror 3, a Moral Absolutist in a murder trial.

Case: {case_content.title}

PERSONALITY & BACKGROUND:
You are a former military officer who believes strongly in accountability and consequences. You've seen what happens when wrongdoers escape justice. You're passionate, principled, and sometimes see issues in black and white. You believe the justice system exists to protect society and punish the guilty. You have strong moral convictions and aren't afraid to express them.

CORE REASONING STYLE:
- You focus on right and wrong, justice and accountability above all else
- You believe that when someone commits murder, they MUST face consequences
- You are less concerned with legal technicalities than with moral truth and justice
- You are passionate about ensuring victims receive justice
- You may be swayed by the severity and brutality of the crime itself
- You trust your moral intuition about guilt and character

DELIBERATION BEHAVIORS:
- You speak with conviction: "This is about justice" or "We owe it to the victim"
- You emphasize the human cost: "Someone died. Someone's family is grieving."
- You challenge others who seem to be "letting the defendant off on technicalities"
- You sometimes appeal to common sense: "We all know what happened here"
- You can be forceful and passionate, occasionally dominating the conversation
- You frame the decision as a moral duty, not just a legal determination

INTERACTION PATTERNS:
- You clash with the Sympathetic Doubter, seeing them as too soft or naive
- You get frustrated with the Evidence Purist's focus on technicalities over justice
- You use rhetorical questions: "Are we really going to let them walk free?"
- You invoke the victim's memory and the defendant's character
- You become more emotional and emphatic when others express doubt
- You sometimes need to be reminded to let others speak

CASE-SPECIFIC FOCUS:
{self._get_moral_absolutist_case_focus(case_content)}
{complexity_guidance}

Keep responses under {max_words} words. Speak naturally as this character would - be passionate, direct, and morally certain, but not unreasonable."""

    def _get_lightweight_prompt(self, case_content: CaseContent, juror_num: int) -> str:
        """Generate prompt for lightweight AI juror."""
        return f"""You are Juror {juror_num} in a murder trial.

Case: {case_content.title}

You contribute brief, thoughtful statements during deliberation. You listen to other jurors and occasionally share your perspective. Keep responses under 100 words and speak infrequently."""

    def _get_evidence_purist_case_focus(self, case_content: CaseContent) -> str:
        """Generate case-specific focus for Evidence Purist."""
        # Analyze evidence to identify what the purist would focus on
        evidence_items = case_content.evidence
        
        focus_points = []
        
        # Look for physical evidence
        physical_evidence = [e for e in evidence_items if e.type == "physical"]
        if physical_evidence:
            focus_points.append(f"You're particularly interested in the physical evidence: {', '.join([e.title for e in physical_evidence[:3]])}")
        
        # Look for documentary evidence
        documentary_evidence = [e for e in evidence_items if e.type == "documentary"]
        if documentary_evidence:
            focus_points.append(f"You scrutinize the documentary evidence: {', '.join([e.title for e in documentary_evidence[:2]])}")
        
        # Look for timeline issues
        if len(evidence_items) >= 3:
            focus_points.append("You're building a timeline from the evidence to check for consistency")
        
        # Default focus
        if not focus_points:
            focus_points.append("You're analyzing all evidence items for consistency and gaps")
        
        # Add general guidance
        focus_points.append("You want to see clear, unbroken chains of evidence, not assumptions")
        
        return "\n- ".join([""] + focus_points)

    def _get_sympathetic_doubter_case_focus(self, case_content: CaseContent) -> str:
        """Generate case-specific focus for Sympathetic Doubter."""
        evidence_items = case_content.evidence
        
        focus_points = []
        
        # Look for gaps in evidence
        if len(evidence_items) < 7:
            focus_points.append("You notice what's MISSING - no murder weapon, no eyewitness, no confession")
        
        # Look for testimonial evidence (which can be unreliable)
        testimonial_evidence = [e for e in evidence_items if e.type == "testimonial"]
        if testimonial_evidence:
            focus_points.append(f"You question the reliability of testimonial evidence: {', '.join([e.title for e in testimonial_evidence[:2]])}")
        
        # Look for timing issues
        focus_points.append("You're looking for timeline inconsistencies that create reasonable doubt")
        
        # Look for alternative explanations
        focus_points.append("You're actively considering: Could someone else have done this? Could this be accidental?")
        
        # Add burden of proof reminder
        focus_points.append("You keep asking: Has the prosecution PROVEN guilt beyond reasonable doubt, or just suggested it?")
        
        return "\n- ".join([""] + focus_points)

    def _get_moral_absolutist_case_focus(self, case_content: CaseContent) -> str:
        """Generate case-specific focus for Moral Absolutist."""
        focus_points = []
        
        # Focus on the victim
        if case_content.narrative and case_content.narrative.victim_profile:
            victim_name = case_content.narrative.victim_profile.name
            focus_points.append(f"You keep thinking about {victim_name} and their family - they deserve justice")
        
        # Focus on the defendant's character and motive
        if case_content.narrative and case_content.narrative.defendant_profile:
            defendant_name = case_content.narrative.defendant_profile.name
            focus_points.append(f"You believe {defendant_name}'s motive and opportunity show their guilt")
        
        # Focus on the severity of murder
        focus_points.append("You emphasize that murder is the ultimate crime - we can't let someone walk free on technicalities")
        
        # Focus on moral certainty
        focus_points.append("You trust your moral intuition: the evidence points to guilt, and justice demands accountability")
        
        # Focus on societal protection
        focus_points.append("You believe the jury's duty is to protect society by holding the guilty accountable")
        
        return "\n- ".join([""] + focus_points)

    def start_deliberation(self) -> str:
        """
        Start jury deliberation phase.
        
        Returns:
            Initial prompt for the user
        """
        self.deliberation_start_time = datetime.now()
        self.deliberation_statements = []
        
        return "Members of the jury, you may now begin your deliberations. What are your initial thoughts on the case?"

    async def process_user_statement(self, statement: str, evidence_references: list[str] = None) -> list[DeliberationTurn]:
        """
        Process user statement and generate AI juror responses.
        
        Args:
            statement: The user's deliberation statement
            evidence_references: List of evidence IDs referenced by user
            
        Returns:
            List of deliberation turns (user + AI responses)
        """
        turns = []
        
        # Record user statement
        user_turn = DeliberationTurn(
            juror_id="juror_human",
            statement=statement,
            timestamp=datetime.now(),
            evidence_references=evidence_references or []
        )
        turns.append(user_turn)
        self.deliberation_statements.append(user_turn)
        
        # Generate responses from active AI jurors (within 15 seconds)
        # TODO: Replace with actual LLM calls
        for juror in self.jurors:
            if juror.type == "active_ai":
                ai_response = await self._generate_juror_response(juror, statement)
                turns.append(ai_response)
                self.deliberation_statements.append(ai_response)
        
        # Occasionally add lightweight juror responses
        if len(self.deliberation_statements) % 3 == 0:
            lightweight = [j for j in self.jurors if j.type == "lightweight_ai"][0]
            lw_response = await self._generate_juror_response(lightweight, statement)
            turns.append(lw_response)
            self.deliberation_statements.append(lw_response)
        
        return turns

    async def _generate_juror_response(self, juror: JurorPersona, context: str) -> DeliberationTurn:
        """
        Generate response from an AI juror using LLM.
        
        Args:
            juror: The juror persona
            context: Context from previous statements
            
        Returns:
            Deliberation turn with juror's response
        """
        # Build conversation context
        recent_statements = "\n".join([
            f"{turn.juror_id}: {turn.statement}"
            for turn in self.deliberation_statements[-5:]  # Last 5 statements
        ])
        
        user_prompt = f"""The jury is deliberating. Recent discussion:

{recent_statements}

Latest statement: {context}

Respond to this statement as part of the deliberation. Keep your response under 200 words."""
        
        # Generate fallback based on persona
        if juror.persona == "evidence_purist":
            fallback = "I need to see concrete evidence. What specific facts support that conclusion?"
        elif juror.persona == "sympathetic_doubter":
            fallback = "But can we really be certain beyond reasonable doubt? There could be other explanations."
        elif juror.persona == "moral_absolutist":
            fallback = "We must consider the gravity of this crime and ensure justice is served."
        else:
            fallback = "I see both sides of this argument."
        
        # Use LLM service if available
        if self.llm_service and juror.system_prompt:
            try:
                # Use GPT-4o for active AI jurors, GPT-4o-mini for lightweight
                model_override = None
                if self.llm_service.provider == "openai":
                    if juror.type == "active_ai":
                        model_override = "gpt-4o"
                    else:  # lightweight_ai
                        model_override = "gpt-4o-mini"
                
                content, used_fallback = await self.llm_service.generate_with_fallback(
                    system_prompt=juror.system_prompt,
                    user_prompt=user_prompt,
                    fallback_text=fallback,
                    max_tokens=200 if juror.type == "active_ai" else 100,
                    timeout=15,  # 15 second limit
                    model_override=model_override
                )
            except Exception as e:
                logger.warning(f"Juror response generation failed: {e}")
                content = fallback
        else:
            content = fallback
        
        return DeliberationTurn(
            juror_id=juror.id,
            statement=content,
            timestamp=datetime.now(),
            evidence_references=[]
        )

    def should_end_deliberation(self) -> bool:
        """
        Check if deliberation should end (6-minute hard limit).
        
        Returns:
            True if deliberation time exceeded, False otherwise
        """
        if not self.deliberation_start_time:
            return False
        
        elapsed = (datetime.now() - self.deliberation_start_time).total_seconds()
        return elapsed >= self.max_deliberation_seconds

    def get_deliberation_duration(self) -> float:
        """
        Get current deliberation duration in seconds.
        
        Returns:
            Duration in seconds
        """
        if not self.deliberation_start_time:
            return 0.0
        
        return (datetime.now() - self.deliberation_start_time).total_seconds()

    async def collect_votes(self, user_vote: Literal["guilty", "not_guilty"]) -> VoteResult:
        """
        Collect votes from all 8 jurors simultaneously.
        
        Args:
            user_vote: The human user's vote
            
        Returns:
            Vote result with verdict
        """
        votes = []
        
        # Add user vote
        votes.append(JurorVote(
            juror_id="juror_human",
            vote=user_vote,
            timestamp=datetime.now()
        ))
        
        # Collect AI juror votes
        # TODO: Replace with actual LLM-based voting
        for juror in self.jurors:
            if juror.type != "human":
                # Placeholder: random vote based on persona
                ai_vote = self._generate_ai_vote(juror)
                votes.append(JurorVote(
                    juror_id=juror.id,
                    vote=ai_vote,
                    timestamp=datetime.now()
                ))
        
        # Calculate verdict
        return self.calculate_verdict(votes)

    def _generate_ai_vote(self, juror: JurorPersona) -> Literal["guilty", "not_guilty"]:
        """
        Generate vote for AI juror based on their deliberation.
        
        For now uses heuristic based on persona. In production, this would
        use LLM to analyze the juror's statements and case evidence.
        """
        # TODO: Replace with LLM-based decision making
        # Could analyze juror's own statements during deliberation
        # and ask them to vote based on their reasoning
        
        if juror.persona == "sympathetic_doubter":
            return "not_guilty"
        elif juror.persona == "moral_absolutist":
            return "guilty"
        else:
            # Evidence purist and lightweight: balanced
            digest = int(hashlib.md5(juror.id.encode()).hexdigest(), 16)
            return "guilty" if digest % 2 == 0 else "not_guilty"

    def calculate_verdict(self, votes: list[JurorVote]) -> VoteResult:
        """
        Calculate verdict from votes using majority rule.
        
        Args:
            votes: List of all juror votes
            
        Returns:
            Vote result with verdict and breakdown
        """
        guilty_count = sum(1 for v in votes if v.vote == "guilty")
        not_guilty_count = len(votes) - guilty_count
        
        # Majority rule: 5 or more votes determines verdict
        verdict = "guilty" if guilty_count >= 5 else "not_guilty"
        
        # Create breakdown
        breakdown = []
        for vote in votes:
            juror = next((j for j in self.jurors if j.id == vote.juror_id), None)
            if juror:
                breakdown.append(JurorBreakdown(
                    juror_id=vote.juror_id,
                    type=juror.type,
                    vote=vote.vote
                ))
        
        return VoteResult(
            verdict=verdict,
            guilty_count=guilty_count,
            not_guilty_count=not_guilty_count,
            juror_breakdown=breakdown
        )

    def reveal_jurors(self, vote_result: VoteResult) -> list[JurorReveal]:
        """
        Reveal AI juror identities and their votes.
        
        Args:
            vote_result: The vote result with breakdown
            
        Returns:
            List of juror reveals
        """
        reveals = []
        
        for juror in self.jurors:
            # Find this juror's vote
            vote_info = next(
                (b for b in vote_result.juror_breakdown if b.juror_id == juror.id),
                None
            )
            
            if vote_info:
                # Get key statements for active AI jurors
                key_statements = []
                if juror.type == "active_ai":
                    key_statements = [
                        turn.statement 
                        for turn in self.deliberation_statements 
                        if turn.juror_id == juror.id
                    ][:2]  # First 2 statements
                
                reveals.append(JurorReveal(
                    juror_id=juror.id,
                    type=juror.type,
                    persona=juror.persona,
                    vote=vote_info.vote,
                    key_statements=key_statements
                ))
        
        return reveals
