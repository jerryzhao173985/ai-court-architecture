# VERITAS Luffa Integration - Refined Plan

## 🎯 Vision

Transform Luffa group chat into an immersive courtroom where AI agents embody characters, users participate as jurors, and the story outcome depends on user choices.

---

## 🤔 Key Considerations

### Current Implementation Analysis

**What Works:**
- ✅ Bot polling and message handling
- ✅ Command processing (/start, /continue, /vote)
- ✅ AI agent response generation
- ✅ Session management per group

**What Needs Refinement:**

1. **Character Identity in Group Chat**
   - Current: Bot posts as "[PROSECUTION]" prefix
   - Better: Each agent should feel like a separate character
   - Solution: Use character names + emojis + formatting

2. **Pacing and Flow**
   - Current: Manual /continue between stages
   - Better: Auto-advance with natural pauses
   - Solution: Configurable auto-advance with user control

3. **Multi-User Participation**
   - Current: Single user vote
   - Better: Multiple users can deliberate and vote
   - Solution: Track multiple human jurors, aggregate votes

4. **Immersion and Atmosphere**
   - Current: Text-only messages
   - Better: Rich formatting, dramatic timing, character voices
   - Solution: Enhanced message formatting, strategic delays

5. **User Agency**
   - Current: Limited to deliberation statements
   - Better: Users can ask questions, challenge agents, influence flow
   - Solution: Natural language processing for user intent

6. **Story Branching**
   - Current: Linear progression
   - Better: Story adapts based on user engagement
   - Solution: Dynamic stage content based on deliberation

---

## 🎭 Refined Design

### Character Representation

**Instead of:**
```
Bot: 🎭 [PROSECUTION]
The evidence shows...
```

**Use:**
```
Bot: ⚖️ Sir Edmund Hartley, KC
     Crown Prosecution

"Members of the jury, the evidence shows beyond any doubt..."
```

**Character Roster:**
- 👨‍⚖️ **The Honourable Justice Pemberton** - Presiding Judge
- ⚖️ **Sir Edmund Hartley, KC** - Crown Prosecution
- 🛡️ **Ms. Catherine Blackwood** - Defence Counsel
- 📋 **Mr. Thomas Wright** - Clerk of the Court
- 🔍 **Dr. Sarah Mitchell** - Fact Checker (silent observer)

**AI Jurors:**
- 👤 **Juror #1** - Evidence Purist
- 👤 **Juror #2** - Sympathetic Doubter
- 👤 **Juror #3** - Moral Absolutist
- 👤 **Juror #4-7** - Thoughtful observers
- 👥 **You** - Human juror(s)

### Enhanced Message Flow

**Stage Progression:**
```
Option A: Auto-Advance (Immersive)
- Stages advance automatically with 10s pauses
- Users can type /pause to stop auto-advance
- Users can type /continue to skip wait

Option B: Manual Control (Current)
- Users type /continue for each stage
- Full control over pacing

Option C: Hybrid (Recommended)
- Auto-advance through trial stages (8 stages)
- Manual control for deliberation
- Auto-advance for reveal sequence
```

### Multi-User Support

**Scenario: 5 people in group chat**

**During Trial:**
- All users watch together
- Anyone can type /continue
- Shared experience

**During Deliberation:**
- All users can share statements
- AI jurors respond to each statement
- Discussion becomes multi-way

**During Voting:**
- Each user votes individually
- Votes aggregated (e.g., 5 humans + 7 AI = 12 total)
- Majority determines verdict

**Reveal:**
- Shows breakdown of all votes
- Each human gets individual reasoning assessment
- Shared truth reveal

### Enhanced Deliberation

**Current Flow:**
```
User: I think the evidence is weak
AI Juror 1: Response
AI Juror 2: Response
AI Juror 3: Response
```

