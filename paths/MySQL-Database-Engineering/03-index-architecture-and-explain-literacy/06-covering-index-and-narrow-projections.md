# Unit 06 — Covering indexes and index-only access paths

Benchmark `SELECT customer_id, status FROM orders WHERE customer_id=?` leveraging composite aligning projection with index columns.

Contrast widened projections forcing heap/table lookups (`SELECT *`).

Interview articulate covering index payoff vs write amplification burdens.
