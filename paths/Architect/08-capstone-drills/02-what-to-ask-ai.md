# What to Ask AI: Architect-Level Prompt Reference

**Before using this sheet:** AI gives you options and analysis. You make the decision. The quality of your output equals the quality of your constraints — if you don't give AI the real constraints, you get generic advice. Every prompt below has a [placeholder]. Fill it with your actual situation before sending.

---

## System Design from Scratch

Use these to generate a structured option space before committing to any design.

```
I'm designing [system name]. Constraints: [team size], [traffic estimate],
[existing stack], [operational maturity], [consistency requirement].
Before proposing any design, list the questions you'd ask to clarify
the architecture drivers.
```

```
Given these constraints: [list constraints], generate 3 architectural options
for [system]. For each option, state: what problem it solves best, what it
makes harder, and at what scale it breaks down.
```

```
I'm designing [system]. What are the top 5 failure modes I should design against,
given [key characteristic: high write volume / external integrations / eventual
consistency / stateless workers]? For each failure mode, name a mitigation.
```

```
What assumptions am I implicitly making in this design: [paste your design sketch]?
List each assumption and the risk if it's wrong.
```

---

## Evaluating a Tradeoff

Use these when you have two or more options and need to make a decision with justification.

```
I'm choosing between [Option A] and [Option B] for [problem].
My constraints are: [list constraints].
Evaluate each option against each constraint explicitly. Do not recommend
until you've completed the matrix.
```

```
What does [Option A] cost to operate at [scale], given a team of [size]?
Include: deployment complexity, observability requirements, on-call burden,
and failure recovery procedures.
```

```
I'm leaning toward [option] for [reason]. What's the strongest argument
against this choice, given [constraint]? I want the counterargument, not
confirmation.
```

```
At what scale or load does [Option A] stop being the right choice and
[Option B] become necessary? Give me a concrete threshold, not a vague
"it depends."
```

---

## Failure Diagnosis

Use these during incidents or in post-incident design review.

```
[System] is exhibiting [symptom: latency spike / dropped messages / 503s].
Walk me through a diagnosis sequence starting from the cheapest observable
signal and escalating to infrastructure changes only if the cheaper checks
don't explain the problem.
```

```
Apply the USE method (Utilization, Saturation, Errors) to [component: Postgres /
RabbitMQ / Go worker / Redis]. For each dimension, what metric do I look at,
what tool surfaces it, and what threshold indicates a problem?
```

```
A cascade failure occurred: [describe sequence of events]. Trace the failure
path backward. What was the proximate cause, what was the contributing condition,
and what architectural assumption broke?
```

```
Here is our postmortem draft: [paste draft]. What is missing from the
"contributing factors" section? What mitigation is implied but not stated?
What would prevent this class of failure, not just this specific incident?
```

---

## Storage Decisions

Use these before choosing a database or proposing a migration.

```
My application has these query patterns: [list read patterns], [list write patterns].
Data shape: [describe]. Volume: [rows/day or GB/month]. Evaluate Postgres, Redis,
and [alternative] against these patterns. Be specific about where each breaks.
```

```
I'm considering migrating from [current store] to [target store].
What are the migration risks specific to this transition?
Include: data consistency during cutover, rollback complexity, and the
operational burden on a team of [size].
```

```
At what data volume or query rate does Postgres full-text search become
insufficient for [use case]? What are the specific signals that indicate
I've hit that ceiling?
```

```
I need to store [data type: time-series events / messages / user sessions /
audit log]. What are the top 3 storage options for this access pattern?
For each, state: what it optimizes for, what it sacrifices, and what the
operational cost is.
```

---

## Async and Event Design

Use these when designing queues, consumers, or event-driven flows.

```
I'm designing a [consumer type] that processes [event type] from [queue].
What are the idempotency requirements? Walk me through how to implement
an idempotency key for this specific operation: [describe operation].
```

```
Design a Dead Letter Queue strategy for [queue/consumer]. Include:
what triggers DLQ routing, how I alert on DLQ depth, and the replay
procedure when the underlying cause is fixed.
```

```
My event schema is [describe current schema]. I need to add [new field /
change field type / remove field]. What schema evolution strategy applies here?
What breaks for consumers that haven't updated yet?
```

```
Explain the transactional outbox pattern for [stack: Symfony + Postgres + RabbitMQ].
What does it guarantee, what does it not guarantee, and what is the
implementation cost? When is it overkill?
```

---

## Communication and Decisions

Use these to translate technical decisions into stakeholder language or to pressure-test an ADR.

```
I've decided to [technical decision]. My audience is [role: CTO / product manager /
senior engineer who disagrees]. Write a 3-sentence explanation of why this decision
was made, what it prevents, and what it costs.
```

```
Review this ADR: [paste ADR]. What is missing from the "Considered Alternatives"
section? What implicit assumption in the decision is not stated? What would make
a future engineer question this decision?
```

```
A stakeholder said "[objection]" about [technical decision]. Generate the
strongest version of their argument. Then give me a response that addresses
the substance without being defensive.
```

```
I need to explain [technical risk: message loss / cache inconsistency / cascading failure]
to a non-technical stakeholder. Use an analogy. Then state the cost of the mitigation
in non-technical terms.
```
