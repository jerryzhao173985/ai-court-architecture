"""Unit tests for case content validation tool.

Tests the CLI validation tool and CaseManager validation logic.
"""

import json
import tempfile
from pathlib import Path

import pytest

from case_manager import CaseManager, ValidationResult
from models import CaseContent


class TestCaseManagerValidation:
    """Test CaseManager validation logic."""
    
    def test_valid_case_blackthorn_hall(self):
        """Test that Blackthorn Hall case passes validation."""
        manager = CaseManager()
        case = manager.load_case("blackthorn-hall-001")
        
        result = manager.validate_case(case)
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_valid_case_digital_deception(self):
        """Test that Digital Deception case passes validation."""
        manager = CaseManager()
        case = manager.load_case("digital-deception-002")
        
        result = manager.validate_case(case)
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_evidence_count_constraint_minimum(self):
        """Test that cases with fewer than 5 evidence items fail validation."""
        manager = CaseManager()
        
        # Create a case with only 4 evidence items
        case_data = {
            "caseId": "test-001",
            "title": "Test Case",
            "narrative": {
                "hookScene": "Test scene",
                "chargeText": "Test charge",
                "victimProfile": {
                    "name": "Victim",
                    "role": "Victim",
                    "background": "Background",
                    "relevantFacts": ["Fact"]
                },
                "defendantProfile": {
                    "name": "Defendant",
                    "role": "Defendant",
                    "background": "Background",
                    "relevantFacts": ["Fact"]
                },
                "witnessProfiles": [
                    {
                        "name": "Witness",
                        "role": "Witness",
                        "background": "Background",
                        "relevantFacts": ["Fact"]
                    }
                ]
            },
            "evidence": [
                {
                    "id": f"evidence-{i:03d}",
                    "type": "physical",
                    "title": f"Evidence {i}",
                    "description": "Description",
                    "timestamp": "2024-01-15T14:30:00Z",
                    "presentedBy": "prosecution",
                    "significance": "Significance"
                }
                for i in range(1, 5)  # Only 4 items
            ],
            "timeline": [
                {
                    "timestamp": "2024-01-15T14:30:00Z",
                    "description": "Event",
                    "evidenceIds": ["evidence-001"]
                }
            ],
            "groundTruth": {
                "actualVerdict": "not_guilty",
                "keyFacts": ["Fact"],
                "reasoningCriteria": {
                    "requiredEvidenceReferences": ["evidence-001"],
                    "logicalFallacies": ["ad_hominem"],
                    "coherenceThreshold": 0.65
                }
            }
        }
        
        # Should fail Pydantic validation
        with pytest.raises(ValueError, match="Evidence items must be between 5 and 7"):
            CaseContent.model_validate(case_data)
    
    def test_evidence_count_constraint_maximum(self):
        """Test that cases with more than 7 evidence items fail validation."""
        manager = CaseManager()
        
        # Create a case with 8 evidence items
        case_data = {
            "caseId": "test-001",
            "title": "Test Case",
            "narrative": {
                "hookScene": "Test scene",
                "chargeText": "Test charge",
                "victimProfile": {
                    "name": "Victim",
                    "role": "Victim",
                    "background": "Background",
                    "relevantFacts": ["Fact"]
                },
                "defendantProfile": {
                    "name": "Defendant",
                    "role": "Defendant",
                    "background": "Background",
                    "relevantFacts": ["Fact"]
                },
                "witnessProfiles": [
                    {
                        "name": "Witness",
                        "role": "Witness",
                        "background": "Background",
                        "relevantFacts": ["Fact"]
                    }
                ]
            },
            "evidence": [
                {
                    "id": f"evidence-{i:03d}",
                    "type": "physical",
                    "title": f"Evidence {i}",
                    "description": "Description",
                    "timestamp": "2024-01-15T14:30:00Z",
                    "presentedBy": "prosecution",
                    "significance": "Significance"
                }
                for i in range(1, 9)  # 8 items
            ],
            "timeline": [
                {
                    "timestamp": "2024-01-15T14:30:00Z",
                    "description": "Event",
                    "evidenceIds": ["evidence-001"]
                }
            ],
            "groundTruth": {
                "actualVerdict": "not_guilty",
                "keyFacts": ["Fact"],
                "reasoningCriteria": {
                    "requiredEvidenceReferences": ["evidence-001"],
                    "logicalFallacies": ["ad_hominem"],
                    "coherenceThreshold": 0.65
                }
            }
        }
        
        # Should fail Pydantic validation
        with pytest.raises(ValueError, match="Evidence items must be between 5 and 7"):
            CaseContent.model_validate(case_data)
    
    def test_missing_required_fields(self):
        """Test that cases with missing required fields fail validation."""
        manager = CaseManager()
        
        # Create a minimal case missing ground truth
        case_data = {
            "caseId": "test-001",
            "title": "Test Case",
            "narrative": {
                "hookScene": "Test scene",
                "chargeText": "Test charge",
                "victimProfile": {
                    "name": "Victim",
                    "role": "Victim",
                    "background": "Background",
                    "relevantFacts": ["Fact"]
                },
                "defendantProfile": {
                    "name": "Defendant",
                    "role": "Defendant",
                    "background": "Background",
                    "relevantFacts": ["Fact"]
                },
                "witnessProfiles": []
            },
            "evidence": [
                {
                    "id": f"evidence-{i:03d}",
                    "type": "physical",
                    "title": f"Evidence {i}",
                    "description": "Description",
                    "timestamp": "2024-01-15T14:30:00Z",
                    "presentedBy": "prosecution",
                    "significance": "Significance"
                }
                for i in range(1, 6)
            ],
            "timeline": []
            # Missing groundTruth
        }
        
        # Should fail Pydantic validation
        with pytest.raises(ValueError):
            CaseContent.model_validate(case_data)
    
    def test_serialization_round_trip(self):
        """Test that serialization and deserialization preserves case content.
        
        Validates: Requirements 1.6
        """
        manager = CaseManager()
        original_case = manager.load_case("blackthorn-hall-001")
        
        # Serialize to JSON
        serialized = manager.serialize_case(original_case)
        
        # Deserialize back
        deserialized_case = manager.deserialize_case(serialized)
        
        # Should be equivalent
        assert deserialized_case.case_id == original_case.case_id
        assert deserialized_case.title == original_case.title
        assert len(deserialized_case.evidence) == len(original_case.evidence)
        assert len(deserialized_case.timeline) == len(original_case.timeline)
        assert deserialized_case.ground_truth.actual_verdict == original_case.ground_truth.actual_verdict


