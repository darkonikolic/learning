---
name: check-prerequisites
description: Before teaching or planning a topic, determine what must be known first and check whether the learner has it. Use when starting a new topic, building a path, or when a topic feels too advanced.
---

# Check prerequisites

## Input

- **Target topic** (e.g. Kubernetes, Go concurrency, German Konjunktiv II).
- Learner's known skills — ask in-session; nothing personal is stored.

## Output

```
To learn <topic>, you need first:
- <prereq A> — have it? ✓ / ✗ / unknown
- <prereq B> — ...
Verdict: ready | learn <missing> first
```

## Rules

- Walk the real dependency chain (e.g. K8s → Linux, TCP/IP, DNS, Docker), not just the topic's own sub-parts.
- For ✗ or unknown prerequisites, propose the shortest path to cover them before the target.
- If competency is only *claimed*, not verified, mark it unknown and suggest a check (`track-competency`).
- Don't block forever — name the minimum viable prerequisite, not an ideal full curriculum.
