# Requirements Document

## Introduction

VERITAS is a 15-minute interactive courtroom drama experience built natively for the Luffa platform. Users experience a fictional British Crown Court murder trial through three acts: an atmospheric opening hook, a structured trial with AI agents representing court roles, and an interactive jury deliberation where the user serves as the only human juror among 7 AI jurors. The system evaluates both the verdict chosen and the quality of reasoning, creating a dual-layer assessment that rewards sound judgment regardless of outcome.

The experience integrates three Luffa platform components: Luffa Bot (courtroom clerk/guide), SuperBox (visual courtroom interface), and Luffa Channel (case distribution). The flagship case, "Blackthorn Hall," involves a wealthy patron found dead after threatening to expose a forged family will.

## Glossary

- **VERITAS_System**: The complete interactive courtroom experience system
- **Luffa_Bot**: Platform component serving as courtroom clerk and user guide
- **SuperBox**: Platform component providing visual courtroom interface
- **Luffa_Channel**: Platform component for case announcements and verdict sharing
- **Trial_Layer**: AI agents representing court roles (Clerk, Prosecution, Defence, Fact_Checker, Judge)
- **Jury_Layer**: AI jurors and human user in deliberation (3 active AI, 4 lightweight AI, 1 human)
- **Evidence_Board**: Visual interface displaying case evidence items with timeline
- **Reasoning_Evaluation**: System assessment of user's logical reasoning quality
- **Verdict_Outcome**: Final jury decision (guilty or not guilty)
- **Truth_Reveal**: Post-verdict disclosure of actual case facts
- **Case_Content**: Structured data containing case narrative, evidence, and character information
- **State_Machine**: Backend system managing experience flow and transitions
- **Hook_Scene**: Short atmospheric opening sequence introducing the case
- **Jury_Deliberation**: Interactive discussion phase where user and AI jurors debate
- **Anonymous_Vote**: Final voting mechanism where juror identities are hidden
- **Dual_Reveal**: Combined disclosure of verdict and reasoning quality assessment
- **Fact_Checker**: AI agent that intervenes during trial to correct misstatements
- **Judge_Summing_Up**: Judge's summary of evidence and legal instructions before deliberation
- **Crown_Court**: British criminal court format used for trial structure
- **Evidence_Item**: Individual piece of case evidence (physical, testimonial, or documentary)
- **Trial_Stage**: Distinct phase of courtroom proceedings (opening, evidence, closing, etc.)
- **Juror_Persona**: Defined reasoning style for AI jurors (Evidence_Purist, Sympathetic_Doubter, Moral_Absolutist)

## Requirements

### Requirement 1: Case Content Management

**User Story:** As a content creator, I want to define structured case data, so that the system can present consistent trial narratives.

#### Acceptance Criteria

1. THE VERITAS_System SHALL store Case_Content in JSON format with fields for narrative, evidence, characters, and timeline
2. WHEN Case_Content is loaded, THE VERITAS_System SHALL validate all required fields are present
3. THE Case_Content SHALL include between 5 and 7 Evidence_Items for the flagship case
4. THE Case_Content SHALL define character profiles for defendant, victim, and witnesses
5. THE Case_Content SHALL specify the ground truth outcome for Reasoning_Evaluation
6. FOR ALL Case_Content objects, serializing then deserializing SHALL produce an equivalent object (round-trip property)

### Requirement 2: Experience State Management

**User Story:** As a user, I want the experience to flow smoothly through trial stages, so that I can follow the courtroom proceedings naturally.

#### Acceptance Criteria

1. THE State_Machine SHALL manage transitions between Hook_Scene, Trial_Stages, Jury_Deliberation, and Dual_Reveal
2. WHEN a Trial_Stage completes, THE State_Machine SHALL advance to the next stage automatically
3. THE State_Machine SHALL prevent users from skipping required Trial_Stages
4. WHEN a user disconnects, THE State_Machine SHALL preserve their progress for 24 hours
5. THE State_Machine SHALL enforce a maximum experience duration of 20 minutes

### Requirement 3: Hook Scene Presentation

