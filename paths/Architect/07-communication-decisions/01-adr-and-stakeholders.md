# ADRs and Stakeholder Communication

An architecture decision no one understands will be reversed by the next engineer who touches it.

---

## ADR Anatomy

The format that actually gets read and accepted. Every field has a reason.

```markdown
# ADR-{number}: {Decision verb + subject}
# Example: "ADR-007: Use outbox pattern for order event publishing"
# Not: "ADR-007: Event publishing approach"

**Status:** Proposed | Accepted | Superseded by ADR-{N}

## Context
What is the situation that requires a decision?
What constraints exist — technical, organizational, compliance?
What is the cost of not deciding?

## Decision
One clear sentence. "We will use X to solve Y."
Not: "We've decided to evaluate options for..."
Not: "We should consider..."

## Consequences
**Better:** What improves because of this decision.
**Worse:** What gets harder or more expensive. Be honest — a whitewashed ADR is useless.
**Required:** What must now be built, learned, or changed because of this decision.

## Alternatives Considered
For each alternative:
- What it is
- Why we did not choose it (specific, not vague)

An ADR without "Alternatives Considered" is an announcement, not a decision record.
```

**What makes an ADR get accepted vs ignored:**

- Title is a decision, not a topic. "Use X for Y" forces clarity. "Approach to Y" defers it.
- Context explains the forcing function. What happens if we don't decide? ADRs with no urgency get deferred.
- Consequences section is honest. If you only list upsides, engineers distrust it — they know there are tradeoffs.
- Alternatives section shows you thought it through. "We considered X but it has [specific cost we cannot absorb]" builds trust faster than "we chose the best option."

---

## Example ADR

```markdown
# ADR-012: Use PgBouncer for Postgres connection pooling

**Status:** Accepted

## Context
The job marketplace API runs on 4 PHP-FPM servers with 20 workers each (80 direct connections).
At current growth trajectory, we will hit Postgres max_connections (100) within 6 weeks.
Direct connection scaling requires either raising max_connections (increases RAM per connection)
or adding PgBouncer as a multiplexing layer. Raising max_connections is a stopgap with
diminishing returns; PgBouncer is the standard solution for this class of problem.

## Decision
We will deploy PgBouncer in transaction pooling mode in front of Postgres, targeting
20 real Postgres connections from PgBouncer regardless of application connection count.

## Consequences
**Better:** Application servers can open as many connections as needed without Postgres load.
Estimated throughput ceiling increases from ~80 concurrent queries to ~500 queries/s.
**Worse:** Prepared statements and advisory locks do not work in transaction pooling mode.
Any code using these must be refactored before deployment.
**Required:** Audit of Doctrine configuration for prepared statement usage. Update deployment
runbook. Add PgBouncer metrics to monitoring dashboard.

## Alternatives Considered
- **Raise max_connections to 200**: Postgres allocates ~10MB RAM per connection. At 200
  connections that's 2GB RAM consumed by idle connections. This is a stopgap that doesn't
  solve the scaling path — we'd be back here at 10 app servers.
- **Switch to async PHP (Swoole/RoadRunner)**: Would reduce connection count by reusing
  connections across requests. Estimated 2-3 sprint effort to migrate, high risk of
  incompatibility with existing Symfony middleware. Disproportionate cost for this problem.
```

---

## Stakeholder Narrative

The same decision explained differently for different audiences. Same facts, different emphasis. This is not spin — it's communication competence.

**Decision being communicated:** Migrating from synchronous DB writes for order events to the outbox pattern.

---

**For engineers:**

> The current approach writes the order record and publishes the event in separate operations. If the app crashes between the two, the event is lost and downstream services don't get notified. The outbox pattern writes both to Postgres in the same transaction, then a separate process reads the outbox table and publishes to the queue. This guarantees at-least-once delivery. You'll need to write idempotent consumers — that means checking event IDs before processing, because the same event may arrive twice during retry. The outbox poller will be a new Go worker. Doctrine entity writes stay the same; you add an `OutboxEvent` row to the same transaction.

**For the engineering manager:**

