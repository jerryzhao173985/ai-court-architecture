# VERITAS Bot Interaction Flow

## Group Chat Experience

### Participants in Group Chat

```
👥 Group: "VERITAS Courtroom"

Bots:
  📋 Clerk Bot (ORQAZCejHdZELLD)
  👔 Prosecution Bot (MZIXVYXwSwRx6Vd)
  🛡️ Defence Bot (NGKIEJGGRlKKnAqC)
  🔍 Fact Checker Bot (GKUPDBfLv23WktAS)
  ⚖️ Judge Bot (YNLJHNCCsRmLBcvU)


Humans:
  👤 You (Juror #8)
  👤 Other users (optional)
```

## Trial Flow Visualization

### Stage 1: Hook Scene

```
[Clerk Bot]: 🎭 THE TRIAL BEGINS

The year is 1923. Blackthorn Hall, a sprawling Victorian estate
in the Cotswolds, stands silent under a grey November sky...

[Continue Button]
```

### Stage 2-3: Opening Statements

```
[Clerk Bot]: 📢 PROSECUTION OPENING STATEMENT

[Prosecution Bot]: 👔 PROSECUTION

Ladies and gentlemen of the jury, this is a case about greed
and betrayal. Marcus Ashford, the trusted estate manager of
Blackthorn Hall, poisoned his employer, Lord Edmund Blackthorn...

[Continue Button]

---

[Clerk Bot]: 📢 DEFENCE OPENING STATEMENT

[Defence Bot]: 🛡️ DEFENCE

Members of the jury, the prosecution will ask you to fill gaps
with assumptions. They will present a theory built on speculation,
not proof. Where are the fingerprints? Where is the direct evidence?

[Continue Button]
```

### Stage 4: Evidence Presentation (With Fact Checking)

```
[Clerk Bot]: 📢 EVIDENCE PRESENTATION

[Prosecution Bot]: 👔 PROSECUTION

I present the forged will, found in the defendant's possession,
showing a £500,000 bequest to Marcus Ashford...

[Fact Checker Bot]: 🔍 FACT CHECKER

Correction: The will was found in the study desk drawer, not in
the defendant's possession. The evidence shows it was discovered
by the housekeeper during routine cleaning.

[Defence Bot]: 🛡️ DEFENCE

Note the security log: my client's vehicle left the estate at
8:20 PM. Lord Blackthorn was last seen alive at 7:48 PM. That's
only 32 minutes...

[Continue Button]
```

### Stage 5: Cross-Examination

```
[Clerk Bot]: 📢 CROSS-EXAMINATION

[Prosecution Bot]: 👔 PROSECUTION

The defence emphasizes the tight timeline, but 32 minutes is
more than enough time to administer poison. The defendant had
access to the medicine cabinet...

[Defence Bot]: 🛡️ DEFENCE

Can the housekeeper really be certain about exact times? She
testified she "thinks" it was around 7:48. That's not certainty
beyond reasonable doubt...

[Continue Button]
```

### Stage 6-7: Closing Statements

```
[Clerk Bot]: 📢 PROSECUTION CLOSING STATEMENT

[Prosecution Bot]: 👔 PROSECUTION

Members of the jury, when you have motive, means, opportunity,
and presence at the scene, that's not coincidence — that's guilt
beyond reasonable doubt...

[Continue Button]

---

[Defence Bot]: 🛡️ DEFENCE

Are you sure? Are you certain beyond reasonable doubt? If there's
any doubt — and there should be — you must find my client not guilty...

[Continue Button]
```

### Stage 8: Judge Summing Up

```
[Clerk Bot]: 📢 JUDGE SUMMING UP

[Judge Bot]: ⚖️ JUDGE

Members of the jury, you have heard the evidence from both sides.
The burden of proof rests entirely with the prosecution. They must
prove guilt beyond reasonable doubt...

[Continue Button]
```

### Stage 9: Jury Deliberation

```
[Clerk Bot]: ⚖️ JURY DELIBERATION

You are now deliberating with 7 AI jurors. Share your thoughts
on the evidence and the case.

[View Evidence Button] [Ready to Vote Button]

---

[You]: I think the timeline is suspicious. 32 minutes is very tight.

[Clerk Bot]: 👤 AI Juror (Evidence Purist):
I agree. The security log is hard evidence. We can't ignore that
the defendant left at 8:20 PM.

[Clerk Bot]: 👤 AI Juror (Sympathetic Doubter):
But what about the motive? The forged will shows clear intent.
Can we really believe this was coincidence?

[Clerk Bot]: 👤 AI Juror (Moral Absolutist):
A man is dead. Someone must be held accountable. The defendant
had the means and opportunity.

[You]: But there are no fingerprints. No physical evidence.

[Clerk Bot]: 👤 AI Juror:
The absence of fingerprints suggests premeditation, not innocence.
Gloves could explain this.

[You]: /vote not_guilty
```