**User Story:** As a user, I want an engaging opening scene, so that I am drawn into the case immediately.

#### Acceptance Criteria

1. WHEN the experience starts, THE VERITAS_System SHALL present the Hook_Scene within 5 seconds
2. THE Hook_Scene SHALL last between 60 and 90 seconds
3. THE Hook_Scene SHALL introduce the victim, defendant, and central mystery
4. WHEN the Hook_Scene completes, THE VERITAS_System SHALL transition to the formal charge reading
5. THE SuperBox SHALL display atmospheric visuals during the Hook_Scene

### Requirement 4: Evidence Board Display

**User Story:** As a user, I want to view all case evidence in one place, so that I can reference it during deliberation.

#### Acceptance Criteria

1. THE Evidence_Board SHALL display all Evidence_Items with descriptions and timestamps
2. WHEN an Evidence_Item is presented during trial, THE Evidence_Board SHALL highlight that item
3. THE Evidence_Board SHALL remain accessible throughout Jury_Deliberation
4. THE Evidence_Board SHALL organize Evidence_Items chronologically on a timeline
5. WHEN a user selects an Evidence_Item, THE SuperBox SHALL display detailed information

### Requirement 5: Trial Layer Agent Orchestration

**User Story:** As a system designer, I want AI agents to perform distinct court roles, so that the trial feels authentic and structured.

#### Acceptance Criteria

1. THE Trial_Layer SHALL include exactly 5 AI agents: Clerk, Prosecution, Defence, Fact_Checker, and Judge
2. WHEN the Prosecution or Defence makes a factual error, THE Fact_Checker SHALL intervene within 10 seconds
3. THE Prosecution SHALL present opening statement before Defence opening statement
4. THE Judge SHALL deliver Judge_Summing_Up after closing speeches and before Jury_Deliberation
5. THE Trial_Layer SHALL follow Crown_Court procedure order: Opening → Prosecution opening → Defence opening → Evidence presentation → Cross-examination → Closing speeches → Judge_Summing_Up

### Requirement 6: Fact Checking Intervention

**User Story:** As a user, I want factual errors corrected during trial, so that I can trust the information presented.

#### Acceptance Criteria

1. WHEN the Prosecution or Defence states a fact contradicting Case_Content, THE Fact_Checker SHALL interrupt
2. THE Fact_Checker SHALL cite the specific Evidence_Item that contradicts the misstatement
3. THE Fact_Checker SHALL intervene a maximum of 3 times per trial to avoid disruption
4. THE Fact_Checker SHALL not intervene during opening or closing speeches (opinion statements)
5. WHEN the Fact_Checker intervenes, THE SuperBox SHALL display the corrected information visually

### Requirement 7: Judge Summing Up Generation

**User Story:** As a user, I want the judge to summarize the case fairly, so that I can deliberate with clear legal guidance.

#### Acceptance Criteria

1. WHEN all closing speeches complete, THE Judge SHALL deliver Judge_Summing_Up
2. THE Judge_Summing_Up SHALL summarize key evidence from both Prosecution and Defence
3. THE Judge_Summing_Up SHALL provide legal instructions on burden of proof and reasonable doubt
4. THE Judge_Summing_Up SHALL last between 90 and 120 seconds
5. THE Judge_Summing_Up SHALL not express opinion on verdict outcome

### Requirement 8: Jury Layer Composition

**User Story:** As a user, I want to deliberate with diverse AI jurors, so that I experience realistic jury dynamics.

#### Acceptance Criteria

1. THE Jury_Layer SHALL include exactly 8 jurors: 3 active AI, 4 lightweight AI, and 1 human user
2. THE Jury_Layer SHALL assign Juror_Personas to the 3 active AI jurors: Evidence_Purist, Sympathetic_Doubter, and Moral_Absolutist
3. THE 4 lightweight AI jurors SHALL contribute brief statements during Jury_Deliberation
4. THE 3 active AI jurors SHALL engage in back-and-forth debate during Jury_Deliberation
5. THE Jury_Layer SHALL not reveal which jurors are AI until after the Dual_Reveal

