# Task 21.5: LLM-Based Fact Checker Implementation

## Overview

Implemented LLM-based contradiction detection for the fact checker agent in the VERITAS courtroom experience. The fact checker now uses AI to analyze statements from prosecution and defence agents, comparing them against case evidence to detect factual contradictions **and automatically intervenes during trial execution**.

## Implementation Details

### Core Functionality

**File**: `src/trial_orchestrator.py`

#### 1. LLM-Based Contradiction Detection (Lines 456-560)

The `check_fact_accuracy()` method:
- Uses LLM to analyze statements against case evidence
- Applies a confidence threshold (0.7 = 70%) to filter interventions
- Returns structured results with contradiction details
- Handles errors gracefully without disrupting the trial

**Key Features**:
- **Evidence Context Building**: Formats all case evidence into a structured prompt
- **JSON Response Parsing**: LLM returns structured data with confidence scores
- **Confidence Threshold**: Only triggers interventions when confidence ≥ 70%
- **Error Handling**: Falls back to no intervention on LLM failures

#### 2. Integration into Trial Execution (Lines 349-392)

**CRITICAL ADDITION**: The fact checker is now automatically invoked during trial execution:

**Evidence Presentation Stage**:
1. Prosecution presents evidence
2. **Fact checker analyzes prosecution statement**
3. **If contradiction detected → intervention inserted**
4. Defence presents evidence
5. **Fact checker analyzes defence statement**
6. **If contradiction detected → intervention inserted**

**Cross-Examination Stage**:
1. Prosecution cross-examines
2. **Fact checker analyzes prosecution statement**
3. **If contradiction detected → intervention inserted**
4. Defence cross-examines
5. **Fact checker analyzes defence statement**
6. **If contradiction detected → intervention inserted**

This ensures fact checking happens in real-time during the trial, not just as a standalone capability.

#### 3. Evidence Context Generation (Lines 545-560)

The `_build_evidence_context()` method:
- Formats all evidence items with titles, descriptions, and significance
- Includes timestamps for temporal context
- Provides comprehensive context for LLM analysis

### LLM Prompt Design

**System Prompt**:
```
You are a fact checker in a British Crown Court trial. Your role is to identify 
factual contradictions between statements and case evidence.

Case Evidence:
[Formatted evidence list]

Analyze the statement and determine if it contradicts any of the case evidence. 
Only flag clear factual contradictions, not differences in interpretation or opinion.

Respond in JSON format:
{
  "is_contradiction": true/false,
  "confidence": 0.0-1.0,
  "contradicting_evidence": "evidence item title or null",
  "correction": "brief correction statement or null"
}
```

**User Prompt**:
```
Statement by [speaker]: "[statement]"

Does this statement contain any factual contradictions with the case evidence? Consider:
1. Does it misstate facts from evidence items?
2. Does it claim something happened that contradicts the timeline?
3. Does it attribute statements or actions incorrectly?

Only flag clear factual errors, not interpretations or arguments.
```

### Configuration

- **Temperature**: 0.1 (low temperature for factual analysis)
- **Max Tokens**: 200 (concise responses)
- **Timeout**: 10 seconds (fast response for real-time checking)
- **Confidence Threshold**: 0.7 (70% confidence required)

## Requirements Validation

### Requirement 6.1
✓ **WHEN the Prosecution or Defence states a fact contradicting Case_Content, THE Fact_Checker SHALL interrupt**

Implementation:
- LLM analyzes statements against all case evidence
- Detects contradictions with specific evidence items
- Triggers intervention when confidence threshold is met

### Requirement 6.2
✓ **THE Fact_Checker SHALL cite the specific Evidence_Item that contradicts the misstatement**

Implementation:
- LLM response includes `contradicting_evidence` field
- Intervention message cites the specific evidence item
- Provides correction text explaining the accurate information

## Testing

## Testing

Created comprehensive test suite with 18 tests across 3 test files:

### Unit Tests (`tests/unit/test_fact_checker.py` - 9 tests)
1. **High Confidence Contradiction**: Detects contradictions with confidence ≥ 0.7
2. **Low Confidence Filtering**: Ignores contradictions with confidence < 0.7
3. **No Contradiction**: Returns no intervention for accurate statements
4. **Stage Restrictions**: Only operates during evidence presentation and cross-examination
5. **Intervention Limit**: Respects 3-intervention maximum
6. **Error Handling**: Handles LLM errors gracefully
7. **Invalid JSON**: Handles malformed LLM responses
8. **No LLM Service**: Works without LLM (returns no contradiction)
9. **Evidence Context**: Properly formats all evidence items

