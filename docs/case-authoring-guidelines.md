# VERITAS Case Content Authoring Guidelines

## Introduction

This guide provides comprehensive instructions for creating high-quality case content for the VERITAS Courtroom Experience. VERITAS cases are designed to be ambiguous—supporting both guilty and not guilty verdicts with sound reasoning. The system evaluates not just whether users reach the "correct" verdict, but whether their reasoning is logical, evidence-based, and coherent.

### What Makes a Good VERITAS Case?

A good VERITAS case:
- **Supports both verdicts**: Users can reach either guilty or not guilty with sound reasoning
- **Rewards careful analysis**: Evidence must be examined closely to understand its implications
- **Creates genuine ambiguity**: The uncertainty should feel natural, not forced
- **Respects the burden of proof**: "Not guilty" should be defensible based on reasonable doubt
- **Engages emotionally**: Characters and narrative should draw users into the story
- **Fits the timeframe**: All content must work within a 15-minute experience

### Design Philosophy

VERITAS cases follow a dual-layer evaluation model:
1. **Verdict correctness**: Did the user reach the ground truth verdict?
2. **Reasoning quality**: Did the user use sound logic and evidence?

This creates four possible outcomes:
- Sound reasoning + correct verdict (best outcome)
- Sound reasoning + incorrect verdict (good reasoning, different conclusion)
- Weak reasoning + correct verdict (right answer, wrong reasons)
- Weak reasoning + incorrect verdict (needs improvement)

The goal is to reward logical thinking regardless of verdict outcome.

## Case Structure Requirements

### Required Fields

Every case must include:

```json
{
  "caseId": "unique-identifier-###",
  "title": "The Crown v. [Defendant Name]",
  "narrative": { ... },
  "evidence": [ ... ],
  "timeline": [ ... ],
  "groundTruth": { ... }
}
```

### Evidence Count Constraint

Cases must have **exactly 5, 6, or 7 evidence items**. This constraint ensures:
- Sufficient evidence for meaningful deliberation
- Not overwhelming users with too much information
- Balanced trial experience within 15-minute timeframe

**Recommended**: 7 evidence items (3-4 prosecution, 3-4 defence)


## Narrative Design

### Hook Scene

The hook scene is the user's first impression—it must immediately engage and establish the central mystery.

**Requirements:**
- Duration: 60-90 seconds when read aloud
- Introduces: victim, defendant, and central mystery
- Tone: Atmospheric and compelling
- Length: 100-150 words

**Example from Blackthorn Hall:**
```
The grand estate of Blackthorn Hall stands silent under a grey English sky. 
Inside the oak-paneled library, Lord Edmund Blackthorn lies dead, a crystal 
tumbler shattered on the Persian rug beside him. Just hours before, he had 
summoned his estate manager with urgent news: he'd discovered the family will 
was a forgery. Now Edmund is dead, and Marcus Ashford—the man who stood to 
lose everything—was the last person to see him alive.
```

**What works here:**
- Vivid setting ("grand estate," "oak-paneled library")
- Clear victim and defendant
- Central mystery (forged will, suspicious death)
- Immediate tension (last person to see victim alive)

**Example from Digital Deception:**
```
The glass towers of London's financial district gleam in the morning sun, but 
inside the offices of Meridian Investment Trust, a scandal is unfolding. £2.3 
million has vanished from client accounts over eighteen months, siphoned through 
a web of phantom transactions. The digital trail leads to Sarah Chen, the firm's 
senior compliance officer—the very person tasked with preventing such fraud. Now 
she stands accused of orchestrating an elaborate scheme, but the evidence that 
seems damning on the surface may tell a more complicated story.
```

**What works here:**
- Contemporary setting (financial district)
- Clear crime (£2.3 million fraud)
- Irony (compliance officer accused of fraud)
- Hints at ambiguity ("more complicated story")

**Tips for Writing Hook Scenes:**
- Start with setting to establish atmosphere
- Introduce the victim's situation first
- Reveal the defendant's connection
- End with a question or tension point
- Use sensory details (sights, sounds)
- Avoid revealing too much—create intrigue


### Charge Text

The formal charge reading establishes the legal framework.

**Format:**
```
[Defendant Name], you are charged with [crime] contrary to [legal statute], 
in that [time period and circumstances]. How do you plead?
```

**Example (Murder):**
```
Marcus Ashford, you are charged with murder contrary to common law, in that 
on the 15th day of January 2024, you did unlawfully kill Lord Edmund Blackthorn. 
How do you plead?
```

**Example (Fraud):**
```
Sarah Chen, you are charged with fraud by abuse of position contrary to Section 4 
of the Fraud Act 2006, in that between June 2022 and December 2023, you dishonestly 
abused your position as compliance officer at Meridian Investment Trust, intending 
to make a gain for yourself or cause loss to others. How do you plead?
```

**Tips:**
- Use formal legal language
- Specify the exact crime and statute
- Include precise dates or time periods
- Keep it concise but complete
- End with "How do you plead?"

### Character Profiles

Characters bring the case to life. Each profile should be detailed enough to feel real but concise enough to absorb quickly.

**Victim Profile Structure:**
```json
{
  "name": "Full Name",
  "role": "Victim",
  "background": "2-3 sentences about who they were",
  "relevantFacts": [
    "Fact directly relevant to the case",
    "Another relevant fact",
    "3-5 facts total"
  ]
}
```

**Example (Blackthorn Hall):**
```json
{
  "name": "Lord Edmund Blackthorn",
  "role": "Victim",
  "background": "Wealthy patron and owner of Blackthorn Hall estate. At 68 years old, 
    Edmund was known for his meticulous attention to detail and his passion for 
    preserving his family's legacy. He had recently begun reviewing estate documents 
    in preparation for updating his will.",
  "relevantFacts": [
    "Discovered the family will had been forged",
    "Summoned Marcus Ashford to discuss the forgery on the evening of his death",
    "Had a history of heart problems but was in stable condition",
    "Was found dead in his library at approximately 8:45 PM"
  ]
}
```

**Defendant Profile Structure:**
Same as victim, but role is "Defendant"

