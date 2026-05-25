# Storage Decisions

Storage is the hardest decision to reverse. Get it wrong and you carry the cost for years. Adding a new API endpoint is hours. Migrating 50M rows to a different storage engine is a multi-week project with downtime risk.

---

## The Storage Decision Tree

Start with query patterns and consistency requirements. Don't start with technology preferences.

| Storage Type | Choose When | Do Not Choose When |
|---|---|---|
| Relational (Postgres, MySQL) | ACID required, joins needed, schema is stable, writes and reads are balanced | Write throughput exceeds ~50k/s on a single node without sharding plan |
| Document (MongoDB, Firestore) | Schema varies significantly per record, document is the unit of read/write, no cross-document joins needed | You have relational data with real joins — you will reimplement SQL badly |
| Key-value (Redis, DynamoDB) | Simple lookups by known key, TTL expiry useful, latency requirements < 5ms, read-heavy | You need to query by anything other than the primary key |
| Search (Elasticsearch, Typesense) | Full-text search, faceting, ranking, fuzzy matching | You are using it as a primary data store — it is not one |
| Time-series (TimescaleDB, InfluxDB) | Append-only write pattern, aggregations over time windows, retention policies needed | Data is not time-ordered or you need to update individual records frequently |

**The actual decision process:**
1. What are your query patterns? (List them: "find by user_id", "full-text search on description", "get latest 100 events for order_id")
2. What consistency do you need per operation? (Strong vs eventual)
3. What is your write volume? (Proven, not projected)
4. How stable is your schema? (Has it changed 3 times in 6 months, or has it been stable for 2 years?)

Most systems need Postgres and Redis. Everything else is additive and carries a cost.

---

## CAP Theorem, Practically

The theory: you cannot simultaneously guarantee Consistency, Availability, and Partition Tolerance. In practice, partition tolerance is not optional in any networked system — so the real choice is between consistency and availability under network partition.

**What this means for your e-commerce system:**

| Component | Priority | Reasoning |
|---|---|---|
| Payments | CP — consistency over availability | A double charge or missed refund is a business liability. If the payment service is unavailable, the correct response is an error, not a stale result. |
| Order state machine | CP | Order status must be authoritative. "Fulfilled" and "Pending" cannot be simultaneously true in two nodes. |
| Product catalog | AP — availability over consistency | A customer seeing a price that is 30 seconds stale is acceptable. The catalog being down is not. |
| Inventory stock levels | Depends | For display purposes: AP (show approximate stock). For reservation at checkout: CP (prevent oversell). These are two different reads of the same data with different consistency requirements. |
| Session store (Redis) | AP | A user being logged out due to a consistency event is a bad UX. Stale session data for seconds is acceptable. |
| Search index | AP | Search is a read replica of source data. Eventual consistency is inherent to the pattern. |

**The practical question is not "which theorem applies."** The practical question is: "if this component returns stale data or returns an error, which is worse for the business?" That answer maps to AP vs CP.

---

## Schema Evolution Without Downtime

`ALTER TABLE ADD COLUMN NOT NULL` on a table with 10M rows and active traffic will:
1. Acquire an exclusive lock on the table
2. Rewrite every row to add the column
3. Block all reads and writes for the duration

On a busy table, this can take minutes. This is how you cause an outage during a migration.

**The four safe migration patterns:**

**1. Expand/Contract (Parallel Change)**

- Phase 1 (Expand): Add the new column as nullable. Deploy code that writes to both old and new column.
- Phase 2: Backfill old rows with the new column value in batches (small transactions, not one giant UPDATE).
- Phase 3 (Contract): Deploy code that only reads/writes the new column. Drop the old column in a separate migration.
- Use when: renaming a column, changing a column type, splitting one column into two.

**2. Shadow Writes**

- Write to both the old store and the new store simultaneously.
- Read from the old store. Compare results in background.
- When confidence is high, flip reads to the new store.
- Flip writes to new store only, stop writing to old.
- Use when: migrating to a different storage engine or table structure.

**3. Read From Both**

- Application reads from both old and new location, merges results.
- Use when: splitting a table and old data hasn't been backfilled yet.
- Temporary — clean up as soon as backfill is complete.

**4. Feature-Flagged Cut Over**

- New schema/store is live but behind a flag.
- Enable for internal users → 1% of traffic → 10% → 100%.
- Rollback is flag disable, not schema revert.
- Use when: high-risk migrations where you need an abort path at any point.

**The pattern for the spine project (Postgres):**

For any column addition: always nullable first, backfill in batches of 1,000–10,000 rows with a small sleep between batches to avoid lock contention, then add NOT NULL constraint as a separate migration after backfill is verified.

---

## Read Replicas and Their Actual Cost

