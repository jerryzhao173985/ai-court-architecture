# Implementation Plan: VERITAS Courtroom Experience

## Overview

This implementation plan breaks down the VERITAS interactive courtroom experience into discrete, testable coding tasks. The system will be built in Python, following the architecture defined in the design document. Implementation follows a bottom-up approach: core data models and validation first, then state management, agent orchestration, and finally integration with Luffa platform components.

The plan includes 40 property-based tests (minimum 100 iterations each) mapped to the correctness properties in the design document, plus unit tests for specific examples and edge cases. Testing tasks are marked as optional with "*" to allow for faster MVP iteration.

## Tasks

- [x] 1. Set up project structure and core data models
  - [x] 1.1 Create project directory structure and configuration
    - Set up Python project with src/ directory structure
    - Create pyproject.toml with dependencies: pydantic, pytest, hypothesis, fastapi, websockets
    - Set up tests/ directory with unit/ and property/ subdirectories
    - Create fixtures/ directory with sample case content
    - _Requirements: 1.1, 1.2_

  - [x] 1.2 Implement case content data models with Pydantic
    - Create CaseContent, EvidenceItem, CharacterProfile, TimelineEvent models
    - Add validation for required fields and constraints (5-7 evidence items)
    - Implement serialization/deserialization methods
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

  - [ ]* 1.3 Write property test for case content serialization round-trip
    - **Property 1: Case Content Serialization Round-Trip**
    - **Validates: Requirements 1.6**

  - [ ]* 1.4 Write property test for case content validation
    - **Property 2: Case Content Validation**
    - **Validates: Requirements 1.2, 1.4, 1.5**

  - [ ]* 1.5 Write unit tests for case content models
    - Test Blackthorn Hall case loads correctly
    - Test validation rejects missing required fields
    - Test evidence item count constraints (5-7 items)
    - _Requirements: 1.1, 1.2, 1.3, 16.1_

- [x] 2. Implement state machine and experience flow
  - [x] 2.1 Create ExperienceState enum and state machine core
    - Define 13 experience states (NOT_STARTED through COMPLETED)
    - Implement StateMachine class with state tracking
    - Add state transition validation logic
    - Implement timing tracking per state
    - _Requirements: 2.1, 2.2, 2.3, 2.5_

  - [x] 2.2 Implement state persistence and recovery
    - Create UserSession model with progress tracking
    - Implement saveProgress() and restoreProgress() methods
    - Add 24-hour retention logic for disconnected sessions
    - _Requirements: 2.4_

  - [ ]* 2.3 Write property test for trial stage sequential progression
    - **Property 3: Trial Stage Sequential Progression**
    - **Validates: Requirements 2.2, 3.4, 5.3, 5.4, 5.5, 7.1, 10.1, 12.1, 18.1**

  - [ ]* 2.4 Write property test for stage skipping prevention
    - **Property 4: Stage Skipping Prevention**
    - **Validates: Requirements 2.3, 18.4**

  - [ ]* 2.5 Write property test for session state persistence round-trip
    - **Property 5: Session State Persistence Round-Trip**
    - **Validates: Requirements 2.4**

  - [ ]* 2.6 Write property test for maximum duration enforcement
    - **Property 6: Maximum Duration Enforcement**
    - **Validates: Requirements 2.5**

  - [ ]* 2.7 Write unit tests for state machine
    - Test state transitions follow Crown Court order
    - Test invalid transitions are rejected
    - Test state machine at final state (no next transition)
    - Test 20-minute maximum duration enforcement
    - _Requirements: 2.1, 2.2, 2.3, 2.5_

