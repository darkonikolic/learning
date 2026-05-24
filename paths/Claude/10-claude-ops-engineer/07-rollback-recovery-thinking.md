# Rollback + recovery thinking

**Theme:** A fix lacking retreat strategy is gambit engineering—architecture-grade ops demands **paired rollback + eventual recovery coherence**.

Perspective contrast:

Weak: patch merged—hope dashboards green.  

Strong:

```
 fix candidate staged
    → explicit rollback choreography (infra + migrations + queues)
         → recovery proof artefacts (Synthetic checks? Shadow traffic? Replay guards?)
```

### Practice vignettes

| Plane | Incident class |
|-------|----------------|
| **Symfony** | Migration partially applied—dual schema read windows & rollback truncation hazards. |
| **Go** | Faulty worker binary—replay / poison handling after downgrade. |
| **Terraform / IaC** | Applied graph partially realized—targeted destroy vs forward-only healing tradeoff realism. |

### LAB invariant attached to corrective change

Rollback section non-negotiable—even “feature flag revert” enumerated with dependencies (cache bust, incompatible schema assumption).

Recovery adds **confidence horizon**: backlog drain expectations, SLA re-stabilisation evidence.

### Checklist

- [ ] Irreversible deltas called out boldly (data destruction class).  
