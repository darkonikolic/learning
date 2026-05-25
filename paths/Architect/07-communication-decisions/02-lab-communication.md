# Lab: Communication and Decisions

Write the artifacts. Generic answers are wrong answers — use the system context (Symfony API + Go worker + Postgres + Redis + queue).

---

## Exercise 1: Write an ADR

**Decision to document:** Adopt the outbox pattern for the `order-placed` event in the e-commerce system.

**Background facts to incorporate:**

- Currently: `OrderService::placeOrder()` writes to Postgres and publishes to RabbitMQ in two separate operations
- The failure window between the two operations has caused missed events in staging (twice in the last sprint)
- The queue is the source of truth for downstream services: fulfillment, notifications, analytics
- An order that succeeds but whose event is never published causes a silent failure — no error, just a missing fulfillment record
- Alternatives you considered: two-phase commit (XA transactions), dual-write with reconciliation job, change data capture (Debezium)

**Write the full ADR using this template:**

```markdown
# ADR-{number}: {Title as a decision, not a topic}

**Status:** {Proposed | Accepted | Superseded}

## Context
{What is the situation? What are the constraints? What is the cost of not deciding?}

## Decision
{One sentence.}

## Consequences
**Better:** {What improves}
**Worse:** {What gets harder — be honest}
**Required:** {What must now be built, learned, or changed}

## Alternatives Considered
- **{Option A}:** {Why not chosen — specific}
- **{Option B}:** {Why not chosen — specific}
- **{Option C}:** {Why not chosen — specific}
```

**Grading your own ADR:**

- [ ] Title is a decision ("Use X for Y"), not a topic ("Approach to Y")
- [ ] Context states the forcing function — what breaks if we don't act?
- [ ] Decision is one sentence, no hedging
- [ ] Consequences section includes something honest in "Worse"
- [ ] Each alternative has a specific reason for rejection, not "it wasn't the best fit"

---

## Exercise 2: Stakeholder Translation

**Decision to communicate:**

> "We need to migrate from RabbitMQ to Kafka because our consumer group scaling is hitting RabbitMQ's architectural limits at our projected message volume. RabbitMQ deletes messages after acknowledgement; Kafka retains them, allowing replay and multiple independent consumers without queue fan-out configuration. At 500k messages/day with 6 downstream consumers, the operational overhead of RabbitMQ exchange/queue topology is becoming a liability."

**Write 3 versions. Each version: 3-5 sentences.**

**Version 1 — For engineers:**

Cover: what technically changes, what they need to learn, what breaks, what gets better. Be specific about the operational implications (consumer group config, offset management, message retention policy).

**Version 2 — For the engineering manager:**

Cover: cost, timeline, risk, what the team needs to learn, what happens if we don't do this. No jargon. The EM does not need to know what a consumer group is — they need to know what the risk is and what it costs to fix it.

**Version 3 — For CTO or VP Engineering:**

Cover: business risk of not acting, cost horizon of acting, what we're committing to, what we're foreclosing. One sentence on the tradeoff. No queue topology discussion.

**Check:** Could each version stand alone without the others? Would a person in that role understand it without asking follow-up questions?

---

## Exercise 3: Meeting Pressure Drill

**Scenario:**

You recommended PostgreSQL with read replicas over MongoDB for a new feature: a candidate profile search with filtering by skills, location, and availability. You chose Postgres because the data model is relational (candidates have applications, which have statuses, which link to jobs), the team knows SQL, and read replicas give you sufficient read scaling.

Your CTO says in the architecture review:

> "I've read that MongoDB scales much better for this kind of flexible document data. Why are we not using it?"

**Part A: Write your response (3-5 sentences)**

Requirements for the response:
- Acknowledge the CTO's point before disagreeing (don't open with "actually")
- State the specific constraint that makes MongoDB a worse choice for this system
- Do not say MongoDB is bad — say why Postgres fits better given what we have
- End with something that closes the challenge, not opens a debate

**Part B: Write the ADR addition**

Write 3-5 sentences to add to the "Alternatives Considered" section of your ADR that would have pre-empted this question.

Format:

```markdown
- **MongoDB:** {Why not chosen — specific to this system's constraints}
```

---

## Example ADR (Reference — Different Decision)

Use this to calibrate format, not content. Write your own ADR for Exercise 1.

```markdown
# ADR-009: Deploy Redis as the session store for Symfony API

**Status:** Accepted

## Context
Symfony API runs on 3 horizontally scaled app servers. PHP file-based sessions are local
to each server. Sticky sessions (load balancer session affinity) are currently used as a
workaround, but this creates uneven load distribution and breaks during deployments when
instances are replaced. Redis is already in the stack for caching.

## Decision
We will configure Symfony to store sessions in Redis using the existing Redis cluster,
with a 2-hour TTL matching the current session lifetime.

## Consequences
**Better:** Sessions survive app server restarts and deployments. Load balancer can use
round-robin without sticky sessions. Deployment downtime for sessions eliminated.
**Worse:** Redis becomes a hard dependency for authenticated requests. Redis failure means
all sessions are lost. Must ensure Redis is included in the high-availability plan.
**Required:** Symfony session handler configuration change. Redis connection pool sizing
review (sessions add ~1KB per active user). Runbook update for Redis failure scenario.

## Alternatives Considered
- **Sticky sessions (status quo):** Does not survive deployments — sessions lost on instance
  replacement. Causes load imbalance when one user has a heavy session. Not viable at scale.
- **Database session store (Postgres):** Works but adds load to Postgres for every
  authenticated request. Redis is faster and already in the stack for this type of workload.
- **JWT stateless auth:** Would eliminate session storage entirely. Estimated 3-sprint
  migration effort. Token revocation requires a blocklist (same Redis infrastructure anyway).
  Disproportionate cost for a deployment friction problem.
```

---

## Self-Check

**Exercise 1:**
- [ ] ADR title is a decision, not a topic
- [ ] Context includes the two staging incidents as the forcing function
- [ ] "Worse" includes the latency cost and the new worker to operate
- [ ] Two-phase commit alternative explains specifically why it was rejected (hint: Postgres and RabbitMQ don't share a transaction coordinator)

**Exercise 2:**
- [ ] Engineer version mentions consumer group offset management or message retention — something technically specific
- [ ] EM version has no acronyms that weren't explained
- [ ] CTO version is one business risk sentence, one cost sentence, one commitment sentence — no topology discussion

**Exercise 3:**
- [ ] Part A opens by acknowledging the point before disagreeing
- [ ] Part A mentions the relational join requirement or existing team SQL knowledge as the specific constraint
- [ ] Part B is written as "MongoDB: [specific reason]" not "MongoDB was not chosen because it wasn't the right fit"
