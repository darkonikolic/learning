# Integration lab — Go performance engineering

Synthetic **worker** subsystem end-to-end: throughput regression or memory creep scenario.

### Required arc

```
 worker baseline characterised
       → PROFILE (CPU + heap + goroutines)
               → Optimize minimal surgically validated deltas
                         → MEASURE / VERIFY reproducibly (bench + behavioural tests intact)
```

### Guardrails

**Forbid** silent tradeoffs: correctness regressions disguised as optimisation, or risky micro-optimisation without profile proof.

### Checkpoint mantra

Comfort shifts away from blaming “slow code” abstractly toward **measurable iteration** tethered to reproducible artefacts.