**Enhanced Flow:**
```
User A: I think the evidence is weak

AI Juror 1 (Evidence Purist): "Which evidence specifically? 
The fingerprints are concrete proof."

User B: But the timeline doesn't add up

AI Juror 2 (Sympathetic Doubter): "Exactly! The prosecution 
hasn't proven opportunity beyond doubt."

AI Juror 3 (Moral Absolutist): "A man is dead. We cannot 
let technicalities obscure justice."

User A: @Juror1 The fingerprints could have been planted

AI Juror 1: "Planted? Show me evidence of that. We must 
stick to facts, not speculation."

[Natural conversation flow]
```

### Story Influence Mechanics

**User Actions That Influence Story:**

1. **Deliberation Focus**
   - Users emphasize certain evidence → AI jurors explore that angle
   - Users raise doubts → Defence arguments get stronger in closing
   - Users cite facts → Prosecution reinforces those points

2. **Question Asking**
   - Users ask about evidence → Fact checker provides clarification
   - Users ask about law → Judge provides guidance
   - Users ask about procedure → Clerk responds

3. **Voting Patterns**
   - Unanimous guilty → Truth reveal emphasizes evidence strength
   - Split decision → Truth reveal explores nuance
   - Unanimous not guilty → Truth reveal highlights reasonable doubt

4. **Engagement Level**
   - High engagement → More AI juror responses
   - Low engagement → Lightweight jurors prompt discussion
   - Questions → Agents provide more detail

---

## 🔧 Implementation Refinements

### 1. Character System

**Add to `src/luffa_bot_service.py`:**

```python
class CharacterProfile:
    """Character profile for trial agents."""
    
    CHARACTERS = {
        "judge": {
            "name": "The Honourable Justice Pemberton",
            "emoji": "👨‍⚖️",
            "title": "Presiding Judge"
        },
        "prosecution": {
            "name": "Sir Edmund Hartley, KC",
            "emoji": "⚖️",
            "title": "Crown Prosecution"
        },
        "defence": {
            "name": "Ms. Catherine Blackwood",
            "emoji": "🛡️",
            "title": "Defence Counsel"
        },
        "clerk": {
            "name": "Mr. Thomas Wright",
            "emoji": "📋",
            "title": "Clerk of the Court"
        },
        "fact_checker": {
            "name": "Dr. Sarah Mitchell",
            "emoji": "🔍",
            "title": "Court Expert"
        }
    }
    
    @classmethod
    def format_message(cls, role: str, content: str) -> str:
        """Format message with character identity."""
        char = cls.CHARACTERS.get(role, {})
        emoji = char.get("emoji", "🎭")
        name = char.get("name", role.title())
        title = char.get("title", "")
        
        return f"{emoji} **{name}**\n_{title}_\n\n\"{content}\""
```

### 2. Auto-Advance System

**Add configuration:**
```python
class TrialPacing:
    """Control trial pacing."""
    
    AUTO_ADVANCE = True  # Auto-advance through trial stages
    STAGE_DELAY = 10  # Seconds between stages
    AGENT_DELAY = 3   # Seconds between agent responses
    JUROR_DELAY = 2   # Seconds between juror responses
    REVEAL_DELAY = 5  # Seconds between reveal parts
```

**Add to service:**
```python
async def auto_advance_trial(self, group_id: str):
    """Auto-advance through trial stages with pauses."""
    orchestrator = self.active_sessions.get(group_id)
    
    while orchestrator.state_machine.get_next_state():
        # Check if paused
        if self.is_paused(group_id):
            break
        
        # Advance stage
        await self.continue_trial(group_id)
        
        # Wait before next stage
        await asyncio.sleep(self.STAGE_DELAY)
```

### 3. Multi-User Voting

