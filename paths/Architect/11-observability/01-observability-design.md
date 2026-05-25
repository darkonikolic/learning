# Observability Design

Observability is not "we have logs." It is: can you answer "what is broken and why" without SSH-ing into a server? If the answer is no, you do not have observability — you have noise.

---

## The Three Pillars

| Pillar | What it answers | Strengths | Weaknesses |
|---|---|---|---|
| **Logs** | What happened in this request | Debugging specific requests, audit trail, error detail | Useless aggregated at scale, no performance trends, expensive to store unstructured |
| **Metrics** | How is the system behaving over time | Dashboards, alerting, SLO tracking, cheap to store | Cannot debug why one specific request failed |
| **Traces** | How did this request move through the system | Latency attribution, dependency mapping, cross-service correlation | Expensive to collect + store, requires instrumentation in every service |

**The rule**: start with metrics (cheapest, most useful for SLOs), add structured logs with request ID correlation, add traces only when you have multiple services and cannot find where latency originates.

Do not add distributed tracing on day 1. Traces without multiple services answer questions you do not yet have.

---

## The Four Golden Signals

These four signals tell you **if** something is wrong. Everything else tells you why.

| Signal | What it measures | Example metric | Alert threshold |
|---|---|---|---|
| **Latency** | How long requests take — p50, p95, p99 (not average) | `http_request_duration_seconds{p99}` | p99 > SLO budget |
| **Traffic** | How many requests per unit time | `http_requests_total` rate | Sudden drop = silent failure |
| **Errors** | How often requests are failing | `http_requests_total{status=~"5.."}` rate | > 1% of total requests |
| **Saturation** | How full is the most constrained resource | Queue depth, connection pool utilization, memory % | Growing trend, not point-in-time |

**Why not average latency**: averages hide tail latency. A p99 of 2000ms on an API that averages 50ms means 1 in 100 users gets a broken experience. p99 is user-facing. Average is not.

**Applied to the spine** — API Gateway → Symfony API → Go worker → Postgres + Redis:

| Component | Latency | Traffic | Errors | Saturation |
|---|---|---|---|---|
| API Gateway | Request duration p50/p99 | Requests/sec per route | 4xx/5xx rate | Concurrent connections |
| Symfony API | Endpoint duration p99 | Requests/sec per endpoint | Exception rate, 5xx rate | PHP-FPM pool active workers |
| Go worker | Job processing duration p99 | Jobs consumed/sec | Job failure/retry rate | Queue depth (unconsumed jobs) |
| Postgres | Query duration p99 | Queries/sec | Error rate, deadlock count | Connection pool active/waiting |
| Redis | Command duration p99 | Commands/sec | Error rate, eviction rate | Memory used / max memory |

---

## Structured Logging Design

Logs must be queryable. Plain text logs are useless at scale — you cannot aggregate, filter, or correlate them across services. Structured logging means JSON with fixed fields.

**Minimum required schema:**

```json
{
  "timestamp": "2026-05-25T10:32:01.123Z",
  "level": "error",
  "service": "symfony-api",
  "request_id": "req_01HXYZ...",
  "user_id": "usr_9182",
  "endpoint": "POST /jobs/{id}/apply",
  "duration_ms": 234,
  "status_code": 500,
  "message": "Database connection timeout",
  "context": {}
}
```

**Field rules:**

| Field | Required | Notes |
|---|---|---|
| `timestamp` | Always | ISO 8601, UTC. Not local time. |
| `level` | Always | `debug`, `info`, `warning`, `error`, `critical` |
| `service` | Always | Fixed string per service. Enables cross-service filtering. |
| `request_id` | Always | The spine of cross-service correlation. See propagation below. |
| `user_id` | When authenticated | Enables "show me everything this user experienced" |
| `duration_ms` | On request completion | Enables latency percentile queries in log tooling |
| `status_code` | HTTP services | Enables error rate queries in logs as fallback |
| `message` | Always | Human-readable. Not structured data — that goes in `context`. |
| `context` | When relevant | Machine-readable key-value pairs for filtering |

**What not to put in logs**: PII beyond user ID (no email, no name), passwords, tokens, credit card numbers. Log the ID; look up the detail when needed.

---

## Request ID Propagation

This is architectural, not implementation. If request_id is not propagated across service boundaries, you cannot reconstruct a distributed request. You have isolated logs, not correlated logs.

**Propagation path** for this spine:

```
API Gateway
  → generates request_id (UUID or ULID) if none present
  → injects as X-Request-ID header
  → logs with request_id

Symfony API
  → reads X-Request-ID from incoming request
  → attaches to all log statements (via Monolog processor)
  → passes X-Request-ID when calling internal APIs
  → writes request_id to job payload when enqueuing

Go worker
  → reads request_id from job payload
  → attaches to all log statements
  → passes as header if calling downstream services

Postgres / Redis
  → query logs tagged with request_id via application-layer logging (not native DB logs)
```

**The architectural decision**: request_id must be in the job message schema from day 1. Adding it later means modifying all job producers, consumers, and message schemas under production load.

---

## Alerting Design

