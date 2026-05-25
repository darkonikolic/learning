# Lab: Observability Design

Two exercises. Design before implementation. Know what you are building before you build it.

---

## Reference: Four Golden Signals per Component

| Component | Latency | Traffic | Errors | Saturation |
|---|---|---|---|---|
| **API Gateway** | Request duration p50 / p99 | Requests/sec (total + per route) | 4xx rate, 5xx rate | Concurrent open connections |
| **Symfony API** | Endpoint duration p99 per route | Requests/sec per endpoint | Exception rate, HTTP 5xx/s | PHP-FPM pool: active / max workers |
| **Go worker** | Job processing duration p99 | Jobs consumed/sec | Job failure count, retry count | Queue depth (unconsumed message count) |
| **Postgres** | Query duration p99 (read / write separately) | Queries/sec | Error count, deadlock/s, rollback/s | Connections: active / pool max, replication lag |
| **Redis** | Command duration p99 | Commands/sec | Error count, eviction count/s | Memory used / maxmemory, hit rate |

---

## Reference: Structured Log Schema

```json
{
  "timestamp": "2026-05-25T10:32:01.123Z",
  "level": "error",
  "service": "symfony-api",
  "request_id": "req_01HXYZ4K2M3N5P6Q7R8S",
  "user_id": "usr_9182",
  "endpoint": "POST /jobs/{id}/apply",
  "method": "POST",
  "status_code": 500,
  "duration_ms": 234,
  "message": "Database connection timeout on job application write",
  "context": {
    "job_id": "job_4421",
    "db_host": "postgres-primary",
    "query_type": "INSERT"
  }
}
```

**Field presence by service:**

| Field | API Gateway | Symfony API | Go worker |
|---|---|---|---|
| `timestamp` | Required | Required | Required |
| `level` | Required | Required | Required |
| `service` | Required | Required | Required |
| `request_id` | Generated here | Propagated from header | Propagated from job payload |
| `user_id` | Optional (if JWT parsed at gateway) | Required when authenticated | Required (from job payload) |
| `endpoint` | Required | Required | N/A — use `job_type` |
| `job_type` | N/A | N/A | Required |
| `duration_ms` | Required (total) | Required (per request) | Required (per job) |
| `status_code` | Required | Required | N/A — use `job_status` |
| `job_status` | N/A | N/A | `success`, `failed`, `retrying` |

---

## Reference: Alert Design

| Alert | Signal type | Threshold | Action | Why |
|---|---|---|---|---|
| API error rate high | Symptom | 5xx rate > 1% over 5 min | Page | User-facing. Every 5xx is a broken user request. |
| API p99 latency breach | Symptom | p99 > [SLO budget] | Page | Users experiencing slow responses at scale |
| Worker queue growing | Symptom | Queue depth > 1000 and not decreasing | Page | Workers are down, stuck, or overwhelmed — jobs not processing |
| Job failure rate high | Symptom | Job failure rate > 5% over 10 min | Page | Downstream dependency failing or data quality issue |
| PHP-FPM pool saturated | Cause | Active workers > 90% of pool max | Notify | Early warning before Symfony starts queuing or rejecting |
| Redis evictions started | Cause | `evicted_keys` counter > 0 | Notify | Cache is full — hot data being evicted, hit rate will fall |
| Postgres connections near limit | Cause | Active connections > 80% of pool max | Notify | Connection exhaustion means next spike fails |

---

## Exercise 1: Observability Design

**System**: API Gateway → Symfony API → Go worker → Postgres + Redis

Work through the four questions in order. Each answer constrains the next.

---

### 1. Metrics per Component (Four Golden Signals)

Using the reference table above, extend it with:
- The specific metric name you would use (Prometheus naming convention: `service_unit_operation_suffix`)
- The label dimensions you would add (e.g. `{route="/jobs/{id}", method="POST", status="5xx"}`)

**Required output format:**

| Component | Signal | Metric name | Labels | Why this label |
|---|---|---|---|---|
| Symfony API | Errors | `http_requests_total` | `{route, method, status_class}` | Route separation reveals which endpoint is broken |
| Go worker | Saturation | `worker_queue_depth` | `{queue_name}` | Multiple queues may have different failure modes |
| ... | ... | ... | ... | ... |

**Constraints to answer:**
- Which Symfony API metrics must be per-route (not just aggregate)? Why?
- What is the minimum Go worker metric that tells you workers are not processing?
- What Postgres metric tells you that the application, not the database, is the bottleneck?

---

### 2. Structured Log Schema

Using the reference schema, design the complete schema for:

**a) Symfony API — HTTP request log** (emitted at request completion)

Required fields: identify which five fields are mandatory for cross-service diagnosis if you had nothing else.

**b) Go worker — job completion log** (emitted when a job finishes, success or failure)

Note: Go worker has no HTTP context. What replaces `endpoint`, `status_code`, `method`? How does `request_id` arrive in the worker?

**c) The propagation contract:**

Complete this sentence for each boundary:
- "API Gateway passes request_id to Symfony API via: ___"
- "Symfony API passes request_id to Go worker via: ___"
- "Go worker passes request_id to its own logs via: ___"

If request_id is not in the **job message payload schema from day 1**, what happens when you try to add it later?

---

### 3. First Two Alerts

Choose the two alerts you would implement first from the reference alert table. For each:

| Decision | Answer |
|---|---|
| Alert name | |
| Signal type (symptom / cause) | |
| Why this one before the others | |
| What observability is required for this alert to exist | |
| What this alert cannot tell you | |

**Forcing constraint**: one of your two alerts must be a symptom alert. If both are cause alerts, you have no user-facing signal. Explain what gap that leaves.

---

