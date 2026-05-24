# Migration ownership

**Theme:** **Enterprise-shaped change** means migrations are **plans** with deploy + validate + cleanup—not a single careless `ALTER` moment.

### Data shape example

Weak: “Apply `ALTER TABLE` in prod.”  

Strong:

```
additive / backward-compat schema choreography
    → deploy code reading both shapes or behind expand contract
        → validated traffic behaviour + metrics calm
             → compaction / deprecation cleanup with explicit sentinel checks
```

### Practice rotations

| Track | Drill idea |
|-------|-------------|
| **DB / MySQL** | Rolling compatible column/table introduction; reversible phases until cleanup lock-in. |
| **Symfony** | **CQRS migration** — projector / read model divergence bridged deliberately. |
| **Go** | **Worker-aware schema drift** — versioned payloads, drain windows, rejection surfacing. |
| **Ops** | Terraform (or IaC analogue) changes as **states with moves** plus guardrails—not surprise applies. |

### Lab deliverable trio

Deliver **migration plan** + **rollback** + **verification** before implementation PR description exceeds a sane review surface.

Distributed note: message ordering, duplicate emits, stale consumers must appear in risk—**diff alone** hides them.

### Checklist

- [ ] Cleanup phase timed only after dashboards / queue depths / dead-letter emptiness justify it.  
