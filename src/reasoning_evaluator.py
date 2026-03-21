"""Reasoning evaluation component for assessing user's deliberation quality."""

import re
from typing import Literal
from models import CaseContent, EvidenceItem
from session import ReasoningAssessment, DeliberationTurn


class ReasoningEvaluator:
    """
    Analyzes user's deliberation statements to assess reasoning quality.
    
    Tracks evidence references, detects logical fallacies, calculates
    coherence, and produces four-category assessment.
    """

    def __init__(self, case_content: CaseContent):
        """
        Initialize reasoning evaluator with case content.
        
        Args:
            case_content: The case content for evaluation context
        """
        self.case_content = case_content
        self.ground_truth = case_content.ground_truth
        
        # Common logical fallacies to detect
        self.fallacy_patterns = {
            "ad_hominem": [
                r"(?i)(he|she|they)\s+(is|are)\s+(just|obviously|clearly)\s+\w+",
                r"(?i)can't trust (him|her|them)",
                r"(?i)(liar|dishonest|untrustworthy)"
            ],
            "appeal_to_emotion": [
                r"(?i)(think about|imagine|feel)",
                r"(?i)(tragic|heartbreaking|terrible)",
                r"(?i)(deserve|victim|suffer)"
            ],
            "false_dichotomy": [
                r"(?i)(either|only two|must be)",
                r"(?i)(no other|no alternative)",
                r"(?i)(black and white|one or the other)"
            ],
            "hasty_generalization": [
                r"(?i)(always|never|everyone|no one)",
                r"(?i)(all \w+ are)",
                r"(?i)(every time)"
            ],
            "straw_man": [
                r"(?i)(so you're saying|what you mean is)",
                r"(?i)(basically claiming|suggesting that)"
            ]
        }

    async def analyze_statements(self, statements: list[DeliberationTurn], user_verdict: Literal["guilty", "not_guilty"]) -> ReasoningAssessment:
        """
        Analyze all user statements to produce reasoning assessment.
        
        Args:
            statements: List of user's deliberation statements
            user_verdict: The verdict the user voted for
            
        Returns:
            Complete reasoning assessment
        """
        # Extract user statements only
        user_statements = [s for s in statements if s.juror_id == "juror_human"]
        
        # Track evidence references
        evidence_refs = self.track_evidence_references(user_statements)
        evidence_score = self._calculate_evidence_score(evidence_refs)
        
        # Detect fallacies
        fallacies = self.detect_fallacies(user_statements)
        
        # Calculate coherence
        coherence_score = self.calculate_coherence(user_statements)
        
        # Determine if verdict is correct
        is_correct = user_verdict == self.ground_truth.actual_verdict
        
        # Determine reasoning quality (sound vs weak)
        is_sound = self._is_reasoning_sound(evidence_score, coherence_score, fallacies)
        
        # Categorize into four outcomes
        if is_sound and is_correct:
            category = "sound_correct"
        elif is_sound and not is_correct:
            category = "sound_incorrect"
        elif not is_sound and is_correct:
            category = "weak_correct"
        else:
            category = "weak_incorrect"
        
        # Generate feedback
        feedback = self.generate_feedback(category, evidence_refs, fallacies, coherence_score)
        
        return ReasoningAssessment(
            category=category,
            evidence_score=evidence_score,
            coherence_score=coherence_score,
            fallacies_detected=fallacies,
            feedback=feedback
        )

    def track_evidence_references(self, statements: list[DeliberationTurn]) -> list[str]:
        """
        Extract evidence item references from statements.
        
        Args:
            statements: User's deliberation statements
            
        Returns:
            List of evidence IDs referenced
        """
        referenced_ids = set()
        
        for statement in statements:
            # Add explicitly tracked references
            referenced_ids.update(statement.evidence_references)
            
            # Also search for evidence mentions in text
            for evidence in self.case_content.evidence:
                # Check for evidence ID
                if evidence.id.lower() in statement.statement.lower():
                    referenced_ids.add(evidence.id)
                
                # Check for evidence title
                if evidence.title.lower() in statement.statement.lower():
                    referenced_ids.add(evidence.id)
                
                # Check for key terms from description
                key_terms = self._extract_key_terms(evidence.title)
                for term in key_terms:
                    if term.lower() in statement.statement.lower():
                        referenced_ids.add(evidence.id)
        
        return list(referenced_ids)

    def _extract_key_terms(self, text: str) -> list[str]:
        """Extract key terms from text (3+ character words)."""
        words = re.findall(r'\b\w{3,}\b', text)
        # Filter out common words
        common = {'the', 'and', 'for', 'with', 'from', 'that', 'this', 'was', 'were'}
        return [w for w in words if w.lower() not in common]

    def _calculate_evidence_score(self, referenced_ids: list[str]) -> float:
        """
        Calculate evidence reference score (0-1).
        
        Args:
            referenced_ids: List of evidence IDs referenced
            
        Returns:
            Score from 0 to 1
        """
        required_refs = self.ground_truth.reasoning_criteria.required_evidence_references
        
        if not required_refs:
            # If no specific requirements, score based on coverage
            total_evidence = len(self.case_content.evidence)
            return min(len(referenced_ids) / max(total_evidence * 0.6, 1), 1.0)
        
        # Score based on required evidence coverage
        referenced_required = sum(1 for ref in required_refs if ref in referenced_ids)
        return referenced_required / len(required_refs)

    def detect_fallacies(self, statements: list[DeliberationTurn]) -> list[str]:
        """
        Detect logical fallacies in statements.
        
        Args:
            statements: User's deliberation statements
            
        Returns:
            List of detected fallacy types
        """
        detected = set()
        
        for statement in statements:
            text = statement.statement
            
            for fallacy_type, patterns in self.fallacy_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, text):
                        detected.add(fallacy_type)
                        break
        
        return list(detected)

    def calculate_coherence(self, statements: list[DeliberationTurn]) -> float:
        """
        Calculate logical coherence score (0-1).
        
        Args:
            statements: User's deliberation statements
            
        Returns:
            Coherence score from 0 to 1
        """
        if not statements:
            return 0.0
        
        # Simple heuristic-based coherence scoring
        score = 1.0
        
        # Check for contradictions (simplified)
        texts = [s.statement.lower() for s in statements]
        
        # Penalty for very short statements (lack of reasoning)
        avg_length = sum(len(s.statement.split()) for s in statements) / len(statements)
        if avg_length < 10:
            score -= 0.3
        
        # Bonus for logical connectors
        connectors = ['because', 'therefore', 'however', 'although', 'since', 'thus']
        connector_count = sum(1 for text in texts for conn in connectors if conn in text)
        score += min(connector_count * 0.1, 0.3)
        
        # Penalty for excessive repetition
        unique_ratio = len(set(texts)) / len(texts)
        if unique_ratio < 0.5:
            score -= 0.2
        
        return max(0.0, min(score, 1.0))

    def _is_reasoning_sound(self, evidence_score: float, coherence_score: float, fallacies: list[str]) -> bool:
        """
        Determine if reasoning is sound based on scores and fallacies.
        
        Args:
            evidence_score: Evidence reference score
            coherence_score: Logical coherence score
            fallacies: List of detected fallacies
            
        Returns:
            True if reasoning is sound, False if weak
        """
        # Get threshold from case criteria
        coherence_threshold = self.ground_truth.reasoning_criteria.coherence_threshold
        
        # Sound reasoning requires:
        # 1. Good evidence usage (>0.5)
        # 2. Coherence above threshold
        # 3. No more than 1 fallacy
        
        return (
            evidence_score >= 0.5 and
            coherence_score >= coherence_threshold and
            len(fallacies) <= 1
        )

    def generate_feedback(self, category: str, evidence_refs: list[str], 
                         fallacies: list[str], coherence_score: float) -> str:
        """
        Generate user-facing feedback based on assessment.
        
        Args:
            category: The reasoning category
            evidence_refs: Evidence items referenced
            fallacies: Detected fallacies
            coherence_score: Coherence score
            
        Returns:
            Feedback text
        """
        feedback_parts = []
        
        # Category-specific opening
        if category == "sound_correct":
            feedback_parts.append("Excellent reasoning! You reached the correct verdict through sound logical analysis.")
        elif category == "sound_incorrect":
            feedback_parts.append("Strong reasoning, though you reached a different conclusion than the evidence ultimately supports.")
        elif category == "weak_correct":
            feedback_parts.append("You reached the correct verdict, but your reasoning could be strengthened.")
        else:  # weak_incorrect
            feedback_parts.append("Your reasoning needs improvement, and the verdict differs from what the evidence supports.")
        
        # Evidence feedback
        evidence_count = len(evidence_refs)
        total_evidence = len(self.case_content.evidence)
        
        if evidence_count >= total_evidence * 0.6:
            feedback_parts.append(f"You referenced {evidence_count} pieces of evidence, showing good engagement with the facts.")
        elif evidence_count >= total_evidence * 0.3:
            feedback_parts.append(f"You referenced {evidence_count} pieces of evidence. Consider engaging more deeply with all available facts.")
        else:
            feedback_parts.append(f"You only referenced {evidence_count} pieces of evidence. Stronger arguments cite more facts.")
        
        # Fallacy feedback
        if fallacies:
            fallacy_names = [f.replace('_', ' ').title() for f in fallacies]
            feedback_parts.append(f"Logical fallacies detected: {', '.join(fallacy_names)}. Avoid these to strengthen your arguments.")
        else:
            feedback_parts.append("No logical fallacies detected in your reasoning.")
        
        # Coherence feedback
        if coherence_score >= 0.8:
            feedback_parts.append("Your arguments were logically coherent and well-structured.")
        elif coherence_score >= 0.6:
            feedback_parts.append("Your arguments showed reasonable coherence but could be more structured.")
        else:
            feedback_parts.append("Your arguments lacked clear logical structure. Use connectors like 'because' and 'therefore'.")
        
        return " ".join(feedback_parts)
