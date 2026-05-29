---
name: build-study-plan
description: Sequence existing material into an ordered study plan toward a goal. Use when the user has material/topics and wants an order to work through them.
---

# Build study plan

## Input

- A goal and a set of topics or an existing `paths/<Program>/` tree.

## Output

- An **ordered sequence** of topics with dependencies noted and a deliverable per checkpoint.

## Rules

- Order by dependency, then progressive difficulty.
- Reuse existing `NN-<area>/NN-<subtopic>.md` ordering; flag gaps or illogical jumps in chat.
- **Pacing/time (days, weeks, hours) stays in chat only** — never written into trace `.md` (`plan-ucenja-ciljevi-i-rad.mdc`).
- If the plan implies new units, scaffold folders only unless bodies are requested.
