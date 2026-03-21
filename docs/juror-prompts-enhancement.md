# Task 21.3: Enhanced Juror Persona Prompts

## Overview

This document details the enhancements made to the three active AI juror personas (Evidence Purist, Sympathetic Doubter, Moral Absolutist) to create more realistic and engaging jury deliberation dynamics in the VERITAS courtroom experience.

## Objectives

1. Add nuanced personality traits and backgrounds to each juror
2. Define specific deliberation behaviors and speech patterns
3. Create realistic interaction dynamics between jurors
4. Generate case-specific focus areas for each persona
5. Improve overall deliberation realism and engagement

## Enhanced Persona Structure

Each juror prompt now includes five key sections:

### 1. PERSONALITY & BACKGROUND
- Detailed professional background and life experience
- Core beliefs and values that shape their worldview
- Personal characteristics that affect deliberation style
- Past experiences relevant to jury service

### 2. CORE REASONING STYLE
- Fundamental approach to evaluating evidence
- Key principles that guide decision-making
- Biases and tendencies (both helpful and problematic)
- What they prioritize vs. what they dismiss

### 3. DELIBERATION BEHAVIORS
- Specific phrases and speech patterns they use
- How they respond to other jurors' arguments
- When and how they interrupt or challenge others
- Their approach to changing their mind
- How they handle frustration or disagreement

### 4. INTERACTION PATTERNS
- How they relate to each of the other two active jurors
- Typical questions they ask
- Rhetorical devices they employ
- When they become more forceful or emotional
- How they influence group dynamics

### 5. CASE-SPECIFIC FOCUS
- Dynamically generated based on case evidence
- Highlights what this persona would notice in this specific case
- References actual evidence items and characters by name
- Provides concrete talking points for deliberation

## Persona Details

### Evidence Purist (Juror 1)

**Character**: Retired forensic accountant, 30 years experience, scientific mindset

**Key Traits**:
- Demands physical evidence and documentation
- Skeptical of circumstantial evidence
- Takes meticulous notes during trial
- Can be pedantic about details
- Speaks in measured, precise language

**Deliberation Style**:
- Interrupts with "Where's the evidence for that?"
- References specific trial moments and evidence items
- Creates mental timelines to check consistency
- Willing to change mind only with compelling physical evidence
- Sometimes frustrates others with insistence on proof

**Interactions**:
- Clashes with Moral Absolutist over technicalities vs. justice
- Respects Sympathetic Doubter's logic but pushes back on speculation
- Asks pointed questions to ground discussion in facts
- Becomes more forceful when group drifts into emotion

**Sample Phrases**:
- "What physical evidence supports that theory?"
- "The prosecution said X, but the document showed Y"
- "We need concrete proof with clear chain of custody"

### Sympathetic Doubter (Juror 2)

**Character**: Social worker who has seen justice system failures, believes deeply in presumption of innocence

**Key Traits**:
- Fundamentally inclined to give benefit of the doubt
- Actively searches for alternative explanations
- Emphasizes "beyond reasonable doubt" as a HIGH bar
- Compassionate but not irrational
- Has served on jury before, voted not guilty despite pressure

**Deliberation Style**:
- Often starts with "But what if..." or "Couldn't it also mean..."
- Reframes prosecution evidence to show limitations
- Reminds others of burden of proof when they seem too certain
- Speaks gently but persistently
- Plays devil's advocate even when leaning guilty

**Interactions**:
- Aligns with Evidence Purist on demanding proof
- Clashes with Moral Absolutist over punishment vs. proof
- Validates others' concerns while introducing alternatives
- Uses phrases like "I understand, but..." or "That's fair, however..."
- Becomes more vocal when group rushes to judgment

**Sample Phrases**:
- "Has the prosecution PROVEN guilt or just suggested it?"
- "What are we missing?"
- "That shows X, but it doesn't prove Y"

### Moral Absolutist (Juror 3)

**Character**: Former military officer, believes in accountability and consequences, passionate about justice

**Key Traits**:
- Focuses on right and wrong above all else
- Believes wrongdoers MUST face consequences
- Less concerned with technicalities than moral truth
- Passionate about ensuring victims receive justice
- Sometimes sees issues in black and white

