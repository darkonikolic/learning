# Bottleneck thinking

**Theme:** Principals continually ask **what throttles the whole system**—human, AI, runtime, process.

### Example bottleneck classes

**Claude stack**

Slow or noisy **retrieval**  

Overloaded **single agent** doing orchestration + implementation  

**Approval** stalls without SLAs  

**Skills** mismatch causing rework loops

**Symfony / Laravel**

Oversized **aggregates / god services**  

**Boundary leaks** coupling contexts  

Doctrine vs DB reality skew (when ORM-heavy)

**Go**

Potential **goroutine / resource leaks**  

**Queue backlog** growth faster than drain  

Retry policies causing **retry storms**

**Ops**

Painful **deploy cadence** or **rollback friction** dragging MTTR  

**Incident** processes lacking sharp ownership

### LAB

For each subsystem you touch this month, enumerate **top three bottlenecks**—prioritised by blast radius × frequency × fixability.

Map each to Principal Template pillar (**DEPENDENCY**, **FAILURE**, **OBSERVABILITY**, …).

### Checklist

- [ ] At least one bottleneck per quarter earns an **explicit ADR / ticket**—not eternal backlog folklore.  