**Track multiple human jurors:**
```python
class GroupSession:
    """Session for a group with multiple users."""
    
    def __init__(self, group_id: str):
        self.group_id = group_id
        self.orchestrator = None
        self.human_jurors = {}  # uid -> vote
        self.votes_collected = False
    
    def add_vote(self, user_uid: str, vote: str):
        """Add vote from a human juror."""
        self.human_jurors[user_uid] = vote
    
    def get_majority_vote(self) -> str:
        """Get majority vote from human jurors."""
        if not self.human_jurors:
            return "not_guilty"  # Default
        
        guilty = sum(1 for v in self.human_jurors.values() if v == "guilty")
        return "guilty" if guilty > len(self.human_jurors) / 2 else "not_guilty"
```

### 4. Natural Language Understanding

**Add intent detection:**
```python
class UserIntent:
    """Detect user intent from natural language."""
    
    @staticmethod
    def detect_intent(text: str) -> str:
        """Detect what user wants to do."""
        text_lower = text.lower()
        
        # Questions
        if any(q in text_lower for q in ["?", "what", "why", "how", "when"]):
            return "question"
        
        # Voting intent
        if any(v in text_lower for v in ["guilty", "not guilty", "innocent", "vote"]):
            return "vote_intent"
        
        # Evidence reference
        if any(e in text_lower for e in ["evidence", "proof", "fingerprint", "witness"]):
            return "evidence_discussion"
        
        # Procedural
        if any(p in text_lower for p in ["continue", "next", "proceed", "skip"]):
            return "advance"
        
        return "deliberation"
```

### 5. Dynamic Story Adaptation

**Track deliberation themes:**
```python
class DeliberationAnalyzer:
    """Analyze deliberation to adapt story."""
    
    def __init__(self):
        self.themes = {
            "evidence_focus": 0,
            "doubt_emphasis": 0,
            "moral_focus": 0,
            "procedural_focus": 0
        }
    
    def analyze_statement(self, statement: str):
        """Analyze statement and update themes."""
        text_lower = statement.lower()
        
        if any(e in text_lower for e in ["evidence", "proof", "fact"]):
            self.themes["evidence_focus"] += 1
        
        if any(d in text_lower for d in ["doubt", "uncertain", "maybe"]):
            self.themes["doubt_emphasis"] += 1
        
        if any(m in text_lower for m in ["justice", "right", "wrong"]):
            self.themes["moral_focus"] += 1
    
    def get_dominant_theme(self) -> str:
        """Get the dominant discussion theme."""
        return max(self.themes, key=self.themes.get)
    
    def adapt_reveal(self, dual_reveal: dict) -> dict:
        """Adapt reveal based on deliberation themes."""
        theme = self.get_dominant_theme()
        
        # Customize feedback based on theme
        if theme == "evidence_focus":
            dual_reveal["reasoningAssessment"]["feedback"] += "\n\nYour evidence-focused approach shows strong analytical thinking."
        elif theme == "doubt_emphasis":
            dual_reveal["reasoningAssessment"]["feedback"] += "\n\nYou correctly applied the reasonable doubt standard."
        
        return dual_reveal
```

---

## 🎮 Enhanced User Experience

### Immersive Elements

**1. Character Voices**
- Each agent has distinct speaking style
- Prosecution: Assertive, evidence-focused
- Defence: Questioning, doubt-creating
- Judge: Formal, balanced
- Jurors: Conversational, varied

**2. Dramatic Timing**
- Pauses between messages (feels natural)
- Longer pauses for dramatic moments
- Quick responses for back-and-forth
- Reveal sequence paced for impact

**3. Visual Formatting**
- **Bold** for character names
- _Italics_ for titles/stage names
- Emojis for visual cues
- Line breaks for readability
- Quotes for dialogue

**4. Interactive Elements**
- Buttons for voting (hidden from others)
- Quick replies for common actions
- Evidence board as formatted list
- Progress indicators

### User Control

**Commands:**
- `/start` - Begin (anyone can start)
- `/continue` - Next stage (anyone can advance)
- `/pause` - Pause auto-advance
- `/resume` - Resume auto-advance
- `/vote <choice>` - Cast vote (individual)
- `/evidence` - View evidence (anytime)
- `/status` - Check progress
- `/help` - Show commands

