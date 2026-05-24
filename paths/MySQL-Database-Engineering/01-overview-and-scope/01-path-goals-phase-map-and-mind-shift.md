# Path goals — moving from SQL syntax toward storage and systems impact

Goal: Stop treating MySQL usage as isolated string execution. Start reasoning about **how data is stored**, **how concurrency works**, **how plans cost resources**, **how replicas and backups behave**, and **how production constraints touch application design**.

Across this trace you practise on a **consistent ecommerce lab model** whenever a unit mentions it: users, products, categories, orders, order items, payments, addresses, reviews, coupons, inventory where relevant — only on databases and environments you fully control.

Study files are numbered for **topic order only** (not calendar scheduling unless you impose your own timetable).

Phase map (`NN-<area>/` — **worksheet counts** mirror your original phase depth; filenames `01`, `02`, … are ordering only):

| Area | Folder | Topics | Units |
|------|--------|--------|------:|
| 02 | sql-fundamentals-query-thinking | Select / join / aggregate / UNION / EXISTS / CTE / windows / NULL / modeling / integration lab | 10 |
| 03 | index-architecture-and-explain-literacy | B-tree intuition, composites, cardinality, covering indexes, anti-patterns, `EXPLAIN`, large-shape drills | 10 |
| 04 | query-optimization-deepening | Plans, filesort, temp tables, joins, rewriter mindset, `EXPLAIN ANALYZE`, N+1, large data reality | 10 |
| 05 | transactions-and-concurrency | ACID, isolation, MVCC, locks, deadlock, races, transactional scope across checkout flows | 10 |
| 06 | storage-scaling-retention-archiving | Replication, lag, partitioning vs sharding narratives, backups, PITR, archiving, capacity sketches | 10 |
| 07 | high-availability-replication-topologies | Former “phase 5.2”: sync/async, topologies, failover/split brain, mirror vs backup, quorum intuition | 6 |
| 08 | production-database-operations | Slow log, pooling, infra signals, migrations/rollback discipline, restores, troubleshooting labs | 10 |
| 09 | interview-labs-and-scenarios | Drills → multi-service rehearsal + **catalogue** worksheet `09-*` (>50 checkpoints) | 9 |
| 10 | enterprise-boundaries-typescript-ssr-and-accessibility-for-data-products | TS at service boundaries, typed row/DTO contracts, narrow unions for state columns, composition over stringly typing, SSR/hydration when SQL feeds HTML, a11y for data-dense UIs | 2 |

Completion bar (you define depth): Each phase ends when you can **explain why** typical choices behave the way they do on MySQL InnoDB workloads, using your own notebooks and artefacts — without treating interview lists as sterile memorisation.
