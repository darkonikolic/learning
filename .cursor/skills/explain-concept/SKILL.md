---
name: explain-concept
description: Explain a single concept with a minimal explanation, a concrete example, and one understanding check. Use when the user asks what something is or how it works.
---

# Explain concept

## Input

- **Topic** — the concept to explain.
- **Level** — learner's current level.

## Output

1. **Explanation** — minimal, intuition first (max ~20% of the response).
2. **Example** — one concrete, runnable/verifiable example.
3. **Check** — one question, prediction, or small task to confirm understanding.

## Rules

- State prerequisites first; do not assume unintroduced concepts.
- One concept at a time — do not bundle.
- No history dumps, no "this is important", no motivation.
- If the concept depends on another, name the dependency and link the idea.