### 4. Request ID: Generation and Propagation

Answer in architecture terms, not implementation terms:

1. **Where is request_id generated?** One place only. Why the gateway and not the API?
2. **What is the format?** UUID vs. ULID — what is the operational difference? (Hint: sort order under log query.)
3. **What happens if Symfony API receives a request with no X-Request-ID header?** (Internal call, health check, misconfigured client.) Generate a new one? Reject? Log a warning?
4. **How does Go worker receive the request_id for jobs enqueued during an HTTP request?** Draw the data flow: HTTP request → Symfony API → job payload → Go worker log.
5. **What is the one place request_id propagation silently fails?** (Hint: what happens when a Symfony service calls an external API without forwarding the header?)

---

## Exercise 2: Incident Diagnosis

**Setup**: You have implemented the observability from Exercise 1.

**Alert fired**: "API error rate > 2% for last 5 minutes" — paged at 02:14.

Walk through the diagnosis in sequence. At each step, name the specific metric or log query you run and what answer you are looking for.

---

### Step 1: First Metric to Check

You have one dashboard open. What is the first panel you look at and why?

It is not "all metrics." It is one signal that tells you whether this is a spike (transient) or a sustained degradation (incident).

| Question | Metric / query | What the answer means |
|---|---|---|
| Is the error rate still > 2%? | `rate(http_requests_total{status_class="5xx"}[5m])` / total | Confirms alert is still firing, not already resolved |
| Is traffic volume normal? | `rate(http_requests_total[5m])` | Sudden traffic spike → resource saturation. Sudden drop → upstream failure |
| When did it start? | Time-series view of error rate, 1h window | Correlates with deploy, config change, or traffic event |

---

### Step 2: Narrow to Which Endpoint

The error rate is confirmed: 2.3%, still rising. The system has 12 endpoints. You do not check all 12.

| Query | What you are looking for |
|---|---|
| `rate(http_requests_total{status_class="5xx"}[5m]) by (route)` | Which route accounts for the majority of errors |
| `histogram_quantile(0.99, rate(http_request_duration_bucket[5m])) by (route)` | Whether the erroring route is also slow (latency spike = different cause than errors alone) |

**Result**: errors are concentrated on `POST /jobs/{id}/apply`. Latency on that route is also elevated (p99: 4200ms, normal: 180ms).

What does the combination of high error rate + high latency on a write endpoint suggest before you open a single log?

---

### Step 3: Find the Failing Requests in Logs

You know the endpoint. Now you need the specific error.

**Log query pattern:**

```
service="symfony-api"
AND endpoint="POST /jobs/{id}/apply"
AND level="error"
AND timestamp > [alert_time - 10 min]
ORDER BY timestamp DESC
LIMIT 50
```

What you extract from the first matching log entry:
- `request_id` — use this to pull the full request trace across services
- `message` — the error class
- `context.query_type` and `context.db_host` — whether this is a database operation

**Cross-service correlation:**

```
request_id="req_01HXYZ4K2M3N5P6Q7R8S"
AND service IN ("api-gateway", "symfony-api", "go-worker")
ORDER BY timestamp ASC
```

This reconstructs the full lifecycle of one failing request across all services. Without `request_id` propagated through all services, this query returns partial results — you see the API error but not what the worker did with the job, or whether the API error was caused by the worker failing to confirm.

---

### Step 4: Determine if It Is a Downstream Dependency

You have the error message: "Database connection timeout on job application write."

| Check | Metric / query | What you are looking for |
|---|---|---|
| Is Postgres query latency elevated? | `histogram_quantile(0.99, rate(pg_query_duration_bucket[5m]))` | Yes → Postgres is slow, not just the app |
| Is connection pool exhausted? | `pg_connections_active / pg_connections_max` | > 90% → connection exhaustion causing timeouts |
| Is Postgres error rate elevated? | `rate(pg_errors_total[5m])` | Yes → queries failing, not just slow |
| Is Redis involved in this endpoint? | Check structured log `context` for Redis commands | If Redis timeout is in the trace, the cause may be Redis, not Postgres |

**Confirming the blast radius:**

```
service="symfony-api"
AND context.db_host="postgres-primary"
AND level="error"
AND timestamp > [alert_time - 10 min]
GROUP BY endpoint
```

If multiple endpoints are showing Postgres errors → it is a Postgres incident, not a code regression on `/jobs/{id}/apply`.

---

### Observability Gaps: What Makes This Diagnosis Impossible

For each gap, name what you cannot answer and what work-around you are forced to do instead:

| Missing observability | Question you cannot answer | Forced work-around |
|---|---|---|
| No per-route error rate metric (only aggregate) | Which endpoint is failing | Check application logs manually, no metric to filter by |
| No request_id in Go worker logs | Whether a job enqueued by the failing request also failed | Check worker logs by time range and hope job_id is logged |
| No Postgres query duration metric | Whether the timeout is from slow queries or connection exhaustion | SSH into Postgres, run `pg_stat_activity` — manual, delayed, requires access |
| No structured logs (plain text only) | Filter logs by endpoint, user, or error type without parsing | `grep` + `awk` on raw files — cannot do in a dashboard at 02:14 |
| No `duration_ms` in logs | Whether this is a timeout (slow) or an immediate error (fail-fast) | Only `status_code` — cannot distinguish timeout from crash |
| No Go worker queue depth metric | Whether jobs from failing requests are piling up | Log into queue management UI or message broker console manually |

**The critical gap**: no `request_id` propagation into Go worker means you can confirm the API is failing but cannot confirm whether the jobs enqueued before the failure were processed, lost, or are retrying. The write endpoint failing after enqueue means partial state — the job may or may not be in the queue. Without cross-service correlation, you do not know.