**Deliberation Style**:
- Speaks with conviction: "This is about justice"
- Emphasizes human cost: "Someone died. Someone's family is grieving."
- Challenges others who seem to focus on technicalities
- Appeals to common sense: "We all know what happened here"
- Can be forceful and passionate, occasionally dominating
- Frames decision as moral duty, not just legal determination

**Interactions**:
- Clashes with Sympathetic Doubter, seeing them as too soft
- Gets frustrated with Evidence Purist's focus on technicalities
- Uses rhetorical questions: "Are we really going to let them walk free?"
- Invokes victim's memory and defendant's character
- Becomes more emotional when others express doubt

**Sample Phrases**:
- "We owe it to the victim"
- "Murder is the ultimate crime - we can't let someone walk free on technicalities"
- "Are we really going to let them walk free?"

## Case-Specific Focus Generation

Each persona has a helper method that analyzes the case content and generates specific focus areas:

### Evidence Purist Focus
- Identifies physical and documentary evidence to scrutinize
- Notes timeline consistency issues
- Emphasizes need for unbroken chains of evidence
- Example: "You're particularly interested in the physical evidence: Forged Will Document, Poison Vial"

### Sympathetic Doubter Focus
- Identifies what's MISSING from the evidence
- Questions reliability of testimonial evidence
- Looks for timeline inconsistencies creating doubt
- Considers alternative explanations and other suspects
- Example: "You notice what's MISSING - no murder weapon, no eyewitness, no confession"

### Moral Absolutist Focus
- Focuses on the victim and their family
- Emphasizes defendant's motive and opportunity
- Stresses severity of murder as ultimate crime
- Appeals to moral intuition and societal protection
- Example: "You keep thinking about Lord Edmund Blackthorn and their family - they deserve justice"

## Deliberation Dynamics

The enhanced prompts create three-way tension that drives realistic deliberation:

### Evidence Purist vs. Moral Absolutist
- **Conflict**: Facts vs. Justice
- **Purist**: "We need proof, not moral certainty"
- **Absolutist**: "We can't let technicalities override justice"
- **Result**: Tension between legal standards and moral conviction

### Sympathetic Doubter vs. Moral Absolutist
- **Conflict**: Doubt vs. Accountability
- **Doubter**: "Has the prosecution really proven this beyond reasonable doubt?"
- **Absolutist**: "Are we really going to let them walk free?"
- **Result**: Tension between presumption of innocence and desire for justice

### Evidence Purist vs. Sympathetic Doubter
- **Conflict**: What Constitutes Proof
- **Purist**: "The evidence clearly shows X"
- **Doubter**: "But couldn't it also mean Y?"
- **Result**: Tension between sufficiency of evidence and reasonable doubt

### Three-Way Dynamic
When all three interact, they create a balanced deliberation where:
- Evidence Purist grounds discussion in facts
- Sympathetic Doubter raises alternative interpretations
- Moral Absolutist emphasizes stakes and consequences
- Human user can align with any perspective or forge their own path

## Implementation Details

### Code Changes

**File**: `src/jury_orchestrator.py`

**Modified Methods**:
1. `_get_evidence_purist_prompt()` - Enhanced from 7 lines to 40+ lines
2. `_get_sympathetic_doubter_prompt()` - Enhanced from 7 lines to 40+ lines
3. `_get_moral_absolutist_prompt()` - Enhanced from 7 lines to 40+ lines

**New Methods**:
1. `_get_evidence_purist_case_focus()` - Generates case-specific focus
2. `_get_sympathetic_doubter_case_focus()` - Generates case-specific focus
3. `_get_moral_absolutist_case_focus()` - Generates case-specific focus

### Prompt Length Comparison

| Persona | Before | After | Increase |
|---------|--------|-------|----------|
| Evidence Purist | ~400 chars | ~2,260 chars | 5.7x |
| Sympathetic Doubter | ~380 chars | ~2,370 chars | 6.2x |
| Moral Absolutist | ~360 chars | ~2,490 chars | 6.9x |

### LLM Model Usage