### Requirement 9: Jury Deliberation Interaction

**User Story:** As a user, I want to participate in jury deliberation, so that I can influence the discussion and form my verdict.

#### Acceptance Criteria

1. WHEN Jury_Deliberation begins, THE VERITAS_System SHALL prompt the user to share their initial thoughts
2. THE Jury_Deliberation SHALL last between 4 and 6 minutes
3. WHEN the user makes a statement, THE active AI jurors SHALL respond within 15 seconds
4. THE VERITAS_System SHALL allow the user to reference Evidence_Items during Jury_Deliberation
5. WHEN 6 minutes elapse, THE VERITAS_System SHALL proceed to Anonymous_Vote regardless of discussion state

### Requirement 10: Anonymous Voting Mechanism

**User Story:** As a user, I want to vote anonymously, so that I can make my decision without social pressure.

#### Acceptance Criteria

1. WHEN Jury_Deliberation completes, THE VERITAS_System SHALL present Anonymous_Vote interface
2. THE Anonymous_Vote SHALL display only "Guilty" and "Not Guilty" options without juror names
3. THE VERITAS_System SHALL collect votes from all 8 jurors simultaneously
4. THE VERITAS_System SHALL not reveal individual votes until Dual_Reveal
5. THE VERITAS_System SHALL determine Verdict_Outcome by majority vote (5 or more jurors)

### Requirement 11: Reasoning Quality Evaluation

**User Story:** As a user, I want my reasoning assessed, so that I can understand the quality of my judgment beyond just the verdict.

#### Acceptance Criteria

1. WHEN the user participates in Jury_Deliberation, THE VERITAS_System SHALL analyze their statements for logical coherence
2. THE Reasoning_Evaluation SHALL assess whether the user referenced relevant Evidence_Items
3. THE Reasoning_Evaluation SHALL identify logical fallacies in user arguments
4. THE Reasoning_Evaluation SHALL produce one of four outcomes: "sound reasoning + correct verdict", "sound reasoning + incorrect verdict", "weak reasoning + correct verdict", "weak reasoning + incorrect verdict"
5. THE Reasoning_Evaluation SHALL complete within 10 seconds of Anonymous_Vote completion

### Requirement 12: Dual Reveal Presentation

**User Story:** As a user, I want to see both the verdict and my reasoning assessment, so that I can reflect on my judgment quality.

#### Acceptance Criteria

1. WHEN all votes are collected, THE VERITAS_System SHALL present Dual_Reveal
2. THE Dual_Reveal SHALL first display the Verdict_Outcome with vote count
3. THE Dual_Reveal SHALL then display the Truth_Reveal showing actual case facts
4. THE Dual_Reveal SHALL display the user's Reasoning_Evaluation with specific feedback
5. THE Dual_Reveal SHALL reveal which jurors were AI and their voting patterns

### Requirement 13: Luffa Bot Integration

**User Story:** As a user, I want guidance from the courtroom clerk, so that I understand what to do at each stage.

#### Acceptance Criteria

1. THE Luffa_Bot SHALL greet users and explain the VERITAS_System experience at the start
2. WHEN a new Trial_Stage begins, THE Luffa_Bot SHALL announce the stage name and purpose
3. THE Luffa_Bot SHALL prompt the user to launch SuperBox when visual content is required
4. WHEN the user asks a procedural question, THE Luffa_Bot SHALL respond within 5 seconds
5. THE Luffa_Bot SHALL maintain a formal but accessible tone matching a court clerk

### Requirement 14: SuperBox Visual Interface

**User Story:** As a user, I want rich visual presentation, so that the courtroom experience feels immersive.

#### Acceptance Criteria

1. THE SuperBox SHALL display the courtroom environment during Trial_Stages
2. THE SuperBox SHALL render the Evidence_Board with interactive Evidence_Items
3. THE SuperBox SHALL display the jury chamber environment during Jury_Deliberation
4. THE SuperBox SHALL show speaker indicators when AI agents or jurors speak
5. THE SuperBox SHALL display the Dual_Reveal with visual verdict and reasoning graphics

