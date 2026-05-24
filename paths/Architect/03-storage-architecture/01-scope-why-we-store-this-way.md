# Unit 1 — Scope: storage reasoning beyond “tables exist”

> **Suggested cadence (informational):** source **Faza 3** pacing is guidance only.

Outcome shift: evolve from **`"where we store"`** toward **`"how storage semantics shape uptime, correctness, latency, ops, and economics"`**.

Vocabulary anchors (apply concretely, not buzzwords):

```
OLTP vs OLAP workloads (shape queries & tooling differently)
Indexing & selective hotspot awareness (hot partitions / skewed keys)
Replication & read replicas (staleness budgeting honestly)
Consistency models articulated per operation—not one global slogan
Sharding / partitioning motivations & cross-shard saga pain previews
Retention, archival lifecycle, backup/restore (RPO/RTO conscious)
Ownership of schemas & bounded contexts bridging modular monolith ideas
Write amplification intuition (especially LSM-heavy stores when relevant)
```

## Practice spine

Return to **`Symfony + Postgres`** reference—even if hypothetical—articulate **migration risk**, **index strategy**, **replication readiness** as architecture outcomes.
