---
name: create-revision-session
description: Build a mixed revision session that interleaves past topics for spaced repetition. Use when the user wants to review, revise, or run spaced repetition over earlier material.
---

# Create revision session

## Output

- A **mixed set** of 8–12 items pulled from several earlier topics, interleaved (not grouped by topic).
- Each item has a solution / answer.
- A short note on which topics were weakest and worth another pass — in chat.

## Rules

- Interleave deliberately: jump between topics to force retrieval.
- Weight toward items the learner previously got wrong, if known.
- Verifiable answers for every item (`always-check-understanding`).
- Spacing cadence is advice in chat only — do not encode schedules into trace `.md`.