**Tips for Defendant Profiles:**
- Establish their relationship to the victim
- Include potential motive (but not too obvious)
- Add humanizing details (age, background, history)
- Include facts that could support innocence
- Create sympathy without manipulation


**Witness Profiles:**

You should have 3-5 witnesses representing different perspectives:
- Expert witnesses (forensic, technical, medical)
- Eyewitnesses (saw or heard something relevant)
- Character witnesses (know defendant or victim)
- Investigating officers (police, detectives)

**Example (Digital Deception - Expert Witness):**
```json
{
  "name": "Dr. James Okonkwo",
  "role": "Cybersecurity Expert",
  "background": "Independent forensic analyst with 15 years experience in digital 
    fraud investigation",
  "relevantFacts": [
    "Analyzed the transaction patterns and found they were automated, not manual",
    "Identified sophisticated malware on Sarah's workstation that could steal credentials",
    "Determined the malware was installed 2 weeks before the first fraudulent transaction",
    "Noted that similar malware has been used in organized cybercrime operations"
  ]
}
```

**Tips for Witness Design:**
- Each witness should contribute unique information
- Mix prosecution and defence perspectives
- Include potential bias or credibility issues
- Expert witnesses should explain technical evidence
- Eyewitnesses should provide timeline details
- Avoid witnesses who simply repeat other evidence

## Evidence Design

Evidence is the heart of your case. Each item should contribute to the ambiguity.

### Evidence Item Structure

```json
{
  "id": "evidence-001",
  "type": "physical" | "testimonial" | "documentary",
  "title": "Short descriptive title",
  "description": "Detailed description of the evidence and what it shows",
  "timestamp": "ISO 8601 timestamp",
  "presentedBy": "prosecution" | "defence",
  "significance": "Why this evidence matters to the case"
}
```

### Evidence Types

**Physical Evidence:**
- Objects, substances, forensic findings
- Examples: weapons, toxicology reports, fingerprints, DNA
- Strengths: Objective, scientific, hard to dispute
- Weaknesses: Requires interpretation, can be circumstantial

**Testimonial Evidence:**
- Witness statements, expert testimony
- Examples: eyewitness accounts, expert analysis, character testimony
- Strengths: Provides context, explains technical details
- Weaknesses: Subject to bias, memory issues, credibility questions

**Documentary Evidence:**
- Written records, digital data, communications
- Examples: emails, financial records, security logs, contracts
- Strengths: Contemporaneous, detailed, verifiable
- Weaknesses: Can be incomplete, requires context


### Evidence Distribution

**Recommended Pattern (7 evidence items):**
- Items 1-3: Prosecution evidence (establishes guilt)
- Items 4-7: Defence evidence (creates doubt)

**Alternative Pattern:**
- Items 1-2: Prosecution
- Item 3: Defence
- Items 4-5: Prosecution
- Items 6-7: Defence

**Key Principle:** Evidence should build tension, not resolve it immediately.

### Example Evidence Sequence (Blackthorn Hall)

**Evidence 1 (Prosecution - Motive):**
```json
{
  "id": "evidence-001",
  "type": "documentary",
  "title": "Forged Will Document",
  "description": "A will document dated 2020 naming Marcus Ashford as a significant 
    beneficiary. Forensic analysis revealed the signature was traced and the paper 
    stock didn't match other Blackthorn family documents from that period. Lord 
    Blackthorn had marked it with red ink: 'FORGERY - Confront MA immediately.'",
  "timestamp": "2024-01-15T19:30:00Z",
  "presentedBy": "prosecution",
  "significance": "Establishes motive - Marcus stood to inherit £500,000 under the 
    forged will and would lose everything if exposed"
}
```

**What works:** Clear motive, physical evidence of forgery, victim's own notes

**Evidence 4 (Defence - Timeline):**
```json
{
  "id": "evidence-004",
  "type": "documentary",
  "title": "Security Gate Log",
  "description": "The estate's front gate security log shows Marcus's vehicle entered 
    at 7:45 PM and exited at 8:20 PM on the night in question. The log is automatically 
    timestamped and cannot be manually altered. The drive from the gate to the main 
    house takes approximately 3 minutes.",
  "timestamp": "2024-01-15T20:30:00Z",
  "presentedBy": "defence",
  "significance": "Creates a tight timeline - Marcus could only have been in the house 
    for approximately 32 minutes maximum"
}
```

**What works:** Objective data, creates time pressure, raises doubt about opportunity

### Writing Effective Evidence Descriptions

**Good Evidence Description:**
- Specific details (times, amounts, names)
- Objective observations first
- Interpretations or implications second
- Acknowledges limitations or ambiguities
- 100-200 words

**Example (Digital Deception - Evidence 6):**
```
DS Foster testifies that the cryptocurrency account was accessed 47 times between 
June 2022 and January 2024. Forensic analysis of IP addresses shows all access 
originated from servers in Romania, Bulgaria, and Ukraine—never from the UK. The 
funds were systematically converted to privacy coins and moved through mixing 
services, consistent with professional money laundering operations.
```

**What works:**
- Specific numbers (47 times, specific countries)
- Technical details (IP addresses, privacy coins, mixing services)
- Clear implication (professional operation, not UK-based)
- Raises questions (if Sarah did it, why Eastern Europe?)


### Evidence Significance Statements

The significance field explains why the evidence matters. Write from the perspective of the presenting side.

**Prosecution Significance Examples:**
- "Establishes motive - defendant stood to gain £500,000"
- "Places defendant at the scene during the critical time window"
- "Demonstrates defendant had exclusive access to the murder weapon"
- "Shows defendant's financial desperation in the weeks before the crime"

**Defence Significance Examples:**
- "Creates reasonable doubt about opportunity - timeline too tight"
- "Provides alternative explanation - malware could have stolen credentials"
- "Raises questions about motive - no evidence defendant benefited"
- "Suggests third-party involvement - professional operation"

**Tips:**
- Be specific about what the evidence proves or suggests
- Use legal concepts (motive, opportunity, means, reasonable doubt)
- Acknowledge what the evidence doesn't prove
- Connect to other evidence when relevant