**Natural Language:**
- Questions → Agents respond
- Statements → Jurors engage
- Evidence mentions → Highlighted in discussion
- Voting language → Detected and processed

---

## 🔄 Refined Flow

### Phase 1: Trial (Auto-Advance)

```
User: /start

Bot: 🎭 VERITAS COURTROOM EXPERIENCE
     Welcome to the trial of The Crown v. Marcus Ashford
     
     [10s pause]

Bot: 📋 Mr. Thomas Wright
     Clerk of the Court
     
     "The court is now in session. All rise for the Honourable Justice Pemberton."
     
     [5s pause]

Bot: 👨‍⚖️ The Honourable Justice Pemberton
     Presiding Judge
     
     "Please be seated. We shall now hear the charges."
     
     [3s pause]

Bot: 📋 Mr. Thomas Wright
     
     "Marcus Ashford, you are charged with murder contrary to common law..."
     
     [Auto-advances through 8 stages with pauses]
     [Users can type /pause to stop, /continue to skip wait]
```

### Phase 2: Deliberation (Interactive)

```
Bot: ⚖️ JURY DELIBERATION BEGINS
     
     You are now in the jury chamber. Discuss the case with your fellow jurors.
     Share your thoughts, ask questions, reference evidence.
     
     Type /evidence to view the evidence board.
     Type /vote when ready to cast your verdict.

User A: The fingerprint evidence seems strong

Bot: 👤 Juror #1 (Evidence Purist)
     "Indeed. Physical evidence doesn't lie. But we must examine the timeline..."

User B: What about the witness testimony?

Bot: 👤 Juror #2 (Sympathetic Doubter)
     "Good question. The witness changed their story twice. That creates doubt."

User A: @Juror1 But couldn't the fingerprints have been planted?

Bot: 👤 Juror #1
     "Planted? That's speculation. Show me evidence of planting. We must stick to facts."

User C: I think we need to consider the motive more carefully

Bot: 👤 Juror #3 (Moral Absolutist)
     "The motive is clear - financial desperation. A man is dead. Justice demands accountability."

Bot: 👤 Juror #5
     "I'm torn. Both sides make valid points."

[Natural conversation continues]
[After 4-6 minutes or when users are ready]

Bot: ⏰ It's time to vote. Each juror, please cast your verdict.
     Type: /vote guilty OR /vote not_guilty
```

### Phase 3: Voting (Individual)

```
User A: /vote not_guilty
Bot: ✓ Vote recorded (hidden from others)

User B: /vote guilty
Bot: ✓ Vote recorded (hidden from others)

User C: /vote not_guilty
Bot: ✓ Vote recorded (hidden from others)

[After all humans vote or timeout]

Bot: 🗳️ Collecting votes from AI jurors...
     [3s pause]
```

### Phase 4: Dual Reveal (Dramatic)

```
Bot: ⚖️ THE VERDICT
     
     The jury has reached a decision...
     [5s pause]
     
     The jury finds the defendant: NOT GUILTY
     
     Vote Breakdown:
     • 5 Not Guilty (3 humans, 2 AI)
     • 7 Guilty (5 AI)
     
     [8s pause]

Bot: 🔍 THE TRUTH
     
     But what really happened?
     [5s pause]
     
     The actual verdict should have been: GUILTY
     
     Marcus Ashford did murder Lord Blackthorn. Here's what the jury missed:
     [Detailed explanation]
     
     [8s pause]

Bot: 📊 REASONING ASSESSMENT
     
     User A: Evidence-Based Reasoning (0.85/1.0)
     "Strong analytical thinking, good evidence focus..."
     
     User B: Moral Reasoning (0.70/1.0)
     "Focused on justice, but missed key evidence..."
     
     User C: Speculative Reasoning (0.60/1.0)
     "Too much focus on alternative theories..."
     
     [8s pause]

Bot: 🎭 THE JURY REVEALED
     
     Who were your fellow jurors?
     
     👤 Juror #1: Evidence Purist - Voted Guilty
     "The fingerprints were conclusive..."
     
     👤 Juror #2: Sympathetic Doubter - Voted Not Guilty
     "I couldn't be certain beyond doubt..."
     
     [Full reveal]
     
     [5s pause]

Bot: ✅ TRIAL COMPLETE
     
     Thank you for your service. The courtroom is adjourned.
     
     Type /start to experience another case.
```

