# Failure Thinking

Reliability is not "does it work?" — it is "how does it degrade when dependencies fail?" Every service will have its dependencies fail. The question is what your service does about it.

---

## SLO/SLI Practically

**SLI (Service Level Indicator):** what you measure. A specific, observable metric.
**SLO (Service Level Objective):** the target. The threshold your team agrees to operate to.
**SLA (Service Level Agreement):** the external contract. Usually less strict than internal SLO to give you operating room.

**Concrete SLIs for a Symfony API:**
- `p99 request latency < 200ms` (measured at the load balancer or application)
- `error rate < 0.1%` (5xx responses / total responses, 5-minute window)
- `availability > 99.9%` (successful health checks / total checks)

Do not set SLOs at theoretical maximums. Set them at what your team can actually defend and what users will actually notice if crossed. If users tolerate 500ms, don't set SLO at 200ms — you'll burn budget on noise.

**SLO should sit below user expectations,** leaving you budget to burn before users feel it.

---

## Error Budget

Error budget = the unreliability you're allowed before you must stop shipping features and do reliability work.

| SLO | Error budget (monthly) | Error budget (weekly) |
|-----|----------------------|----------------------|
| 99.9% availability | ~44 minutes | ~10 minutes |
| 99.5% availability | ~3.6 hours | ~50 minutes |
| 99.0% availability | ~7.2 hours | ~1.7 hours |

**The mechanism that forces tradeoffs:**
- Budget remaining → ship features, accept some instability
- Budget depleted → feature freeze, reliability work only

Without error budget, reliability and feature velocity are both "important" and neither has leverage. Error budget makes the tradeoff explicit and gives the reliability team standing to say "no new features."

**Error budget consumption triggers:**
- Incident duration × proportion of traffic affected
- Planned maintenance (counts against budget — incentivizes good change management)
- Failed deploys that caused errors

---

## Cascading Failure

The failure pattern that takes down systems, not services:

```
Service A slow (high latency)
  → Service B waits for A (threads held)
  → Service B thread pool exhausted (no threads to serve new requests)
  → Service B unavailable
    → Service C times out waiting for B
    → Service C thread pool exhausted
    → Total outage
```

This happens because of **unbounded waits**: B waits for A with no timeout. One slow dependency fills all threads.

**Three controls:**

**1. Timeouts on every dependency call.**
Every HTTP call, every DB query, every Redis operation needs a timeout. The timeout should be lower than your own SLO response time. If your SLO is p99 < 200ms and you have 3 downstream calls, each dependency gets a ~50ms timeout — not "default" (which is usually infinite or 30 seconds).

**2. Circuit breakers on high-fanout dependencies.**
When a dependency is failing, stop sending requests to it immediately — don't wait for each request to time out. Circuit breaker opens after N consecutive failures, rejects requests fast (fast-fail vs slow timeout), half-opens after a cooldown to probe recovery.

Circuit breaker states:
- **Closed** (normal): requests pass through
- **Open** (failing): requests rejected immediately, no calls to dependency
- **Half-open** (probing): one request allowed through; if it succeeds, close; if not, re-open

**3. Bulkheads (separate thread pools per dependency).**
If all dependencies share one thread pool, one slow dependency starves all others. Dedicate thread pools per downstream service. Service B's slowness cannot exhaust the thread pool used for Service C.

---

## Degradation Posture

When a dependency fails, three options. Choose based on: how important is this data? How stale is acceptable?

| Option | What it does | When to use |
|--------|-------------|-------------|
| **Fail fast** | Return error immediately | Dependency is critical and no substitute exists; stale data is worse than no data |
| **Degrade gracefully** | Return cached or partial data | Stale data is acceptable; user experience is better with approximate answer than error |
| **Queue for retry** | Accept the request, process when dependency recovers | Write operation; losing the request is worse than delayed processing |

**Degradation is not a fallback you design last.** It is a first-class design decision made when you design the happy path. For every dependency: "If this is down, what does my service do?"

