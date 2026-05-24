# Architecture ownership

**Unit:** `02` of final lab (week 2 focus).

**Theme:** Architecture comes **before** code at scale. Narrate how data and responsibility move through the payment platform.

### Reference flow (illustrative)

Payment API → **RabbitMQ** → **worker** (Go) → **MySQL** → **audit** trail → **notifications**

### What the architecture pack must include

**Tradeoffs** — at least two plausible shapes (e.g. choreography vs orchestration, sync edge vs async core) with a chosen path and why  

**Risks** — scaling hotspots, duplicate delivery, partial failure, PSP dependency  

**Failure ownership** — who detects, who compensates, what is “done” after a failed leg  

**Scaling** — coarse capacity story (not slogans): read vs write paths, queue depth, DB contention  

**Resilience primitives** — which edges get **circuit breaker**, **bulkhead**, **rate limit** semantics (capacity vs correctness tradeoffs explicit)

### Distributed systems obligations (earn the RabbitMQ/MySQL pairing)

Document brief honest answers—you will implement against them:

**CAP intuition (practical)** — Partition behaviour: does the payments edge favour **availability** + deferred reconciliation vs **consistency strongholds** during splits? Which user-visible guarantees break?  

**Consistency models named** — e.g. *read-your-writes* on command API, **eventual** on notification projection lag tolerances  

**Transactional outbox / inbox** — how domain commits and broker publishes stay **eventually aligned** without dual-write fantasy  

**Saga choreography vs orchestrator** — your refund/inventory saga: compensate steps & **failure ownership per leg**  

**Eventual consistency** — inventory reservation vs PSP capture: ambiguity windows callers must tolerate (surface in API/errors)  

**Circuit breaker / bulkhead / rate limiting** — PSP client, webhook ingress, worker pools: defaults, half-open probes, shedding rules  

Detailed worked mental models plus lab ideas: **`09-enterprise-depth-appendix.md` § Distributed systems.**

### LAB deliverables

**Risk map** (table: risk → likelihood/impact → mitigation → owner)  

**Ownership map** (component / bounded context → deciding team or role)  

**Dependency graph** (services, queues, DB, external PSP—edges labelled with contract type)

### Practice links

Symfony **DDD boundaries** for payment vs refund vs inventory touchpoints.  

Go **worker ownership**: consume, ack/nack, DLQ, idempotency hooks, metrics.

### Checklist

- [ ] Every integration names **timeouts** and **retry class** (transport vs domain) at the edge.  

- [ ] Architecture pack states **partition / broker / DB degraded** behaviours—not only happy path arrows.  

- [ ] **Outbox/inbox story** sketches how you avoid lost or double-published lifecycle events versus DB truth.  
