# Unit 03 — Aggregation and reporting primitives

Applications live on CRUD; leadership lives on aggregates.

Use `orders(amount, status, created_at)` (adapt names to your lab).

Skills: `COUNT`, `SUM`, `AVG`, `MIN`, `MAX`, `GROUP BY`, `HAVING`.

## Practices

Daily revenue rollup.

Orders per geography or segment you model.

Higher-order customer spend statistics.

Top‑N purchasers (defer window-function polish until the dedicated windows unit unless you peek ahead consciously).

## Lab

Contrast **`WHERE` (pre-aggregation filter)** with **`HAVING` (post-aggregation predicate)** — write two variant queries illustrating each.

Enumerate common pitfalls: forgetting non-aggregated projections, grouping granularity mistakes.

## Interview angles

Motivation for `HAVING` existence.

Mis-grouped aggregates and duplication inflation when joins widen grain before aggregates.