- [x] 3. Implement case manager component
  - [x] 3.1 Create CaseManager class with loading and validation
    - Implement loadCase() to read JSON case files
    - Implement validateCase() with comprehensive checks
    - Add getEvidenceItems() and getEvidenceByTimestamp() methods
    - Implement serializeCase() and deserializeCase()
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6_

  - [x] 3.2 Create Blackthorn Hall flagship case content
    - Write complete JSON case file with narrative, evidence, timeline
    - Include 5-7 evidence items with timestamps
    - Define victim, defendant, and witness profiles
    - Set ground truth with timing inconsistencies supporting both verdicts
    - _Requirements: 16.1, 16.2, 16.3, 16.4, 16.5_

  - [ ]* 3.3 Write unit tests for case manager
    - Test Blackthorn Hall case loads successfully
    - Test validation rejects malformed JSON
    - Test evidence sorting by timestamp
    - Test case with missing required fields fails validation
    - _Requirements: 1.1, 1.2, 16.1_

- [x] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Implement evidence board component
  - [x] 5.1 Create EvidenceBoard class with timeline rendering
    - Implement renderTimeline() to organize evidence chronologically
    - Add highlightItem() to emphasize current evidence
    - Implement selectItem() for detailed view
    - Add filterByType() and searchEvidence() methods
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

  - [ ]* 5.2 Write property test for evidence board completeness
    - **Property 8: Evidence Board Completeness**
    - **Validates: Requirements 4.1, 4.4**

  - [ ]* 5.3 Write property test for evidence highlighting
    - **Property 9: Evidence Highlighting**
    - **Validates: Requirements 4.2**

  - [ ]* 5.4 Write property test for evidence board accessibility during deliberation
    - **Property 29: Evidence Board Accessibility During Deliberation**
    - **Validates: Requirements 4.3**

  - [ ]* 5.5 Write unit tests for evidence board
    - Test evidence board displays all items with descriptions
    - Test chronological timeline organization
    - Test highlighting updates when item presented
    - Test evidence board accessible during deliberation state
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [x] 6. Implement trial layer agent orchestration
  - [x] 6.1 Create TrialAgent base class and agent configurations
    - Define TrialAgent dataclass with role, systemPrompt, characterLimit, responseTimeout
    - Create system prompts for Clerk, Prosecution, Defence, Fact Checker, Judge
    - Implement agent initialization with case context
    - _Requirements: 5.1, 19.1, 19.2, 19.3, 19.4_

  - [x] 6.2 Create TrialOrchestrator class with agent coordination
    - Implement initializeAgents() to set up 5 trial agents with case context
    - Implement executeStage() to run agents for current trial stage
    - Add agent response timeout handling with fallback responses
    - Enforce character limits per agent and stage
    - _Requirements: 5.1, 5.3, 5.4, 5.5, 19.3, 19.4, 20.1_

  - [x] 6.3 Implement fact checker logic
    - Create checkFactAccuracy() to validate statements against case content
    - Implement intervention triggering when contradictions detected
    - Add 3-intervention limit enforcement
    - Restrict fact checking to evidence and cross-examination stages only
    - _Requirements: 5.2, 6.1, 6.2, 6.3, 6.4, 6.5_

  - [x] 6.4 Implement judge summing up generation
    - Create generateJudgeSummary() with case evidence summary
    - Include legal instructions on burden of proof and reasonable doubt
    - Ensure no explicit verdict opinion in summary
    - Enforce 90-120 second duration target
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

  - [ ]* 6.5 Write property test for fact checker contradiction detection
    - **Property 10: Fact Checker Contradiction Detection**
    - **Validates: Requirements 6.1, 6.2**

  - [ ]* 6.6 Write property test for fact checker intervention limit
    - **Property 11: Fact Checker Intervention Limit**
    - **Validates: Requirements 6.3**

  - [ ]* 6.7 Write property test for fact checker stage restriction
    - **Property 12: Fact Checker Stage Restriction**
    - **Validates: Requirements 6.4**

  - [ ]* 6.8 Write property test for judge summary content requirements
    - **Property 13: Judge Summary Content Requirements**
    - **Validates: Requirements 7.2, 7.3, 7.5**

  - [ ]* 6.9 Write property test for agent character limit enforcement
    - **Property 33: Agent Character Limit Enforcement**
    - **Validates: Requirements 19.3**

  - [ ]* 6.10 Write property test for agent case context provision
    - **Property 34: Agent Case Context Provision**
    - **Validates: Requirements 19.4**

  - [ ]* 6.11 Write property test for agent information sequencing
    - **Property 35: Agent Information Sequencing**
    - **Validates: Requirements 19.5**

  - [ ]* 6.12 Write property test for agent timeout fallback
    - **Property 36: Agent Timeout Fallback**
    - **Validates: Requirements 20.1**

  - [ ]* 6.13 Write unit tests for trial orchestrator
    - Test trial layer has exactly 5 agents with correct roles
    - Test prosecution presents opening before defence
    - Test fact checker intervenes on contradictions during evidence stage
    - Test fact checker does not intervene during opening/closing speeches
    - Test fact checker stops at 3rd intervention
    - Test agent timeout triggers fallback response
    - _Requirements: 5.1, 5.2, 5.3, 6.1, 6.3, 6.4, 20.1_

