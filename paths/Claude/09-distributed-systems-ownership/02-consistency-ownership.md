# Consistency ownership

**Theme:** Declare **who may observe which truth state** across services, caches, replicas, and read models—not hand-wavy “eventually it matches.”

### Vocabulary rehearsal

| Intuition | Probe |
|-----------|-------|
| **Strong / linearizable (where applicable)** | Single logical order of observable writes—narrow scope only when justified. |
| **Serializable transaction island** | When one database boundary hides distribution—still revisit cross-service lies. |
| **Eventual consistency** | Converges via defined channels; divergence window bounded by **measurable** artefacts (lag, versioning). |

### Eventual consistency — ownership specifics

Naming **upstream authority**, **projection lag SLA**, conflict resolution (last-write-wins only when safe), versioning on events / rows, stale read disclaimers at API edges.

### Cross-cutting — idempotency ownership

Any eventual path multiplies retries; processors must tolerate **duplicate command/event** delivery without corrupting aggregates—carry stable natural keys forward from design spec.

### LAB — dual ownership vignettes

1. **Inventory ownership**  

   Reservations vs oversell narratives; versioning / optimistic gates; phantom reads hiding in aggregates.  

2. **Payments ownership**  

   Authorized vs settled vs disputed; authoritative ledger vs projecting notification state.

Expose **dual-write hazards** bluntly anytime two stores must reflect one business moment.

### Checklist

- [ ] Written **consumer expectations** (“read model may lag N seconds / events”—numeric or tied to SLA).  
