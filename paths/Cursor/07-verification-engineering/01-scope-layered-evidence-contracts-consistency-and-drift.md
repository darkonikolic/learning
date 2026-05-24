# Unit 1 — Scope: verification engineering — evidence beats narration

Mindset shift: model output is **untrusted until validated** via layered checks—not single glance review.

## Learning outcomes

- **Verification ownership tiers**: unit, contract, integration, smoke, exploratory.
- **Acceptance verification** tying human-visible behaviour to artefacts.
- **Specification verification**: traceability rows ↔ tests/checks.
- **Implementation verification**: diff aligns with invariant list.
- **Constraint validation hooks**: linter + policy-as-code snippets.
- **Output validation**: generated files compile, format, lint, typed if applicable.
- **Regression validation**: flaky signal triage—not ignored because “AI authored”.
- **Architecture verification**: module dependency rules / import boundaries.
- **Consistency verification**: log field stability, telemetry schema coherence.
- **Trust verification discipline**: rerun failing command after assistant claims fix.
- **Drift verification**: detect silent behaviour change lacking test update.
- **Correctness narratives**: inversion—how would we know we were silently wrong?
- **Benchmark-verified claims** where performance touted.
- **Repair ownership**: if verification fails → structured diagnostic chain (hypothesis backlog).

Amplifies **`11-*`** testing depth; dovetails **`18-*`** evaluation metrics mindset.
