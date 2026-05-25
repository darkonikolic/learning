# Scaling Decisions

Scale the bottleneck, not the system. Scaling everything costs 10x and fixes nothing.

---

## Bottleneck Identification First

Before scaling anything, find the constraint. Scaling a non-bottleneck wastes money and shifts the bottleneck somewhere harder to see.

**The USE Method** — apply per resource before any scaling decision:

| Metric | What it measures | Alarm signal |
|---|---|---|
| **Utilization** | % of time resource is busy | >70% sustained |
| **Saturation** | Work waiting to be processed (queue depth) | Any queue growing over time |
| **Errors** | Failed operations on this resource | Any non-zero error rate |

**Resources to check in order:**

1. CPU (application server, Postgres, Redis)
2. Memory (swap activity = saturation alarm)
3. Disk I/O (Postgres: `pg_stat_bgwriter`, `iostat`)
4. Network (bandwidth, packet loss, latency between services)
5. Connection pool (Postgres: `pg_stat_activity`, waiting clients)
6. Thread pool (PHP-FPM workers, Go goroutine queue)

**Critical rule**: the bottleneck changes after you fix it. Measure again after every intervention. The system you diagnosed last month is not the system you have today after 3x traffic growth.

---

## Vertical Before Horizontal

Vertical scaling (bigger machine) is simpler, cheaper, and reversible. Do it first.

| Dimension | Vertical | Horizontal |
|---|---|---|
| Implementation complexity | Low — resize and restart | High — load balancing, session affinity, distributed state |
| Cost | Linear until hardware ceiling | Linear but with coordination overhead |
| Reversibility | Easy | Hard — you've now built distributed infra |
| New failure modes introduced | None | Split-brain, network partition, clock skew |
| When you hit the ceiling | ~32 cores, ~256GB RAM for most cloud instances | No hard ceiling |

Horizontal scaling introduces distributed systems problems that cannot be undestroyed. Session state must be externalized. Caches must be shared or invalidated across nodes. Scheduled jobs must be deduplicated. Do not introduce these until vertical hits its ceiling.

**Symfony + Postgres stack**: a single 32-core RDS instance handles 5k-10k req/s for typical CRUD workloads. Most teams never need to go horizontal on Postgres.

---

## Database Scaling Path

Work this list in order. Stop when the problem is solved.

1. **Add indexes** for slow queries. Check `pg_stat_statements` for top queries by total time. An unindexed foreign key on a 10M-row table is a ticking clock.
2. **Connection pooling via PgBouncer**. Postgres forks a process per connection. 500 direct connections = 500 processes. PgBouncer multiplexes 500 app connections into 20-50 Postgres connections. Free performance.
3. **Query optimization**. Run `EXPLAIN (ANALYZE, BUFFERS)` on slow queries. Look for sequential scans on large tables, hash joins with no statistics, N+1 in Doctrine (use `JOIN FETCH` or batch loading).
4. **Read replicas** for read-heavy load. Streaming replication to a hot standby, then route read-only queries there. Works for reporting, search, analytics. Does not help write-heavy workloads.
5. **Caching for hot reads**. Redis for data that is read frequently, changes infrequently, and can tolerate brief staleness. Requires a cache invalidation strategy (see below).
6. **Partitioning for large tables**. Partition by time range (logs, events) or list (tenant, status). Postgres 12+ declarative partitioning. Reduces index size, enables partition pruning.
7. **Sharding**. Split data across multiple Postgres instances by key. Rarely needed. Very expensive in ops complexity. If you need this, you probably already know it.

**Most systems stop at step 3 or 4.** Teams that jump to step 5 before doing step 1 spend weeks building cache infrastructure that a missing index would have made unnecessary.

---

## Caching as Architectural Decision

Cache is not a performance patch. It is an architectural commitment. You now have two sources of truth.

**Cache invalidation strategies:**

| Strategy | Consistency | Complexity | Use when |
|---|---|---|---|
| TTL | Eventual — data is stale until TTL expires | Low | Read-heavy, staleness acceptable (product catalog, static config) |
| Event-driven invalidation | Strong — invalidated on write | High — requires event publishing on every write | User-facing data where staleness is noticeable |
| Write-through | Strong — cache updated synchronously on write | Medium — write path is now two operations | Small hot datasets, low write volume |
| Cache-aside (lazy load) | Eventual — miss triggers DB read and cache fill | Low | General case, read-heavy, infrequent writes |

