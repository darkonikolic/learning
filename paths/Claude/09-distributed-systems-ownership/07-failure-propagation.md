# Failure propagation

**Theme:** Understand **fault pressure gradients** traversing tiers—silent amplification is organisational debt.

Narrative stress:

```
broker backlog growth / sluggish consumers
       → lengthening worker timeouts (retry amplification)
               → amplified DB contention or connection starvation
                         → cascading healthcheck red waves
```

### Trace propagation LAB

Practice stitching **trace / span** continuity across enqueue boundaries (propagation headers vs embedded correlation identifiers in messages).

Elevate causal narrative: dashboards tie queue age → DB pool waits → PSP latency spikes—not isolated blips.

### Idempotency ownership echo

Amplified retries **multiply** duplication risk—revisit keys at every amplification hop.

### Checklist

- [ ] Blast radius diagrams updated when new fan-out pathways appear (bulk fan-in jobs, analytic exports).  
