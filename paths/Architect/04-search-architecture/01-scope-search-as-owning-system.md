# Unit 1 — Scope: search as a subsystem, not SQL hacks

> **Suggested cadence (informational):** ordering is thematic (`04-*` follows storage), not a timetable.

Treat **search** as an operational subsystem with its own failure modes—not “bigger Postgres `ILIKE`”.

## Architectural distinctions

```
Full-text retrieval vs curated filters vs hybrid workloads (facet + text)
Ranking / relevance vs deterministic ordering (explain when each dominates)
Indexing lag & eventual freshness (explicit user-visible behaviour)
Fan-out costs & abusive query shaping (timeouts, quotas, sandboxing costly paths)
Operational ownership (index rebuild windows, versioning, synonym/dictionary churn)
Synchronisation honesty (dual-write pitfalls vs ingestion pipeline / CDC / outbox-style publication—pick consciously)
```

## Practice spine

Relate **`Symfony API + Postgres` source-of-truth** to downstream **search index** with rollback story if indexer corrupts—not “silent divergence forever.”