**What must be designed before implementation:**

- What is the cache key structure? (`user:{id}:profile`, not `user_profile_{id}`)
- What invalidates this cache entry? A write to which table/event triggers invalidation?
- What is the TTL if event-driven invalidation fails? (Always have a TTL backstop)
- What happens on cache miss under high load? (Cache stampede — use probabilistic early expiration or locking)
- What does stale data look like to the user? Is it acceptable?

**For the Symfony + Redis stack**: use Symfony Cache with tag-based invalidation. Cache tags let you invalidate all keys associated with a domain object in one call. This is event-driven invalidation without building a separate event pipeline.

---

## Capacity Envelope Calculation

Rough math to know if a design is in the right order of magnitude. Takes 5 minutes. Saves weeks of debugging.

**Template:**

```
Peak req/s = daily requests × peak multiplier / 86400
DB queries per request = (measure with profiler, estimate 5-20 for CRUD)
Peak DB queries/s = peak req/s × queries per request
Max Postgres queries/s = (connections in pool) / (avg query duration in seconds)
Is it enough? = max DB queries/s > peak DB queries/s
```

**Worked example — job marketplace:**

```
Daily searches: 50k
Peak multiplier: 10x
Peak searches/s = 50,000 × 10 / 86,400 ≈ 6 req/s (searches)
Daily applications: 5k → peak = 5,000 × 10 / 86,400 ≈ 0.6 req/s (writes)

Assume 5 DB queries per search, 3 per application write:
Peak DB queries/s = (6 × 5) + (0.6 × 3) = 32 queries/s

PgBouncer pool of 20 connections, avg query 50ms:
Max queries/s = 20 / 0.05 = 400 queries/s

400 > 32 → single Postgres instance is fine with connection pooling.
```

If the math shows you're within 2x of the ceiling, add a buffer and start the next scaling step. If you're at 10% of ceiling, stop and ship.

---

## Decision Table

| Bottleneck | Traffic pattern | Team ops maturity | Recommended action |
|---|---|---|---|
| Slow queries (Postgres high CPU) | Steady, predictable | Any | Step 1: indexes + EXPLAIN |
| Connection exhaustion | Spiky | Any | Step 2: PgBouncer |
| Read-heavy, write-light | Any | Any | Step 4: read replica or Step 5: cache |
| Write-heavy, no read issues | Any | High | Optimize write queries, batch writes |
| App server CPU saturated | Growing | Medium | Vertical scale app server first |
| App server CPU saturated at ceiling | Growing | High | Horizontal scale app servers (stateless by design) |
| Go worker queue depth growing | Bursty | Any | Add worker replicas (workers are stateless, safe to scale) |
| Redis memory full | Any | Any | Eviction policy + key expiry audit before scaling Redis |

---

## Anti-Patterns

- **Cache before profiling**: adding Redis before identifying the slow query. You've now cached a slow query's result instead of fixing the query. The query still runs, just less often.
- **Horizontal scale of stateful services**: scaling Symfony app servers when session state is in PHP files. New requests go to nodes without the session. Users get logged out.
- **"We'll just add more servers"**: without knowing what's saturated. If Postgres is the bottleneck, more app servers make it worse — more connections, more load.
- **Cache without invalidation strategy**: adding a 24-hour TTL to user profile data, then wondering why users see stale names after account updates.
- **Read replica without query routing**: setting up a read replica but routing all queries to primary because "it's easier." The replica is unused infrastructure.
- **Partitioning as first response**: partitioning a 500k-row table. Partitioning pays off at tens of millions of rows. Before that, it adds complexity with no benefit.

---

## Šta da pitaš AI

- "Our [component] is showing [USE metric: e.g. 80% CPU utilization]. Walk me through the USE method to identify whether this is the actual bottleneck or whether something upstream is causing it."
- "We have [X req/s] with [Y ms] average [operation] hitting [component]. Is this within the capacity envelope? Show the math and tell me at what point we'd need the next scaling step."
- "We want to add caching for [read pattern: e.g. job listing detail pages]. Our consistency requirement is [e.g. updates visible within 60 seconds]. What are the cache invalidation options and their tradeoffs?"
- "We're seeing slow queries in Postgres. Here's the output of `pg_stat_statements` ordered by total_time: [paste]. What do I do first?"
- "We're at step [N] in the database scaling path. Walk me through what step [N+1] requires operationally — not just the configuration, but what breaks, what to monitor, what rollback looks like."