- [x] 7. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Implement jury layer orchestration
  - [x] 8.1 Create JurorPersona configurations and jury composition
    - Define JurorPersona dataclass with type and persona fields
    - Create system prompts for Evidence Purist, Sympathetic Doubter, Moral Absolutist
    - Create system prompts for 4 lightweight AI jurors
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 19.2_

  - [x] 8.2 Create JuryOrchestrator class with deliberation management
    - Implement initializeJury() to create 7 AI jurors (3 active + 4 lightweight)
    - Implement startDeliberation() to begin deliberation phase
    - Add processUserStatement() to handle user input and generate AI responses
    - Enforce 15-second AI response time
    - Implement 4-6 minute deliberation duration with hard 6-minute cutoff
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 9.1, 9.2, 9.3, 9.4, 9.5_

  - [x] 8.3 Implement anonymous voting mechanism
    - Create collectVotes() to gather votes from all 8 jurors simultaneously
    - Implement VoteCollection and VoteResult models
    - Add calculateVerdict() using majority rule (5+ votes)
    - Ensure individual votes hidden until dual reveal
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

  - [x] 8.4 Implement juror reveal functionality
    - Create revealJurors() to disclose AI identities and votes
    - Include persona information and key statements for active AI jurors
    - _Requirements: 8.5, 12.5_

  - [ ]* 8.5 Write property test for deliberation hard time limit
    - **Property 15: Deliberation Hard Time Limit**
    - **Validates: Requirements 9.5**

  - [ ]* 8.6 Write property test for anonymous voting identity concealment
    - **Property 16: Anonymous Voting Identity Concealment**
    - **Validates: Requirements 10.2, 10.4, 8.5**

  - [ ]* 8.7 Write property test for vote collection completeness
    - **Property 17: Vote Collection Completeness**
    - **Validates: Requirements 10.3**

  - [ ]* 8.8 Write property test for majority verdict calculation
    - **Property 18: Majority Verdict Calculation**
    - **Validates: Requirements 10.5**

  - [ ]* 8.9 Write unit tests for jury orchestrator
    - Test jury composition is exactly 3 active AI + 4 lightweight AI + 1 human
    - Test jury personas are Evidence Purist, Sympathetic Doubter, Moral Absolutist
    - Test user prompted for initial thoughts when deliberation begins
    - Test AI jurors respond within 15 seconds
    - Test deliberation proceeds to vote at 6-minute mark
    - Test verdict calculation with various vote distributions
    - _Requirements: 8.1, 8.2, 9.1, 9.3, 9.5, 10.5_

