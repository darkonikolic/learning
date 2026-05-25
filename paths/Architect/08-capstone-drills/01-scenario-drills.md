# Capstone Drills: Scenario-Based Practice

Six scenarios drawn from the full spine (Symfony API + Go worker + Postgres + Redis + queue). Each asks you to produce specific outputs before reading the good answer. Self-evaluate: if your answer matches the structure and reasoning, not just the words, you're on track.

---

## Scenario 1: "The CTO Wants Microservices"

**Situation**
Your Symfony monolith handles 200 req/s at peak. Team has 4 engineers. Response times are fine. The CTO read an article about Netflix and wants to "modernize the architecture with microservices." You think this is the wrong move.

**Produce**
1. The 3 constraints you'd state that push back on this.
2. A counter-proposal: what you'd suggest instead.
3. The one condition under which you'd agree to split.

**What to ask AI**
```
We have a Symfony monolith, 4 engineers, 200 req/s peak, no scaling or ownership pain.
Leadership wants microservices. Give me the three strongest constraint-based arguments
against splitting now, framed for a non-technical executive.
```

```
What specific operational costs does a team of 4 incur when moving from a monolith
to microservices? Be concrete: CI/CD, observability, on-call, deployment coordination.
```

**Good answer includes**
- Conway's Law stated explicitly: 4 engineers will produce a distributed monolith, not independent services, because communication paths don't map to service ownership
- Operational cost itemized: separate deploys, distributed tracing, inter-service auth, network failure modes — each adds work without team to absorb it
- The problem microservices solve (independent scaling, independent deployability per domain, separate failure domains) is not a problem you currently have
- Counter-proposal: modular monolith — enforce domain boundaries inside the codebase via namespace conventions and no cross-domain direct DB access
- The one condition: a single domain needs to scale independently AND has a clearly separate ownership boundary. Not "because the CTO read an article."

---

## Scenario 2: "Postgres Is Too Slow"

**Situation**
An engineer escalates: "Postgres is our bottleneck. We need to switch to Cassandra." No profiling data exists. The Go worker that processes orders is experiencing latency spikes under load.

**Produce**
1. The 5 things you'd measure before agreeing to any infrastructure change.
2. The diagnosis sequence using the USE method (Utilization, Saturation, Errors).
3. The earliest point at which Cassandra becomes the right answer.

**What to ask AI**
```
A Postgres instance is showing latency spikes under load. I have no profiling data yet.
Give me a prioritized diagnostic checklist, starting from the cheapest checks (query analysis)
before any infrastructure change. Include specific queries or tools for each step.
```

```
Apply the USE method to Postgres latency diagnosis. For each of Utilization, Saturation,
and Errors, what metric do I look at and what threshold signals a problem?
```

**Good answer includes**
- Measure first: (1) slow query log / `pg_stat_statements` — are specific queries responsible? (2) index coverage — run `EXPLAIN ANALYZE` on the hot queries (3) connection pool saturation — are workers waiting for connections? (4) disk I/O — are you hitting read amplification? (5) table bloat / dead tuples — when was `VACUUM` last run?
- USE sequence: Utilization = CPU %, I/O wait, connection count vs `max_connections`; Saturation = query queue depth, replication lag; Errors = lock waits, deadlocks, checkpoint warnings
- Cassandra is the right answer only when: query patterns are genuinely write-heavy at scale where Postgres write amplification is proven, data is wide-row or time-series shaped, and you've exhausted read replicas, connection pooling (PgBouncer), and index tuning. Not before.
- "Switching databases" is never the first answer. Missing index is.

---

## Scenario 3: "We Lost Messages in the Queue"

**Situation**
3am. Orders were placed but fulfillment never triggered. Root cause: the Go worker was restarted mid-processing — it had consumed messages off the queue but hadn't committed the fulfillment action to Postgres before the restart.

**Produce**
1. Immediate triage steps (what do you do right now).
2. Root cause hypothesis: what exactly broke and why.
3. The architectural change that prevents recurrence.
4. What you'd write in the postmortem.

**What to ask AI**
```
A queue consumer was restarted mid-processing. Messages were dequeued but downstream
actions were not completed. Walk me through a root cause analysis and the architectural
patterns that prevent this failure class.
```

```
Explain the transactional outbox pattern. When does it apply, what does it guarantee,
and what are its implementation costs in a Symfony + Postgres + RabbitMQ stack?
```

**Good answer includes**
- Triage: identify which orders are in the gap (placed_at timestamp range where queue consumer was down), check Postgres for fulfillment records vs order records, replay or manually process missing orders
- Root cause: at-least-once delivery was not implemented — the worker ACKed or auto-ACKed before processing was durable. Restart lost in-flight work.
- Architectural change: (1) move to manual ACK — only ACK after the fulfillment write commits to Postgres; (2) implement idempotency key on fulfillment so replayed messages don't double-process; (3) add a Dead Letter Queue for messages that fail repeatedly so they don't disappear; (4) for the full solution, transactional outbox — write event to outbox table in same transaction as the originating change, separate relay publishes to queue
- Postmortem: state the failure (not blame), identify the assumption that broke (processing is atomic with consumption), name the mitigation, give timeline for implementation

---

## Scenario 4: "New Feature That Breaks the Architecture"

**Situation**
Product wants real-time inventory counts on the product listing page. Current architecture: inventory stored in Postgres, page queries DB on load. Requirement: inventory updates visible across 50k product listings within 100ms of a stock change.

**Produce**
1. Why the current architecture cannot satisfy this requirement.
2. Three options with tradeoffs.
3. The option you'd recommend and why.

