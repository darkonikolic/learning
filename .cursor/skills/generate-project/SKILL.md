---
name: generate-project
description: Design a realistic practice project with phases and acceptance criteria. Use when the user wants a project, capstone, or something hands-on to build.
---

# Generate project

## Output

- **Description** — what it is and why it mirrors real work.
- **Phases** — ordered, each shippable on its own.
- **Acceptance criteria** — objective, testable conditions for "done".

## Format

```
# Project: <name>
## What & why
## Phases
1. <phase> — outcome
...
## Acceptance criteria
- [ ] <objective, testable condition>
```

## Rules

- Scope to the learner's level; one new hard thing at a time.
- Mirror industry workflow, not toy problems (`real-world-focus`).
- Acceptance criteria must be checkable (a test passes, an endpoint responds, a lab box is owned).