- [x] 9. Implement reasoning evaluation component
  - [x] 9.1 Create ReasoningEvaluator class with analysis logic
    - Implement analyzeStatements() to evaluate user deliberation statements
    - Create trackEvidenceReferences() to extract evidence mentions
    - Implement detectFallacies() for logical fallacy identification
    - Add calculateCoherence() for logical consistency scoring
    - Implement generateFeedback() for user-facing assessment
    - Ensure evaluation completes within 10 seconds
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

  - [x] 9.2 Implement four-category reasoning assessment
    - Create ReasoningAssessment model with category, scores, fallacies, feedback
    - Implement logic to categorize as sound_correct, sound_incorrect, weak_correct, weak_incorrect
    - Compare user verdict with ground truth for correctness
    - _Requirements: 11.4_

  - [ ]* 9.3 Write property test for reasoning evaluation four-category output
    - **Property 19: Reasoning Evaluation Four-Category Output**
    - **Validates: Requirements 11.4**

  - [ ]* 9.4 Write property test for reasoning evaluation evidence tracking
    - **Property 20: Reasoning Evaluation Evidence Tracking**
    - **Validates: Requirements 11.2**

  - [ ]* 9.5 Write property test for reasoning evaluation fallacy detection
    - **Property 21: Reasoning Evaluation Fallacy Detection**
    - **Validates: Requirements 11.3**

  - [ ]* 9.6 Write property test for jury deliberation user evidence references
    - **Property 14: Jury Deliberation User Evidence References**
    - **Validates: Requirements 9.4**

  - [ ]* 9.7 Write unit tests for reasoning evaluator
    - Test evidence reference tracking in user statements
    - Test fallacy detection for ad hominem, appeal to emotion, false dichotomy
    - Test four-category classification with various inputs
    - Test evaluation completes within 10 seconds
    - _Requirements: 11.1, 11.2, 11.3, 11.4_

- [x] 10. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 11. Implement dual reveal system
  - [x] 11.1 Create DualReveal data model and assembly logic
    - Create DualReveal model with verdict, groundTruth, reasoningAssessment, jurorReveal
    - Implement assembleDualReveal() to combine data from vote result, case content, reasoning evaluation, juror reveal
    - Ensure sequential presentation: verdict → truth → reasoning → juror identities
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_

  - [ ]* 11.2 Write property test for dual reveal completeness
    - **Property 22: Dual Reveal Completeness**
    - **Validates: Requirements 12.2, 12.3, 12.4, 12.5**

  - [ ]* 11.3 Write unit tests for dual reveal
    - Test dual reveal includes verdict with vote count
    - Test dual reveal includes ground truth explanation
    - Test dual reveal includes reasoning assessment
    - Test dual reveal reveals AI juror identities and votes
    - _Requirements: 12.2, 12.3, 12.4, 12.5_

- [x] 12. Implement hook scene and trial stage content
  - [x] 12.1 Create hook scene presentation logic
    - Implement presentHookScene() to display atmospheric opening
    - Ensure hook scene includes victim, defendant, and central mystery
    - Enforce 60-90 second duration
    - Trigger transition to charge reading on completion
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

  - [x] 12.2 Implement trial stage progression and timing
    - Create stage duration tracking for each trial stage
    - Implement automatic transitions between stages
    - Add pause functionality with 2-minute limit
    - Create progress indicators showing current stage
    - _Requirements: 17.1, 17.2, 17.3, 17.4, 17.5, 18.1, 18.2, 18.3, 18.4, 18.5_

  - [ ]* 12.3 Write property test for hook scene content completeness
    - **Property 7: Hook Scene Content Completeness**
    - **Validates: Requirements 3.3**

  - [ ]* 12.4 Write property test for pause duration limit
    - **Property 30: Pause Duration Limit**
    - **Validates: Requirements 18.3**

  - [ ]* 12.5 Write property test for progress indicator accuracy
    - **Property 31: Progress Indicator Accuracy**
    - **Validates: Requirements 18.5**

  - [ ]* 12.6 Write property test for agent prompt storage
    - **Property 32: Agent Prompt Storage**
    - **Validates: Requirements 19.1, 19.2**

  - [ ]* 12.7 Write unit tests for hook scene and trial stages
    - Test hook scene presents within 5 seconds
    - Test hook scene duration between 60-90 seconds
    - Test hook scene transitions to charge reading
    - Test trial stages follow Crown Court order
    - Test pause allowed for up to 2 minutes between stages
    - Test total experience targets 15 minutes
    - _Requirements: 3.1, 3.2, 3.4, 17.1, 18.1, 18.3_

