# Unit 4 — Liveness vs readiness endpoints (distinct Kubernetes signals)

Orchestrators distinguish:

| Probe | Typical question |
|-------|-------------------|
| **Liveness** | Should this instance be restarted? (Use carefully—false positives restart-storm outages.) |
| **Readiness** | Should traffic be routed here right now? (Often reflects dependency health.) |

## Practice (`prod-service/`)

Implement:

```
GET /health   (minimal “process alive” / cheap checks)
GET /ready    (dependency checks—DB ping, migrations gate, critical cache dependency, etc.)
```

Simulate “database unavailable” (feature flag/env toggle) and show how `/ready` should fail **while `/health` can still succeed** if that matches your reliability policy.

## Interview prompts

Why using **liveness** to detect downstream outages tends to produce restart storms instead of graceful traffic shedding.