### Requirement 15: Luffa Channel Distribution

**User Story:** As a user, I want to discover new cases and share verdicts, so that I can engage with the VERITAS community.

#### Acceptance Criteria

1. THE Luffa_Channel SHALL announce when new Case_Content becomes available
2. WHEN a user completes a case, THE VERITAS_System SHALL offer to share their Verdict_Outcome to Luffa_Channel
3. THE Luffa_Channel SHALL display aggregate verdict statistics across all users
4. THE Luffa_Channel SHALL not reveal individual user Reasoning_Evaluation scores publicly
5. WHERE a user opts in, THE VERITAS_System SHALL share their verdict anonymously to Luffa_Channel

### Requirement 16: Blackthorn Hall Case Content

**User Story:** As a user, I want to experience the flagship case, so that I can evaluate the VERITAS_System with polished content.

#### Acceptance Criteria

1. THE VERITAS_System SHALL include complete Case_Content for "Blackthorn Hall" case
2. THE Blackthorn Hall case SHALL involve a wealthy patron found dead after threatening to expose a forged will
3. THE Blackthorn Hall case SHALL present evidence suggesting the defendant had motive, access, and opportunity
4. THE Blackthorn Hall case SHALL include timing inconsistencies that create reasonable doubt
5. THE Blackthorn Hall case SHALL support both guilty and not guilty verdicts with sound reasoning

### Requirement 17: Experience Duration Management

**User Story:** As a user, I want the experience to complete in 15 minutes, so that it fits into my schedule.

#### Acceptance Criteria

1. THE VERITAS_System SHALL target a total experience duration of 15 minutes
2. THE Hook_Scene SHALL consume approximately 1.5 minutes
3. THE Trial_Stages SHALL consume approximately 7 minutes total
4. THE Jury_Deliberation SHALL consume approximately 5 minutes
5. THE Dual_Reveal SHALL consume approximately 1.5 minutes

### Requirement 18: Trial Stage Progression

**User Story:** As a user, I want to follow the trial structure, so that I understand the flow of evidence and arguments.

#### Acceptance Criteria

1. THE VERITAS_System SHALL present Trial_Stages in this order: Charge reading, Prosecution opening, Defence opening, Evidence presentation, Cross-examination, Prosecution closing, Defence closing, Judge_Summing_Up
2. WHEN Evidence presentation begins, THE Evidence_Board SHALL become accessible
3. THE VERITAS_System SHALL allow users to pause between Trial_Stages for up to 2 minutes
4. WHEN a Trial_Stage is in progress, THE VERITAS_System SHALL prevent navigation to other stages
5. THE VERITAS_System SHALL display progress indicators showing current Trial_Stage

### Requirement 19: AI Agent Prompt Management

**User Story:** As a system designer, I want to configure AI agent behavior, so that agents perform their roles convincingly.

#### Acceptance Criteria

1. THE VERITAS_System SHALL store prompts for each Trial_Layer agent defining their role and constraints
2. THE VERITAS_System SHALL store prompts for each Juror_Persona defining their reasoning style
3. WHEN an AI agent generates content, THE VERITAS_System SHALL enforce character limits appropriate to the Trial_Stage
4. THE VERITAS_System SHALL provide Case_Content context to all AI agents
5. THE VERITAS_System SHALL prevent AI agents from revealing information not yet presented in the trial

### Requirement 20: Error Recovery and Graceful Degradation

**User Story:** As a user, I want the experience to continue even if technical issues occur, so that I can complete the case.

#### Acceptance Criteria

1. WHEN an AI agent fails to respond within 30 seconds, THE VERITAS_System SHALL use a fallback response
2. WHEN SuperBox fails to load, THE Luffa_Bot SHALL provide text-based alternatives for visual content
3. WHEN Reasoning_Evaluation fails, THE VERITAS_System SHALL still display Verdict_Outcome and Truth_Reveal
4. THE VERITAS_System SHALL log all errors for debugging without interrupting user experience
5. WHEN a critical failure occurs, THE VERITAS_System SHALL offer the user an option to restart from the last completed Trial_Stage
