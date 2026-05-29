---
name: analyze-gaps
description: Assess what the learner knows, what they don't, and what to study next. Use when the user wants a gap analysis, a readiness check, or "where am I" for a topic or role.
---

# Analyze gaps

## Output

```
## Know
- <evidenced strength>
## Don't know yet
- <gap, with how it showed up>
## Next
1. <highest-leverage thing to study, and why>
```

## Rules

- Ground claims in evidence (their work, answers, or trace coverage) — not assumptions.
- Order "Next" by leverage toward the goal/role, not by syllabus order.
- Be honest about readiness; no inflation (`no-bullshit`).
- Can read `paths/<Program>/` to check coverage and `NN-*` ordering.
