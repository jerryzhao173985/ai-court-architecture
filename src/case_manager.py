"""Case manager component for loading and validating case content."""

import json
from pathlib import Path
from typing import Optional
import logging

from models import CaseContent, EvidenceItem
from cache import get_response_cache

logger = logging.getLogger("veritas")


class ValidationResult:
    """Result of case content validation."""
    
    def __init__(self, is_valid: bool, errors: Optional[list[str]] = None):
        self.is_valid = is_valid
        self.errors = errors or []
    
    def __bool__(self) -> bool:
        return self.is_valid
    
    def __repr__(self) -> str:
        if self.is_valid:
            return "ValidationResult(valid=True)"
        return f"ValidationResult(valid=False, errors={self.errors})"


class CaseManager:
    """Manages case content loading, validation, and access."""
    
    def __init__(self, cases_directory: str = "fixtures"):
        """Initialize case manager with cases directory path.
        
        Args:
            cases_directory: Path to directory containing case JSON files
        """
        # Handle both relative paths from src/ and from project root
        cases_path = Path(cases_directory)
        if not cases_path.exists():
            # Try from parent directory (when running from src/)
            cases_path = Path("..") / cases_directory
        
        self.cases_directory = cases_path
        self._cache = get_response_cache()
    
    def load_case(self, case_id: str) -> CaseContent:
        """Load and validate a case from JSON file.
        
        Args:
            case_id: Identifier for the case to load
            
        Returns:
            Validated CaseContent object
            
        Raises:
            FileNotFoundError: If case file doesn't exist
            ValueError: If case content is invalid
            json.JSONDecodeError: If JSON is malformed
        """
        # Check cache first (with TTL)
        cached_case = self._cache.get_case_content(case_id)
        if cached_case is not None:
            logger.debug(f"Loaded case {case_id} from cache")
            return cached_case
        
        # Construct file path
        case_file = self.cases_directory / f"{case_id}.json"
        
        if not case_file.exists():
            raise FileNotFoundError(f"Case file not found: {case_file}")
        
        # Read and parse JSON
        with open(case_file, 'r', encoding='utf-8') as f:
            json_content = f.read()
        
        # Deserialize and validate
        case_content = CaseContent.deserialize(json_content)
        
        # Additional validation
        validation_result = self.validate_case(case_content)
        if not validation_result.is_valid:
            raise ValueError(f"Case validation failed: {', '.join(validation_result.errors)}")
        
        # Cache the loaded case with TTL
        self._cache.set_case_content(case_id, case_content)
        logger.info(f"Loaded and cached case {case_id}")
        
        return case_content
    
    def validate_case(self, content: CaseContent) -> ValidationResult:
        """Validate case content has all required fields and constraints.
        
        Args:
            content: CaseContent object to validate
            
        Returns:
            ValidationResult indicating if case is valid
        """
        errors = []
        
        # Validate narrative fields
        if not content.narrative.hook_scene:
            errors.append("Missing hookScene in narrative")
        if not content.narrative.charge_text:
            errors.append("Missing chargeText in narrative")
        if not content.narrative.victim_profile:
            errors.append("Missing victimProfile in narrative")
        if not content.narrative.defendant_profile:
            errors.append("Missing defendantProfile in narrative")
        if not content.narrative.witness_profiles:
            errors.append("Missing witnessProfiles in narrative")
        
        # Validate evidence array (5-7 items constraint already enforced by Pydantic)
        if not content.evidence:
            errors.append("Missing evidence array")
        elif not (5 <= len(content.evidence) <= 7):
            errors.append(f"Evidence items must be between 5 and 7, got {len(content.evidence)}")
        
        # Validate timeline
        if not content.timeline:
            errors.append("Missing timeline")
        
        # Validate ground truth
        if not content.ground_truth:
            errors.append("Missing groundTruth")
        else:
            if not content.ground_truth.actual_verdict:
                errors.append("Missing actualVerdict in groundTruth")
            if not content.ground_truth.key_facts:
                errors.append("Missing keyFacts in groundTruth")
            if not content.ground_truth.reasoning_criteria:
                errors.append("Missing reasoningCriteria in groundTruth")
        
        # Validate character profiles have required fields
        if content.narrative.victim_profile and not content.narrative.victim_profile.name:
            errors.append("Victim profile missing name")
        if content.narrative.defendant_profile and not content.narrative.defendant_profile.name:
            errors.append("Defendant profile missing name")
        
        return ValidationResult(is_valid=len(errors) == 0, errors=errors)
    
    def get_evidence_items(self, case_id: Optional[str] = None, 
                          case_content: Optional[CaseContent] = None) -> list[EvidenceItem]:
        """Get all evidence items for a case.
        
        Args:
            case_id: Case identifier (if loading from cache/file)
            case_content: CaseContent object (if already loaded)
            
        Returns:
            List of evidence items
            
        Raises:
            ValueError: If neither case_id nor case_content provided
        """
        if case_content:
            return case_content.evidence
        elif case_id:
            case = self.load_case(case_id)
            return case.evidence
        else:
            raise ValueError("Must provide either case_id or case_content")
    
    def get_evidence_by_timestamp(self, case_id: Optional[str] = None,
                                  case_content: Optional[CaseContent] = None) -> list[EvidenceItem]:
        """Get evidence items sorted chronologically by timestamp.
        
        Args:
            case_id: Case identifier (if loading from cache/file)
            case_content: CaseContent object (if already loaded)
            
        Returns:
            List of evidence items sorted by timestamp
            
        Raises:
            ValueError: If neither case_id nor case_content provided
        """
        evidence_items = self.get_evidence_items(case_id=case_id, case_content=case_content)
        return sorted(evidence_items, key=lambda item: item.timestamp)
    
    def serialize_case(self, case_content: CaseContent) -> str:
        """Serialize case content to JSON string.
        
        Args:
            case_content: CaseContent object to serialize
            
        Returns:
            JSON string representation
        """
        return case_content.serialize()
    
    def deserialize_case(self, json_str: str) -> CaseContent:
        """Deserialize case content from JSON string.
        
        Args:
            json_str: JSON string to deserialize
            
        Returns:
            CaseContent object
            
        Raises:
            ValueError: If JSON is invalid or doesn't match schema
        """
        return CaseContent.deserialize(json_str)
    
    def list_available_cases(self) -> list[tuple[str, str]]:
        """List all available case files in the cases directory.
        
        Scans the cases directory for *.json files, loads and validates each,
        and returns a list of (case_id, title) tuples.
        
        Returns:
            List of (case_id, title) tuples for all valid cases
        """
        available_cases = []
        
        # Scan directory for JSON files
        if not self.cases_directory.exists():
            logger.warning(f"Cases directory not found: {self.cases_directory}")
            return available_cases
        
        for case_file in self.cases_directory.glob("*.json"):
            # Skip sample_case.json as it's a template
            if case_file.stem == "sample_case":
                continue
            
            case_id = case_file.stem
            
            try:
                # Try to load and validate the case
                case_content = self.load_case(case_id)
                available_cases.append((case_id, case_content.title))
                logger.debug(f"Found valid case: {case_id} - {case_content.title}")
            except Exception as e:
                logger.warning(f"Skipping invalid case file {case_file}: {e}")
                continue

        return sorted(available_cases)  # Consistent ordering for number-based selection

    def resolve_case_id(self, query: str) -> Optional[tuple[str, str]]:
        """Resolve a user query to a case_id.

        Supports:
        - Number: "1", "2" → picks by position in sorted list
        - Partial match: "blackthorn", "digital" → matches against case_id or title
        - Full case_id: "blackthorn-hall-001" → exact match

        Args:
            query: User input (number, partial name, or full case_id)

        Returns:
            (case_id, title) tuple if found, None if no match
        """
        available = self.list_available_cases()
        if not available:
            return None

        # Try as number (1-indexed)
        try:
            idx = int(query) - 1
            if 0 <= idx < len(available):
                return available[idx]
        except ValueError:
            pass

        # Try exact match on case_id
        for case_id, title in available:
            if case_id == query:
                return (case_id, title)

        # Try partial match on case_id or title (case-insensitive)
        query_lower = query.lower()
        matches = [(cid, t) for cid, t in available
                   if query_lower in cid.lower() or query_lower in t.lower()]
        if len(matches) == 1:
            return matches[0]

        return None