**What to ask AI**
```
I need to push inventory updates to 50k product listing pages within 100ms of a stock change.
Current setup: Postgres source of truth, pages query on load. Give me 3 architectural options
with explicit tradeoffs on consistency, infrastructure cost, and implementation complexity.
```

```
Compare Redis pub/sub, SSE (Server-Sent Events), and WebSockets for pushing real-time
inventory updates to a browser. I have a Symfony backend and 50k concurrent product pages.
What breaks at scale for each?
```

**Good answer includes**
- Why current architecture fails: polling at 100ms interval across 50k pages = 500k queries/second. DB will not survive it. Even 1s polling is 50k q/s. This is a push problem, not a query optimization problem.
- Option A — Redis cache + event invalidation: inventory change writes to Postgres and publishes invalidation event, Symfony reads from Redis cache on page load, Go worker updates cache on event. Tradeoff: cache staleness window, added complexity, but solves DB pressure. Read path stays fast.
- Option B — SSE from Symfony: browser holds open connection, server pushes inventory deltas on change. Tradeoff: connection count at 50k concurrent is real infrastructure cost, but low latency and no polling. Correct for truly real-time.
- Option C — WebSockets via dedicated service: same push semantics as SSE but bidirectional. Overkill unless you already need bidirectional comms. Higher complexity for same result.
- Recommendation: Redis cache with invalidation for inventory reads (solves the query pressure), SSE for the real-time push to browser only on pages actively being viewed. Don't hold 50k connections open for users who aren't looking at the page.
- The wrong answer: "we'll add an index and query faster." This is a throughput problem at the DB layer, not a latency problem.

---

## Scenario 5: "Stakeholder Doesn't Trust the Decision"

**Situation**
You've proposed the transactional outbox pattern to ensure reliable event publishing. In the design review, a senior engineer says: "This is over-engineering. We've shipped this system for two years without it. You're solving a problem we don't have."

**Produce**
1. Your in-meeting response (3-5 sentences, out loud).
2. What you'd add to the ADR.
3. The condition under which the senior engineer is right.

**What to ask AI**
```
Help me write a non-defensive response to "this is over-engineering" when proposing
the transactional outbox pattern. The audience is a senior engineer who hasn't seen
the failure this pattern prevents. I need to name the specific failure clearly.
```

```
Write the "Considered Alternatives" and "Consequences" sections of an ADR for adopting
the transactional outbox pattern. Include the explicit failure case the pattern prevents
and the cost of implementing it post-incident vs now.
```

**Good answer includes**
- In-meeting response: name the specific failure (not "reliability" — "an event fails to publish after the DB write commits, because they're not in the same transaction; the order exists in Postgres but the fulfillment queue never sees it"). Acknowledge it hasn't happened. State the cost to implement now (one outbox table, one relay process) vs after the incident (data reconciliation, customer impact, incident cost). Don't argue. Give the engineer a way to agree without losing face.
- ADR addition: "Rejected alternative: fire-and-forget publish after DB commit. Risk: partial failure leaves system in inconsistent state with no recovery path. Cost of mitigation post-incident exceeds implementation cost now."
- When the senior engineer is right: if the service publishes events that are informational only (no downstream state change depends on them), at-least-once delivery with occasional loss is acceptable. The outbox is overhead if the subscriber can tolerate gaps. State this in the ADR explicitly.

---

## Scenario 6: "Design a New System from Scratch"

**Situation**
Design a job application tracking system. Employers post jobs. Applicants apply. Both sides can message each other. Rough scale: 10k new jobs/day, 100k applications/day, high-volume messaging.

**Produce**
1. Constraints you'd gather before designing anything.
2. Components and their boundaries.
3. Storage decision for each data type.
4. The one async boundary you'd introduce first and why.
5. The SLO you'd propose for job search.

**What to ask AI**
```
Before designing a job application tracking system, what constraints should I gather
from stakeholders? Give me a list organized by: scale, consistency requirements,
operational constraints, and non-functional requirements.
```

```
I'm designing a system with 10k jobs/day, 100k applications/day, and high-volume
messaging between employers and applicants. Identify the three subsystems most likely
to have independent scaling or failure characteristics, and explain why splitting them
makes sense at this scale.
```

```
Compare Postgres, Elasticsearch, and a dedicated search service for job search at
10k new documents/day. What query patterns drive the decision, and at what scale
does Postgres full-text search become insufficient?
```

**Good answer includes**
- Constraints to gather: read/write ratio per subsystem (search is read-heavy, messaging is write-heavy), consistency requirement per operation (is a missed message acceptable? Is a double-application a problem?), existing infrastructure, team size and operational capacity, SLA per user-facing feature
- Components: (1) Job service — CRUD for job listings, search index; (2) Application service — tracks application state machine; (3) Messaging service — high-volume, append-only, separate from structured data; (4) Notification service — fan-out of events to email/push
- Storage decisions: jobs in Postgres + Elasticsearch for search; applications in Postgres (structured, relational, low write volume relative to read); messages in Postgres partitioned by conversation or a dedicated append-only store (messages are immutable, high write volume, accessed by range); Redis for session, rate limiting, notification deduplication
- Async boundary: application submission triggers downstream processing (employer notification, matching, analytics) via queue. This is the highest-volume write path and the downstream steps do not need to be synchronous with the HTTP response. Decoupling here prevents application submission latency from being coupled to notification infrastructure.
- Search SLO: p99 < 200ms for job search queries, 99.5% availability. Justify why: search is the primary acquisition path; degraded search = users leave. Index staleness acceptable at 60s (new job visible within 1 minute of posting).
- Demonstrates constraints-first: you cannot design the storage until you know the query patterns. You cannot design the async boundary until you know the consistency requirement per operation.
