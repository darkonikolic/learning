# Unit 1 — Scope: specification-driven engineering (SDD mindset)

Mindset shift: **spec-first** artefacts — machine- or human-auditable — precede exploratory coding; ambiguity is surfaced early, never sidestepped with generation.

## Learning outcomes

- **Goal Specification Development / SDD hybrids**: unify goal statements → constraints → observable acceptance probes.
- **Executable specification ethos**: behaviours expressible as verifiable predicates (tests, linters, contract checks) even when not literal DSL.
- **Ownership lattice** explicit for:
  - **Acceptance** (business-visible proof).
  - **Non-functional constraints** (latency envelopes, tenancy, auditing).
  - **Definition of Done** bridging release + rollback posture.
  - **Requirement completeness** sanity (negative paths, quotas, abusive usage).
  - **Failure ownership** when spec contradictions emerge mid-build.
- **Specification hierarchy navigation**: roadmap → milestone → epic → story → invariant → task — keep mapping consistent.
- **Specification drift signals**: creeping scope, silent relaxations (“quick hack”), divergence between docs/tests/code.
- **Implementation consistency checkpoints**: refactor cannot silently orphan earlier acceptance stories.
- **Boundary ownership**: module boundaries coincide with behavioural contracts (DDD-friendly without mandating jargon).
- **Validation loops**: reviewer + tooling + exploratory manual scenario triangulation.

Linkage forward: richer context layering appears in **`03-*`**; governance gates in **`06-*`**; runtime enforcement in **`16-*`** (specification-ish checks at integration edges).
