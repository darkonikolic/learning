# Rollback ownership

**Theme:** Shipping culture without rehearsed reversal paths is gamble — architect owns **panic dampening choreography**.

### Anti-pattern symptom train

```
deploy spike  → anomaly storm  → unbounded thrash
```

### Healthy spine

```
deploy attempt
    → validations / instrumentation eyeing regression budget
        → consciously chosen rollback doorway
             → stabilized observation window
                  → iterative forward retry only once safe
```

### Practice vignettes

| Track | Drill |
|-------|-------|
| **Symfony** | **Migration failure cascade** reversing schema drift without orphaned rows. |
| **Go** | **Worker malfunction** draining poison without burning platform trust. |
| **Ops / Terraform drift** | `plan` divergence surfacing latent conflict — scripted retreat story. |

## Lab invariant

Deployment / rollout narrative **must attach explicit rollback choreography** bullets before “LGTM culturally” settles.

### Concept tag recap

● **rollback ownership** — not last-minute improvisation alone  

### Checklist

- [ ] Rollback steps enumerate **ordering constraints** (“cannot undo B before reverting A”).  
- [ ] Data migration reversibility or compensating manoeuvres articulated honestly.  
