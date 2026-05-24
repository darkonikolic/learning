# Unit 03 — Replica lag and read-your-writes pitfalls

Tell story: payment success on primary followed by immediate stale read replica missing row.

Classify workloads tolerating eventual consistency versus those requiring staleness shields (routing critical reads back to primary, feature-level fallbacks—not hand-wavy “just use caching” defaults).
