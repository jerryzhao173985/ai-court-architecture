"""Unit tests for case complexity analyzer."""

import pytest
from src.complexity_analyzer import CaseComplexityAnalyzer
from src.models import (
    CaseContent, CaseNarrative, CharacterProfile, EvidenceItem,
    TimelineEvent, GroundTruth, ReasoningCriteria
)


@pytest.fixture
def simple_case():
    """Create a simple case with minimal complexity."""
    return CaseContent(
        caseId="simple-001",
        title="Simple Case",
        narrative=CaseNarrative(
            hookScene="A simple scene",
            chargeText="Murder charge",
            victimProfile=CharacterProfile(
                name="Victim",
                role="victim",
                background="Background",
                relevantFacts=["fact1"]
            ),
            defendantProfile=CharacterProfile(
                name="Defendant",
                role="defendant",
                background="Background",
                relevantFacts=["fact1"]
            ),
            witnessProfiles=[
                CharacterProfile(
                    name="Witness",
                    role="witness",
                    background="Background",
                    relevantFacts=["fact1"]
                )
            ]
        ),
        evidence=[
            EvidenceItem(
                id="e1",
                type="physical",
                title="Evidence 1",
                description="Short description",
                timestamp="2024-01-01T10:00:00Z",
                presentedBy="prosecution",
                significance="Minor"
            ),
            EvidenceItem(
                id="e2",
                type="physical",
                title="Evidence 2",
                description="Short description",
                timestamp="2024-01-01T11:00:00Z",
                presentedBy="defence",
                significance="Minor"
            ),
            EvidenceItem(
                id="e3",
                type="physical",
                title="Evidence 3",
                description="Short description",
                timestamp="2024-01-01T12:00:00Z",
                presentedBy="prosecution",
                significance="Minor"
            ),
            EvidenceItem(
                id="e4",
                type="physical",
                title="Evidence 4",
                description="Short description",
                timestamp="2024-01-01T13:00:00Z",
                presentedBy="defence",
                significance="Minor"
            ),
            EvidenceItem(
                id="e5",
                type="physical",
                title="Evidence 5",
                description="Short description",
                timestamp="2024-01-01T14:00:00Z",
                presentedBy="prosecution",
                significance="Minor"
            )
        ],
        timeline=[
            TimelineEvent(
                timestamp="2024-01-01T10:00:00Z",
                description="Event 1",
                evidenceIds=["e1"]
            ),
            TimelineEvent(
                timestamp="2024-01-01T11:00:00Z",
                description="Event 2",
                evidenceIds=["e2"]
            )
        ],
        groundTruth=GroundTruth(
            actualVerdict="guilty",
            keyFacts=["fact1", "fact2"],
            reasoningCriteria=ReasoningCriteria(
                requiredEvidenceReferences=["e1"],
                logicalFallacies=["ad_hominem"],
                coherenceThreshold=0.7
            )
        )
    )