## Creating Ambiguity

Ambiguity is the core of VERITAS cases. Both verdicts must be defensible with sound reasoning.

### Techniques for Creating Ambiguity

**1. Timeline Uncertainty**

Create windows where events could have happened differently.

**Example (Blackthorn Hall):**
- Poison takes 30-60 minutes to work
- Defendant was present for 32 minutes
- Death occurred 30 minutes after defendant left
- **Ambiguity:** Poison could have been administered before, during, or after defendant's visit

**2. Missing Evidence**

What's absent can be as important as what's present.

**Example (Digital Deception):**
- £2.3 million stolen, but none found in defendant's possession
- No unusual spending patterns
- **Ambiguity:** If defendant stole it, where did it go?

**3. Alternative Explanations**

Provide credible alternative theories.

**Example (Digital Deception):**
- Prosecution theory: Defendant used her credentials to steal funds
- Defence theory: Sophisticated malware stole her credentials
- **Ambiguity:** Both theories fit the evidence

**4. Circumstantial Evidence**

Use evidence that suggests but doesn't prove.

**Example (Blackthorn Hall):**
- Defendant had motive (forged will)
- Defendant had opportunity (was present)
- Defendant had means (access to poison)
- **But:** No direct evidence of poisoning (no fingerprints on glass or medicine cabinet)

**5. Credibility Questions**

Make witnesses imperfect.

**Example (Digital Deception):**
- Former colleague testifies against defendant
- But admits she left after a dispute with defendant
- **Ambiguity:** Is she credible or biased?


### Balancing Prosecution and Defence

Both sides must have strong arguments. A good case feels like it could go either way.

**Prosecution Strengths (Guilty Verdict):**
- Clear motive
- Defendant had opportunity
- Defendant had means/access
- Circumstantial evidence points to defendant
- Defendant's behavior seems suspicious

**Defence Strengths (Not Guilty Verdict):**
- Alternative explanation exists
- Timeline creates doubt
- Missing evidence (no benefit, no weapon, no direct proof)
- Prosecution relies on circumstantial evidence
- Reasonable doubt standard not met

**Testing Balance:**

Ask yourself:
1. Can I make a strong argument for guilty using 3-4 evidence items?
2. Can I make a strong argument for not guilty using 3-4 evidence items?
3. Does each side have to address the other side's strongest points?
4. Would a reasonable person struggle to decide?

If you answer "no" to any question, rebalance your evidence.

### Common Ambiguity Mistakes

**Mistake 1: Obvious Guilt**
- Too much direct evidence
- No credible alternative explanation
- Defence evidence is weak or irrelevant

**Fix:** Add evidence that creates genuine doubt (timeline issues, missing motive, alternative suspects)

**Mistake 2: Obvious Innocence**
- Prosecution case is weak
- Defence has ironclad alibi or proof
- No reasonable person would convict

**Fix:** Strengthen prosecution evidence (add motive, opportunity, suspicious behavior)

**Mistake 3: Forced Ambiguity**
- Evidence contradicts itself unrealistically
- Relies on unlikely coincidences
- Feels artificial or contrived

**Fix:** Make ambiguity arise naturally from incomplete information, not contradictions

**Mistake 4: Too Complex**
- Too many suspects or theories
- Evidence is confusing or contradictory
- Users can't follow the logic

**Fix:** Simplify to two clear theories, make evidence clearer

## Timeline Design

The timeline organizes events chronologically and links them to evidence.

### Timeline Structure

```json
{
  "timestamp": "ISO 8601 timestamp",
  "description": "What happened at this time",
  "evidenceIds": ["evidence-001", "evidence-003"]
}
```

### Timeline Best Practices

**1. Include Key Events Only**

Don't list every detail—focus on events that matter to the case.

**Good timeline events:**
- Crime occurred
- Defendant's movements
- Evidence discovered
- Witness observations
- Critical communications

**2. Use Precise Timestamps**

ISO 8601 format: `2024-01-15T20:15:00Z`

**3. Link to Evidence**

Every timeline event should reference at least one evidence item.


**Example Timeline (Blackthorn Hall):**

```json
[
  {
    "timestamp": "2024-01-15T19:30:00Z",
    "description": "Lord Blackthorn discovers forged will and marks it 'FORGERY'",
    "evidenceIds": ["evidence-001"]
  },
  {
    "timestamp": "2024-01-15T19:45:00Z",
    "description": "Marcus's vehicle enters estate gate (security log)",
    "evidenceIds": ["evidence-004"]
  },
  {
    "timestamp": "2024-01-15T20:00:00Z",
    "description": "Housekeeper hears confrontation in library",
    "evidenceIds": ["evidence-002"]
  },
  {
    "timestamp": "2024-01-15T20:15:00Z",
    "description": "Marcus leaves library, seen by housekeeper",
    "evidenceIds": ["evidence-002", "evidence-005"]
  },
  {
    "timestamp": "2024-01-15T20:20:00Z",
    "description": "Marcus's vehicle exits estate gate (security log)",
    "evidenceIds": ["evidence-004"]
  },
  {
    "timestamp": "2024-01-15T20:45:00Z",
    "description": "Housekeeper discovers Lord Blackthorn's body",
    "evidenceIds": ["evidence-002"]
  }
]
```

**What works:**
- Clear sequence of events
- Tight timeline creates tension
- Multiple evidence items confirm key events
- Shows defendant's window of opportunity

### Timeline and Ambiguity

Use timeline to create doubt:
- **Tight windows:** Not enough time to commit crime?
- **Gaps:** What happened during unaccounted time?
- **Overlapping events:** Could defendant be in two places?
- **Delayed effects:** When did poison/malware/action actually occur?

## Ground Truth Design

Ground truth defines the "correct" verdict and reasoning criteria.

### Ground Truth Structure

