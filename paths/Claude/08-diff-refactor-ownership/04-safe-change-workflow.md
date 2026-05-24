# Safe change workflow

**Theme:** You are reshaping **the system**, not scribbling detached code. Behavioural truth lives in rollout evidence.

```
frozen spec excerpt + SUCCESS for this slice
    → impact map (consumers / data / infra)
        → migration choreography selected
             → guarded deploy posture
                  → layered validation ladders
                       → articulated rollback doorway
```

### Practice rotations

| Stack | Scenario seed |
|-------|----------------|
| **Go** | Distributed **retry / backoff / idempotency** policy shift — quantify thundering herds + duplicate completions. |
| **Symfony** | **Payment aggregate** invariant adjustment — concurrency + saga / process manager edges explored. |

### Lab invariant

**Every behavioural change carries an explicit rollback story**—even when rollback is flag flip + redeploy—not “figure it out if red”.

Impact section names **latency**, **ordering**, **consistency**, **capacity** regressions hypothesised—not only compile-time edits.

### Checklist

- [ ] Blast radius enumerated for **integrations you do not control** — webhooks, partner web clients, cron overlap.  
