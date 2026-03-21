"""Case complexity analysis for dynamic prompt adjustment."""

from typing import Literal
from models import CaseContent, EvidenceItem


class ComplexityLevel:
    """Complexity level with associated parameters."""
    
    def __init__(
        self,
        level: Literal["simple", "moderate", "complex"],
        verbosity_multiplier: float,
        argumentation_depth: str
    ):
        self.level = level
        self.verbosity_multiplier = verbosity_multiplier
        self.argumentation_depth = argumentation_depth


class CaseComplexityAnalyzer:
    """
    Analyzes case content to determine complexity level.
    
    Complexity is determined by:
    - Number of evidence items
    - Number of witnesses
    - Evidence type diversity
    - Timeline complexity
    - Narrative length
    """

    def analyze_complexity(self, case_content: CaseContent) -> ComplexityLevel:
        """
        Analyze case content and return complexity level.
        
        Args:
            case_content: The case to analyze
            
        Returns:
            ComplexityLevel with parameters for prompt adjustment
        """
        score = 0
        
        # Evidence count (5-7 items, higher = more complex)
        evidence_count = len(case_content.evidence)
        if evidence_count >= 7:
            score += 3
        elif evidence_count >= 6:
            score += 2
        else:
            score += 1
        
        # Evidence type diversity (more types = more complex)
        evidence_types = set(e.type for e in case_content.evidence)
        score += len(evidence_types)  # 1-3 points
        
        # Witness count (more witnesses = more complex)
        witness_count = len(case_content.narrative.witness_profiles)
        if witness_count >= 3:
            score += 2
        elif witness_count >= 2:
            score += 1
        
        # Timeline complexity (more events = more complex)
        timeline_count = len(case_content.timeline)
        if timeline_count >= 7:
            score += 2
        elif timeline_count >= 5:
            score += 1
        
        # Narrative complexity (longer descriptions = more complex)
        avg_evidence_desc_length = sum(
            len(e.description) for e in case_content.evidence
        ) / len(case_content.evidence)
        
        if avg_evidence_desc_length > 200:
            score += 2
        elif avg_evidence_desc_length > 100:
            score += 1
        
        # Key facts complexity
        key_facts_count = len(case_content.ground_truth.key_facts)
        if key_facts_count >= 5:
            score += 2
        elif key_facts_count >= 3:
            score += 1
        
        # Classify based on total score
        # Score range: 5-15
        if score <= 8:
            return ComplexityLevel(
                level="simple",
                verbosity_multiplier=0.8,
                argumentation_depth="concise"
            )
        elif score <= 11:
            return ComplexityLevel(
                level="moderate",
                verbosity_multiplier=1.0,
                argumentation_depth="balanced"
            )
        else:
            return ComplexityLevel(
                level="complex",
                verbosity_multiplier=1.2,
                argumentation_depth="detailed"
            )
    
    def get_complexity_guidance(self, complexity: ComplexityLevel) -> str:
        """
        Get guidance text for agents based on complexity level.
        
        Args:
            complexity: The complexity level
            
        Returns:
            Guidance text to append to agent prompts
        """
        if complexity.level == "simple":
            return """
CASE COMPLEXITY: SIMPLE
- Keep arguments concise and focused on core facts
- Avoid over-elaboration of straightforward evidence
- Use clear, direct language without excessive detail
- Focus on 2-3 key points rather than exhaustive analysis"""
        
        elif complexity.level == "moderate":
            return """
CASE COMPLEXITY: MODERATE
- Balance conciseness with thorough analysis
- Address multiple evidence items and their connections
- Provide reasonable depth without overwhelming detail
- Connect 3-4 key arguments in a logical sequence"""
        
        else:  # complex
            return """
CASE COMPLEXITY: COMPLEX
- Provide detailed, nuanced argumentation
- Address multiple evidence items and their interrelationships
- Explore alternative interpretations and counter-arguments
- Build comprehensive arguments connecting 4-5+ key points
- Acknowledge complexity and address potential contradictions"""
    
    def adjust_character_limit(
        self,
        base_limit: int,
        complexity: ComplexityLevel
    ) -> int:
        """
        Adjust character limit based on complexity while respecting bounds.
        
        Args:
            base_limit: The base character limit
            complexity: The complexity level
            
        Returns:
            Adjusted character limit
        """
        adjusted = int(base_limit * complexity.verbosity_multiplier)
        
        # Ensure we don't exceed reasonable bounds
        # Minimum 200 chars, maximum 2500 chars
        return max(200, min(2500, adjusted))