```json
{
  "actualVerdict": "guilty" | "not_guilty",
  "keyFacts": [
    "Fact that supports the ground truth verdict",
    "Another key fact",
    "5-8 facts total"
  ],
  "reasoningCriteria": {
    "requiredEvidenceReferences": ["evidence-004", "evidence-006", "evidence-007"],
    "logicalFallacies": ["ad_hominem", "appeal_to_emotion", "hasty_generalization"],
    "coherenceThreshold": 0.65
  }
}
```

### Choosing the Ground Truth Verdict

The ground truth verdict should be the one that best satisfies the legal standard of proof.

**For "not guilty" ground truth:**
- Reasonable doubt exists
- Alternative explanation is credible
- Prosecution relies heavily on circumstantial evidence
- Missing evidence creates gaps in prosecution case

**For "guilty" ground truth:**
- Evidence strongly points to defendant
- Alternative explanations are weak or implausible
- Defendant's actions are highly suspicious
- Circumstantial evidence is overwhelming

**Both existing cases use "not guilty" ground truth** because they emphasize reasonable doubt and alternative explanations.


### Key Facts

Key facts explain why the ground truth verdict is correct. These should:
- Reference specific evidence
- Explain the reasoning
- Address the strongest counter-arguments
- Apply legal standards (reasonable doubt, burden of proof)

**Example (Blackthorn Hall - Not Guilty):**

```json
"keyFacts": [
  "The timeline creates reasonable doubt - digoxin could have been administered 
   before Marcus arrived or after he left",
  "Absence of Marcus's fingerprints on the glass and medical cabinet suggests he 
   didn't handle the poison",
  "The tight 32-minute window from gate entry to exit makes it difficult to prove 
   Marcus had opportunity to access medical supplies and administer poison",
  "The pathologist's testimony about variable digoxin response times creates 
   ambiguity about when poison was administered",
  "While Marcus had motive and was present during a critical window, the prosecution 
   cannot prove beyond reasonable doubt that he administered the poison"
]
```

**What works:**
- Each fact references specific evidence
- Addresses prosecution's strongest points (motive, presence)
- Applies "beyond reasonable doubt" standard
- Explains why doubt is reasonable, not just possible

### Required Evidence References

List 3-5 evidence items that users should reference to demonstrate sound reasoning.

**Selection criteria:**
- Evidence that supports the ground truth verdict
- Evidence that creates reasonable doubt (for not guilty)
- Evidence that addresses key questions
- Mix of prosecution and defence evidence

**Example (Digital Deception):**

```json
"requiredEvidenceReferences": [
  "evidence-004",  // Malware analysis (alternative explanation)
  "evidence-005",  // Financial records (no benefit)
  "evidence-006",  // Cryptocurrency access logs (Eastern Europe)
  "evidence-007"   // Security warnings (inconsistent with guilt)
]
```

**Note:** Users don't need to reference ALL of these, but referencing several indicates thorough analysis.

### Logical Fallacies

List fallacies to detect in user reasoning. Common fallacies:

- **ad_hominem**: Attacking the person, not the argument
- **appeal_to_emotion**: Using emotion instead of logic
- **hasty_generalization**: Drawing conclusions from insufficient evidence
- **false_dichotomy**: Presenting only two options when more exist
- **post_hoc**: Assuming causation from correlation
- **straw_man**: Misrepresenting the opposing argument
- **appeal_to_authority**: Accepting claims based on authority alone
- **slippery_slope**: Assuming one thing will lead to extreme consequences

**Example usage:**
```json
"logicalFallacies": [
  "ad_hominem",
  "appeal_to_emotion",
  "hasty_generalization",
  "false_dichotomy"
]
```

### Coherence Threshold

A value between 0 and 1 indicating how coherent user reasoning should be.

**Recommended values:**
- **0.65**: Standard threshold (used in both existing cases)
- **0.70**: For cases requiring more rigorous logic
- **0.60**: For cases with more subjective elements

**What coherence measures:**
- Logical flow between statements
- Consistency of argument
- Evidence-based reasoning
- Absence of contradictions


## Crime Type Selection

Choose crimes that:
- Create moral complexity
- Allow for ambiguous evidence
- Fit within British Crown Court jurisdiction
- Engage users emotionally

### Suitable Crime Types

**Murder / Manslaughter**
- **Pros:** High stakes, clear victim, strong emotional engagement
- **Cons:** Can be too dark, requires forensic detail
- **Example:** Blackthorn Hall (poisoning)

**Fraud / Financial Crimes**
- **Pros:** Modern, technical, less violent
- **Cons:** Can be dry, requires financial understanding
- **Example:** Digital Deception (fraud by abuse of position)

**Theft / Burglary**
- **Pros:** Relatable, clear crime, property focus
- **Cons:** Lower stakes, less emotional engagement

**Assault / GBH**
- **Pros:** Personal conflict, witness testimony important
- **Cons:** Can be disturbing, victim testimony sensitive

**Conspiracy / Organized Crime**
- **Pros:** Complex, multiple actors, sophisticated
- **Cons:** Can be too complex, hard to follow

**Recommended:** Alternate between violent crimes (murder, assault) and non-violent crimes (fraud, theft) to provide variety.

### Crime Type Considerations

**For Murder Cases:**
- Use indirect methods (poison, staged accidents) rather than graphic violence
- Focus on mystery and investigation, not gore
- Create sympathy for both victim and defendant
- Use forensic evidence to create ambiguity

**For Fraud Cases:**
- Make financial details accessible to non-experts
- Use visual evidence (transaction logs, emails)
- Create human impact (victims, consequences)
- Use technical evidence to create alternative explanations

**For All Cases:**
- Avoid gratuitous violence or disturbing content
- Respect victim dignity
- Create moral complexity, not simple good vs. evil
- Focus on evidence and reasoning, not shock value

## Case Authoring Workflow

### Step 1: Concept Development

