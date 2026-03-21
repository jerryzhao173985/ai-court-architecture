# Case Content Validation Tool

## Overview

The case content validation tool (`scripts/validate_case.py`) is a CLI utility for validating VERITAS case JSON files before adding them to the system. It ensures case files meet all structural requirements and constraints defined in the design specification.

## Features

The validation tool checks:

1. **Required Fields**: All mandatory fields are present (narrative, evidence, timeline, groundTruth)
2. **Evidence Count**: Between 5 and 7 evidence items (Requirement 1.3)
3. **Timeline Consistency**: Timeline events reference valid evidence IDs (Requirement 1.5)
4. **Character Profiles**: Victim, defendant, and witness profiles are complete (Requirement 1.4)
5. **Ground Truth**: Proper structure with valid verdict, key facts, and reasoning criteria (Requirement 1.5)
6. **Evidence References**: Ground truth references valid evidence IDs
7. **Coherence Threshold**: Value between 0 and 1
8. **JSON Structure**: Valid JSON syntax and schema compliance

## Installation

The tool is part of the VERITAS project and requires Python 3.10+. No additional installation is needed if you have the project dependencies installed.

```bash
# Ensure you're in the project root and have activated the virtual environment
source venv/bin/activate  # On Unix/macOS
# or
venv\Scripts\activate  # On Windows

# Optional: Install the package in development mode to use the console script
pip install -e .
```

After installing in development mode, you can use the `validate-case` command directly:

```bash
validate-case fixtures/blackthorn-hall-001.json
```

Otherwise, use the script directly:

```bash
python scripts/validate_case.py fixtures/blackthorn-hall-001.json
```

## Usage

### Basic Usage

Validate a single case file:

```bash
python scripts/validate_case.py fixtures/blackthorn-hall-001.json
```

### Validate Multiple Files

Validate all case files in a directory:

```bash
python scripts/validate_case.py fixtures/*.json
```

Or specify multiple files explicitly:

```bash
python scripts/validate_case.py fixtures/case1.json fixtures/case2.json
```

### Quiet Mode

Only show validation failures (useful for CI/CD):

```bash
python scripts/validate_case.py -q fixtures/*.json
```

### Suppress Warnings

Only show errors, hide warnings:

```bash
python scripts/validate_case.py --no-warnings fixtures/my-case.json
```

## Output Format

### Valid Case

```
======================================================================
Validating: fixtures/blackthorn-hall-001.json
======================================================================

✓ VALID - All checks passed!
```

### Invalid Case

```
======================================================================
Validating: fixtures/invalid-case.json
======================================================================

✗ INVALID - Validation failed

3 Error(s):
  1. Timeline event 0 references non-existent evidence ID: evidence-999
  2. Ground truth references non-existent evidence ID: evidence-999
  3. Coherence threshold must be between 0 and 1, got 1.5

1 Warning(s):
  1. Defendant profile has no relevant facts
```

### Multiple Files Summary

When validating multiple files, a summary is displayed:

```
======================================================================
SUMMARY
======================================================================

Total files: 3
Valid: 2
Invalid: 1

Failed files:
  - fixtures/invalid-case.json
```

## Exit Codes

- `0`: All files passed validation
- `1`: One or more files failed validation

This makes the tool suitable for use in CI/CD pipelines:

```bash
# In a CI script
python scripts/validate_case.py fixtures/*.json
if [ $? -ne 0 ]; then
    echo "Case validation failed!"
    exit 1
fi
```

## Validation Rules

### Required Fields

All case files must include:

- `caseId`: Unique identifier
- `title`: Case title
- `narrative`: Complete narrative structure
  - `hookScene`: Opening scene text
  - `chargeText`: Formal charge reading
  - `victimProfile`: Victim character profile
  - `defendantProfile`: Defendant character profile
  - `witnessProfiles`: Array of witness profiles
- `evidence`: Array of 5-7 evidence items
- `timeline`: Array of timeline events
- `groundTruth`: Ground truth data
  - `actualVerdict`: "guilty" or "not_guilty"
  - `keyFacts`: Array of key facts
  - `reasoningCriteria`: Reasoning evaluation criteria