---

## 🎯 Key Improvements

### 1. Character Depth
- Named characters (not just roles)
- Distinct personalities
- Consistent voices
- Memorable interactions

### 2. Natural Pacing
- Auto-advance option
- Strategic pauses
- Skip-able waits
- User control maintained

### 3. Multi-User Experience
- Multiple humans can participate
- Individual votes tracked
- Personalized assessments
- Shared reveal

### 4. Conversational Flow
- Natural language understanding
- Context-aware responses
- Multi-way discussions
- @mentions supported

### 5. Story Adaptation
- Deliberation themes tracked
- Reveal customized to discussion
- Agent responses adapt
- Dynamic feedback

---

## 📊 Technical Implementation

### Enhanced Bot Service Structure

```python
class EnhancedLuffaBotService:
    """Enhanced bot service with refined features."""
    
    def __init__(self):
        self.client = LuffaBotAPIClient(config)
        self.sessions = {}  # group_id -> GroupSession
        self.character_profiles = CharacterProfile()
        self.pacing_config = TrialPacing()
        self.intent_detector = UserIntent()
        self.deliberation_analyzer = DeliberationAnalyzer()
    
    async def handle_message(self, msg):
        """Enhanced message handling."""
        # Detect intent
        intent = self.intent_detector.detect_intent(msg["text"])
        
        if intent == "question":
            await self.handle_question(msg)
        elif intent == "vote_intent":
            await self.handle_vote_intent(msg)
        elif intent == "advance":
            await self.continue_trial(msg["uid"])
        else:
            await self.handle_deliberation(msg)
    
    async def post_as_character(self, group_id: str, role: str, content: str):
        """Post message as a character."""
        formatted = self.character_profiles.format_message(role, content)
        await self.client.send_group_message(group_id, formatted)
        
        # Pace messages
        await asyncio.sleep(self.pacing_config.AGENT_DELAY)
```

### Multi-User Session Management

```python
class GroupSession:
    """Enhanced session for multi-user groups."""
    
    def __init__(self, group_id: str, orchestrator: ExperienceOrchestrator):
        self.group_id = group_id
        self.orchestrator = orchestrator
        self.human_jurors = {}  # uid -> {vote, statements, assessment}
        self.auto_advance = True
        self.paused = False
        self.deliberation_analyzer = DeliberationAnalyzer()
    
    def add_human_juror(self, uid: str):
        """Register a human juror."""
        if uid not in self.human_jurors:
            self.human_jurors[uid] = {
                "vote": None,
                "statements": [],
                "assessment": None
            }
    
    def record_statement(self, uid: str, statement: str):
        """Record user statement."""
        self.add_human_juror(uid)
        self.human_jurors[uid]["statements"].append(statement)
        self.deliberation_analyzer.analyze_statement(statement)
    
    def record_vote(self, uid: str, vote: str):
        """Record user vote."""
        self.add_human_juror(uid)
        self.human_jurors[uid]["vote"] = vote
    
    def all_voted(self) -> bool:
        """Check if all active users have voted."""
        return all(
            juror["vote"] is not None 
            for juror in self.human_jurors.values()
        )
    
    def get_aggregated_vote(self) -> str:
        """Get majority vote from human jurors."""
        if not self.human_jurors:
            return "not_guilty"
        
        votes = [j["vote"] for j in self.human_jurors.values() if j["vote"]]
        guilty_count = sum(1 for v in votes if v == "guilty")
        
        return "guilty" if guilty_count > len(votes) / 2 else "not_guilty"
```