> We have a data integrity risk: order events can be silently lost under failure conditions, causing downstream services (fulfillment, notifications) to miss orders. This has happened twice in staging, not yet in production. The fix (outbox pattern) requires 1 sprint to implement, 1 sprint to test and roll out. The tradeoff is a small increase in write latency (~5ms) and a new Go worker to operate. The alternative — living with the risk — means we'll eventually have a production incident where orders are processed but fulfillment isn't triggered.

**For the CTO or VP Engineering:**

> We have a reliability gap: order processing can succeed while order fulfillment silently fails. At current scale this is recoverable manually, but at 10x volume it becomes a support and refund cost. We're addressing it this sprint with an industry-standard pattern (transactional outbox). The cost is 2 sprints of engineering time. The risk of doing nothing scales with our order volume. This closes a known gap before it becomes a customer-visible incident.

---

## The 5-Minute Pitch Format

When you need a decision in a meeting, not a document.

```
"We have [problem].
It's causing [observable business impact — not technical impact].
We have [N] options: [A], [B], [C].
I recommend [X] because [specific reason tied to our constraints].
The main risk is [Y] and we'd mitigate it by [Z].
I need [decision / resource / timeline] by [date]."
```

**What this format does:** gives the decision-maker what they need without requiring them to understand the technical details. The business impact sentence is the load-bearing sentence — if you can't state it, you're not ready to ask for the decision.

**Example:**

> "We have connection exhaustion in Postgres. It's causing request failures at peak traffic, currently in staging — production is 6 weeks away at current growth. We have three options: raise max_connections, add PgBouncer, or reduce PHP-FPM workers. I recommend PgBouncer because it solves the problem permanently without capping our concurrency. The main risk is that it doesn't support prepared statements, and we'd mitigate that by auditing our Doctrine config this week before deploying. I need a decision today so we can start the work this sprint."

---

## Defending Under Pressure

When someone challenges your decision in a meeting.

| Challenge | Response pattern | What not to do |
|---|---|---|
| "Why didn't you consider X?" | "We did. X costs [specific thing] that we can't absorb because [constraint]." | "We didn't think of that" or dismissing it without engaging |
| "This is overengineered" | "The constraint that requires this is [X]. Without it, [failure mode] occurs." | Getting defensive, restating the solution without addressing the concern |
| "Can't we just do Y?" | "Y gives up [specific guarantee] that is non-negotiable for [reason]." | "Y won't work" without explaining what it costs |
| "This will take too long" | "The estimate is [N]. We can descope [optional part] to [N/2] if needed." | Defending the estimate without offering a path |
| "I've read that [other approach] is better" | "For [use case], yes. Our constraint is [X], which changes the tradeoff because [reason]." | Dismissing the source or getting into a credibility contest |

**What to never do:** get defensive, dismiss the challenge, defer without committing to when you'll have an answer. A challenge is information. Treat it as such.

---

## Losing Gracefully

When the decision goes against you.

1. **State your objection on the record.** In the ADR under "Dissenting views" or in the meeting notes. Not to relitigate — to document that the risk was surfaced.
2. **Commit to executing the agreed decision.** Disagreement in discussion, alignment in execution. An architect who undermines decisions they lost is a team hazard.
3. **Note the condition under which you'd revisit.** "If we see [specific signal — error rate, incident type, metric threshold], I'll raise this again." This converts your concern into a monitoring condition, not a standing grievance.

---

## Šta da pitaš AI

- "Here's the context for an architecture decision: [paste context]. Help me write an ADR. Challenge me if the Consequences section is too optimistic or the Alternatives section is too thin."
- "I need to explain [technical decision] to a CTO who doesn't have a technical background. What business impact framing would make this land? What am I probably leaving out?"
- "I'm preparing to defend [decision] in a meeting. What are the three most likely challenges I'll face, and what's the strongest response to each?"
- "Here's an ADR I wrote: [paste]. What would make an experienced engineer distrust this? What's missing from the Alternatives section?"
- "I lost a decision in a meeting. The decision was [X] and I recommended [Y]. Write the 'dissenting view' paragraph for the ADR that records my concern without sounding adversarial."