@pytest.fixture
def complex_case():
    """Create a complex case with high complexity."""
    return CaseContent(
        caseId="complex-001",
        title="Complex Case",
        narrative=CaseNarrative(
            hookScene="A complex scene with many details",
            chargeText="Murder charge with multiple counts",
            victimProfile=CharacterProfile(
                name="Victim",
                role="victim",
                background="Detailed background",
                relevantFacts=["fact1", "fact2", "fact3"]
            ),
            defendantProfile=CharacterProfile(
                name="Defendant",
                role="defendant",
                background="Detailed background",
                relevantFacts=["fact1", "fact2", "fact3"]
            ),
            witnessProfiles=[
                CharacterProfile(
                    name="Witness 1",
                    role="witness",
                    background="Background",
                    relevantFacts=["fact1"]
                ),
                CharacterProfile(
                    name="Witness 2",
                    role="witness",
                    background="Background",
                    relevantFacts=["fact2"]
                ),
                CharacterProfile(
                    name="Witness 3",
                    role="witness",
                    background="Background",
                    relevantFacts=["fact3"]
                )
            ]
        ),
        evidence=[
            EvidenceItem(
                id="e1",
                type="physical",
                title="Physical Evidence 1",
                description="This is a very detailed description of the physical evidence that goes into great depth about the circumstances and implications of this particular piece of evidence in the case.",
                timestamp="2024-01-01T10:00:00Z",
                presentedBy="prosecution",
                significance="Critical"
            ),
            EvidenceItem(
                id="e2",
                type="testimonial",
                title="Testimonial Evidence 1",
                description="This is a very detailed description of the testimonial evidence that goes into great depth about the circumstances and implications of this particular piece of evidence in the case.",
                timestamp="2024-01-01T11:00:00Z",
                presentedBy="defence",
                significance="Critical"
            ),
            EvidenceItem(
                id="e3",
                type="documentary",
                title="Documentary Evidence 1",
                description="This is a very detailed description of the documentary evidence that goes into great depth about the circumstances and implications of this particular piece of evidence in the case.",
                timestamp="2024-01-01T12:00:00Z",
                presentedBy="prosecution",
                significance="Critical"
            ),
            EvidenceItem(
                id="e4",
                type="physical",
                title="Physical Evidence 2",
                description="This is a very detailed description of the physical evidence that goes into great depth about the circumstances and implications of this particular piece of evidence in the case.",
                timestamp="2024-01-01T13:00:00Z",
                presentedBy="defence",
                significance="Critical"
            ),
            EvidenceItem(
                id="e5",
                type="testimonial",
                title="Testimonial Evidence 2",
                description="This is a very detailed description of the testimonial evidence that goes into great depth about the circumstances and implications of this particular piece of evidence in the case.",
                timestamp="2024-01-01T14:00:00Z",
                presentedBy="prosecution",
                significance="Critical"
            ),
            EvidenceItem(
                id="e6",
                type="documentary",
                title="Documentary Evidence 2",
                description="This is a very detailed description of the documentary evidence that goes into great depth about the circumstances and implications of this particular piece of evidence in the case.",
                timestamp="2024-01-01T15:00:00Z",
                presentedBy="defence",
                significance="Critical"
            ),
            EvidenceItem(
                id="e7",
                type="physical",
                title="Physical Evidence 3",
                description="This is a very detailed description of the physical evidence that goes into great depth about the circumstances and implications of this particular piece of evidence in the case.",
                timestamp="2024-01-01T16:00:00Z",
                presentedBy="prosecution",
                significance="Critical"
            )
        ],
        timeline=[
            TimelineEvent(
                timestamp="2024-01-01T10:00:00Z",
                description="Event 1",
                evidenceIds=["e1"]
            ),
            TimelineEvent(
                timestamp="2024-01-01T11:00:00Z",
                description="Event 2",
                evidenceIds=["e2"]
            ),
            TimelineEvent(
                timestamp="2024-01-01T12:00:00Z",
                description="Event 3",
                evidenceIds=["e3"]
            ),
            TimelineEvent(
                timestamp="2024-01-01T13:00:00Z",
                description="Event 4",
                evidenceIds=["e4"]
            ),
            TimelineEvent(
                timestamp="2024-01-01T14:00:00Z",
                description="Event 5",
                evidenceIds=["e5"]
            ),
            TimelineEvent(
                timestamp="2024-01-01T15:00:00Z",
                description="Event 6",
                evidenceIds=["e6"]
            ),
            TimelineEvent(
                timestamp="2024-01-01T16:00:00Z",
                description="Event 7",
                evidenceIds=["e7"]
            )
        ],
        groundTruth=GroundTruth(
            actualVerdict="guilty",
            keyFacts=["fact1", "fact2", "fact3", "fact4", "fact5", "fact6"],
            reasoningCriteria=ReasoningCriteria(
                requiredEvidenceReferences=["e1", "e2", "e3"],
                logicalFallacies=["ad_hominem", "appeal_to_emotion"],
                coherenceThreshold=0.8
            )
        )
    )


def test_simple_case_complexity(simple_case):
    """Test that simple cases are classified correctly."""
    analyzer = CaseComplexityAnalyzer()
    
    complexity = analyzer.analyze_complexity(simple_case)
    
    assert complexity.level == "simple"
    assert complexity.verbosity_multiplier == 0.8
    assert complexity.argumentation_depth == "concise"


def test_complex_case_complexity(complex_case):
    """Test that complex cases are classified correctly."""
    analyzer = CaseComplexityAnalyzer()
    
    complexity = analyzer.analyze_complexity(complex_case)
    
    assert complexity.level == "complex"
    assert complexity.verbosity_multiplier == 1.2
    assert complexity.argumentation_depth == "detailed"


def test_complexity_guidance(simple_case):
    """Test that complexity guidance is generated."""
    analyzer = CaseComplexityAnalyzer()
    
    complexity = analyzer.analyze_complexity(simple_case)
    guidance = analyzer.get_complexity_guidance(complexity)
    
    assert "SIMPLE" in guidance
    assert "concise" in guidance.lower()


def test_character_limit_adjustment(simple_case, complex_case):
    """Test that character limits are adjusted based on complexity."""
    analyzer = CaseComplexityAnalyzer()
    
    simple_complexity = analyzer.analyze_complexity(simple_case)
    complex_complexity = analyzer.analyze_complexity(complex_case)
    
    base_limit = 1000
    
    simple_limit = analyzer.adjust_character_limit(base_limit, simple_complexity)
    complex_limit = analyzer.adjust_character_limit(base_limit, complex_complexity)
    
    # Simple cases should have lower limits
    assert simple_limit < base_limit
    assert complex_limit > base_limit
    
    # Limits should be within bounds
    assert 200 <= simple_limit <= 2500
    assert 200 <= complex_limit <= 2500


def test_character_limit_bounds(simple_case):
    """Test that character limits respect minimum and maximum bounds."""
    analyzer = CaseComplexityAnalyzer()
    
    complexity = analyzer.analyze_complexity(simple_case)
    
    # Test minimum bound
    very_small_limit = analyzer.adjust_character_limit(100, complexity)
    assert very_small_limit >= 200
    
    # Test maximum bound
    very_large_limit = analyzer.adjust_character_limit(5000, complexity)
    assert very_large_limit <= 2500
