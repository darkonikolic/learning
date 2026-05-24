# Isolation ownership — database framing

## Phase framing — Database Enterprise Systems (“Phase 6.3”)

**Units in this folder:** `01`–`06` (topic order only).

### Themes carried through

**Transaction isolation levels** • **deadlock reasoning** • **replication topology + lag truth** • **partitioning strategies** • **optimistic vs pessimistic locking** • cross-cutting **consistency ownership**

### Workflow spine for each substantive story

```
 Query  →  Transaction scope  →  Lock stance  →  Validation  →  Recovery
```

**Checkpoint mindset:** default thinking moves from implicit “database works fine” toward explicit **ownership** of anomalies, timings, drift, and corrective narrative.

### Database slice worksheet — reuse across labs

| Column | Holds |
|--------|-------|
| **QUERY / access pattern** | Read vs write mix, hotspots, aggregates, paging. |
| **TRANSACTION** | Boundary granularity, propagation style, rollback semantics intent. |
| **LOCK** | Row/gap/metadata locks; explicit `SELECT … FOR UPDATE` vs version columns. |
| **VALIDATION** | Invariants asserted where (constraints, app guards, assertions). |
| **RECOVERY** | Deadlock retry, failover, reconcile jobs, saga compensations tying back to rows. |

Add a **consistency claim** bullet: what any reader anywhere may assume and for **how long** (especially with replicas).

### Engine reality note

Isolation behaviour is **vendor- and edition-specific**. When you practise on **MySQL / InnoDB** (recommended for this syllabus), correlate each exercise with official docs for **your installed major version**, including optional settings that change locking (e.g. gap-lock behaviour knobs). Do not memorize folklore as universal SQL law.

---

**Theme (this unit):** **Isolation ownership** — same SQL text, different anomalies allowed.

### Canonical levels (conceptual layering)

**Read committed (RC)** — no dirty reads; **non-repeatable reads** plus **phantoms** remain possible depending on engine.  

**Repeatable read (RR)** — stable read snapshot semantics in many engines—but **serialization anomalies** beyond engine docs still exist without full serializable guarantees.  

**Serializable** — strongest practical SQL isolation in many deployments; throughput cost and lock escalation patterns hinge on workload.

LAB—**MySQL ownership**: classify which anomaly classes survive per configured isolation in your sandbox; replay a **lost update** vignette guarded only by naive read-modify-write.

### Checklist

- [ ] Explicit statement of **session / connection default isolation** versus per-transaction overrides.  
