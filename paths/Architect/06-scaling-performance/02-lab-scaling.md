# Lab: Scaling Decisions

No scaffolding. Work the exercises. Wrong answer with correct reasoning is better than right answer with no reasoning — show your math.

---

## Exercise 1: Capacity Envelope

**System:** job marketplace on Symfony + Postgres + Redis.

**Known numbers:**
- 100k active job listings in database
- 50k daily searches
- 5k daily job applications (writes)
- Peak traffic: 10x daily average

**Your job:**

1. Calculate peak searches per second
2. Calculate peak applications per second
3. Estimate peak Postgres query load (assume 8 DB queries per search, 4 per application write)
4. Determine whether a single Postgres instance with PgBouncer (pool of 25, average query time 40ms) can handle this
5. If it cannot, what is the first thing to add? Why that and not something else?

**Capacity math template:**

```
Peak req/s = (daily requests × peak multiplier) / 86400

Peak DB queries/s = sum of (req type req/s × queries per request)

Max Postgres throughput = pool_connections / avg_query_duration_seconds

Verdict = max throughput vs peak load
```

**Show your work. State your assumptions explicitly.**

---

## Exercise 2: Bottleneck Diagnosis

**Situation:** production API for the job marketplace.

**Symptoms:**
- 3 months ago: average API response time 50ms
- Today: average API response time 800ms
- Traffic grew 3x over the same period
- No error rate increase — 200s, just slow
- No recent deployments that changed query patterns

**Your job:**

Walk through the diagnosis in sequence. For each bottleneck layer, state:
1. Which USE metric to check
2. How to check it (specific tool/query/command)
3. What you expect to find given the symptoms
4. What the fix is if this layer is the bottleneck

**Bottleneck layers to evaluate in order:**

```
Layer 1: Application server (PHP-FPM workers / Symfony)
Layer 2: Database connections (connection pool saturation)
Layer 3: Database query performance (query execution time)
Layer 4: Database I/O (disk, buffer cache hit rate)
Layer 5: Network (between app and DB)
Layer 6: Redis (if caching layer exists)
```

**Hint:** 3x traffic growth with no code changes and no errors usually points to one of two places. You should identify which two and explain why.

---

## USE Method Checklist

Run this before any scaling conversation.

```
Resource: ________________

Utilization
  - Current value: _______%
  - How measured: _________________
  - Alarm threshold: 70% sustained

Saturation
  - Queue depth / wait time: _______
  - How measured: _________________
  - Alarm threshold: Any non-zero growth over time

Errors
  - Error rate: _______
  - How measured: _________________
  - Alarm threshold: Any non-zero

Verdict:
  [ ] This is the bottleneck — address first
  [ ] This is not saturated — check next resource
  [ ] Inconclusive — need more data (specify what)
```

---

## Database Scaling Path — Quick Reference

```
1. Indexes          → pg_stat_statements, EXPLAIN (ANALYZE, BUFFERS)
2. PgBouncer        → pg_stat_activity, waiting connection count
3. Query optimize   → EXPLAIN plan, N+1 detection, Doctrine profiler
4. Read replica     → pg_stat_replication, replica lag
5. Redis cache      → cache hit rate, invalidation strategy defined
6. Partitioning     → table size > 10M rows, sequential scan on date range
7. Sharding         → last resort, requires full architecture change
```

---

## Worked Example: Connection Pool Math

```
Scenario: Symfony app, 20 PHP-FPM workers per server, 3 app servers.
Direct connections to Postgres: 20 × 3 = 60 connections.
Postgres max_connections: 100 (default).
At peak traffic, 60 connections is fine. At 5 app servers: 100 connections = hitting the ceiling.

With PgBouncer (transaction pooling):
  App → PgBouncer: 20 × N connections per server (cheap, PgBouncer handles these)
  PgBouncer → Postgres: 20 real connections (configurable)
  
Throughput at 20 real connections, 40ms avg query:
  20 / 0.04 = 500 queries/s

This is 8x more throughput than without pooling, from configuration alone.
```

---

## Self-Check

After completing both exercises, verify:

- [ ] Exercise 1: Did you show the arithmetic, not just the conclusion?
- [ ] Exercise 1: Did you state whether single Postgres is sufficient before recommending what to add?
- [ ] Exercise 1: Did you recommend step 1 of the database scaling path, not step 5?
- [ ] Exercise 2: Did you check connection saturation before assuming slow queries?
- [ ] Exercise 2: Did you specify the exact tool/query for each layer, not just "check the database"?
- [ ] Exercise 2: Did you identify the two most likely bottlenecks given 3x traffic growth with no code changes?

---

## Reference Numbers for Estimation

| Component | Rough throughput ceiling | Notes |
|---|---|---|
| Single Postgres (8-core RDS) | 2k-5k simple queries/s | Drops fast with complex joins |
| PgBouncer (20 Postgres connections) | ~500 queries/s at 40ms avg | Adjust for your query profile |
| Redis | 100k ops/s single thread | Rarely the bottleneck |
| PHP-FPM worker | 1 request at a time | Worker count = max concurrency |
| Go worker (goroutine) | Thousands concurrent | Bottleneck is usually downstream, not the worker |
| Network (same datacenter) | <1ms latency | If you're seeing >5ms, investigate |