### Evidence Count Constraint

Cases must have exactly 5, 6, or 7 evidence items. This constraint ensures:
- Sufficient evidence for meaningful deliberation
- Not overwhelming users with too much information
- Balanced trial experience within 15-minute timeframe

### Timeline Consistency

Timeline events must reference valid evidence IDs. The tool checks:
- All `evidenceIds` in timeline events exist in the evidence array
- Evidence IDs are unique
- Evidence IDs follow the `evidence-XXX` naming convention (warning if not)

### Character Profile Completeness

Character profiles must include:
- `name`: Character's full name (required)
- `role`: Character's role in the case (required)
- `background`: Character background information (warning if missing)
- `relevantFacts`: Array of relevant facts (warning if empty)

### Ground Truth Validation

Ground truth data must include:
- Valid verdict: "guilty" or "not_guilty"
- Key facts array (warning if empty)
- Reasoning criteria with:
  - `requiredEvidenceReferences`: Must reference valid evidence IDs
  - `logicalFallacies`: Array of fallacy types to detect
  - `coherenceThreshold`: Value between 0 and 1

## Common Validation Errors

### Evidence Count Error

```
Error: Evidence items must be between 5 and 7, got 4
```

**Solution**: Add more evidence items to reach the minimum of 5.

### Timeline Reference Error

```
Error: Timeline event 0 references non-existent evidence ID: evidence-999
```

**Solution**: Update the timeline event to reference a valid evidence ID from your evidence array.

### Invalid Coherence Threshold

```
Error: Coherence threshold must be between 0 and 1, got 1.5
```

**Solution**: Set `coherenceThreshold` to a value between 0 and 1 (e.g., 0.65).

### Missing Required Field

```
Error: Missing hookScene in narrative
```

**Solution**: Add the missing field to your case JSON.

## Integration with Development Workflow

### Pre-commit Hook

Add validation to your pre-commit workflow:

```bash
# .git/hooks/pre-commit
#!/bin/bash
python scripts/validate_case.py fixtures/*.json
```

### CI/CD Pipeline

Example GitHub Actions workflow:

```yaml
- name: Validate Case Files
  run: |
    python scripts/validate_case.py fixtures/*.json
```

### Case Authoring Workflow

1. Create new case JSON file in `fixtures/` directory
2. Run validation: `python scripts/validate_case.py fixtures/your-case.json`
3. Fix any errors or warnings
4. Re-validate until all checks pass
5. Test case in the system
6. Commit validated case file

## Related Documentation

- [Case Content Authoring Guidelines](../docs/case-authoring-guidelines.md) - Guidelines for creating effective cases
- [Requirements Document](../.kiro/specs/veritas-courtroom-experience/requirements.md) - Full requirements specification
- [Design Document](../.kiro/specs/veritas-courtroom-experience/design.md) - System design and architecture

## Troubleshooting

### Import Errors

If you see import errors when running the tool:

```bash
# Ensure you're in the project root directory
cd /path/to/veritas-courtroom-experience

# Activate virtual environment
source venv/bin/activate

# Run the tool
python scripts/validate_case.py fixtures/your-case.json
```

### JSON Syntax Errors

If you see "Invalid JSON" errors:

1. Use a JSON validator (e.g., jsonlint.com) to check syntax
2. Ensure all strings are properly quoted
3. Check for trailing commas (not allowed in JSON)
4. Verify all brackets and braces are balanced

### Schema Validation Errors

If you see Pydantic validation errors:

1. Check the error message for the specific field that failed
2. Refer to the `models.py` file for the expected schema
3. Ensure field names use camelCase (e.g., `caseId`, not `case_id`)
4. Verify data types match the schema (strings, arrays, objects)

## Future Enhancements

Potential improvements for future versions:

- JSON schema export for IDE autocomplete
- Interactive validation mode with fix suggestions
- Batch validation with parallel processing
- Integration with case authoring tools
- Validation report export (JSON, HTML)
- Custom validation rules configuration
