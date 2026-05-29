---
name: create-drills
description: Generate a graded set of practice exercises with solutions for a topic. Use when the user wants exercises, drills, practice problems, or a quiz.
---

# Create drills

## Output

- **10 tasks** by default, escalating: recall → apply → combine → debug → design.
- **Solutions** for every task (separate section so the learner can try first).

## Format

```
## Drills: <topic> (<level>)
1. <task>
...
10. <task>

## Solutions
1. <solution + one-line why>
...
```

## Rules

- Lead with the task; minimal setup text.
- Mix formats: predict-the-output, fix-the-bug, fill-in, build-small.
- Every task is verifiable. No task without a solution.
- Scheduling/spacing advice (if any) goes in chat, not into trace `.md`.
