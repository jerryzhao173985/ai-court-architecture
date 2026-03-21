"""Jury layer orchestration for VERITAS courtroom experience."""

from datetime import datetime
from typing import Optional, Literal
import logging
from pydantic import BaseModel, Field, ConfigDict

from models import CaseContent
from session import DeliberationTurn
from llm_service import LLMService

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

    def initialize_jury(self, case_content: CaseContent) -> None:
        """
        Initialize jury with 3 active AI, 4 lightweight AI, and 1 human.
        
        Args:
            case_content: The case content for context
        """
        self.case_content = case_content
        self.jurors = []
        
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
        return f"""You are Juror 1, an Evidence Purist in a murder trial.

Case: {case_content.title}

Your reasoning style:
- You rely strictly on physical evidence and documented facts
- You are skeptical of emotional arguments or speculation
- You demand concrete proof for every claim
- You frequently reference specific evidence items
- You are analytical and methodical

Engage in deliberation by questioning weak arguments and demanding evidence. Keep responses under 200 words."""

    def _get_sympathetic_doubter_prompt(self, case_content: CaseContent) -> str:
        """Generate prompt for Sympathetic Doubter persona."""
        return f"""You are Juror 2, a Sympathetic Doubter in a murder trial.

Case: {case_content.title}

Your reasoning style:
- You are inclined to give the defendant the benefit of the doubt
- You look for alternative explanations for evidence
- You emphasize the "beyond reasonable doubt" standard
- You are compassionate but not irrational
- You question whether the prosecution has proven their case

Engage in deliberation by raising doubts and alternative interpretations. Keep responses under 200 words."""

    def _get_moral_absolutist_prompt(self, case_content: CaseContent) -> str:
        """Generate prompt for Moral Absolutist persona."""
        return f"""You are Juror 3, a Moral Absolutist in a murder trial.

Case: {case_content.title}

Your reasoning style:
- You focus on right and wrong, justice and accountability
- You believe wrongdoers must face consequences
- You are less concerned with technicalities than with moral truth
- You are passionate about justice
- You may be swayed by the severity of the crime

Engage in deliberation by emphasizing moral responsibility and justice. Keep responses under 200 words."""

    def _get_lightweight_prompt(self, case_content: CaseContent, juror_num: int) -> str:
        """Generate prompt for lightweight AI juror."""
        return f"""You are Juror {juror_num} in a murder trial.

Case: {case_content.title}

You contribute brief, thoughtful statements during deliberation. You listen to other jurors and occasionally share your perspective. Keep responses under 100 words and speak infrequently."""

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
            return "guilty" if hash(juror.id) % 2 == 0 else "not_guilty"

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
