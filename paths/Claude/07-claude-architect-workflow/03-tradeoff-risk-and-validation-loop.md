# Tradeoff, risk, and validation loop

**Theme:** Outputs are scrutinised systematically — scepticism owns the loop alongside creativity.

### Vocabulary alignment

| Term | Typical meaning |
|------|----------------|
| **Verification** | Matches frozen **architecture + spec + SUCCESS CRITERIA** structurally. |
| **Validation** | **Behaviour** and intent hold under scenarios that matter commercially. |

### Loop (with Claude drafts, you certify)

```
Spec / SUCCESS frozen for slice
    → implementation plan authorised
        → incremental build
            → automated / scripted verification
                → stakeholder-scale validation checkpoints
                    → deliberate repair iterations
```

### Distributed-system lens

Call out tradeoffs affecting **latency**, **availability**, **consistency** (e.g. MySQL replication lag, duplicated messages, skewed caches and how you invalidated or TTL’d read models).

### Practice rotations

| Stack | Scenario |
|-------|----------|
| **Symfony** | **DDD aggregate** change under invariant-heavy tests / reviews. |
| **Go** | **Queue worker** duplicate-delivery probes. |

### Lab choreography

1. Implementation slice **within explicit tradeoff+RISK preamble**  

2. **Verification checklist** replay vs frozen bullets  

3. **Repair ledger** documenting drift classes  

### Checklist

- [ ] Tradeoff section lists **≥ two** plausible architecture forks + chosen path rationale.  
