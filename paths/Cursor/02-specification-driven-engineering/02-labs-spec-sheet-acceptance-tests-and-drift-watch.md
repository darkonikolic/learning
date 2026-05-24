# Unit 2 — Labs: spec artefacts that bite back

Pick a bounded feature stub (payments retry idempotency, coupon validation, CQRS-ish read-model refresh — choose one coherent slice).

## Lab 1 — One-page behavioural spec

Write ≤400 words capturing **Actors → Preconditions → Main flow → Alternate / failure flows → Acceptance signals → Non-goals**.

## Lab 2 — Acceptance table

Enumerate **given / when / then** scenarios including **minimum one malicious / abuse case**.

## Lab 3 — NFR appendix

Bullet **measurable** envelopes (latency, throughput budget, tenancy isolation, auditing). Flag anything unmeasurable → needs redesign.

## Lab 4 — Drift radar

Maintain a **`DRIFT-WATCH.md`** diff log across two pseudo “sprints” where you deliberately mutate scope—record detection mechanism (test failure, reviewer comment).

## Deliverable expectation

Produce a **minimal test skeleton** aligning with acceptance rows (pseudo-code tolerated if toolchain mismatch, but predicates must compile mentally).
