"""Core data models for VERITAS courtroom experience."""

from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator


class CharacterProfile(BaseModel):
    """Profile for a character in the case (victim, defendant, witness)."""
    name: str
    role: str
    background: str
    relevant_facts: list[str] = Field(alias="relevantFacts")

    class Config:
        populate_by_name = True


class EvidenceItem(BaseModel):
    """Individual piece of case evidence."""
    id: str
    type: Literal["physical", "testimonial", "documentary"]
    title: str
    description: str
    timestamp: str  # ISO 8601 format
    presented_by: Literal["prosecution", "defence"] = Field(alias="presentedBy")
    significance: str

    class Config:
        populate_by_name = True


class TimelineEvent(BaseModel):
    """Event on the case timeline."""
    timestamp: str  # ISO 8601 format
    description: str
    evidence_ids: list[str] = Field(alias="evidenceIds")

    class Config:
        populate_by_name = True


class ReasoningCriteria(BaseModel):
    """Criteria for evaluating reasoning quality."""
    required_evidence_references: list[str] = Field(alias="requiredEvidenceReferences")
    logical_fallacies: list[str] = Field(alias="logicalFallacies")
    coherence_threshold: float = Field(alias="coherenceThreshold")

    class Config:
        populate_by_name = True


class GroundTruth(BaseModel):
    """Ground truth information for case evaluation."""
    actual_verdict: Literal["guilty", "not_guilty"] = Field(alias="actualVerdict")
    key_facts: list[str] = Field(alias="keyFacts")
    reasoning_criteria: ReasoningCriteria = Field(alias="reasoningCriteria")

    class Config:
        populate_by_name = True


class CaseNarrative(BaseModel):
    """Narrative elements of the case."""
    hook_scene: str = Field(alias="hookScene")
    charge_text: str = Field(alias="chargeText")
    victim_profile: CharacterProfile = Field(alias="victimProfile")
    defendant_profile: CharacterProfile = Field(alias="defendantProfile")
    witness_profiles: list[CharacterProfile] = Field(alias="witnessProfiles")

    class Config:
        populate_by_name = True


class CaseContent(BaseModel):
    """Complete case content structure."""
    case_id: str = Field(alias="caseId")
    title: str
    narrative: CaseNarrative
    evidence: list[EvidenceItem]
    timeline: list[TimelineEvent]
    ground_truth: GroundTruth = Field(alias="groundTruth")

    @field_validator("evidence")
    @classmethod
    def validate_evidence_count(cls, v: list[EvidenceItem]) -> list[EvidenceItem]:
        """Validate that evidence items are between 5 and 7."""
        if not (5 <= len(v) <= 7):
            raise ValueError(f"Evidence items must be between 5 and 7, got {len(v)}")
        return v

    class Config:
        populate_by_name = True

    def serialize(self) -> str:
        """Serialize case content to JSON string."""
        return self.model_dump_json(by_alias=True, indent=2)

    @classmethod
    def deserialize(cls, json_str: str) -> "CaseContent":
        """Deserialize case content from JSON string."""
        return cls.model_validate_json(json_str)
