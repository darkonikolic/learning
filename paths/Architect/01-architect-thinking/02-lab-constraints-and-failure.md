# Lab: Constraints audit and failure-first design

Two exercises. Do Exercise 1 before reading the example answers. Do Exercise 2 before comparing against the failure table.

---

## Exercise 1: Constraints audit

**Scenario:** "We need to add real-time notifications to our Symfony + Go worker app. Users should see when their order status changes."

This is a real request from a stakeholder. Before proposing anything, your job is to audit the constraints.

### Step 1 — Fill the constraints template

Copy this template. Fill it in before reading further.

```
CONSTRAINTS AUDIT
=================
Problem statement (one sentence, observable outcome):


Team constraints:
- Team size:
- Ops experience:
- On-call / alerting setup:

Stack constraints:
- Current stack:
- What we cannot change:
- Existing client contracts (API consumers):

Infrastructure constraints:
- Hosting model (bare metal / managed / k8s):
- Current monitoring:
- Budget ceiling for new services:

Compliance / data constraints:
- Data residency:
- PII in notifications:
- Audit requirements:

Timeline constraints:
- Hard deadline:
- What must not be disrupted:

Reversibility constraints:
- Which decisions here are hard to undo:
```

**Minimum 6 constraints before proceeding.** If you have fewer than 6, you have not understood the problem.

### Step 2 — Generate 3 options

With constraints filled in, generate 3 options for delivering real-time order status notifications.

For each option:
- Name it
- One sentence: what it is
- Implementation complexity (days, rough)
- Ops overhead (ongoing)
- What it forecloses
- Which constraints eliminate it (if any)

### Step 3 — Eliminate options by constraints

For each option, mark: **VIABLE**, **ELIMINATED BY [constraint]**, or **RISKY — requires [mitigation]**.

---

### Example answers — Exercise 1

Read only after completing your own audit.

**Plausible constraints for this scenario (assuming a 3-person team, no dedicated ops):**

1. Team has no experience operating WebSocket servers at scale — SSE or polling is lower ops risk
2. Stack is Symfony (PHP) + Go worker; no Node.js or dedicated realtime service in production
3. No current on-call rotation — silent failures in push channels will not be noticed quickly
4. GDPR applies — notification payload cannot leak order details from other users (multi-tenant check)
5. RabbitMQ already in stack — event publishing is already possible without new infrastructure
6. API already has Symfony consumers; changing the API contract for websocket upgrade would break existing clients
7. Timeline: 6 weeks — no time to introduce and stabilize a new managed service (e.g., Pusher, Ably)
8. Budget: no new paid services approved this quarter

**Three options:**

**Option A: Server-Sent Events (SSE) from Symfony API**
- What it is: Long-lived HTTP connections from the browser to a Symfony endpoint that pushes events
- Complexity: 3–5 days
- Ops overhead: Connection count monitoring, PHP worker limits (fpm config), sticky sessions if load balanced
- Forecloses: Easy horizontal scaling (SSE connections are stateful per server)
- Constraint check: RISKY — fpm worker exhaustion under load; manageable with low user count

**Option B: Polling from the frontend every 5–10 seconds**
- What it is: Frontend calls a Symfony endpoint to fetch latest order status
- Complexity: 1 day
- Ops overhead: Minimal; just another API endpoint with Redis cache
- Forecloses: True real-time (5–10 second lag); not viable if latency requirement is sub-second
- Constraint check: VIABLE if latency requirement is "near real-time" not "instant"

**Option C: Managed WebSocket service (Pusher/Ably)**
- What it is: Events published from Go worker → managed push service → browser via WebSocket
- Complexity: 3–4 days
- Ops overhead: External dependency, vendor account management, cost per connection
- Forecloses: Full control of delivery guarantees, cost scaling
- Constraint check: ELIMINATED — budget constraint (no new paid services this quarter) + timeline risk of new vendor onboarding

**Result:** Option C is eliminated by constraints. Option B is viable immediately. Option A is viable with a risk mitigation note on fpm capacity. This is an architect's output — not "we should use WebSockets."

---

## Exercise 2: Failure-first design

**Given stack:** `Symfony API → RabbitMQ queue → Go worker → Postgres`

For each component below, answer all three questions before reading the failure table.

**Questions for each component:**
1. What is the failure mode?
2. What does the user observe?
3. What does the system do without human intervention?

**Components to analyze:**
- Queue full (RabbitMQ backpressure / max-length reached)
- Go worker crashes mid-processing
- Postgres slow (not down — queries taking 5–30x normal time)
- Symfony API timeout on queue publish (RabbitMQ unreachable or slow ACK)