### Integration Tests (`tests/unit/test_fact_checker_integration.py` - 5 tests)
1. **Blackthorn Hall Case**: Tests with real case data
2. **Confidence Threshold**: Validates 70% threshold enforcement
3. **Evidence Context Completeness**: Verifies all evidence included
4. **Max Interventions**: Confirms 3-intervention limit
5. **Stage Restrictions**: Tests all trial stages

### Execution Integration Tests (`tests/unit/test_fact_checker_execution.py` - 4 tests)
1. **Evidence Presentation Integration**: Verifies fact checking automatically invoked during evidence stage
2. **Cross-Examination Integration**: Verifies fact checking automatically invoked during cross-examination
3. **Opening Statement Exclusion**: Confirms no fact checking during opening statements
4. **Multiple Interventions**: Tests multiple interventions can occur in one stage

**Test Results**: All 18 tests pass ✓ (100 total unit tests pass)

## Usage Example

```python
# Initialize orchestrator with LLM service
orchestrator = TrialOrchestrator(llm_service=llm_service)
orchestrator.initialize_agents(case_content)

# Check a statement during evidence presentation
result = await orchestrator.check_fact_accuracy(
    statement="Marcus Ashford left at 9:00 PM",
    speaker="prosecution",
    stage=ExperienceState.EVIDENCE_PRESENTATION
)

if result and result.is_contradiction:
    # Trigger intervention
    intervention = orchestrator.trigger_fact_check_intervention(result)
    # Display intervention to user
```

## Demonstration

Run the demonstration script to see the fact checker in action:

```bash
python demo_fact_checker.py
```

This demonstrates:
- Loading the Blackthorn Hall case
- Testing various statements (accurate and contradictory)
- Showing LLM analysis and intervention messages
- Tracking intervention count

## Design Decisions

### 1. Confidence Threshold (70%)

**Rationale**: Balances accuracy with user experience
- Too low: False positives disrupt trial flow
- Too high: Misses legitimate contradictions
- 70% provides good balance based on testing

### 2. Low Temperature (0.1)

**Rationale**: Factual analysis requires consistency
- Reduces randomness in contradiction detection
- Ensures reliable, repeatable results
- Appropriate for objective fact-checking

### 3. Structured JSON Response

**Rationale**: Enables programmatic handling
- Confidence scores allow threshold filtering
- Specific evidence citations improve interventions
- Correction text provides clear feedback

### 4. Graceful Error Handling

**Rationale**: Trial must continue despite LLM failures
- Returns no contradiction on errors
- Logs errors for debugging
- Doesn't interrupt user experience

## Future Enhancements

### Potential Improvements

1. **Adaptive Confidence Threshold**: Adjust based on case complexity
2. **Evidence Relevance Scoring**: Prioritize most relevant evidence
3. **Temporal Reasoning**: Better handling of timeline contradictions
4. **Multi-Turn Context**: Consider previous statements in analysis
5. **Intervention Prioritization**: Save interventions for most critical errors

### Performance Optimization

1. **Caching**: Cache LLM responses for repeated statements
2. **Batch Processing**: Check multiple statements in one LLM call
3. **Parallel Checking**: Run fact checking concurrently with agent generation
4. **Evidence Indexing**: Pre-process evidence for faster retrieval

## Related Files

- `src/trial_orchestrator.py` - Main implementation with execute_stage() integration
- `src/llm_service.py` - LLM service interface
- `src/models.py` - Data models (CaseContent, EvidenceItem)
- `tests/unit/test_fact_checker.py` - Unit tests (9 tests)
- `tests/unit/test_fact_checker_integration.py` - Integration tests (5 tests)
- `tests/unit/test_fact_checker_execution.py` - Execution integration tests (4 tests)
- `demo_fact_checker.py` - Demonstration script

## Conclusion

The LLM-based fact checker successfully implements Requirements 6.1 and 6.2, providing intelligent contradiction detection that **automatically intervenes during trial execution**. The implementation is robust, well-tested (18 tests), and fully integrated into the trial flow. The fact checker now operates in real-time during evidence presentation and cross-examination stages, enhancing the authenticity and educational value of the VERITAS experience.
