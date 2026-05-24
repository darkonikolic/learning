# Trace thinking

**Theme:** Across distributed hops, **localized exceptions mislead**: know where forked timelines diverged.

Illustrative flow you instrument mentally:

```
 API gateway / edge
       → authentication / entitlement
           → payments domain call
               → inventory reservation async edge
                       → outbound queue ingest
                               → notifications fan-out worker
```

### Hypothesis choreography

Produce **minimum three trace-level hypotheses**, e.g.:

1. Blocking remote segment exceeding budget vs local CPU spin invisible to span parent.  

2. Propagation header loss collapsing unrelated spans falsely “single hop slow.”  

3. Downstream amplification via serial dependency chain masquerading as single fat span.

### Practice anchors

| Stack | Drill framing |
|-------|----------------|
| **Go** | Distributed **timeouts** cascading vs parent span cancellation semantics. |
| **Symfony CQRS / async** | Command acceptance vs projector lag vs transactional boundary confusion. |

### Checklist

- [ ] Sampling / head-drop risks acknowledged—not every prod trace exists magically.  
