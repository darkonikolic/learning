# Lab: Failure Scenarios and Degradation Design

Two exercises. Work through each before checking the reference answers.

---

## Exercise 1: Cascade Failure Trace

**Stack:** `Gateway → Symfony API → Go worker → Postgres → Redis`

**Scenario:** Postgres starts returning queries in 8 seconds instead of the normal 20ms. Postgres is not down — it is responding, just slowly. No timeouts are currently configured.

**Tasks:**
1. Trace the cascade: what happens at each layer in sequence?
2. What does the user see and when?
3. What metrics spike and in what order?
4. What breaks first?
5. Design mitigations at each layer.

Work through this before reading the reference below.

---

### Reference: Cascade Trace (No Mitigations)

**Timeline:**

| Time | Layer | What happens |
|------|-------|-------------|
| T+0s | Postgres | Queries start taking 8s (slow disk, lock contention, runaway query — root cause TBD) |
| T+0–8s | Symfony API | First requests to Postgres hang. PHP-FPM workers waiting for DB response. |
| T+8s | Symfony API | First requests return (slowly). p99 latency now ~8s. FPM worker count drops as each worker is occupied for 8s instead of 20ms — capacity drops ~400x. |
| T+10–30s | Symfony API | FPM pool fills. New requests queue behind waiting workers. Queue backs up at the Gateway. |
| T+30–60s | Gateway | Connection pool to Symfony API fills. Gateway starts returning 502/504 to users. |
| T+30–60s | Go worker | Worker polls Postgres (job queue or state reads). Worker goroutines hang waiting for DB. Worker throughput drops to near zero. |
| T+60s+ | Full outage visible | Users get 502s or timeouts. No new requests are being processed. |

**What the user sees:**
- First ~10 seconds: normal (in-flight requests complete before the pool fills)
- 10–30 seconds: requests are slow (8s response times)
- 30s+: requests fail entirely (502, 504, connection refused)

**Metrics that spike, in order:**
1. `postgres_query_duration_p99` (first signal — if you have it)
2. `php_fpm_active_processes` approaching `php_fpm_max_children`
3. `http_request_duration_p99` at Symfony API
4. `gateway_upstream_errors` and `gateway_request_queue_depth`
5. `go_worker_goroutine_count` climbing (goroutines blocked)
6. `http_error_rate` (502/504) — this is what most teams alert on, but it's the last signal

**What breaks first:** Symfony API FPM pool. The connection pool is the first bounded resource that fills. Everything downstream of it (user responses, worker processing) degrades from there.

---

### Reference: Mitigations by Layer

| Layer | Mitigation | Mechanism | Effect |
|-------|-----------|-----------|--------|
| **Symfony API → Postgres** | DB query timeout | `PDO::ATTR_TIMEOUT` or Doctrine `defaultQueryTimeout` = 500ms | Queries fail fast instead of holding FPM workers for 8s. FPM pool freed. |
| **Symfony API → Postgres** | Connection pool limit + timeout | `max_connections` tuned to FPM pool size; connection acquisition timeout | Prevents connection exhaustion at Postgres level |
| **Symfony API** | FPM pool sizing | `pm.max_children` sized to handle burst, not unlimited | Bounded resource — explicit ceiling rather than implicit |
| **Symfony API** | Circuit breaker on DB | Open after N consecutive DB timeouts; fast-fail new requests | Stops hammering slow Postgres, gives it recovery time |
| **Symfony API** | Read from Redis cache | Cache hot data; serve stale reads when DB is slow | API continues serving read requests from cache |
| **Gateway → Symfony API** | Upstream timeout + retry | Gateway timeout < SLO; retry on 503, not on 500 | Gateway fails fast rather than queuing indefinitely |
| **Go worker** | DB query timeout | Per-query context with timeout | Worker goroutines don't accumulate |
| **Go worker** | Backoff on DB failure | Exponential backoff with jitter when DB queries fail | Reduces Postgres load during degradation, aids recovery |
| **Postgres** | Query timeout at DB level | `statement_timeout = 2000ms` in Postgres config | Server-side safety net catches all clients |
| **Postgres** | Identify slow query | `pg_stat_activity`, `auto_explain` | Find the root cause (runaway query, missing index, lock) |

**After mitigations — same scenario:**
- Postgres slows to 8s
- Symfony API queries time out at 500ms
- Circuit breaker opens after 5 failures
- API serves reads from Redis cache
- API returns 503 (degraded) for writes — fast, not slow
- FPM pool stays available
- Go worker backs off, waits for circuit to close
- User sees: "service degraded, read-only mode" or cached results — not a 502

---

## Exercise 2: Degradation Posture Design

**Service:** Product search
**Stack:** Symfony API with three data sources:
- Elasticsearch (primary — full-text search, facets, relevance ranking)
- Redis cache (recent query results, TTL 5 minutes)
- Postgres (canonical product data — all fields, no search capability)

**Task:** Design the degradation posture for each failure scenario. For each:
- What does the user get?
- What do you log?
- What is the alerting threshold?
- What is the recovery path?

Work through all four cases before reading the reference.

