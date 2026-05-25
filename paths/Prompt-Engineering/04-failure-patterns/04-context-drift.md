# Context Drift

## Detection signals

- Turn 3 output contradicts a constraint that turn 1 output correctly followed
- The model produces something it already produced and you already rejected
- A decision you made three turns ago is reversed without you changing the prompt
- The model's behavior gradually shifts across a session without any prompt change
- You re-read your earlier prompt and confirm the rule is there — the model simply stopped following it

---

## Why it happens

In a multi-turn session, the model does not have perfect recall of every earlier message. After several turns, early messages are compressed into a summary representation. The constraint is still "there" in some sense, but it no longer has the weight or precision of the original statement.

The model is not ignoring you. It is working from a degraded version of what you said.

This is not a bug. It is how attention over long contexts works. The operating cost of treating every token in a long session equally is prohibitive. Early tokens get less weight.

**The constraint you stated once in turn 1 is not the constraint you have in turn 6.**

---

## Recovery

Do not repeat the constraint in the same turn where you detect the drift. That does not fix the underlying issue — it adds one more instance of the constraint to an already degraded context.

**Restart the session with a checkpoint.**

1. Stop the current session.
2. Write a checkpoint prompt that includes:
   - The current state of the work (what was built, what was decided)
   - The non-negotiable constraints stated explicitly, not by reference
   - The specific next task
3. Open a new session (new conversation in Claude Code; new composer in Cursor) and start from the checkpoint.

```
# Checkpoint prompt structure

## Current state
- GET /tasks endpoint exists in internal/api/task_handler.go
- Task model defined in internal/task/model.go
- No external packages imported; all stdlib

## Non-negotiable constraints
- Must use stdlib only — no external packages
- Must not modify internal/api/task_handler.go
- All new code goes in internal/task/query.go

## Next task
Add substring search: a function ListByTitle(tasks []Task, q string) []Task
that returns tasks whose Title contains q (case-insensitive).
```

This is more work than re-reading the original prompt. It is less work than debugging context drift across four more turns.

---

## Prevention

Write the most important constraint in every turn where it applies — not just the first.

The repetition feels redundant. It is not. You are not reminding yourself. You are providing the constraint at full weight in every turn's working context.

### The constraint anchor

A 2-3 line block appended to every prompt in a session:

```
---
Anchor: stdlib only | no external packages | changes in internal/task/ only
---
```

Keep it short. Keep it identical across turns. Paste it at the end of every prompt.

The anchor serves two functions:
1. It ensures the constraint appears at full weight in each turn's local context, regardless of how early turns have been compressed.
2. It makes drift visible: if the model violates a constraint that appeared in the same turn's prompt, that is a different failure (constraint failure, not context drift).

---

## Distinguishing context drift from constraint failure

| Constraint failure | Context drift |
|-------------------|--------------|
| Constraint in prompt; model ignores it | Constraint from earlier turn; model forgets it |
| Soft language or buried rule | Hard rule, correctly followed in early turns |
| Fix: harden the constraint in same session | Fix: restart with checkpoint |
| Happens on turn 1 as easily as turn 5 | Happens more as session length grows |

If you added the anchor and the model still violated a constraint stated in the same turn — that is constraint failure, not drift. Apply the constraint failure recovery.

---

## Session length heuristic

Context drift becomes likely when:
- The session is longer than ~15 substantive turns
- You are deep in a debugging loop (many small turns)
- You have introduced major new context mid-session (pasted a new file, changed the goal)

At that point, proactively write a checkpoint rather than waiting to detect drift.

---

## Checklist

- [ ] Constraint anchor appended to every prompt in sessions longer than 5 turns
- [ ] On detecting drift: session stopped, not patched inline
- [ ] Checkpoint includes current state + explicit constraints + next task
- [ ] New session started from checkpoint, not continuation of drifted session
- [ ] Anchor is identical across turns (variation introduces its own ambiguity)
- [ ] Session restart triggered proactively at 15+ turns, not just reactively
