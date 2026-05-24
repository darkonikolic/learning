# Failure and rollback ownership

**Theme:** Architect-grade **failure ownership** — rehearsed reversal paths dampen organisational panic during distributed-system incidents.

### Anti-pattern symptom train

```
release thrust  →  surprise regression storm  →  unstructured thrash
```

### Healthier cadence

```
deploy / change window
    → validation & observable guardrails armed
        → articulated rollback doorway
             → rehearsed sequencing (DB / queue / runtime / config)
                  → deliberate forward replay only once stable
```

### Practice vignettes

| Track | Failure drill idea |
|-------|---------------------|
| **Symfony** | **Migration** midway failure — reversing partial schema creep safely with data truth. |
| **Go** | **Worker catastrophe** mid-batch — draining poison, protecting idempotent edges. |
| **Ops / Terraform** | Divergent `plan` — scripted retreat preserving state coherence. |

## Lab invariant

Any release / rollout plan that touches production truth includes explicit **rollback plan block** bullets **ordering-dependent** (“cannot unwind B until A”).  

Distributed note: rollback must consider **dual writes**, **replay**, and **compensating transactions** honestly.

### Concept tag recap

● **failure ownership** — reproducible timelines, causal narrative, guarding tests after learning  

● **rollback ownership** — choreography pre-agreed  

### Checklist

- [ ] Rollback honours **ordering** constraints across MySQL migrations, queues, and cache invalidation bursts.  