A read replica is not free reads. It is eventual consistency with a lag.

**What you are buying:**
- Read throughput offloaded from the primary
- A node that can be promoted to primary in failover
- Lower latency for read-heavy analytics queries

**What you are getting in exchange:**
- Replication lag: typically milliseconds, but can be seconds under write pressure
- Read-after-write inconsistency: a user creates an order, you route the next read to a replica, the replica hasn't caught up, the user sees their order is missing

**Places where replica lag breaks your app:**

| Operation | Problem if Routed to Replica |
|---|---|
| After user registration | User logs in, replica hasn't replicated the new user row, login fails |
| After order creation | Redirect to order confirmation page, order not found |
| After payment | Payment confirmed, order status still shows "pending" |
| After inventory reservation | Stock count shows as unreserved |

**Mitigation patterns:**
- Read from primary for N seconds after a write (sticky reads)
- Read from primary when the session has modified data in this request
- Use Redis as the read surface for data that you just wrote, with a short TTL until replication catches up
- Accept the lag only for genuinely read-only workloads (reporting, search indexing, analytics)

---

## When Postgres Is Enough

Most systems at most scales need Postgres with proper indexing and a connection pool. The evidence for "Postgres can't handle this" is almost always missing.

**Before adding a second database type, prove:**

| Check | How |
|---|---|
| Query time with index | `EXPLAIN ANALYZE` the slow query. Is the index being used? Is it the right index? |
| Connection pool config | Are you exhausting connections? `pg_stat_activity`. Is PgBouncer in front? |
| N+1 query pattern | Are you running 1 query per row in a list? Fix that before adding a cache. |
| Table bloat | `pg_stat_user_tables`. Dead rows from high-UPDATE tables inflate table size and slow scans. Run VACUUM. |
| Query at scale | Does the query plan change at 10M rows vs 100k rows? Test it. |

**Actual Postgres limits (rough order of magnitude):**
- 10,000 writes/second: achievable on commodity hardware with proper indexing
- 1B rows in a table: fine with correct indexes and partitioning
- 100 concurrent connections: manageable with PgBouncer
- Sub-millisecond reads on indexed lookups: normal

The benchmark you need before adding a second database: does `EXPLAIN ANALYZE` on your slow query show a sequential scan on a large table? If yes, add an index. If the index exists and is used and the query is still slow, now you have a real problem to solve.

---

## Decision Table: Query Pattern → Storage

| Query Pattern | Consistency Need | Write Volume | Schema Stability | Storage Choice |
|---|---|---|---|---|
| Lookup by primary key, ACID writes | Strong | Moderate | Stable | Postgres |
| Full-text search with ranking | Eventual OK | Low (index updates) | Moderate | Elasticsearch / Typesense + Postgres as source of truth |
| Session data, TTL expiry | Eventual OK | High | N/A | Redis |
| Append-only events, time-window aggregations | Eventual OK | Very high | Stable | TimescaleDB or Postgres with partitioning |
| Highly variable schema per document | Eventual OK | Moderate | Unstable | Document store — but verify joins aren't needed first |
| Rate limiting, distributed counters | Eventual OK | Very high | N/A | Redis (INCR with TTL) |
| Job queue, task state | Strong | Moderate | Stable | Postgres (with advisory locks) or Redis (if Postgres queue adds latency) |

---

## Anti-Patterns

**Adding a cache before profiling the slow query.** Redis in front of an unindexed Postgres query means you now have two systems to operate and the underlying problem still exists. `EXPLAIN ANALYZE` first. Add an index. Then decide if a cache is still needed.

**Using MongoDB because "schema flexibility."** If your schema has been stable for 6 months, the flexibility argument is moot. You've traded ACID guarantees and joins for a problem you don't have. The real cost appears when you need to query across documents or enforce referential integrity.

**Separate database per microservice when the microservices share transactions.** If splitting orders from inventory requires a distributed transaction (saga pattern) to keep stock consistent, you've added enormous complexity. Shared transactions are a signal that the services are not truly independent and should either be merged or redesigned with eventual consistency explicitly accepted.

---

## Šta da pitaš AI

- "Given these query patterns: [list them with approximate frequency]. What storage type fits each? What are the consistency tradeoffs if we use Postgres for all of them?"

- "We want to add [column definition] to [table name] which has [N] million rows and [X] writes per second in production. What migration strategy avoids downtime? Write out the steps."

- "Our Postgres query takes [X]ms: [paste query]. Before we add a cache, what should we check? What does EXPLAIN ANALYZE output tell us about this query plan?"

- "We're considering a read replica for [use case]. Which of our read operations are safe to route to the replica, and which must go to primary? Walk through each endpoint."
