# Unit 1 — Scope: prompt engineering — engineered instructions, not vibes

Mindset shift: prompts are **specifications for statistical programs** — structure beats cleverness.

## Learning outcomes

- **Constraint prompting**: explicit forbids (“do not mutate migrations”, “preserve public signatures”).
- **Architecture prompting**: package boundaries / bounded context bullets first.
- **Decomposition prompting**: staged micro-tasks minimizing cross-file thrash risk.
- **Specification prompting**: restate acceptance as machine-checkable where possible.
- **Retrieval prompting**: define search anchors not vague “investigate slowdown”.
- **Review prompting**: adversarial reviewer persona with checklist (security regressions diff focus).
- **Repair prompting**: post-failure deltas—what hypothesis failed vs next measurement.
- **Migration / refactor prompting**: compatibility invariants enumerated first.
- **Validation prompting**: require evidence blocks (snippet + command + expectation).
- **Anti-hallucination hygiene**: forbid invention of unseen symbols; cite or mark UNKNOWN.
- **Chain ownership**: who approves chaining multi-step autonomy vs human gates each hop.
- **Output shaping**: response format enforcing diff hunks vs narrative-only drift.
- **Context optimisation trade-offs**: iterative narrowing vs risking omitted evidence.
- **Failure prompting hooks**: escalate when contradictory instructions detected.
- **Approval / rollback meta prompts**: scripted language for cancelling unsafe partial application.

Linkage: amplifies **`03-*`** layering; dovetails **`06-*`** governance language for automatic vs manual chains.
