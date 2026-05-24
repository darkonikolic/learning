# Lock ownership — optimistic vs pessimistic

**Theme:** Concurrency correctness is negotiated—**locking strategy** aligns business contention expectations with observable latency.

| Stance | When it excels | Hazard class |
|--------|-----------------|--------------|
| **Pessimistic (`FOR UPDATE`, explicit row locks)** | High conflict probability hotspots; deterministic failure surface | Deadlock amplification; long transactions holding contention |
| **Optimistic (`version`, updated_at CAS checks)** | Read-heavy intermittent collisions; shorter critical sections | Silent lost updates if application forgets predicates; UX retry loops |

LAB—**inventory decrement** style mutation:

Simulate bursts—measure conflict rate vs retry overhead both strategies.

Blend patterns deliberately: pessimistic guards on extremely narrow aggregates + optimistic bookkeeping on projections when safe.

### Checklist

- [ ] Conflict metrics instrumented—not only correctness happy path anecdotes.  
