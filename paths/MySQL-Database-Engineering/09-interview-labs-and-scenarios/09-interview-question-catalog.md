# Unit 09 — Condensed interview prompt catalogue (>50 checkpoints)

Use this catalogue for orientation—not rote cramming. Expand bullets with artefacts from labs.

## SQL semantics

1. Explain `WHERE` versus `ORDER BY`.
2. `LIMIT` interplay with nondeterministic ordering risks.
3. `DISTINCT` cost intuition.
4. Inner vs outer join fallout on unmatched rows.
5. NULL-bearing columns meaning under outer joins.
6. Aggregate pitfalls (implicit grouping grain / forgotten keys).
7. `HAVING` purpose versus mis-filtering aggregates with `WHERE` alone.
8. `UNION` duplicate elimination implication.
9. `UNION ALL` when uniqueness is guaranteed upstream.
10. Correlated vs uncorrelated subquery clarity.
11. `EXISTS` vs `IN` with NULL pitfalls.
12. CTE readability vs measure-after refactor discipline.
13. Window partition grain vs collapsing aggregates (`GROUP BY`).
14. `ROW_NUMBER` vs `RANK` tie semantics.
15. Running totals via windows versus awkward self joins.
16. Three-valued logic and NULL predicates.
17. `COUNT(*)` vs `COUNT(column)` omissions.
18. Join fan-out exploding aggregates before collapsing.

## Indexing literacy

19. B-tree ordered key intuition.
20. Leftmost composite prefix rules.
21. Low-cardinality lone secondary index traps.
22. Covering index vs write-amplification converse.
23. Selectivity ties to cardinality.
24. Explain extras such as covering / filter pushdown cues (consult your engine version docs for exact wording).
25. Leading-wildcard `LIKE` and index abandonment.
26. Functions on indexed columns → range-friendly rewrites.
27. Index-only access vs widening projections.
28. Composite column order mismatch with real query predicates.
29. Stale optimizer statistics contributing to regressions (`ANALYZE TABLE` awareness).

## Optimisation narratives

30. Interpret `type` tending toward full scans.
31. Trust boundaries for estimated `rows`.
32. Filesort avoidance via aligned sort keys / indexes.
33. Temporary materialisation signals around heavy aggregates.
34. Nested-loop join mental model (engine evolution caveat).
35. Driving-table heuristics vs measurement.
36. Optimiser declining a seemingly usable index—skew and costing story.
37. Semantics-preserving rewrites lowering cost.
38. `SELECT *` widening payloads.
39. Datetime predicates as half-open ranges instead of wrapping functions.

## Through-application patterns

40. Semi-join rewrites (`IN` vs `EXISTS`) measured, not dogmatic.
41. N+1 symptom patterns across ORMs (e.g., Doctrine analogue).
42. Batch loading / join consolidation remediation.
43. Small-row-count lies versus large-shape truth.
44. Oversized transactions and contention.
45. Holding transactions across network / external APIs anti-pattern.

## Concurrency lore

46. ACID with concrete failure stories—not acronyms alone.
47. Isolation ladder phenomena you personally attempted to illustrate (honest reproducibility caveats).
48. MVCC snapshot read intuition.
49. Gap / next-key locking purpose tied to repeatable-read phantom mitigation (cite official docs layers you used).
50. Pessimistic `FOR UPDATE`.
51. Optimistic versioning collisions.
52. Deadlock cyclic acquisition remediation.
53. Lost-update races absent atomic decrement / proper isolation layering.
54. InnoDB isolation default reproducible statement—verify with `SHOW VARIABLES` on **your** instance.

## Replication, scaling, DR

55. Replication for read scale vs failover vs HA objectives—do not conflate blindly.
56. Async replication staleness impacting read-after-write expectations.
57. Replica lag alerting versus feature-level staleness shields.
58. Shard vs partition differentiator—scope of routing and cross-boundary joins complexity.
59. Sharding complication inventory (routing, resharding migrations, ops fragmentation).
60. Mirrors / replicas versus offline backups.
61. PITR story: coordinated snapshot + redo / binlog chain (follow vendor docs wording).
62. Capacity sketch including index amplification and retention deltas.

## Production operations

63. Slow log threshold producing noise paralysis.
64. Connection pool starvation distinct from purely slow SQL.
65. Correlate CPU / memory / disk / IOPS narratives with plausible DB internals.
66. Incident triage ordering under simultaneous anomalies (dashboards + saturation + replicas).
67. Retention pruning job silent failure swelling storage.
68. Verified restore rehearsals versus checkbox backups.
69. Expand/contract migration talking points anchored in literature you actually read.
70. Rollforward-only correction strategies when DDL cannot roll back cleanly.