### Adaptive AI Responses

```python
async def generate_adaptive_response(
    self,
    juror: JurorPersona,
    context: str,
    deliberation_theme: str
) -> str:
    """Generate AI response adapted to deliberation theme."""
    
    # Enhance prompt based on theme
    theme_guidance = {
        "evidence_focus": "Focus on concrete evidence in your response.",
        "doubt_emphasis": "Acknowledge the reasonable doubt concerns.",
        "moral_focus": "Consider the moral and justice aspects."
    }
    
    enhanced_prompt = f"""{context}

{theme_guidance.get(deliberation_theme, '')}

Respond as part of the deliberation."""
    
    return await self.llm_service.generate_response(
        system_prompt=juror.system_prompt,
        user_prompt=enhanced_prompt,
        max_tokens=200
    )
```

---

## 🎨 Message Formatting

### Character Messages
```
👨‍⚖️ **The Honourable Justice Pemberton**
_Presiding Judge_

"Members of the jury, you must consider the evidence carefully and apply the law without prejudice."
```

### Stage Announcements
```
📢 **EVIDENCE PRESENTATION**

The court will now hear the evidence. Pay close attention to each item presented.
```

### Juror Responses
```
👤 **Juror #1** _(Evidence Purist)_

"I need to see concrete proof. The fingerprints are compelling, but what about the timeline?"
```

### System Messages
```
⏰ **DELIBERATION TIME REMAINING: 2 minutes**

Continue your discussion or type /vote to cast your verdict.
```

---

## 🚀 Implementation Priority

### Phase 1: Core Refinements (Do First)
1. ✅ Character profiles with names
2. ✅ Enhanced message formatting
3. ✅ Multi-user vote tracking
4. ✅ Natural language intent detection
5. ✅ Deliberation theme analysis

### Phase 2: Experience Polish
1. ⏸️ Auto-advance system
2. ⏸️ Adaptive AI responses
3. ⏸️ Dynamic reveal customization
4. ⏸️ Question handling
5. ⏸️ @mention support

### Phase 3: Advanced Features
1. ⏸️ Multiple case selection
2. ⏸️ Custom case creation
3. ⏸️ Statistics tracking
4. ⏸️ Replay system
5. ⏸️ Achievement system

---

## 📋 Next Steps

### Immediate Actions:
1. **Refine bot service** with character system
2. **Add multi-user support** for voting
3. **Enhance message formatting** for immersion
4. **Test with real bot** in Luffa group
5. **Iterate based on feedback**

### Testing Plan:
1. Test with 1 user (basic flow)
2. Test with 3 users (multi-user)
3. Test with 5+ users (scalability)
4. Test edge cases (disconnects, errors)
5. Test full experience end-to-end

---

## 💡 Key Insights

### What Makes This Special:

1. **Group Chat Native**: Everything happens in Luffa, no external apps
2. **AI as Characters**: Not just responses, but embodied personalities
3. **Social Experience**: Multiple users participate together
4. **User Agency**: Your input genuinely influences the story
5. **Educational**: Learn while being entertained
6. **Replayable**: Different discussions lead to different experiences

### Critical Success Factors:

1. **Pacing**: Must feel natural, not rushed or slow
2. **Character**: Agents must feel like real people
3. **Engagement**: Users must feel their input matters
4. **Clarity**: Users must understand what to do
5. **Polish**: Professional, bug-free experience

---

## 🎬 Conclusion

The foundation is solid. Now we need to refine:
- Character presentation
- Multi-user support
- Natural pacing
- Adaptive responses
- Immersive formatting

This will transform a functional bot into a truly immersive group chat experience.

---

**Ready to refine?** Let's implement these improvements! 🎭⚖️
