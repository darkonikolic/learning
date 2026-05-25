# Architect thinking framework

The shift from senior engineer to architect is not about knowing more technology. It is about changing what question you ask first.

Senior engineer: "How do I build this?"
Architect: "Should we build this, and if so, which version of it, given what we cannot change?"

---

## Constraints-first

Before proposing any solution, list what constrains the solution space. Engineers jump to solutions. Architects start with constraints because a solution that violates a constraint is not a solution.

**Constraint categories to always audit:**

| Category | Examples |
|---|---|
| Team | 2 backend devs, no dedicated ops, no Kubernetes experience |
| Ops maturity | Manual deploys, no observability beyond logs, no on-call rotation |
| Existing stack | Symfony API, Go worker, Postgres 14, Redis, RabbitMQ |
| Budget | No new paid services, or $X/month ceiling |
| Compliance | GDPR data residency, PCI scope, audit trail requirements |
| Timeline | Must ship in 6 weeks, cannot touch payment flow before Q4 |
| Reversibility | API contract already published to 3 clients, cannot break it |

**Rule:** Any option that violates a hard constraint is eliminated before evaluation. Write the constraints down before opening your editor or talking to AI. If you cannot list at least 4 constraints, you have not understood the problem.

---

## Failure-first thinking

For any design, the first question is: "What breaks first and under what conditions?" — not "does this work?"

Happy-path thinking produces systems that work in demos and fail in production. Failure-first thinking produces systems that degrade gracefully.

**For every component, ask three questions:**
1. What is the failure mode? (not "if it fails" — it will fail, ask how)
2. What does the user observe when this happens?
3. What does the system do without human intervention?

**Applied to the reference stack:**

| Component | Failure mode | User observes | System behavior without intervention |
|---|---|---|---|
| RabbitMQ queue | Queue full (backpressure) | API returns 503 or hangs | Messages dropped or publisher blocks |
| Go worker | Crash mid-processing | Order stuck in "processing" | No retry unless supervisor restarts |
| Postgres | Slow queries (not down) | API latency spike, timeouts | Connection pool exhausted, cascading timeout |
| Redis | OOM eviction | Cache misses, DB spike | Depends on eviction policy — silent failure |

Design decisions flow from this table, not from the happy path. If the worker crashes mid-processing, you need idempotent message handling and dead-letter queues before you need anything else.

---

## Options before decisions

Never propose one solution. Always produce 2–3 options with explicit tradeoffs. The decision belongs to you or your team. The options are the architect's core contribution.

**Format for each option:**

```
Option N: [Name]
What it is: one sentence
Cost: implementation time, infrastructure cost, ops overhead
What it forecloses: what you can no longer do easily if you pick this
Risk: what can go wrong with this choice
```

**Why "do nothing" is always an option:** it is often the correct one. Naming it forces an honest comparison. If "do nothing" is obviously worse, you can show that. If it is not obviously worse, you have found a scope problem.

---

## Reversibility as a dimension

Every architectural decision sits on a spectrum from fully reversible to effectively irreversible.

**Reversible (default to these when uncertain):**
- Adding a new API endpoint (does not break existing clients)
- Adding a new queue consumer (additive)
- Adding a Redis cache layer in front of Postgres
- Changing internal service configuration

**Irreversible (require explicit justification):**
- Postgres schema changes that remove or rename columns used by multiple consumers
- Published API contracts (once clients depend on them, you own them)
- Data model decisions that split or merge tables at scale
- Choosing a message format for an event stream other services consume
- Infrastructure choices that create vendor lock-in

**Practice:** Before finalizing a decision, ask: "If we discover this is wrong in 6 months, what does it cost to undo?" If the answer is "a coordinated multi-team migration and potential downtime," that is an irreversible decision. Treat it accordingly — slow down, write the ADR, get more input.

---

## The 3-year test

"Will the team that inherits this system in 3 years understand why this decision was made?"