**Degradation responses in practice:**
- Search service → Elasticsearch down → return cached results from Redis with staleness indicator
- Product page → pricing service slow → return last-known price with "price may have changed" note
- Checkout → payment processor down → fail fast with "payment unavailable, try again shortly"
- Order write → DB slow → queue for retry (cannot lose the write)

---

## The Minimum Monitoring Set

Four categories. Without these, you cannot answer "is the service healthy?" or "what is breaking?"

**1. Your SLIs**
- Request latency (p50, p95, p99) — histograms, not averages
- Error rate (5xx / total, per endpoint)
- Availability (uptime probe)

**2. Dependency health**
- Response time and error rate for each downstream service
- DB connection pool utilization (near-full pool is pre-failure signal)
- Redis hit/miss rate and latency
- Queue consumer lag (how far behind is the consumer from the producer?)

**3. Queue depth and age**
- Current depth per queue
- Age of oldest unprocessed message (depth can look fine if one old message is stuck)
- DLQ depth (anything > 0 is a signal)

**4. Error budget remaining**
- Current SLO attainment vs target
- Budget consumed this period
- Burn rate (if you're burning 10x normal rate, you'll exhaust budget before the period ends)

If you don't have these four categories instrumented, start here before adding any other monitoring.

---

## Decision Table: Degradation

| Dependency fails | Data freshness requirement | User impact if degraded | Decision |
|-----------------|--------------------------|------------------------|----------|
| Not critical path | Stale OK (minutes) | Minimal | Degrade gracefully — serve from cache |
| Not critical path | Stale OK (hours) | None | Queue for retry |
| Critical path | Must be fresh | High | Fail fast with clear error |
| Write operation | N/A — must persist | High if lost | Queue for retry |
| Critical path | Stale marginally OK | Medium | Degrade with staleness indicator |

---

## Anti-patterns

**No timeout on database queries.** One slow query holds a thread. 20 slow queries hold all threads. DB timeouts are not optional — they are the load-shedding mechanism that keeps your thread pool from being the bottleneck when DB degrades.

**Circuit breaker with no fallback.** You break the circuit and return 500. From the user's perspective, that's the same as the timeout you just avoided — you just made it faster. A circuit breaker without a degradation strategy is not a reliability improvement; it's a latency improvement. The user still gets an error.

**SLO set at "100% uptime."** Impossible. Means nobody takes reliability seriously because the target can't be met. A 100% SLO also means there's no error budget — no tolerance for any failure anywhere, which paralyzes deployment and change management.

**Monitoring only the happy path.** Your dashboards show success rates and green latency while the queue is 10,000 messages deep and aging out. Monitor what breaks, not what works.

**Timeout set equal to or longer than your SLO.** If your SLO is 200ms and your downstream timeout is 30 seconds, the timeout never triggers before you've already violated your SLO. Timeouts must be tuned relative to your own latency budget.

---

## Šta da pitaš AI

**For cascade analysis:**
> "Service A calls services B, C, D. B is responding in [X ms] instead of [Y ms]. Walk through the cascade failure: what fills up at each layer? What does the user see? What metrics spike first? Then tell me what timeouts, circuit breakers, and bulkheads I should add and at which layer."

**For SLI/SLO instrumentation:**
> "Our SLO is [availability/latency/error rate target]. What are the specific SLIs I need to measure it? For a Symfony API with Postgres and Redis, what instrumentation do I add and where? Show me the Prometheus metrics and alert rules."

**For degradation design:**
> "Dependency [X] just went down. My service does [describe function]. Walk through each degradation option — fail fast, degrade gracefully, queue for retry. What does the user get in each case? What are the risks of each? Which would you recommend given [your constraints]?"

**For error budget:**
> "Our SLO is [X]. We had an incident that caused [Y minutes] of [Z% error rate]. How much error budget did that consume? At our current burn rate, when do we exhaust the monthly budget? What does that trigger for our team?"
