# Unit 03 — Composite index column ordering

Contrast `(customer_id, status)` versus `(status, customer_id)` under realistic compound predicates (`customer_id=? AND status=?` vs status-only probes).

Hypothesise mismatches vs actual optimiser selections.

Interview: coupling selectivity anecdotes with cardinality awareness (preview next units).