This is not about documentation for its own sake. It is a quality check on the decision itself. If you cannot explain a decision clearly enough for a future engineer to understand the constraints you faced, one of two things is true:

1. The decision is not well-reasoned — you made it for unstated reasons (familiarity, momentum, "everyone does it this way")
2. The decision is fine but needs an ADR

Use this as a filter. If a decision fails the 3-year test and you cannot write a clear ADR for it, reconsider the decision before writing anything down.

---

## Decision-making process (step by step)

1. **Gather constraints** — list what cannot change before anything else. Budget, team, stack, compliance, timeline, reversibility constraints. Minimum 4.

2. **State the problem precisely** — one sentence, observable outcome. Not "improve performance." Instead: "The Go worker fails to process all orders within 30 seconds during peak load of 500 orders/minute, causing user-visible stuck orders."

3. **Generate 2–3 options including "do nothing"** — each option should be distinct, not variations of the same approach. If your three options are all "use a different queue," you have not generated real options.

4. **For each option:** cost (time and money), what it forecloses, what it risks. Fill in the format above. No option is presented without all three.

5. **Make a decision and write an ADR** — the ADR records: what was decided, why, what was rejected and why, and what would change the decision. Date it.

---

## Anti-patterns

**"The modern way to do this is X"** — Modernness is not a constraint. It is not a reason. RabbitMQ is "older" than Kafka. It is also the right choice for most teams under 20 engineers. Defend choices with constraints, not with currency.

**Designing for scale you do not have** — Designing a Symfony API for 10,000 requests/second when current peak is 50 is engineering theater. It costs real complexity for imaginary load. Scale when you have evidence of need.

**Solving the problem you imagine instead of the problem you have** — "Users complain about slowness" does not mean the database is slow. Measure before designing. State the observable problem in step 2 before generating options.

**One option presented as "the only reasonable choice"** — This is either groupthink, salesmanship, or incomplete thinking. If you truly cannot generate a second option, you do not understand the problem space well enough yet.

**Premature abstraction** — Building a plugin system, an event bus, or a generic framework before you have two concrete use cases. Wait for the second use case before abstracting. This applies to microservice splits: one service split is speculative, three service splits with a shared pain point is architecture.

**Consensus by exhaustion** — Holding design discussions until the most vocal person wins is not a decision process. Options + criteria + explicit decision is.

---

## What to ask AI

These prompts get architectural output, not tutorial output.

**For generating options:**
> "Given these constraints: [list them explicitly], what are 3 options for [state the problem precisely]? For each option: implementation complexity (days), operational overhead (ongoing), what it forecloses, and what would make it the wrong choice."

**For failure-first analysis:**
> "Given this design: [Symfony API → RabbitMQ → Go worker → Postgres], what are the top 3 failure modes? For each: how does it manifest to the user, does the system recover without intervention, and what is the minimal mitigation?"

**For reversibility check:**
> "I am deciding between [option A] and [option B]. Which decision is harder to reverse in 18 months and why? What would make it irreversible?"

**For the 3-year test:**
> "Here is my proposed ADR: [paste it]. What constraints or reasoning am I missing that a future engineer would need to understand this decision?"

**For constraint discovery:**
> "I need to add [feature] to a Symfony API + Go worker + Postgres + Redis stack with a team of 3. What constraints am I likely not thinking about that typically eliminate options in this scenario?"

---

## ADR format (minimal)

```markdown
## ADR-NNN: [Title]

**Date:** YYYY-MM-DD
**Status:** Accepted

**Context:**
[One paragraph: what problem, what constraints, what was the forcing function]

**Decision:**
[What we decided, one sentence]

**Options considered:**
- Option A: [why rejected]
- Option B: [why rejected]
- Option C (chosen): [why chosen]

**Consequences:**
[What this enables, what this forecloses, what would change this decision]
```

The ADR is not bureaucracy. It is the artifact that makes the 3-year test passable.
