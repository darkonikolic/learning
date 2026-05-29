---
name: generate-interview
description: Produce interview questions with model answers and probing follow-ups for a role or topic. Use when the user wants to practice or simulate a technical, architectural, or German-language interview.
---

# Generate interview

## Input

- **Role / topic** and **level** (e.g. "mid Go backend", "B1 speaking").

## Output

```
## Q1: <question>
**Model answer:** <what a strong answer covers>
**Follow-ups:** <2–3 probes that test depth>
```

Repeat for the requested count (default 5).

## Rules

- Calibrate difficulty to the stated level and target role.
- Follow-ups must escalate — probe edge cases and "why", not trivia.
- For German interviews, write questions and answers in German.
- End with the 1–2 areas the learner should shore up.
