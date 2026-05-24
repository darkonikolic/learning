# Unit 6 — Capstone: repository integration harness (confidence over line count)

Build a thin but real integration harness that proves **`sqlx`/Postgres-backed repositories** behave with real DB semantics—not only mocks.

Recommended checks (adapt to scope):

```
UNIQUE constraint violation maps to typed domain errors (no string contains hacks)
explicit transaction rollback on forced failure smoke path
migration apply on blank DB repeatable (or documented alternative fixture strategy)
performance sanity optional micro-benchmark not mandatory core here—confidence first
```

Write a half-page rationale: **why these tests earned CI time**.