### Stage 10-12: Voting and Dual Reveal

```
[Clerk Bot]: 🗳️ Collecting votes from all jurors...

---

[Clerk Bot]: ⚖️ THE VERDICT

The jury finds the defendant: NOT GUILTY

📊 Vote: 5 not guilty, 3 guilty

---

[Judge Bot]: 🔍 THE TRUTH

Actual verdict: GUILTY

The defendant did poison Lord Ashford. The security log was
tampered with. The defendant actually left at 9:15 PM, giving
him 87 minutes, not 32...

---

[Clerk Bot]: 📊 REASONING ASSESSMENT

Category: Sound Incorrect

Evidence Score: 0.85/1.0
Coherence Score: 0.90/1.0

You used strong reasoning and cited relevant evidence (security
log, missing fingerprints, timeline analysis). Your logic was
coherent and you avoided fallacies. However, you reached the
wrong conclusion because you trusted the tampered security log...

---

[Clerk Bot]: 🎭 AI JUROR IDENTITIES

• juror_1: Evidence Purist - Voted Not Guilty
• juror_2: Sympathetic Doubter - Voted Not Guilty  
• juror_3: Moral Absolutist - Voted Guilty
• juror_4: Lightweight AI - Voted Not Guilty
• juror_5: Lightweight AI - Voted Not Guilty
• juror_6: Lightweight AI - Voted Guilty
• juror_7: Lightweight AI - Voted Guilty

---

[Clerk Bot]: ✅ Trial complete! Thank you for participating.

[Start New Trial Button]
```

## Bot Behavior Patterns

### Clerk Bot (Orchestrator)
- Announces all stage transitions
- Handles all commands
- Provides procedural guidance
- Coordinates other bots
- Manages voting and reveal

### Prosecution Bot
- Argues for guilty verdict
- Presents incriminating evidence
- Challenges defence arguments
- Emphasizes motive, means, opportunity
- Confident, methodical tone

### Defence Bot
- Creates reasonable doubt
- Highlights missing evidence
- Challenges timeline and witnesses
- Emphasizes burden of proof
- Skeptical, questioning tone

### Fact Checker Bot
- Monitors for contradictions
- Intervenes briefly and precisely
- Cites specific evidence
- Neutral, factual tone
- Max 3 interventions per trial

### Judge Bot
- Provides legal instructions
- Summarizes evidence fairly
- Explains reasonable doubt
- Reveals ground truth
- Authoritative, impartial tone

## Message Timing

- Stage announcements: Immediate
- Agent responses: 2-3 seconds (LLM generation)
- Between messages: 1-2 second pause (readability)
- Fact checker: 10 seconds max
- AI juror responses: 15 seconds max

## Interactive Elements

### Buttons

**Continue Button:**
```json
{
  "name": "Continue",
  "selector": "/continue",
  "isHidden": "0"
}
```

**Vote Buttons (Hidden from others):**
```json
{
  "name": "Vote Guilty",
  "selector": "/vote guilty",
  "isHidden": "1"
}
```

**Evidence Button:**
```json
{
  "name": "View Evidence",
  "selector": "/evidence",
  "isHidden": "0"
}
```

## Multi-User Scenarios

### Scenario 1: Sequential Trials

```
[User A]: /start
[Clerk Bot]: Welcome User A!
[User A]: /continue
[Prosecution Bot]: [For User A] ...
[User A]: /vote guilty

[User B]: /start
[Clerk Bot]: Welcome User B!
[User B]: /continue
[Prosecution Bot]: [For User B] ...
```

### Scenario 2: Concurrent Trials

```
[User A]: /start
[Clerk Bot]: Welcome User A!

[User B]: /start
[Clerk Bot]: Welcome User B!

[User A]: /continue
[Prosecution Bot]: [For User A] ...

[User B]: /continue
[Prosecution Bot]: [For User B] ...
```

Each user has independent progress.

## Summary

Your VERITAS multi-bot system creates a **realistic, immersive courtroom experience** in Luffa group chat with:

- 5 distinct AI participants (bots)
- Realistic courtroom dialogue
- Interactive commands and buttons
- Multi-user support
- Fact checking with interventions
- Comprehensive reasoning assessment
- Dual reveal sequence

**Status**: ✅ Fully implemented and ready to deploy

**Action**: Add bots to group and run `./run_multi_bot.sh`
