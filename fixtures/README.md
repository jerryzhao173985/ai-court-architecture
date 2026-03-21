# VERITAS Case Library

This directory contains case content files for the VERITAS Courtroom Experience.

## Available Cases

### 1. Blackthorn Hall (blackthorn-hall-001)
**Title**: The Crown v. Marcus Ashford  
**Crime Type**: Murder  
**Setting**: Country estate in England  
**Synopsis**: A wealthy patron is found dead after threatening to expose a forged family will. The estate manager was the last person to see him alive.

**Key Features**:
- Traditional murder mystery
- Physical evidence and toxicology
- Timing inconsistencies create reasonable doubt
- Classic "whodunit" structure

**Evidence**: 7 items (physical, testimonial, documentary)  
**Ground Truth**: Not guilty

---

### 2. Digital Deception (digital-deception-002)
**Title**: The Crown v. Sarah Chen  
**Crime Type**: Fraud by Abuse of Position  
**Setting**: London financial district  
**Synopsis**: £2.3 million vanished from investment accounts using the credentials of a senior compliance officer. Was she the perpetrator or a victim of cybercriminals?

**Key Features**:
- Modern financial crime
- Digital forensics and cybersecurity evidence
- Technical complexity creates ambiguity
- Corporate victim vs. individual defendant

**Evidence**: 7 items (documentary, testimonial)  
**Ground Truth**: Not guilty

---

## Case Structure

Each case file follows this JSON structure:

```json
{
  "caseId": "unique-identifier",
  "title": "The Crown v. Defendant Name",
  "narrative": {
    "hookScene": "Atmospheric opening scene",
    "chargeText": "Formal criminal charge",
    "victimProfile": { ... },
    "defendantProfile": { ... },
    "witnessProfiles": [ ... ]
  },
  "evidence": [ ... ],
  "timeline": [ ... ],
  "groundTruth": {
    "actualVerdict": "guilty" | "not_guilty",
    "keyFacts": [ ... ],
    "reasoningCriteria": { ... }
  }
}
```

## Design Principles

All cases are designed to:

1. **Support Both Verdicts**: Evidence allows sound reasoning to reach either guilty or not guilty
2. **Create Ambiguity**: No single piece of evidence is conclusive
3. **Reward Reasoning**: The system evaluates reasoning quality independently from verdict correctness
4. **Follow Crown Court Procedure**: Cases work with the trial stage structure
5. **Meet Evidence Requirements**: 5-7 evidence items with chronological timeline

## Adding New Cases

To add a new case:

1. Create a JSON file following the structure above
2. Choose a unique case ID (format: `name-###`)
3. Select a different crime type from existing cases
4. Design 5-7 evidence items supporting both verdicts
5. Create character profiles for victim, defendant, and witnesses
6. Validate using `CaseManager.load_case()` and `CaseManager.validate_case()`
7. Document the case design in `docs/case-{case-id}.md`

## Validation

Cases are validated for:
- Required fields (narrative, evidence, timeline, groundTruth)
- Evidence count (5-7 items)
- Character profiles (victim, defendant, witnesses)
- Ground truth structure (verdict, key facts, reasoning criteria)
- Timeline consistency (events reference valid evidence IDs)
- JSON schema compliance

### Using the Validation Tool

The recommended way to validate cases is using the CLI validation tool:

```bash
# Validate a single case
python scripts/validate_case.py fixtures/blackthorn-hall-001.json

# Validate all cases
python scripts/validate_case.py fixtures/*.json

# Quiet mode (only show failures)
python scripts/validate_case.py -q fixtures/*.json
```

See [Case Validation Tool Documentation](../docs/case-validation-tool.md) for complete usage guide.

### Programmatic Validation

You can also validate cases programmatically using the CaseManager:

```python
from case_manager import CaseManager

manager = CaseManager('fixtures')
case = manager.load_case('case-id')
validation = manager.validate_case(case)
print(validation)
```

## Documentation

Each case has detailed design documentation in `docs/`:
- `docs/case-blackthorn-hall-001.md` (if created)
- `docs/case-digital-deception-002.md`

Documentation includes:
- Design rationale
- Crime type selection
- Character design
- Evidence structure
- Timeline construction
- Ground truth justification
- Technical considerations