- [x] 13. Implement Luffa Bot integration
  - [x] 13.1 Create LuffaBot interface and message handling
    - Define LuffaBotMessage model with type, content, metadata
    - Implement greeting message on experience start
    - Create stage announcement messages for each trial stage
    - Add SuperBox launch prompts for visual stages
    - Implement procedural question response handling
    - Ensure formal but accessible tone
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5_

  - [ ]* 13.2 Write property test for stage announcement on transition
    - **Property 23: Stage Announcement on Transition**
    - **Validates: Requirements 13.2**

  - [ ]* 13.3 Write property test for SuperBox launch prompts
    - **Property 24: SuperBox Launch Prompts**
    - **Validates: Requirements 13.3**

  - [ ]* 13.4 Write unit tests for Luffa Bot integration
    - Test Luffa Bot greeting on experience start
    - Test stage announcements generated on transitions
    - Test SuperBox launch prompts for visual stages
    - Test procedural question responses within 5 seconds
    - _Requirements: 13.1, 13.2, 13.3, 13.4_

- [x] 14. Implement SuperBox visual interface integration
  - [x] 14.1 Create SuperBox scene models and rendering logic
    - Define SuperBoxScene model with sceneType and elements
    - Create scene configurations for courtroom, jury chamber, evidence board, reveal
    - Implement speaker indicators for AI agents and jurors
    - Add visual verdict and reasoning graphics for dual reveal
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5_

  - [ ]* 14.2 Write property test for SuperBox failure graceful degradation
    - **Property 37: SuperBox Failure Graceful Degradation**
    - **Validates: Requirements 20.2**

  - [ ]* 14.3 Write unit tests for SuperBox integration
    - Test courtroom environment displayed during trial stages
    - Test evidence board rendered with interactive items
    - Test jury chamber displayed during deliberation
    - Test speaker indicators shown when agents speak
    - Test SuperBox failure triggers text-only mode
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 20.2_

- [x] 15. Implement Luffa Channel integration
  - [x] 15.1 Create LuffaChannel interface and announcement handling
    - Define ChannelAnnouncement and VerdictShare models
    - Implement new case announcement generation
    - Create verdict sharing functionality with opt-in
    - Add anonymous attribution for shared verdicts
    - Ensure reasoning scores not included in public shares
    - Implement aggregate verdict statistics display
    - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5_

  - [ ]* 15.2 Write property test for new case announcement
    - **Property 25: New Case Announcement**
    - **Validates: Requirements 15.1**

  - [ ]* 15.3 Write property test for completion share offer
    - **Property 26: Completion Share Offer**
    - **Validates: Requirements 15.2**

  - [ ]* 15.4 Write property test for reasoning score privacy
    - **Property 27: Reasoning Score Privacy**
    - **Validates: Requirements 15.4**

  - [ ]* 15.5 Write property test for opt-in anonymous sharing
    - **Property 28: Opt-In Anonymous Sharing**
    - **Validates: Requirements 15.5**

  - [ ]* 15.6 Write unit tests for Luffa Channel integration
    - Test new case announcement when case added
    - Test verdict share offer on experience completion
    - Test shared verdicts are anonymous
    - Test reasoning scores not included in shares
    - Test aggregate statistics display
    - _Requirements: 15.1, 15.2, 15.4, 15.5_

