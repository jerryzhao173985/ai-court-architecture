#!/usr/bin/env python3
"""CLI tool to validate case JSON files for VERITAS Courtroom Experience.

This tool validates case content files to ensure they meet all requirements:
- All required fields are present
- Evidence count is between 5 and 7 items
- Timeline events reference valid evidence IDs
- Character profiles are complete
- Ground truth data is properly structured
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from case_manager import CaseManager, ValidationResult
from models import CaseContent


class CaseValidator:
    """Enhanced case validator with detailed reporting."""
    
    def __init__(self):
        self.case_manager = CaseManager()
        self.errors = []
        self.warnings = []
    
    def validate_file(self, file_path: Path) -> bool:
        """Validate a case JSON file.
        
        Args:
            file_path: Path to the case JSON file
            
        Returns:
            True if validation passes, False otherwise
        """
        self.errors = []
        self.warnings = []
        
        # Check file exists
        if not file_path.exists():
            self.errors.append(f"File not found: {file_path}")
            return False
        
        # Check file extension
        if file_path.suffix != '.json':
            self.warnings.append(f"File does not have .json extension: {file_path}")
        
        # Read and parse JSON
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json_content = f.read()
        except Exception as e:
            self.errors.append(f"Failed to read file: {e}")
            return False
        
        # Parse JSON
        try:
            json_data = json.loads(json_content)
        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON: {e}")
            return False
        
        # Validate JSON structure
        if not isinstance(json_data, dict):
            self.errors.append("JSON root must be an object")
            return False
        
        # Deserialize and validate with Pydantic
        try:
            case_content = CaseContent.deserialize(json_content)
        except Exception as e:
            self.errors.append(f"Schema validation failed: {e}")
            return False
        
        # Run CaseManager validation
        validation_result = self.case_manager.validate_case(case_content)
        if not validation_result.is_valid:
            self.errors.extend(validation_result.errors)
            return False
        
        # Additional validation checks
        self._validate_timeline_consistency(case_content)
        self._validate_evidence_references(case_content)
        self._validate_character_completeness(case_content)
        self._validate_ground_truth(case_content)
        
        return len(self.errors) == 0
    
    def _validate_timeline_consistency(self, case: CaseContent) -> None:
        """Validate timeline events reference valid evidence IDs."""
        evidence_ids = {item.id for item in case.evidence}
        
        for i, event in enumerate(case.timeline):
            for evidence_id in event.evidence_ids:
                if evidence_id not in evidence_ids:
                    self.errors.append(
                        f"Timeline event {i} references non-existent evidence ID: {evidence_id}"
                    )
        
        # Check timeline is chronologically ordered
        timestamps = [event.timestamp for event in case.timeline]
        sorted_timestamps = sorted(timestamps)
        if timestamps != sorted_timestamps:
            self.warnings.append(
                "Timeline events are not in chronological order"
            )
    
    def _validate_evidence_references(self, case: CaseContent) -> None:
        """Validate evidence items and their references."""
        # Check evidence IDs are unique
        evidence_ids = [item.id for item in case.evidence]
        if len(evidence_ids) != len(set(evidence_ids)):
            self.errors.append("Evidence IDs must be unique")
        
        # Check evidence ID format
        for item in case.evidence:
            if not item.id.startswith('evidence-'):
                self.warnings.append(
                    f"Evidence ID '{item.id}' does not follow 'evidence-XXX' convention"
                )
        
        # Check ground truth references valid evidence
        if case.ground_truth and case.ground_truth.reasoning_criteria:
            required_refs = case.ground_truth.reasoning_criteria.required_evidence_references
            evidence_ids_set = set(evidence_ids)
            for ref in required_refs:
                if ref not in evidence_ids_set:
                    self.errors.append(
                        f"Ground truth references non-existent evidence ID: {ref}"
                    )
    
    def _validate_character_completeness(self, case: CaseContent) -> None:
        """Validate character profiles are complete."""
        # Validate victim profile
        if case.narrative.victim_profile:
            profile = case.narrative.victim_profile
            if not profile.name:
                self.errors.append("Victim profile missing name")
            if not profile.background:
                self.warnings.append("Victim profile missing background")
            if not profile.relevant_facts:
                self.warnings.append("Victim profile has no relevant facts")
        
        # Validate defendant profile
        if case.narrative.defendant_profile:
            profile = case.narrative.defendant_profile
            if not profile.name:
                self.errors.append("Defendant profile missing name")
            if not profile.background:
                self.warnings.append("Defendant profile missing background")
            if not profile.relevant_facts:
                self.warnings.append("Defendant profile has no relevant facts")
        
        # Validate witness profiles
        if not case.narrative.witness_profiles:
            self.warnings.append("No witness profiles defined")
        else:
            for i, profile in enumerate(case.narrative.witness_profiles):
                if not profile.name:
                    self.errors.append(f"Witness profile {i} missing name")
                if not profile.background:
                    self.warnings.append(f"Witness profile {i} missing background")
    
    def _validate_ground_truth(self, case: CaseContent) -> None:
        """Validate ground truth data is properly structured."""
        if not case.ground_truth:
            self.errors.append("Missing ground truth data")
            return
        
        # Check verdict is valid
        if case.ground_truth.actual_verdict not in ['guilty', 'not_guilty']:
            self.errors.append(
                f"Invalid actual verdict: {case.ground_truth.actual_verdict}"
            )
        
        # Check key facts exist
        if not case.ground_truth.key_facts:
            self.warnings.append("Ground truth has no key facts")
        
        # Check reasoning criteria
        if not case.ground_truth.reasoning_criteria:
            self.errors.append("Missing reasoning criteria in ground truth")
        else:
            criteria = case.ground_truth.reasoning_criteria
            if not criteria.required_evidence_references:
                self.warnings.append("No required evidence references in reasoning criteria")
            if not criteria.logical_fallacies:
                self.warnings.append("No logical fallacies defined in reasoning criteria")
            if not (0 <= criteria.coherence_threshold <= 1):
                self.errors.append(
                    f"Coherence threshold must be between 0 and 1, got {criteria.coherence_threshold}"
                )
    
    def print_results(self, file_path: Path, is_valid: bool) -> None:
        """Print validation results in a user-friendly format."""
        print(f"\n{'='*70}")
        print(f"Validating: {file_path}")
        print(f"{'='*70}\n")
        
        if is_valid and not self.warnings:
            print("✓ VALID - All checks passed!")
        elif is_valid and self.warnings:
            print("✓ VALID - With warnings")
        else:
            print("✗ INVALID - Validation failed")
        
        if self.errors:
            print(f"\n{len(self.errors)} Error(s):")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")
        
        if self.warnings:
            print(f"\n{len(self.warnings)} Warning(s):")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")
        
        print()


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Validate VERITAS case JSON files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate a single case file
  python scripts/validate_case.py fixtures/blackthorn-hall-001.json
  
  # Validate all case files in a directory
  python scripts/validate_case.py fixtures/*.json
  
  # Quiet mode (only show errors)
  python scripts/validate_case.py -q fixtures/my-case.json
        """
    )
    
    parser.add_argument(
        'files',
        nargs='+',
        type=Path,
        help='Case JSON file(s) to validate'
    )
    
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Quiet mode - only show validation failures'
    )
    
    parser.add_argument(
        '--no-warnings',
        action='store_true',
        help='Suppress warnings, only show errors'
    )
    
    args = parser.parse_args()
    
    validator = CaseValidator()
    all_valid = True
    results = []
    
    # Validate each file
    for file_path in args.files:
        is_valid = validator.validate_file(file_path)
        results.append((file_path, is_valid, list(validator.errors), list(validator.warnings)))
        
        if not is_valid:
            all_valid = False
        
        # Print results unless in quiet mode and valid
        if not (args.quiet and is_valid):
            if args.no_warnings:
                validator.warnings = []
            validator.print_results(file_path, is_valid)
    
    # Print summary if multiple files
    if len(args.files) > 1:
        print(f"{'='*70}")
        print("SUMMARY")
        print(f"{'='*70}\n")
        
        valid_count = sum(1 for _, is_valid, _, _ in results if is_valid)
        invalid_count = len(results) - valid_count
        
        print(f"Total files: {len(results)}")
        print(f"Valid: {valid_count}")
        print(f"Invalid: {invalid_count}")
        
        if invalid_count > 0:
            print("\nFailed files:")
            for file_path, is_valid, _, _ in results:
                if not is_valid:
                    print(f"  - {file_path}")
        
        print()
    
    # Exit with appropriate code
    sys.exit(0 if all_valid else 1)


if __name__ == '__main__':
    main()