**Alert on symptoms, not causes.**

| Type | Example | Problem |
|---|---|---|
| Symptom alert | API error rate > 1% | User-facing. Something is broken right now. |
| Cause alert | Postgres CPU > 80% | Infrastructure signal. May not yet affect users. |

Start with symptom alerts. Add cause alerts only when you have learned which causes predictably lead to which symptoms — and even then, cause alerts are for early warning, not paging.

**What to page on:**
- User-facing error rate exceeds threshold
- API p99 latency exceeds SLO budget
- Queue depth growing with no consumption (workers are down or stuck)

**What to notify (not page) on:**
- Postgres connection pool near saturation (early warning)
- Redis memory > 80% (before eviction starts)
- Deploy completed (context for correlating metric changes)

---

## SLO-Based Alerting: Burn Rate

Point-in-time alerting ("error rate > 1% for 5 minutes") pages on noise. A 5-minute spike in errors that recovers is not an incident. An error rate that has been 1.5% for 3 hours has consumed a significant fraction of your monthly error budget — that is an incident, even if the rate looks "low."

**Error budget burn rate:**

```
monthly error budget = (1 - SLO) × total requests for the month
burn rate = actual error rate / (1 - SLO)

e.g. SLO = 99.9%, error budget = 0.1%
if current error rate = 0.2%, burn rate = 2x
at 2x burn rate, 30-day budget is consumed in 15 days
```

**Burn rate thresholds (Google SRE model):**

| Burn rate | Action | Window |
|---|---|---|
| > 14.4x | Page immediately | 1 hour window |
| > 6x | Page (business hours) | 6 hour window |
| > 3x | Create ticket | 3 day window |
| > 1x | Monitor | Weekly review |

At 14.4x burn rate, the entire monthly budget is consumed in 2 hours. That is always page-worthy.

---

## Decision Table: Which Pillars to Implement First

| System complexity | Team size | SLO requirement | Start with |
|---|---|---|---|
| Single service | Small (1-5) | None / informal | Structured logs + 4 golden signal metrics |
| 2-3 services | Small-medium | Informal SLO | Metrics + structured logs + request_id propagation |
| 3+ services | Any | Formal SLO with budget | Metrics + logs + burn rate alerting, then traces |
| 3+ services | Medium-large | Strict SLO (99.9%+) | All three pillars, traces from week 1 |
| Microservices (10+) | Large | Strict SLO | Traces are mandatory — latency is otherwise unattributable |

For this spine (API + Go worker + Postgres + Redis): metrics + structured logs + request_id propagation. Add traces when you have a latency problem you cannot locate with logs alone.

---

## Observability Cost

| Pillar | Storage cost | Instrumentation cost | Query cost |
|---|---|---|---|
| Metrics | Low — aggregated time series | Low — counters and histograms | Low — pre-aggregated |
| Logs | Medium — grows with request volume | Medium — schema design + propagation | Medium — depends on indexing |
| Traces | High — one trace per request, cross-service | High — all services must be instrumented | High — sampling required at scale |

**Design for cost from day 1:**
- Do not log at DEBUG level in production. DEBUG is for development. Production logs should be INFO and above.
- Sample traces at the gateway. 100% sampling at 1000 req/s is 86M traces/day. Sample at 10% or sample only slow/error requests.
- Set log retention by tier: error logs 90 days, info logs 30 days, debug logs 3 days maximum.

---

## Anti-Patterns

- **Logging everything at DEBUG level in production**: costs money, generates noise, makes signal impossible to find. Logs must be filtered before they are useful — do not create the filtering problem yourself.
- **No request ID propagation**: the most expensive oversight to fix retroactively. You have logs per service but cannot join them into a request story. Every cross-service incident becomes manual detective work.
- **Alerting on infrastructure metrics only**: Postgres CPU at 80% does not tell you whether users are experiencing failures. You can have a saturated database and happy users (slow, but succeeding). Always have a user-facing error rate alert.
- **Adding distributed tracing before 2+ services**: single-service traces add overhead and answer no questions you could not answer with logs. The value of tracing is attribution across service boundaries.
- **No SLO → no alerting discipline**: without an error budget, every alert is a judgment call. Budget burn rate turns alerting into math.
- **Alerting on every error**: individual errors are noise. Rate over window is signal.

---

## Šta da pitaš AI

- "We have [describe system: components, request flow, expected traffic]. What are the four golden signals for each component? What specific metrics would we collect, and what would we alert on?"
- "Design the structured log schema for [service type, e.g. async job processor]. What fields must be present for cross-service correlation? What should never appear in logs?"
- "Our SLO is [X% availability over 30 days]. What burn rate alerting thresholds make sense? At what burn rate do we page vs. just notify? Show the math."
- "We have [N] services. We have metrics and structured logs but no traces. Our p99 latency SLO is violated but we cannot find the cause. What is the minimum tracing setup to locate the latency? What do we instrument first?"
- "Our observability costs are growing linearly with traffic. We are logging at DEBUG in production and sampling traces at 100%. What is the prioritized list of changes to cut cost without losing diagnostic ability?"