class TestCaseValidationCLI:
    """Test the CLI validation tool."""
    
    def test_validate_valid_case_file(self, tmp_path):
        """Test validating a valid case file."""
        from scripts.validate_case import CaseValidator
        
        # Create a valid case file
        case_data = {
            "caseId": "test-valid-001",
            "title": "Test Valid Case",
            "narrative": {
                "hookScene": "A compelling opening scene",
                "chargeText": "Test charge",
                "victimProfile": {
                    "name": "Test Victim",
                    "role": "Victim",
                    "background": "Background",
                    "relevantFacts": ["Fact 1", "Fact 2"]
                },
                "defendantProfile": {
                    "name": "Test Defendant",
                    "role": "Defendant",
                    "background": "Background",
                    "relevantFacts": ["Fact 1"]
                },
                "witnessProfiles": [
                    {
                        "name": "Test Witness",
                        "role": "Witness",
                        "background": "Background",
                        "relevantFacts": ["Fact 1"]
                    }
                ]
            },
            "evidence": [
                {
                    "id": f"evidence-{i:03d}",
                    "type": "physical",
                    "title": f"Evidence {i}",
                    "description": "Description",
                    "timestamp": f"2024-01-15T{14+i}:30:00Z",
                    "presentedBy": "prosecution" if i % 2 == 0 else "defence",
                    "significance": "Significance"
                }
                for i in range(1, 6)
            ],
            "timeline": [
                {
                    "timestamp": f"2024-01-15T{14+i}:30:00Z",
                    "description": f"Event {i}",
                    "evidenceIds": [f"evidence-{i:03d}"]
                }
                for i in range(1, 6)
            ],
            "groundTruth": {
                "actualVerdict": "not_guilty",
                "keyFacts": ["Fact 1", "Fact 2"],
                "reasoningCriteria": {
                    "requiredEvidenceReferences": ["evidence-001", "evidence-002"],
                    "logicalFallacies": ["ad_hominem", "appeal_to_emotion"],
                    "coherenceThreshold": 0.65
                }
            }
        }
        
        # Write to temp file
        case_file = tmp_path / "test-case.json"
        with open(case_file, 'w') as f:
            json.dump(case_data, f)
        
        # Validate
        validator = CaseValidator()
        is_valid = validator.validate_file(case_file)
        
        assert is_valid
        assert len(validator.errors) == 0
    
    def test_validate_invalid_timeline_references(self, tmp_path):
        """Test that invalid timeline evidence references are caught."""
        from scripts.validate_case import CaseValidator
        
        # Create a case with invalid timeline references
        case_data = {
            "caseId": "test-invalid-001",
            "title": "Test Invalid Case",
            "narrative": {
                "hookScene": "A compelling opening scene",
                "chargeText": "Test charge",
                "victimProfile": {
                    "name": "Test Victim",
                    "role": "Victim",
                    "background": "Background",
                    "relevantFacts": ["Fact 1"]
                },
                "defendantProfile": {
                    "name": "Test Defendant",
                    "role": "Defendant",
                    "background": "Background",
                    "relevantFacts": ["Fact 1"]
                },
                "witnessProfiles": [
                    {
                        "name": "Test Witness",
                        "role": "Witness",
                        "background": "Background",
                        "relevantFacts": ["Fact 1"]
                    }
                ]
            },
            "evidence": [
                {
                    "id": f"evidence-{i:03d}",
                    "type": "physical",
                    "title": f"Evidence {i}",
                    "description": "Description",
                    "timestamp": f"2024-01-15T{14+i}:30:00Z",
                    "presentedBy": "prosecution",
                    "significance": "Significance"
                }
                for i in range(1, 6)
            ],
            "timeline": [
                {
                    "timestamp": "2024-01-15T14:30:00Z",
                    "description": "Event",
                    "evidenceIds": ["evidence-999"]  # Non-existent evidence
                }
            ],
            "groundTruth": {
                "actualVerdict": "not_guilty",
                "keyFacts": ["Fact 1"],
                "reasoningCriteria": {
                    "requiredEvidenceReferences": ["evidence-001"],
                    "logicalFallacies": ["ad_hominem"],
                    "coherenceThreshold": 0.65
                }
            }
        }
        
        # Write to temp file
        case_file = tmp_path / "test-case.json"
        with open(case_file, 'w') as f:
            json.dump(case_data, f)
        
        # Validate
        validator = CaseValidator()
        is_valid = validator.validate_file(case_file)
        
        assert not is_valid
        assert any("evidence-999" in error for error in validator.errors)
    
    def test_validate_invalid_coherence_threshold(self, tmp_path):
        """Test that invalid coherence threshold is caught."""
        from scripts.validate_case import CaseValidator
        
        # Create a case with invalid coherence threshold
        case_data = {
            "caseId": "test-invalid-002",
            "title": "Test Invalid Case",
            "narrative": {
                "hookScene": "A compelling opening scene",
                "chargeText": "Test charge",
                "victimProfile": {
                    "name": "Test Victim",
                    "role": "Victim",
                    "background": "Background",
                    "relevantFacts": ["Fact 1"]
                },
                "defendantProfile": {
                    "name": "Test Defendant",
                    "role": "Defendant",
                    "background": "Background",
                    "relevantFacts": ["Fact 1"]
                },
                "witnessProfiles": [
                    {
                        "name": "Test Witness",
                        "role": "Witness",
                        "background": "Background",
                        "relevantFacts": ["Fact 1"]
                    }
                ]
            },
            "evidence": [
                {
                    "id": f"evidence-{i:03d}",
                    "type": "physical",
                    "title": f"Evidence {i}",
                    "description": "Description",
                    "timestamp": f"2024-01-15T{14+i}:30:00Z",
                    "presentedBy": "prosecution",
                    "significance": "Significance"
                }
                for i in range(1, 6)
            ],
            "timeline": [
                {
                    "timestamp": "2024-01-15T14:30:00Z",
                    "description": "Event",
                    "evidenceIds": ["evidence-001"]
                }
            ],
            "groundTruth": {
                "actualVerdict": "not_guilty",
                "keyFacts": ["Fact 1"],
                "reasoningCriteria": {
                    "requiredEvidenceReferences": ["evidence-001"],
                    "logicalFallacies": ["ad_hominem"],
                    "coherenceThreshold": 1.5  # Invalid: must be 0-1
                }
            }
        }
        
        # Write to temp file
        case_file = tmp_path / "test-case.json"
        with open(case_file, 'w') as f:
            json.dump(case_data, f)
        
        # Validate
        validator = CaseValidator()
        is_valid = validator.validate_file(case_file)
        
        assert not is_valid
        assert any("Coherence threshold" in error for error in validator.errors)