- [x] 16. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 17. Implement error handling and recovery
  - [x] 17.1 Create error handling infrastructure
    - Implement error logging without user interruption
    - Create fallback response system for agent failures
    - Add graceful degradation for SuperBox failures
    - Implement reasoning evaluation failure isolation
    - Create critical failure recovery with restart offer
    - _Requirements: 20.1, 20.2, 20.3, 20.4, 20.5_

  - [x] 17.2 Implement state preservation and recovery
    - Add auto-save every 30 seconds during active stages
    - Persist state on every stage transition
    - Implement 24-hour recovery window for disconnected sessions
    - Add checkpoint before critical operations (voting, evaluation)
    - _Requirements: 2.4_

  - [ ]* 17.3 Write property test for reasoning evaluation failure isolation
    - **Property 38: Reasoning Evaluation Failure Isolation**
    - **Validates: Requirements 20.3**

  - [ ]* 17.4 Write property test for error logging without interruption
    - **Property 39: Error Logging Without Interruption**
    - **Validates: Requirements 20.4**

  - [ ]* 17.5 Write property test for critical failure recovery offer
    - **Property 40: Critical Failure Recovery Offer**
    - **Validates: Requirements 20.5**

  - [ ]* 17.6 Write unit tests for error handling
    - Test agent timeout uses fallback response
    - Test SuperBox failure switches to text-only mode
    - Test reasoning evaluation failure still shows verdict
    - Test invalid state transition rejected
    - Test critical failure offers restart from last completed stage
    - Test errors logged without interrupting user experience
    - _Requirements: 20.1, 20.2, 20.3, 20.4, 20.5_

- [x] 18. Implement API endpoints and WebSocket communication
  - [x] 18.1 Create FastAPI application with REST endpoints
    - Set up FastAPI app with CORS configuration
    - Create POST /api/sessions to start new experience
    - Create GET /api/sessions/{sessionId} to retrieve session state
    - Create POST /api/sessions/{sessionId}/statements for user deliberation input
    - Create POST /api/sessions/{sessionId}/vote for user voting
    - Create GET /api/cases/{caseId} to retrieve case content
    - _Requirements: 2.1, 9.1, 10.1_

  - [x] 18.2 Implement WebSocket connection for real-time updates
    - Create WebSocket endpoint at /ws/{sessionId}
    - Implement real-time trial stage updates
    - Send agent responses as they're generated
    - Push AI juror statements during deliberation
    - Send state transition notifications
    - _Requirements: 2.1, 5.1, 8.1, 9.1_

  - [ ]* 18.3 Write integration tests for API endpoints
    - Test session creation and retrieval
    - Test user statement submission during deliberation
    - Test vote submission and verdict calculation
    - Test case content retrieval
    - Test WebSocket connection and message flow
    - _Requirements: 2.1, 9.1, 10.1_

- [x] 19. Wire all components together in main application
  - [x] 19.1 Create main application orchestrator
    - Implement ExperienceOrchestrator class coordinating all components
    - Wire state machine to trigger case manager, trial orchestrator, jury orchestrator
    - Connect evidence board updates to trial stage transitions
    - Integrate reasoning evaluator with jury orchestrator
    - Connect dual reveal assembly to vote completion
    - Wire Luffa Bot, SuperBox, and Channel integrations
    - _Requirements: All requirements_

  - [x] 19.2 Implement complete experience flow end-to-end
    - Start experience → Load case → Hook scene → Trial stages → Deliberation → Vote → Dual reveal → Completion
    - Ensure all state transitions trigger appropriate component actions
    - Verify timing constraints enforced throughout
    - Test error recovery at each stage
    - _Requirements: All requirements_

  - [ ]* 19.3 Write integration tests for complete experience flow
    - Test full experience from start to completion
    - Test state transitions trigger correct component actions
    - Test evidence board accessible during deliberation
    - Test dual reveal assembles data from all components
    - Test Luffa Bot announcements on stage transitions
    - Test timing constraints enforced (15-minute target, 20-minute max)
    - _Requirements: All requirements_

- [x] 20. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property-based tests require minimum 100 iterations each
- All property tests must reference their design document property number
- Implementation uses Python with Pydantic for data models, FastAPI for API, Hypothesis for property testing
- Testing framework: pytest for unit tests, Hypothesis for property tests
- AI agent integration assumes LLM API (OpenAI/Anthropic) with structured prompts
- Luffa platform integration (Bot, SuperBox, Channel) assumes existing APIs
- Case content stored as JSON files with potential migration to database later
- WebSocket used for real-time trial updates and deliberation
