# Unit 3 — Config ownership, structured logging refinement & safe feature flags

## Goals

- Keep configuration **validated at startup** (`fail fast`).
- Separate **deployment config** vs **business feature toggles**.
- Understand feature flags pitfalls: unpredictable hot-path cost, auditing, accidental inconsistent evaluation across replicas.

## Practice sketch

Extend `prod-service/` (or parallel mini service) reading:

```
required env vars
optional feature flag env/default policy explicitly documented per flag purpose
structured logs noting flag decisions only when useful (avoid spam)
```

Interview hooks: rollout strategies (percentage rollouts caveat high-level)—mesh/gateway splits optional mention without turning into vendor training.
