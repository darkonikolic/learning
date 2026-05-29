---
name: map-to-known
description: Teach a new concept by mapping it to the experienced learner's existing knowledge instead of explaining from zero. Use when the learner already knows an adjacent stack/language and is learning a new one.
---

# Map to known

## Input

- **New concept** + **learner's existing expertise** — ask in-session; do not store or persist it.

## Output

A mapping table, then only the *delta* — what's genuinely different.

```
| New (target)            | ≈ Known (your background) | Difference that matters |
|-------------------------|---------------------------|-------------------------|
| Go service              | Symfony service           | manual DI, no container |
| Go interface (implicit) | PHP interface (explicit)  | no `implements` keyword |
```

## Rules

- Don't re-teach shared fundamentals; assume the transferable knowledge.
- Be explicit where the analogy **breaks** — that's where mistakes happen.
- If you don't know the learner's background, ask in-session; don't assume beginner and don't persist the answer.
