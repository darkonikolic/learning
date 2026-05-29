---
name: track-competency
description: Assess what the learner can demonstrably do (not just claim), based on verified tasks, within the current session. Use after the learner completes a drill/project, claims a skill, or asks "where am I". Does not store personal data.
---

# Track competency

Assesses **demonstrated** ability, not completed lessons. **Session-only** — nothing personal is written to disk.

## When a skill is claimed or a task is done

1. **Claim ≠ competency** — if only claimed, ask for a task first.
2. Judge from the evidence in this session (a passed task/drill/project artifact).

## Output to the user (in chat)

```
Can do:   ✓ <skill> — <evidence in this session>
Partial:  ~ <skill> — <what's missing>
Not yet:  ✗ <skill>
```

## Rules

- A "can do" verdict requires evidence here and now, not a past claim or memory.
- Do **not** persist competency to any file — assess in-session and discard.
- For decay/revision, ask what the learner last practiced; pair with `create-revision-session`. Keep any 7/30/90-day suggestion in chat.
- Never write schedules or competency into trace `.md` (governance).
