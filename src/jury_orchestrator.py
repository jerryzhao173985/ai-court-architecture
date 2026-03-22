"""Jury layer orchestration for VERITAS courtroom experience."""

import json
import random
from datetime import datetime
from typing import Optional, Literal
import hashlib
import logging
from pydantic import BaseModel, Field, ConfigDict

from models import CaseContent
from session import DeliberationTurn
from llm_service import LLMService
from complexity_analyzer import CaseComplexityAnalyzer, ComplexityLevel
from reasoning_evaluator import ReasoningEvaluator

logger = logging.getLogger("veritas")

# Juror persona display mapping (emoji, display name)
JUROR_DISPLAY = {
    "evidence_purist": ("🔬", "Juror 1"),
    "sympathetic_doubter": ("🤔", "Juror 2"),
    "moral_absolutist": ("⚖️", "Juror 3")
}


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
        self.reasoning_evaluator: Optional[ReasoningEvaluator] = None
        self.vote_reasoning: dict[str, str] = {}
        # Track which evidence each juror has already engaged with
        self.juror_engaged_evidence: dict[str, set[str]] = {}
        # Track juror response rotation to ensure each responds at least every 2 rounds
        self.juror_last_response_round: dict[str, int] = {}

    def initialize_jury(self, case_content: CaseContent) -> None:
        """
        Initialize jury with 3 active AI, 4 lightweight AI, and 1 human.
        
        Args:
            case_content: The case content for context
        """
        self.case_content = case_content
        self.jurors = []
        
        # Initialize reasoning evaluator with case content
        self.reasoning_evaluator = ReasoningEvaluator(case_content)
        
        # Initialize engaged evidence tracking for all jurors
        self.juror_engaged_evidence = {}
        
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
        
        return f"""You are Juror 1 in a criminal trial. You are an independent thinker who values evidence and clear reasoning.

Case: {case_content.title}

PERSONALITY & BACKGROUND:
You are a retired forensic accountant with 30 years of experience. You have a scientific mindset but you're also human — you can be persuaded by a good argument, surprised by new angles, and genuinely uncertain. You are NOT a robot that only says "show me the evidence." You think deeply and express nuanced views.

HOW YOU THINK:
- You START by analyzing physical evidence and documents, but you can be moved by strong logical arguments from other jurors
- You are genuinely open-minded — if someone raises a point you hadn't considered, acknowledge it
- You sometimes change your position mid-discussion when presented with compelling reasoning
- You can feel conflicted and express that uncertainty: "I keep going back and forth on this..."
- You weigh probability, not just proof — "The evidence leans toward X, but I can see how Y is possible"

HOW YOU ENGAGE:
- You actively lead discussion when the group seems stuck: "Let me lay out what we know for certain..."
- You ask the human juror direct questions: "What do you make of the timeline? Does it add up to you?"
- You sometimes encourage quieter jurors: "I'd like to hear what others think about this point"
- You push back on weak arguments from ANY side, but respectfully
- You build on others' points: "That's a good observation — and it connects to..."
- You occasionally summarize the group's position to move discussion forward
- Vary your tone — sometimes confident, sometimes genuinely uncertain, sometimes surprised

CASE-SPECIFIC FOCUS:
{self._get_evidence_purist_case_focus(case_content)}
{complexity_guidance}

Keep responses under {max_words} words. Be natural, dynamic, and engaged — NOT formulaic or predictable."""

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
        
        return f"""You are Juror 2 in a criminal trial. You are thoughtful, empathetic, and care deeply about getting this right.

Case: {case_content.title}

PERSONALITY & BACKGROUND:
You are a social worker who has seen how the justice system can fail people. You believe in the presumption of innocence — not as a legal technicality, but because you've seen wrongful convictions destroy lives. You've served on a jury before. You are NOT automatically "the doubt person" — you think independently and can lean guilty if the evidence is strong enough.

HOW YOU THINK:
- You start from "what has actually been proven?" and genuinely evaluate
- You can be persuaded toward guilty if the evidence is truly overwhelming
- You notice things others miss — gaps in testimony, alternative explanations, human factors
- You sometimes surprise yourself: "I came in thinking one way, but now I'm not so sure..."
- You weigh the human cost on BOTH sides — the victim deserves justice, but so does the accused
- You can feel genuinely torn and express it honestly

HOW YOU ENGAGE:
- You draw out the human juror's reasoning: "Can you walk us through your thinking on that?"
- You sometimes lead with a provocative question: "What if we're all wrong about this?"
- You challenge groupthink: "I notice we're all leaning one way — let me push back on that"
- You validate good points from anyone: "That's actually a really strong observation"
- You bring up what hasn't been discussed: "Has anyone considered the [witness/evidence] angle?"
- You occasionally mediate between jurors who disagree
- Vary between confident and uncertain — be genuinely unpredictable

CASE-SPECIFIC FOCUS:
{self._get_sympathetic_doubter_case_focus(case_content)}
{complexity_guidance}

Keep responses under {max_words} words. Be natural, dynamic, and engaged — NOT always the "doubt" person."""

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
        
        return f"""You are Juror 3 in a criminal trial. You have strong moral convictions but you are not a caricature.

Case: {case_content.title}

PERSONALITY & BACKGROUND:
You are a former military officer who has seen real consequences when accountability fails. You believe in justice deeply, but you also know that justice means getting it RIGHT, not just punishing someone. You've disciplined soldiers and seen innocent people accused — both experiences shape you.

HOW YOU THINK:
- You start from the victim's perspective — {case_content.narrative.victim_profile.name} was harmed and that matters
- But you can be moved by genuine reasonable doubt if the evidence truly doesn't hold up
- You weigh the human cost on both sides — a wrong conviction is also an injustice
- You are sometimes surprised by your own uncertainty: "I was sure at first, but now..."
- You think about what you'd want if YOU were wrongly accused — fairness matters to you too
- You can feel the tension between wanting justice and needing proof

HOW YOU ENGAGE:
- You bring the emotional weight of the case into focus when the discussion gets too abstract
- You ask direct, challenging questions: "But {case_content.narrative.victim_profile.name} was harmed — how do we explain that?"
- You can agree with other jurors when they make good points
- You push back when you think the group is being too lenient OR too hasty
- You occasionally step back and listen, then come in with a strong point
- You speak with conviction but can also say "I need to think about that"

CASE-SPECIFIC FOCUS:
{self._get_moral_absolutist_case_focus(case_content)}
{complexity_guidance}

Keep responses under {max_words} words. Be natural, passionate but fair — NOT a one-note "guilty" voice."""

    def _get_lightweight_prompt(self, case_content: CaseContent, juror_num: int) -> str:
        """Generate prompt for lightweight AI juror."""
        defendant = case_content.narrative.defendant_profile.name
        charge = case_content.narrative.charge_text[:150]
        evidence_titles = ", ".join([e.title for e in case_content.evidence[:4]])

        return f"""You are Juror {juror_num} in a criminal trial.

Case: {case_content.title}
Defendant: {defendant}
Charge: {charge}
Key evidence: {evidence_titles}

You contribute brief, thoughtful statements during deliberation. Listen to other jurors and occasionally share your perspective. Keep responses under 100 words."""

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
            focus_points.append("You notice what's MISSING from the prosecution's case — gaps in direct evidence, absent witnesses, unexplained inconsistencies")
        
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
        
        # Focus on the defendant and evidence
        if case_content.narrative and case_content.narrative.defendant_profile:
            defendant_name = case_content.narrative.defendant_profile.name
            focus_points.append(f"You keep coming back to the question: did {defendant_name} do this, and what does the evidence actually show?")

        # Focus on accountability — but open-minded
        focus_points.append("You believe in accountability, but you also know that convicting the wrong person is its own injustice")
        focus_points.append("You weigh the evidence seriously — if it's strong, you lean toward conviction; if it's weak, you can accept acquittal")
        focus_points.append("You think about what justice means for everyone involved — the victim, the accused, and society")
        
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
        
        # Calculate current round number (number of user statements)
        current_round = len([t for t in self.deliberation_statements if t.juror_id == "juror_human"])
        
        # Get active AI jurors
        active_jurors = [j for j in self.jurors if j.type == "active_ai"]
        
        # Select 2 active jurors to respond this round
        # Rotation logic: ensure each juror responds at least every 2 rounds
        selected_jurors = self._select_responding_jurors(active_jurors, current_round)
        
        # Generate responses from selected active AI jurors (within 15 seconds)
        for juror in selected_jurors:
            ai_response = await self._generate_juror_response(juror, statement)
            turns.append(ai_response)
            self.deliberation_statements.append(ai_response)
            # Update last response round for this juror
            self.juror_last_response_round[juror.id] = current_round
        
        # Occasionally add lightweight juror responses (every 4th round)
        if current_round > 0 and current_round % 4 == 0:
            lightweight = [j for j in self.jurors if j.type == "lightweight_ai"][0]
            lw_response = await self._generate_juror_response(lightweight, statement)
            turns.append(lw_response)
            self.deliberation_statements.append(lw_response)

        # Sometimes a bot juror (juror_1 or juror_2) adds a follow-up to encourage discussion
        if current_round >= 2 and random.random() < 0.4:  # 40% chance after round 2
            bot_jurors = [j for j in self.jurors if j.id in ("juror_1", "juror_2")]
            available = [j for j in bot_jurors if j.id not in [s.id for s in selected_jurors]]
            if available:
                follow_up_juror = random.choice(available)
                # Build context from what was just said this round
                recent = "\n".join([
                    f"{t.juror_id}: {t.statement}"
                    for t in self.deliberation_statements[-4:]
                ])
                follow_up = await self._generate_juror_response(
                    follow_up_juror,
                    f"The discussion so far:\n{recent}\n\nRespond to what was just said — ask a follow-up question, challenge a point, or raise something others missed."
                )
                turns.append(follow_up)
                self.deliberation_statements.append(follow_up)

        return turns

    def _select_responding_jurors(self, active_jurors: list[JurorPersona], current_round: int) -> list[JurorPersona]:
        """
        Select 2-3 active jurors to respond. Bot jurors (juror_1, juror_2) are prioritized
        and sometimes both respond in the same round.

        Args:
            active_jurors: List of active AI jurors
            current_round: Current round number (1-indexed)

        Returns:
            List of 2-3 jurors to respond this round
        """
        # Initialize tracking if needed
        for juror in active_jurors:
            if juror.id not in self.juror_last_response_round:
                self.juror_last_response_round[juror.id] = 0
        
        # Bot jurors (juror_1, juror_2) are prioritized — they have dedicated bots
        bot_jurors = [j for j in active_jurors if j.id in ("juror_1", "juror_2")]
        clerk_jurors = [j for j in active_jurors if j.id not in ("juror_1", "juror_2")]

        selected = []

        # Always include at least 1 bot juror
        if bot_jurors:
            # Alternate which bot juror goes first
            if current_round % 2 == 1:
                selected.append(bot_jurors[0])
            else:
                selected.append(bot_jurors[-1])

        # 30% chance both bot jurors respond (makes deliberation more dynamic)
        if len(bot_jurors) >= 2 and random.random() < 0.3:
            for bj in bot_jurors:
                if bj not in selected:
                    selected.append(bj)

        # Guarantee clerk jurors (juror_3) respond at least every 2 rounds
        for cj in clerk_jurors:
            if current_round - self.juror_last_response_round[cj.id] >= 2:
                if cj not in selected:
                    selected.append(cj)

        # Ensure at least 2 respondents total
        if len(selected) < 2:
            remaining = [j for j in active_jurors if j not in selected]
            remaining.sort(key=lambda j: self.juror_last_response_round[j.id])
            for j in remaining:
                if len(selected) >= 2:
                    break
                selected.append(j)

        return selected

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
        
        # Detect evidence references in the latest user statement
        # Only process if we have a reasoning evaluator and the context is from the human juror
        if self.reasoning_evaluator and self.case_content:
            # Get the last user statement (human juror)
            user_statements = [turn for turn in self.deliberation_statements if turn.juror_id == "juror_human"]
            
            if user_statements:
                # Track evidence references from user statements
                referenced_evidence_ids = self.reasoning_evaluator.track_evidence_references(user_statements)
                
                # Initialize engaged evidence set for this juror if not exists
                if juror.id not in self.juror_engaged_evidence:
                    self.juror_engaged_evidence[juror.id] = set()
                
                # Find new evidence that this juror hasn't engaged with yet
                new_evidence_ids = [eid for eid in referenced_evidence_ids 
                                   if eid not in self.juror_engaged_evidence[juror.id]]
                
                if new_evidence_ids:
                    # Look up the EvidenceItem objects
                    evidence_items = [e for e in self.case_content.evidence if e.id in new_evidence_ids]
                    
                    if evidence_items:
                        # Append USER REFERENCED EVIDENCE section to the prompt
                        evidence_section = "\n\nUSER REFERENCED EVIDENCE:\n"
                        for item in evidence_items:
                            evidence_section += f"- {item.title}: {item.description}\n"
                        
                        user_prompt += evidence_section
                        
                        # Mark these evidence items as engaged by this juror
                        self.juror_engaged_evidence[juror.id].update(new_evidence_ids)
        
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
                    agent_role=juror.id,  # For caching (juror.id is already "juror_1" etc.)
                    stage="deliberation",  # For caching
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
        
        # Collect AI juror votes with LLM-based decision making
        for juror in self.jurors:
            if juror.type != "human":
                # Get LLM-based vote with reasoning
                ai_vote, reasoning = await self._generate_ai_vote(juror)
                votes.append(JurorVote(
                    juror_id=juror.id,
                    vote=ai_vote,
                    timestamp=datetime.now()
                ))
                
                # Store reasoning for dual reveal
                self.vote_reasoning[juror.id] = reasoning
        
        # Calculate verdict
        return self.calculate_verdict(votes)

    async def _generate_ai_vote(self, juror: JurorPersona) -> tuple[Literal["guilty", "not_guilty"], str]:
        """
        Generate vote for AI juror based on their deliberation using LLM.
        
        Args:
            juror: The juror persona to generate a vote for
            
        Returns:
            Tuple of (vote, reasoning) where reasoning is the juror's rationale
        """
        # Fallback heuristic based on persona
        def get_fallback_vote() -> Literal["guilty", "not_guilty"]:
            if juror.persona == "sympathetic_doubter":
                return "not_guilty"
            else:
                # All others (evidence purist, moral absolutist, lightweight): balanced
                digest = int(hashlib.md5(juror.id.encode()).hexdigest(), 16)
                return "guilty" if digest % 2 == 0 else "not_guilty"
        
        # If no LLM service available, use fallback
        if not self.llm_service or not juror.system_prompt:
            fallback_vote = get_fallback_vote()
            return fallback_vote, f"Vote based on persona: {juror.persona or 'balanced'}"
        
        # Build evidence summary (full descriptions for informed voting)
        evidence_summary = ""
        if self.case_content:
            evidence_items = []
            for item in self.case_content.evidence:
                evidence_items.append(f"- {item.title} ({item.type}): {item.description}")
            evidence_summary = "\n".join(evidence_items)

        # Get the full deliberation transcript (user + all jurors)
        deliberation_transcript = []
        for turn in self.deliberation_statements:
            speaker = "Human Juror" if turn.juror_id == "juror_human" else turn.juror_id
            deliberation_transcript.append(f"{speaker}: {turn.statement}")
        transcript_text = "\n".join(deliberation_transcript[-15:]) if deliberation_transcript else "No deliberation occurred."

        # Get this juror's own statements
        juror_statements = [
            turn.statement
            for turn in self.deliberation_statements
            if turn.juror_id == juror.id
        ]
        own_statements_text = "\n".join([f"- {stmt}" for stmt in juror_statements]) if juror_statements else "You did not speak during deliberation."

        # Build prompt for voting decision
        user_prompt = f"""The jury deliberation has concluded. You must now cast your vote.

EVIDENCE SUMMARY:
{evidence_summary}

DELIBERATION TRANSCRIPT (recent):
{transcript_text}

YOUR OWN STATEMENTS:
{own_statements_text}

Based on the evidence, the full deliberation, and your own reasoning, decide: Is the defendant GUILTY or NOT GUILTY?

You MUST respond with valid JSON only, in this exact format:
{{"vote": "guilty", "reasoning": "Your rationale in 1-2 sentences"}}
or
{{"vote": "not_guilty", "reasoning": "Your rationale in 1-2 sentences"}}"""
        
        try:
            # Use LLM with temperature 0.3 for consistency, 10s timeout
            response = await self.llm_service.generate_response(
                system_prompt=juror.system_prompt,
                user_prompt=user_prompt,
                max_tokens=150,
                temperature=0.3,
                timeout=10,
                response_format={"type": "json_object"}
            )
            
            # Parse JSON response
            result = json.loads(response)
            vote = result.get("vote", "").lower().replace(" ", "_")
            reasoning = result.get("reasoning", "")
            
            # Validate vote
            if vote not in ["guilty", "not_guilty"]:
                logger.warning(f"Invalid vote '{vote}' from {juror.id}, using fallback")
                fallback_vote = get_fallback_vote()
                return fallback_vote, f"Fallback vote due to invalid response: {juror.persona or 'balanced'}"
            
            return vote, reasoning
            
        except Exception as e:
            logger.warning(f"LLM voting failed for {juror.id}: {e}, using fallback")
            fallback_vote = get_fallback_vote()
            return fallback_vote, f"Fallback vote due to error: {juror.persona or 'balanced'}"

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
                    # Include deliberation statements
                    key_statements = [
                        turn.statement 
                        for turn in self.deliberation_statements 
                        if turn.juror_id == juror.id
                    ][:2]  # First 2 statements
                
                # Add vote reasoning if available
                if juror.id in self.vote_reasoning:
                    vote_reasoning = self.vote_reasoning[juror.id]
                    key_statements.append(f"Vote reasoning: {vote_reasoning}")
                
                reveals.append(JurorReveal(
                    juror_id=juror.id,
                    type=juror.type,
                    persona=juror.persona,
                    vote=vote_info.vote,
                    key_statements=key_statements
                ))
        
        return reveals

    def get_juror_display_info(self, juror_id: str) -> tuple[str, str]:
        """
        Get display information for a juror.
        
        Args:
            juror_id: The juror ID
            
        Returns:
            Tuple of (emoji, display_name) for the juror
        """
        juror = next((j for j in self.jurors if j.id == juror_id), None)
        
        if not juror:
            return ("👤", "AI Juror")
        
        if juror.type == "human":
            return ("👤", "You")
        
        # Get persona display info
        if juror.persona and juror.persona in JUROR_DISPLAY:
            return JUROR_DISPLAY[juror.persona]
        
        # Fallback for lightweight jurors or unknown personas
        juror_num = juror_id.replace("juror_", "")
        return ("👤", f"Juror {juror_num}")