**Scenarios:**
1. Elasticsearch is down (connection refused)
2. Elasticsearch is slow (responding in > 500ms, SLO is p99 < 200ms)
3. Redis is down (connection refused)
4. All three down simultaneously

---

### Reference: Degradation Posture Table

| Scenario | User gets | Logging | Alert threshold | Recovery path |
|----------|-----------|---------|-----------------|---------------|
| **ES down** | Results from Redis cache (if hit). If cache miss: fallback to Postgres `ILIKE` search with note "limited search results." If Postgres also fails: "Search unavailable, browse by category." | `ERROR elasticsearch.unavailable + circuit_state=open`. Log every cache hit vs fallback vs total failure per request. | ES circuit breaker opens (immediately); alert ops. DLQ if search queries are queued. | ES recovers → circuit half-opens → probe → close. No replay needed (stateless read). |
| **ES slow (>500ms)** | Results from Redis cache if hit (TTL not expired). If cache miss: serve Postgres fallback with degradation note. New queries not sent to ES (circuit opens after N slow responses). | `WARN elasticsearch.latency p99=Xms threshold=500ms`. Log slowness + fallback type per request. | p99 > 500ms for 30s window → alert. | ES latency returns to normal → circuit half-opens → probes succeed → close. |
| **Redis down** | Results from Elasticsearch directly (normal search, slightly higher ES load). Cache writes silently dropped (don't fail the request for a write failure). | `WARN redis.unavailable`. Log every request that would have been a cache hit (to measure ES load increase). | Redis circuit opens → immediate alert (ES load will spike 3–10x without cache). | Redis recovers → circuit closes → cache warm-up naturally through traffic. |
| **All three down** | Static fallback: return featured/bestseller product list from in-memory config (last-known, compiled at deploy time). Clear degradation message: "Search is temporarily limited — showing popular products." | `CRITICAL search.all_backends_unavailable`. Alert immediately, page on-call. Log every request hitting the static fallback. | Immediate page — this is a P1 incident. | Restore any one backend. Prioritize Redis (fastest recovery path to partial function). Then ES. Then Postgres (should never be down independently in this stack). |

---

### Example Worked: Case 1 (Elasticsearch Down)

Request arrives: `GET /search?q=running+shoes`

```
1. Check circuit breaker for Elasticsearch → OPEN (ES is down)
2. Skip ES entirely (fast-fail — no timeout needed, circuit is open)
3. Check Redis cache → cache HIT for this query
4. Return cached results
5. Log: search.request{backend=redis_cache, es_state=circuit_open, cache_hit=true}
6. Response time: ~5ms (Redis), not 200ms (ES)
```

Request arrives: `GET /search?q=obscure+product+no+one+searched+before`

```
1. Check circuit breaker for Elasticsearch → OPEN
2. Skip ES
3. Check Redis cache → cache MISS (never searched before)
4. Fallback to Postgres: SELECT id, name, description FROM products
   WHERE to_tsvector('english', name || ' ' || description) @@ plainto_tsquery($1)
   LIMIT 20
5. Return results with header: X-Search-Mode: degraded
   Response body note: "Search results may be limited"
6. Log: search.request{backend=postgres_fallback, es_state=circuit_open, cache_hit=false}
7. Write result to Redis cache (so next identical query hits cache)
8. Response time: ~80ms (Postgres), not 200ms (ES)
```

**What the Postgres fallback cannot do vs Elasticsearch:**
- Full-text relevance ranking (Postgres gives you match, not ranked match)
- Faceted navigation (color, size, brand filters)
- Fuzzy matching / typo tolerance
- Synonym handling

The user gets results. They're less good. That is the correct tradeoff vs "search unavailable."

---

### Cascade Tracing Template

For any failure analysis, walk this structure:

```
Failing component: [name, what failure mode: down / slow / corrupted]
Bounded resources at each layer: [thread pools, connection pools, queue depth]

Layer 1 [component closest to failing dependency]:
  - What fills up first?
  - At what threshold does it become visible to the next layer?

Layer 2 [next component]:
  - What does it see? (slow response? errors? connection failures?)
  - What of its resources fills up?

Layer 3 [next component]:
  - Same

User impact:
  - First symptom (time, what user sees)
  - Full failure (time, what user sees)

Metrics spike order:
  1. [first indicator — usually internal to the failing component]
  2. [second — usually latency at the next layer]
  3. [third — usually error rate at the layer after that]
  4. [last — usually what the dashboard shows]
```

---

## Summary: Degradation Decision Matrix

| Dependency | Data type | Stale OK? | Fallback exists? | Posture |
|------------|-----------|-----------|-----------------|---------|
| Elasticsearch | Search index | Yes (minutes) | Redis cache + Postgres | Degrade gracefully |
| Redis | Cache | N/A (it is the cache) | Go to source | Remove cache layer, serve from source |
| Postgres | Canonical data | No | None | Fail fast for writes; serve from Redis/ES for reads |
| Payment processor | External | No | None | Fail fast with clear error |
| Email service | Notification | Yes (minutes to hours) | Queue for retry via DLQ | Queue + retry |
| Analytics service | Reporting | Yes (hours) | Drop and log | Silent drop, catch up later |