Fill in this table:

```
FAILURE TABLE
=============
| Component                  | Failure mode | User observes | System behavior (no human) |
|----------------------------|--------------|---------------|----------------------------|
| Queue full                 |              |               |                            |
| Go worker crash mid-proc   |              |               |                            |
| Postgres slow (not down)   |              |               |                            |
| API timeout on publish     |              |               |                            |
```

---

### Failure table — example answers

Read only after completing your own table.

| Component | Failure mode | User observes | System behavior without intervention |
|---|---|---|---|
| Queue full | RabbitMQ hits max-length; publisher gets channel error or message rejected | API returns 500 or hangs (depending on publish timeout config); order appears to not submit | Without dead-letter queue: messages dropped silently. With DLQ: messages routed to DLQ, still not processed. Queue does not self-drain. |
| Go worker crash mid-processing | Worker process exits during message processing (panic, OOM, signal) | Order stuck in "processing" state indefinitely | Message is un-acked, returns to queue after visibility timeout (if configured). Without requeue config: message lost. With supervisor restart: worker restarts but same message may reprocess — requires idempotency. |
| Postgres slow (not down) | Long-running queries block connection pool; pool exhausts | API latency spikes; requests start timing out; users see errors on read-heavy pages first | Connection pool fills; new requests queue then fail. Read replica (if exists) may absorb reads. Without intervention: cascading timeout — API, worker, everything that touches DB starts failing. Self-recovery: only if slow queries finish and pool drains. |
| API timeout on publish | Symfony cannot reach RabbitMQ (network partition, RabbitMQ restart, slow ACK) | Order submission fails; user sees error or spinner timeout | Without circuit breaker: every API request that publishes hangs for full timeout (e.g., 30s), exhausting PHP-FPM workers rapidly. With circuit breaker: fast fail after threshold, returns 503. Without either: full API degradation within seconds at moderate load. |

---

### What the failure table tells you

Each row is a design requirement, not just an observation.

**Queue full** requires:
- Dead-letter queue configuration
- Max-length policy that rejects (not silently drops)
- Alerting on queue depth before it hits max

**Worker crash mid-processing** requires:
- Idempotent message processing (safe to reprocess)
- Message requeue on worker crash (RabbitMQ nack + requeue=true)
- Dead-letter queue for messages that fail repeatedly
- Supervisor or container restart policy

**Postgres slow** requires:
- Connection pool sizing with a ceiling (pgBouncer or application-level)
- Query timeout at the application layer (not just DB)
- Alerting on pool saturation, not just query count
- Separate read replica for read-heavy operations if write-path isolation matters

**API timeout on publish** requires:
- Publish timeout configured short (500ms–1s, not 30s)
- Circuit breaker on the RabbitMQ client
- Fallback: synchronous DB write to an outbox table if publish fails
- Or: accept the 503 and let the client retry — simpler, fewer moving parts

None of these are optional polish. They are the system. The happy path is already obvious. This table is the architecture.

---

## Debrief checklist

After both exercises, check:

- [ ] Did you fill in constraints before generating options?
- [ ] Did any of your options get eliminated by your own constraint list?
- [ ] Is your problem statement one sentence with an observable outcome?
- [ ] Does your failure table have a row for each component, not just the most obvious one?
- [ ] Did the failure table change any of your option choices from Exercise 1?

If the failure table changed your options: good. That is the point. Failure-first analysis is a design input, not a retrospective.

---

## What to ask AI for these exercises

**Constraint discovery:**
> "I need to add real-time order status notifications to a Symfony + Go worker app. Team size: 3. No dedicated ops. Stack: Symfony, Go, Postgres, Redis, RabbitMQ. What constraints am I likely overlooking that would eliminate options before I evaluate them?"

**Option generation:**
> "Given these constraints [paste list], generate 3 options for real-time order notifications. For each: implementation complexity in days, ops overhead, what it forecloses, and which of my constraints eliminates it."

**Failure analysis:**
> "For this stack: Symfony API → RabbitMQ → Go worker → Postgres, give me a failure table. For each component: the realistic failure mode, what the user observes, and what happens without human intervention. Include Postgres slow (not down) as a distinct case from Postgres down."

**Turning the failure table into requirements:**
> "Here is my failure table: [paste it]. For each failure mode, what is the minimal mitigation that a 3-person team with no dedicated ops can actually maintain? Rank by user impact."