**Define the core elements:**
1. Crime type
2. Victim (who they were, why they matter)
3. Defendant (relationship to victim, potential motive)
4. Central mystery (what's ambiguous?)
5. Ground truth verdict

**Example (Blackthorn Hall):**
- Crime: Murder by poisoning
- Victim: Wealthy estate owner who discovered forgery
- Defendant: Estate manager who forged will
- Mystery: Did defendant poison victim, or did someone else?
- Ground truth: Not guilty (timeline creates reasonable doubt)

### Step 2: Evidence Planning

**Create evidence outline:**
1. List 7 potential evidence items
2. Assign 3-4 to prosecution, 3-4 to defence
3. Ensure each item contributes unique information
4. Check that both verdicts are supportable

**Evidence checklist:**
- [ ] Establishes motive
- [ ] Establishes opportunity
- [ ] Establishes means
- [ ] Creates timeline
- [ ] Provides alternative explanation
- [ ] Addresses credibility
- [ ] Creates reasonable doubt


### Step 3: Character Development

**Create character profiles:**
1. Victim profile (background, relevantFacts)
2. Defendant profile (background, relevantFacts)
3. 3-5 witness profiles (varied perspectives)

**Character checklist:**
- [ ] Each character has clear role
- [ ] Background is detailed but concise
- [ ] Relevant facts connect to evidence
- [ ] Characters feel real, not stereotypical
- [ ] Mix of sympathetic and unsympathetic traits

### Step 4: Narrative Writing

**Write the narrative elements:**
1. Hook scene (100-150 words)
2. Charge text (formal legal language)
3. Character profiles (2-3 sentences background + facts)

**Narrative checklist:**
- [ ] Hook scene is engaging and atmospheric
- [ ] Charge text is legally accurate
- [ ] Characters are well-developed
- [ ] Tone is consistent throughout
- [ ] Language is accessible but not simplistic

### Step 5: Evidence Drafting

**Write detailed evidence items:**
1. Create evidence ID (evidence-001, evidence-002, etc.)
2. Choose type (physical, testimonial, documentary)
3. Write title (short, descriptive)
4. Write description (100-200 words, specific details)
5. Set timestamp (ISO 8601 format)
6. Assign to prosecution or defence
7. Write significance statement

**Evidence checklist:**
- [ ] 5-7 evidence items total
- [ ] Mix of types (physical, testimonial, documentary)
- [ ] Balanced between prosecution and defence
- [ ] Each item has specific details
- [ ] Descriptions are clear and objective
- [ ] Significance explains importance

### Step 6: Timeline Creation

**Build the timeline:**
1. List key events chronologically
2. Assign timestamps (ISO 8601)
3. Link each event to evidence items
4. Ensure timeline creates tension/ambiguity

**Timeline checklist:**
- [ ] Events are in chronological order
- [ ] Timestamps are precise
- [ ] Each event references evidence
- [ ] Timeline supports ambiguity
- [ ] Key moments are included

### Step 7: Ground Truth Definition

**Define ground truth:**
1. Choose verdict (guilty or not guilty)
2. Write 5-8 key facts explaining verdict
3. List 3-5 required evidence references
4. List logical fallacies to detect
5. Set coherence threshold (typically 0.65)

**Ground truth checklist:**
- [ ] Verdict is defensible
- [ ] Key facts reference specific evidence
- [ ] Key facts apply legal standards
- [ ] Required evidence supports verdict
- [ ] Fallacy list is appropriate
- [ ] Coherence threshold is reasonable

### Step 8: Validation

**Run the validation tool:**
```bash
python scripts/validate_case.py fixtures/your-case.json
```

**Fix any errors:**
- Missing required fields
- Evidence count outside 5-7 range
- Invalid evidence references
- Invalid timestamps
- Invalid coherence threshold

**Validation checklist:**
- [ ] All required fields present
- [ ] 5-7 evidence items
- [ ] Timeline references valid evidence IDs
- [ ] Ground truth references valid evidence IDs
- [ ] Coherence threshold between 0 and 1
- [ ] JSON is valid and well-formatted


### Step 9: Testing Both Verdicts

**Test guilty verdict reasoning:**
1. List 3-4 evidence items supporting guilty
2. Write a paragraph arguing for guilty
3. Check if reasoning is sound and logical
4. Identify any logical fallacies

**Test not guilty verdict reasoning:**
1. List 3-4 evidence items supporting not guilty
2. Write a paragraph arguing for not guilty
3. Check if reasoning is sound and logical
4. Apply "reasonable doubt" standard

**Both verdicts checklist:**
- [ ] Can make strong argument for guilty
- [ ] Can make strong argument for not guilty
- [ ] Both arguments use specific evidence
- [ ] Both arguments are logically coherent
- [ ] Neither argument relies on fallacies
- [ ] Case feels genuinely ambiguous

### Step 10: Peer Review

**Get feedback from others:**
1. Have someone read the case without knowing ground truth
2. Ask them to reach a verdict
3. Ask them to explain their reasoning
4. Check if they referenced key evidence
5. Assess if they found it ambiguous

**Peer review questions:**
- Did they find the case engaging?
- Was the evidence clear and understandable?
- Did they struggle to decide?
- Did they reference multiple evidence items?
- Did they apply legal standards correctly?
- Did they find any confusing or contradictory elements?

## Common Pitfalls and Solutions

### Pitfall 1: Too Much Information

**Problem:** 10+ evidence items, complex timeline, too many witnesses

**Solution:**
- Limit to 7 evidence items maximum
- Combine similar evidence into single items
- Focus on quality over quantity
- Each piece of evidence should be essential

### Pitfall 2: Unclear Ambiguity

**Problem:** Users can't understand why the case is ambiguous

**Solution:**
- Make both theories explicit in evidence
- Use significance statements to highlight key questions
- Ensure defence evidence directly addresses prosecution evidence
- Create clear "if this, then that" logic chains

### Pitfall 3: Unrealistic Evidence

**Problem:** Evidence that wouldn't exist in real cases or contradicts itself

**Solution:**
- Research real cases for inspiration
- Consult legal/forensic resources
- Ensure evidence is internally consistent
- Avoid convenient coincidences

### Pitfall 4: Biased Presentation

**Problem:** Evidence heavily favors one side

**Solution:**
- Count prosecution vs. defence evidence items
- Test both verdict arguments
- Ensure defence has strong counter-evidence
- Make prosecution case rely on circumstantial evidence

### Pitfall 5: Technical Overload

**Problem:** Too much jargon, complex technical details

**Solution:**
- Explain technical terms in plain language
- Use analogies for complex concepts
- Focus on implications, not mechanisms
- Have non-experts review for clarity


### Pitfall 6: Weak Ground Truth

**Problem:** Ground truth verdict doesn't feel justified

**Solution:**
- Write detailed key facts explaining verdict
- Reference specific evidence in key facts
- Apply legal standards explicitly
- Address strongest counter-arguments
- Consider if opposite verdict might be better ground truth

### Pitfall 7: Boring Hook Scene

**Problem:** Hook scene doesn't engage or create intrigue

**Solution:**
- Start with vivid setting details
- Create immediate tension or mystery
- Introduce victim and defendant quickly
- End with a question or cliffhanger
- Use sensory language (sights, sounds, atmosphere)

### Pitfall 8: Flat Characters

**Problem:** Characters feel like cardboard cutouts

**Solution:**
- Add specific details (age, background, personality)
- Include humanizing elements
- Create mixed motivations
- Avoid stereotypes
- Give characters history and relationships

## Tips for Balancing Prosecution and Defence

### Prosecution Strategy

**Build a circumstantial case:**
- Establish motive (why defendant would commit crime)
- Establish opportunity (defendant was present)
- Establish means (defendant had access)
- Show suspicious behavior
- Present timeline that fits guilt theory

**Example (Blackthorn Hall Prosecution):**
- Motive: Forged will worth £500,000
- Opportunity: Last person to see victim alive
- Means: Access to poison in medical cabinet
- Suspicious: Confrontation overheard
- Timeline: Death occurred shortly after defendant left

### Defence Strategy

**Create reasonable doubt:**
- Provide alternative explanation
- Challenge timeline (too tight, too loose)
- Point to missing evidence (no benefit, no weapon)
- Question witness credibility
- Emphasize burden of proof

**Example (Blackthorn Hall Defence):**
- Alternative: Someone else poisoned victim before or after
- Timeline: Only 32 minutes, not enough time
- Missing evidence: No fingerprints on glass or cabinet
- Burden of proof: Prosecution hasn't proven beyond reasonable doubt

### Balance Checklist

Use this checklist to ensure balance:

**Prosecution has:**
- [ ] Clear motive
- [ ] Evidence of opportunity
- [ ] Evidence of means
- [ ] 3-4 strong evidence items
- [ ] Logical theory of the crime

**Defence has:**
- [ ] Alternative explanation
- [ ] Evidence creating doubt
- [ ] 3-4 strong evidence items
- [ ] Challenges to prosecution theory
- [ ] Reasonable doubt argument

**Overall:**
- [ ] Both sides address each other's strongest points
- [ ] Neither side has overwhelming advantage
- [ ] Reasonable people could disagree
- [ ] Both verdicts are defensible with sound reasoning


## Writing Style Guidelines

### Tone

**Formal but accessible:**
- Use proper legal terminology
- Explain technical terms
- Avoid overly casual language
- Don't talk down to users

**Example (Good):**
```
Dr. Chen testifies that digoxin overdose typically takes 30-60 minutes to cause 
cardiac arrest. Given the time of death (between 8:00-8:45 PM), the poison would 
need to have been administered between 7:00-8:15 PM.
```

**Example (Too casual):**
```
The doc says the poison takes like half an hour to an hour to kill someone, so 
whoever did it must have given it to him sometime around dinner.
```

**Example (Too formal):**
```
The pathologist's testimony indicates that the pharmacokinetics of digoxin 
intoxication demonstrate a latency period of thirty to sixty minutes prior to 
the manifestation of fatal cardiac dysrhythmia.
```

### Clarity

**Be specific:**
- Use exact numbers, times, amounts
- Name people and places
- Describe actions precisely
- Avoid vague language

**Good:** "Marcus's vehicle entered at 7:45 PM and exited at 8:20 PM"
**Bad:** "Marcus arrived in the evening and left a little while later"

**Good:** "£2.3 million was transferred through 127 transactions"
**Bad:** "A lot of money was moved around in many transactions"

### Objectivity

**Present facts, then interpretations:**
1. State what was observed/found
2. Explain what it might mean
3. Acknowledge limitations

**Example:**
```
Forensic analysis found Marcus's fingerprints on the library door handle, the 
chair he sat in, and the forged will document. However, no fingerprints were 
found on the medical cabinet, the whisky decanter, or Lord Blackthorn's glass. 
The glass contained traces of digoxin mixed with whisky.
```

**What works:**
- Facts first (fingerprints found here, not found there)
- Neutral language (no "suspicious" or "incriminating")
- Relevant detail (glass contained poison)
- Lets users draw conclusions

### Conciseness

**Every word should matter:**
- Cut unnecessary adjectives
- Avoid redundancy
- Use active voice
- Get to the point

**Wordy:** "It is important to note that the defendant, who was the estate manager, had been working at the estate for a period of fifteen years"

**Concise:** "The defendant had managed the estate for fifteen years"

### Consistency

**Maintain consistency in:**
- Character names (don't switch between "Marcus" and "Ashford")
- Terminology (pick "defendant" or "accused," not both)
- Tone (formal throughout)
- Tense (past tense for events, present for testimony)
- Format (evidence IDs, timestamps)

## Technical Requirements

### JSON Formatting

**Use proper JSON syntax:**
- Double quotes for strings
- No trailing commas
- Proper escaping of special characters
- Consistent indentation (2 spaces)

**Validate JSON:**
```bash
# Use a JSON validator
python -m json.tool fixtures/your-case.json
```

### ISO 8601 Timestamps

**Format:** `YYYY-MM-DDTHH:MM:SSZ`

**Examples:**
- `2024-01-15T19:30:00Z` (7:30 PM on January 15, 2024)
- `2022-06-15T09:23:00Z` (9:23 AM on June 15, 2022)

**Tips:**
- Use 24-hour time
- Include seconds
- End with Z (UTC timezone)
- Be consistent with date format


### Evidence ID Naming

**Format:** `evidence-XXX` where XXX is a three-digit number

**Examples:**
- `evidence-001`
- `evidence-002`
- `evidence-007`

**Rules:**
- Start at 001
- Use leading zeros
- Sequential numbering
- Lowercase "evidence"

### Case ID Naming

**Format:** `descriptive-name-###` where ### is a three-digit number

**Examples:**
- `blackthorn-hall-001`
- `digital-deception-002`
- `riverside-conspiracy-003`

**Rules:**
- Descriptive name (2-3 words)
- Lowercase with hyphens
- Three-digit number
- Unique across all cases

## Quality Checklist

Use this comprehensive checklist before submitting a case:

### Structure
- [ ] Case ID is unique and properly formatted
- [ ] Title follows "The Crown v. [Defendant]" format
- [ ] All required fields are present
- [ ] JSON is valid and well-formatted

### Narrative
- [ ] Hook scene is 100-150 words
- [ ] Hook scene introduces victim, defendant, and mystery
- [ ] Charge text is legally accurate
- [ ] Victim profile is complete
- [ ] Defendant profile is complete
- [ ] 3-5 witness profiles are included
- [ ] All characters have background and relevant facts

### Evidence
- [ ] 5-7 evidence items total
- [ ] Mix of physical, testimonial, and documentary
- [ ] Each item has unique ID (evidence-001, etc.)
- [ ] Each item has type, title, description, timestamp
- [ ] Each item is presented by prosecution or defence
- [ ] Each item has significance statement
- [ ] Descriptions are 100-200 words
- [ ] Evidence is balanced between prosecution and defence

### Timeline
- [ ] Timeline events are chronological
- [ ] Timestamps use ISO 8601 format
- [ ] Each event references valid evidence IDs
- [ ] Timeline creates tension or ambiguity
- [ ] Key moments are included

### Ground Truth
- [ ] Verdict is "guilty" or "not_guilty"
- [ ] 5-8 key facts explain verdict
- [ ] Key facts reference specific evidence
- [ ] 3-5 required evidence references listed
- [ ] Required evidence IDs are valid
- [ ] Logical fallacies list is appropriate
- [ ] Coherence threshold is between 0 and 1

### Ambiguity
- [ ] Can argue for guilty with 3-4 evidence items
- [ ] Can argue for not guilty with 3-4 evidence items
- [ ] Both arguments are logically sound
- [ ] Case feels genuinely ambiguous
- [ ] Neither verdict is obvious

### Quality
- [ ] Writing is clear and concise
- [ ] Tone is formal but accessible
- [ ] Technical terms are explained
- [ ] Characters feel real and developed
- [ ] Evidence is realistic and credible
- [ ] No logical contradictions
- [ ] Case is engaging and compelling

### Validation
- [ ] Passes validation tool with no errors
- [ ] No warnings (or warnings are acceptable)
- [ ] Tested with both verdict arguments
- [ ] Peer reviewed by at least one person
- [ ] Ready for integration into VERITAS system


## Example Case Analysis

Let's analyze Blackthorn Hall to see these principles in action.

### What Makes Blackthorn Hall Effective

**Strong Hook Scene:**
- Atmospheric setting ("grand estate," "grey English sky")
- Immediate mystery (dead body, forged will)
- Clear stakes (£500,000 inheritance)
- Compelling tension (last person to see victim alive)

**Balanced Evidence:**
- Prosecution (Items 1-3): Motive, opportunity, means
- Defence (Items 4-7): Timeline doubt, missing fingerprints, variable poison timing
- Each side has strong arguments

**Effective Ambiguity:**
- Timeline creates genuine doubt (32-minute window)
- Missing evidence (no fingerprints on glass)
- Scientific uncertainty (poison timing varies)
- Circumstantial case (no direct proof)

**Well-Developed Characters:**
- Victim: Wealthy, meticulous, discovered forgery
- Defendant: Trusted manager, financial troubles, 15-year history
- Witnesses: Forensic expert, housekeeper, detective (varied perspectives)

**Clear Ground Truth:**
- Not guilty verdict justified by reasonable doubt
- Key facts reference specific evidence
- Applies legal standard ("beyond reasonable doubt")
- Addresses prosecution's strongest points

### What Could Be Improved

**More Witness Diversity:**
- Could add character witness for defendant
- Could include forensic accountant on forgery
- Could add family member with different perspective

**Additional Defence Evidence:**
- Could show defendant's alibi after leaving
- Could present evidence of other suspects
- Could include expert testimony on forgery timing

**Deeper Character Development:**
- Could explore defendant's relationship with victim
- Could add more background on victim's family
- Could develop housekeeper's observations more

## Resources and References

### Legal Resources

**British Crown Court Procedure:**
- Opening speeches (prosecution, then defence)
- Evidence presentation
- Cross-examination
- Closing speeches (prosecution, then defence)
- Judge's summing up
- Jury deliberation and verdict

**Legal Standards:**
- **Burden of proof:** Prosecution must prove guilt
- **Standard of proof:** Beyond reasonable doubt
- **Presumption of innocence:** Defendant is innocent until proven guilty

### Forensic Resources

**Common Evidence Types:**
- DNA evidence
- Fingerprints
- Toxicology reports
- Digital forensics
- Financial records
- Witness testimony

**Forensic Limitations:**
- Evidence can be circumstantial
- Timing can be uncertain
- Interpretation varies
- Contamination possible

### Writing Resources

**Narrative Techniques:**
- Show, don't tell
- Use specific details
- Create atmosphere
- Build tension gradually
- End scenes with questions

**Character Development:**
- Give characters history
- Create mixed motivations
- Avoid stereotypes
- Use specific details
- Show through actions


## Frequently Asked Questions

### Q: How long should evidence descriptions be?

**A:** 100-200 words per evidence item. Long enough to provide specific details, short enough to read quickly. Focus on facts first, then implications.

### Q: Can I use real cases as inspiration?

**A:** Yes, but change names, locations, and specific details. Real cases can provide realistic evidence patterns and legal procedures. Always fictionalize completely.

### Q: Should I always use "not guilty" as ground truth?

**A:** No. Both existing cases use "not guilty" because they emphasize reasonable doubt, but "guilty" ground truth is equally valid if the evidence strongly supports it. Choose based on which verdict best fits the evidence.

### Q: How do I know if my case is ambiguous enough?

**A:** Test both verdicts. Write a paragraph arguing for guilty and another for not guilty. If both arguments are strong and use specific evidence, your case is ambiguous. If one argument is obviously stronger, rebalance your evidence.

### Q: Can I have more than 7 evidence items?

**A:** No. The system requires 5-7 evidence items. More than 7 overwhelms users and extends the experience beyond 15 minutes. If you have more, combine similar items or cut less essential ones.

### Q: What if my evidence contradicts itself?

**A:** Avoid direct contradictions—they feel unrealistic. Instead, create ambiguity through:
- Incomplete information (missing evidence)
- Timing uncertainty (when did it happen?)
- Alternative explanations (could be this or that)
- Credibility questions (is the witness reliable?)

### Q: How technical can I make the evidence?

**A:** Technical evidence is fine, but explain it in accessible language. Assume users are intelligent but not experts. Use analogies, examples, and plain language explanations.

### Q: Should witnesses be biased?

**A:** Some bias is realistic and adds complexity. A former employee with a grudge, a family member who's loyal, or an expert hired by one side—these create credibility questions. But don't make all witnesses biased or users won't trust any evidence.

### Q: How do I create a tight timeline?

**A:** Use precise timestamps and short windows. Example: Defendant arrives at 7:45 PM, leaves at 8:20 PM, victim found dead at 8:45 PM. The 35-minute window creates pressure—was there enough time?

### Q: What makes a good hook scene?

**A:** Start with atmosphere, introduce the mystery quickly, create immediate tension, and end with a question. Use sensory details and specific language. Aim for 100-150 words.

### Q: Can I use multiple defendants or victims?

**A:** Possible, but complex. VERITAS is designed for one defendant, one victim. Multiple defendants complicate the verdict (guilty of what? all of them?). Multiple victims can work if they're part of the same crime.

### Q: How do I validate my case?

**A:** Run the validation tool:
```bash
python scripts/validate_case.py fixtures/your-case.json
```
Fix any errors, then test both verdict arguments with peers.

## Conclusion

Creating effective VERITAS cases requires balancing multiple elements:
- **Narrative engagement** (compelling story and characters)
- **Evidential ambiguity** (supporting both verdicts)
- **Legal accuracy** (realistic procedures and standards)
- **User experience** (clear, accessible, 15-minute timeframe)

The best cases feel like real trials—complex, ambiguous, and thought-provoking. Users should struggle to decide, reference multiple evidence items, and apply legal standards. Whether they reach the "correct" verdict matters less than whether they think carefully and reason soundly.

Use this guide as a reference throughout your authoring process. Start with a strong concept, develop balanced evidence, create compelling characters, and test thoroughly. The validation tool ensures technical correctness, but peer review ensures quality and ambiguity.

Good luck creating your VERITAS case!

## Appendix: Case Template

Use this template to start your case:

```json
{
  "caseId": "your-case-name-###",
  "title": "The Crown v. [Defendant Name]",
  "narrative": {
    "hookScene": "[100-150 words: atmospheric opening introducing victim, defendant, and mystery]",
    "chargeText": "[Defendant Name], you are charged with [crime] contrary to [statute], in that [circumstances]. How do you plead?",
    "victimProfile": {
      "name": "[Full Name]",
      "role": "Victim",
      "background": "[2-3 sentences about who they were]",
      "relevantFacts": [
        "[Fact 1]",
        "[Fact 2]",
        "[Fact 3]",
        "[Fact 4]"
      ]
    },
    "defendantProfile": {
      "name": "[Full Name]",
      "role": "Defendant",
      "background": "[2-3 sentences about who they are]",
      "relevantFacts": [
        "[Fact 1]",
        "[Fact 2]",
        "[Fact 3]",
        "[Fact 4]"
      ]
    },
    "witnessProfiles": [
      {
        "name": "[Witness 1 Name]",
        "role": "[Their role]",
        "background": "[1-2 sentences]",
        "relevantFacts": [
          "[Fact 1]",
          "[Fact 2]",
          "[Fact 3]"
        ]
      }
    ]
  },
  "evidence": [
    {
      "id": "evidence-001",
      "type": "physical|testimonial|documentary",
      "title": "[Short descriptive title]",
      "description": "[100-200 words: specific details about the evidence]",
      "timestamp": "YYYY-MM-DDTHH:MM:SSZ",
      "presentedBy": "prosecution|defence",
      "significance": "[Why this evidence matters]"
    }
  ],
  "timeline": [
    {
      "timestamp": "YYYY-MM-DDTHH:MM:SSZ",
      "description": "[What happened]",
      "evidenceIds": ["evidence-001"]
    }
  ],
  "groundTruth": {
    "actualVerdict": "guilty|not_guilty",
    "keyFacts": [
      "[Fact explaining verdict]",
      "[Another fact]",
      "[5-8 facts total]"
    ],
    "reasoningCriteria": {
      "requiredEvidenceReferences": [
        "evidence-001",
        "evidence-002"
      ],
      "logicalFallacies": [
        "ad_hominem",
        "appeal_to_emotion",
        "hasty_generalization",
        "false_dichotomy"
      ],
      "coherenceThreshold": 0.65
    }
  }
}
```

## Related Documentation

- **[Case Validation Tool](case-validation-tool.md)**: Technical documentation for the validation tool
- **[Requirements Document](../.kiro/specs/veritas-courtroom-experience/requirements.md)**: Full system requirements
- **[Design Document](../.kiro/specs/veritas-courtroom-experience/design.md)**: System architecture and design
- **[Blackthorn Hall Case](../fixtures/blackthorn-hall-001.json)**: Example murder case
- **[Digital Deception Case](../fixtures/digital-deception-002.json)**: Example fraud case

---

**Document Version:** 1.0  
**Last Updated:** January 2024  
**Maintained By:** VERITAS Development Team