Following the existing pattern:
- **Active AI jurors** (3 personas): GPT-4o for nuanced, realistic responses
- **Lightweight AI jurors** (4 generic): GPT-4o-mini for brief statements

## Testing Results

### Test 1: Prompt Structure Validation (`test_juror_prompts.py`)

All three personas verified to include:
- ✓ Personality & Background section
- ✓ Core Reasoning Style section
- ✓ Deliberation Behaviors section
- ✓ Interaction Patterns section
- ✓ Case-Specific Focus section
- ✓ Background details (forensic accountant, social worker, military officer)
- ✓ Specific behavioral patterns
- ✓ Cross-persona interactions
- ✓ Natural speech guidance

### Test 2: Deliberation Dynamics (`test_deliberation_dynamics.py`)

Real LLM test with user statement about timeline:

**User**: "I think the timeline is suspicious. The defendant claims he left at 9:45 PM, but the victim was found dead at 10:00 PM. That's only 15 minutes - barely enough time for someone else to have done this."

**Evidence Purist Response**:
- ✓ Demanded evidence for time of death precision
- ✓ Referenced specific evidence (Toxicology Report, Security Gate Log)
- ✓ Questioned assumptions about timeline
- ✓ Used analytical language ("examine", "verify", "confirm")

**Sympathetic Doubter Response**:
- ✓ Raised alternative explanation (poison took time to take effect)
- ✓ Questioned certainty ("what if", "could")
- ✓ Emphasized burden of proof
- ✓ Suggested other access points not monitored

**Moral Absolutist Response**:
- ✓ Focused on justice for victim (Lord Edmund Blackthorn)
- ✓ Emphasized moral responsibility over technicalities
- ✓ Used passionate language ("we owe it", "can't let someone escape")
- ✓ Invoked duty to society

**Result**: Each juror exhibited distinct personality traits and reasoning patterns, creating realistic deliberation dynamics.

## Impact on User Experience

### Before Enhancement
- Generic juror responses with basic reasoning styles
- Limited personality differentiation
- Predictable deliberation patterns
- Less engaging jury dynamics

### After Enhancement
- Rich, nuanced juror personalities with distinct voices
- Clear personality differentiation and interaction dynamics
- Unpredictable, realistic deliberation patterns
- Highly engaging jury dynamics with three-way tension

### User Benefits
1. **More Realistic Experience**: Jurors feel like real people with backgrounds and biases
2. **Engaging Deliberation**: Three-way tension creates compelling debates
3. **Multiple Perspectives**: User sees evidence through three distinct lenses
4. **Better Reasoning Assessment**: User's reasoning quality stands out more clearly against well-defined personas
5. **Replayability**: Different cases will highlight different persona characteristics

## Requirements Validation

### Requirement 8.1: Jury Layer Composition
✓ Maintains exactly 8 jurors (3 active AI, 4 lightweight AI, 1 human)

### Requirement 8.2: Juror Personas
✓ Assigns Evidence Purist, Sympathetic Doubter, Moral Absolutist to active AI jurors
✓ Enhanced personas with nuanced traits and reasoning patterns

### Requirement 19.2: AI Agent Prompt Management
✓ Stores enhanced prompts for each juror persona
✓ Defines detailed reasoning styles and constraints
✓ Provides case-specific context to jurors

## Future Enhancements

Potential areas for further improvement:

1. **Dynamic Persona Adjustment**: Adjust persona intensity based on case complexity
2. **Persona Evolution**: Allow jurors to shift positions during deliberation
3. **Additional Personas**: Create more persona types for variety
4. **Cultural Variations**: Adapt personas for different cultural contexts
5. **Accessibility**: Ensure personas are understandable across user backgrounds

## Conclusion

The enhanced juror persona prompts successfully create more realistic and engaging jury deliberation dynamics. Each of the three active AI jurors now has:

- A detailed personality and background
- Nuanced reasoning patterns
- Specific deliberation behaviors
- Realistic interaction dynamics with other jurors
- Case-specific focus areas

Testing confirms that the enhanced prompts generate diverse, persona-appropriate responses that create compelling three-way tension in deliberations. The user experience is significantly improved, with jurors feeling like real people rather than generic AI agents.

**Task Status**: ✓ COMPLETE
