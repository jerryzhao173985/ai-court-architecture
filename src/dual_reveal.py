"""Dual reveal system for presenting verdict and reasoning assessment."""

from pydantic import BaseModel, Field, ConfigDict
from models import CaseContent
from session import ReasoningAssessment
from jury_orchestrator import VoteResult, JurorReveal


class GroundTruthReveal(BaseModel):
    """Ground truth information revealed after voting."""
    model_config = ConfigDict(populate_by_name=True)
    
    actual_verdict: str = Field(alias="actualVerdict")
    explanation: str
    key_evidence: list[str] = Field(alias="keyEvidence")


class DualReveal(BaseModel):
    """Complete dual reveal data structure."""
    model_config = ConfigDict(populate_by_name=True)
    
    verdict: VoteResult
    ground_truth: GroundTruthReveal = Field(alias="groundTruth")
    reasoning_assessment: ReasoningAssessment = Field(alias="reasoningAssessment")
    juror_reveal: list[JurorReveal] = Field(alias="jurorReveal")


class DualRevealAssembler:
    """
    Assembles dual reveal data from various components.
    
    Combines verdict, ground truth, reasoning assessment, and juror
    identities into a structured reveal presentation.
    """

    def __init__(self, case_content: CaseContent):
        """
        Initialize dual reveal assembler.
        
        Args:
            case_content: The case content for ground truth
        """
        self.case_content = case_content

    def assemble_dual_reveal(
        self,
        vote_result: VoteResult,
        reasoning_assessment: ReasoningAssessment,
        juror_reveals: list[JurorReveal]
    ) -> DualReveal:
        """
        Assemble complete dual reveal data.
        
        Args:
            vote_result: The jury's vote result
            reasoning_assessment: User's reasoning evaluation
            juror_reveals: Revealed juror identities and votes
            
        Returns:
            Complete dual reveal structure
        """
        # Extract ground truth from case content
        ground_truth = self._create_ground_truth_reveal()
        
        # Assemble dual reveal
        return DualReveal(
            verdict=vote_result,
            ground_truth=ground_truth,
            reasoning_assessment=reasoning_assessment,
            juror_reveal=juror_reveals
        )

    def _create_ground_truth_reveal(self) -> GroundTruthReveal:
        """
        Create ground truth reveal from case content.
        
        Returns:
            Ground truth reveal structure
        """
        gt = self.case_content.ground_truth
        
        # Generate explanation based on actual verdict
        if gt.actual_verdict == "guilty":
            explanation = self._generate_guilty_explanation()
        else:
            explanation = self._generate_not_guilty_explanation()
        
        return GroundTruthReveal(
            actual_verdict=gt.actual_verdict,
            explanation=explanation,
            key_evidence=gt.key_facts
        )

    def _generate_guilty_explanation(self) -> str:
        """Generate explanation for guilty verdict."""
        key_facts = self.case_content.ground_truth.key_facts
        
        explanation = f"The evidence ultimately supports a guilty verdict. "
        
        if key_facts:
            explanation += f"Key facts include: {', '.join(key_facts[:3])}. "
        
        explanation += "The prosecution's case, when examined closely, establishes guilt beyond reasonable doubt."
        
        return explanation

    def _generate_not_guilty_explanation(self) -> str:
        """Generate explanation for not guilty verdict."""
        key_facts = self.case_content.ground_truth.key_facts
        
        explanation = f"The evidence ultimately supports a not guilty verdict. "
        
        if key_facts:
            explanation += f"Critical issues include: {', '.join(key_facts[:3])}. "
        
        explanation += "The prosecution failed to prove guilt beyond reasonable doubt, and reasonable doubt exists."
        
        return explanation

    def present_sequential_reveal(self, dual_reveal: DualReveal) -> dict:
        """
        Present dual reveal in sequential stages.
        
        Args:
            dual_reveal: The complete dual reveal data
            
        Returns:
            Dictionary with sequential reveal stages
        """
        return {
            "stage_1_verdict": {
                "title": "The Verdict",
                "verdict": dual_reveal.verdict.verdict,
                "guilty_count": dual_reveal.verdict.guilty_count,
                "not_guilty_count": dual_reveal.verdict.not_guilty_count
            },
            "stage_2_truth": {
                "title": "The Truth",
                "actual_verdict": dual_reveal.ground_truth.actual_verdict,
                "explanation": dual_reveal.ground_truth.explanation,
                "key_evidence": dual_reveal.ground_truth.key_evidence
            },
            "stage_3_reasoning": {
                "title": "Your Reasoning Assessment",
                "category": dual_reveal.reasoning_assessment.category,
                "evidence_score": dual_reveal.reasoning_assessment.evidence_score,
                "coherence_score": dual_reveal.reasoning_assessment.coherence_score,
                "fallacies": dual_reveal.reasoning_assessment.fallacies_detected,
                "feedback": dual_reveal.reasoning_assessment.feedback
            },
            "stage_4_jurors": {
                "title": "The Jury Revealed",
                "jurors": [
                    {
                        "id": j.juror_id,
                        "type": j.type,
                        "persona": j.persona,
                        "vote": j.vote,
                        "key_statements": j.key_statements
                    }
                    for j in dual_reveal.juror_reveal
                ]
            }
        }
