# Lab: Technology Evaluation

---

## Exercise 1: Message Queue Evaluation

### Context

E-commerce platform. Currently using RabbitMQ for order processing. Volume: 5,000 orders/day (~0.06 msg/s average, peaks at ~20 msg/s during flash sales). Team: 5 engineers, no dedicated ops. Stack: Symfony API + Go worker + Postgres.

**New requirements:**
1. Real-time analytics dashboard showing order trends (requires streaming order events to an analytics consumer)
2. Compliance audit log with 90-day replay capability (auditors can re-run any 90-day window)

RabbitMQ in its current configuration cannot satisfy requirement 2 (no replay) and satisfies requirement 1 only partially (no durable consumer replay).

### Options to evaluate

- **Option A: RabbitMQ (stay)** — extend current setup, potentially with message archiving workaround
- **Option B: Kafka (replace RabbitMQ)** — self-hosted, team operates it
- **Option C: AWS Kinesis (replace RabbitMQ)** — managed cloud stream, vendor-specific

### Step 1: Define your constraints

List the constraints that eliminate options or bound the decision. Consider: team size, ops capacity, existing cloud provider (assume AWS), compliance requirements (90-day replay must be durable and auditable), timeline.

Write your constraints here before proceeding.

---

### Step 2: Define criteria with weights

Complete this table. Add or remove rows as needed. Assign weights 1–5 (5 = most important for this decision).

| Criterion | Weight (1–5) | Why this weight for this decision |
|---|---|---|
| Replay capability | | |
| Throughput | | |
| Operational complexity | | |
| Team expertise required | | |
| Cost (TCO, 1 year) | | |
| Migration effort from RabbitMQ | | |
| Ecosystem / tooling | | |

---

### Step 3: Score each option

Complete this matrix. Score 1–5 per criterion per option. Add a brief justification for each score.

| Criterion | Weight | RabbitMQ (A) | Score | Kafka (B) | Score | Kinesis (C) | Score |
|---|---|---|---|---|---|---|---|
| Replay capability | | | | | | | |
| Throughput | | | | | | | |
| Operational complexity | | | | | | | |
| Team expertise required | | | | | | | |
| Cost (TCO) | | | | | | | |
| Migration effort | | | | | | | |
| Ecosystem / tooling | | | | | | | |
| **Weighted total** | | | | | | | |

Calculate: weighted total = sum of (weight × score) for each option.

---

### Step 4: State the decision

Write: "We choose [option] because we are optimizing for [primary criteria]. The key tradeoff we accept is [what we're sacrificing]. If [condition changes], we should re-evaluate."

---

### Reference answer (review after completing)

<details>
<summary>Expand after you've written your own answer</summary>

**Constraints:**
- Team of 5, no dedicated ops — eliminates self-operated systems with high operational overhead unless the team explicitly accepts the investment
- Already on AWS — AWS-native options carry no additional vendor lock-in beyond existing commitment
- 90-day replay must be durable and auditable — eliminates vanilla RabbitMQ (messages are deleted after consumption)
- Timeline: assume normal (not emergency) — 2–3 week evaluation window acceptable

**Sample scoring rationale:**

| Criterion | Weight | RabbitMQ | Score | Kafka | Score | Kinesis | Score |
|---|---|---|---|---|---|---|---|
| Replay capability | 5 | Needs archiving workaround; not native | 2 | Native, configurable retention | 5 | Native, 7–365 day retention | 5 |
| Throughput | 2 | Sufficient for current volume | 4 | Massive headroom | 5 | Sufficient, managed ceiling | 4 |
| Operational complexity | 5 | Low — team already operates it | 5 | High — Kafka expertise, ZooKeeper/KRaft, JVM tuning | 2 | Minimal — managed service | 5 |
| Team expertise required | 4 | Already known | 5 | Significant ramp-up needed | 2 | Moderate — AWS SDK, Kinesis concepts | 4 |
| Cost (TCO 1yr) | 3 | Low — existing infra | 5 | Medium — EC2/EKS overhead + eng time for ops | 3 | Medium — per-shard pricing, higher than EC2 at scale | 3 |
| Migration effort | 3 | Minimal — extend, not replace | 5 | High — parallel run, consumer migration, data cutover | 2 | Medium — producers/consumers need rewrite | 3 |
| Ecosystem / tooling | 2 | Mature, well-known | 4 | Excellent — Kafka Connect, Kafka Streams, Confluent | 5 | Good — AWS ecosystem, Kinesis Data Analytics | 4 |

**Weighted totals (approximate):**
- RabbitMQ: (2×5)+(4×2)+(5×5)+(5×4)+(5×3)+(5×3)+(4×2) = 10+8+25+20+15+15+8 = 101
- Kafka: (5×5)+(5×2)+(2×5)+(2×4)+(3×3)+(2×3)+(5×2) = 25+10+10+8+9+6+10 = 78
- Kinesis: (5×5)+(4×2)+(5×5)+(4×4)+(3×3)+(3×3)+(4×2) = 25+8+25+16+9+9+8 = 100

**Decision: Kinesis (narrowly over extended RabbitMQ).**

"We choose Kinesis because we are optimizing for operational simplicity (team of 5, no ops headcount) and replay capability (compliance requirement). The key tradeoffs we accept are AWS vendor lock-in (beyond existing commitment) and higher per-unit cost at scale. We are not choosing Kafka because the operational burden for self-hosting is too high for our team size, and the throughput advantage is irrelevant at our volume. We are not extending RabbitMQ because the replay workaround adds operational complexity without solving the compliance requirement cleanly. If we grow to a team with a dedicated platform engineer, or if volume exceeds 100k msg/s, re-evaluate Kafka."

**Alternative valid answer:** RabbitMQ with a message archive pattern (write to S3 on consume, replay from S3 for audit) is legitimate if migration cost is weighted heavily. The scoring exercise should surface this tradeoff explicitly.

</details>

---

## Exercise 2: PoC Design

### Context

You've chosen Kinesis (or Kafka — use whichever you chose in Exercise 1) for the order processing and compliance audit log use case. Before committing to full implementation, you want to run a PoC.

A bad PoC tests "does the technology work" — it always does. A good PoC tests the riskiest assumption about your specific use case.

### Your task

Design the PoC by answering these four questions:

**1. What specifically are you testing?**

Not "does Kinesis receive and deliver messages." State the specific capability or behavior that, if it fails, would invalidate the decision. What did you assume would be true that you haven't verified against your actual use case?

**2. What is the riskiest assumption?**

State the single assumption that is most likely to be wrong and most expensive to discover late. For the audit log use case, think about: replay latency at volume, consumer group behavior during catch-up, integration with your existing Go worker, cost at projected volume.

**3. What does a passing PoC look like?**

Define the success criterion precisely. "It works" is not a success criterion. State: observable behavior, measurable threshold, and how you verify it.

**4. What does a failing PoC tell you?**

If the PoC fails, what does that mean for the decision? Does it mean "don't use Kinesis" or "Kinesis needs to be configured differently" or "our Go worker needs to be redesigned"? A failing PoC should give you information, not just a red light.

---

### PoC Design Template

```
Technology:
Use case being tested:

Riskiest assumption:
  "We assumed that [X]. This could be wrong because [Y]."

PoC scope (what we build):
  - [ ]
  - [ ]
  - [ ] (keep it minimal — only what's needed to test the assumption)

Success criterion:
  "[Observable behavior] is [measurable threshold] when [conditions]."
  Verified by: [how you measure it]

Failure criterion:
  If [observable failure], we conclude [specific conclusion].
  This means: [go back to RabbitMQ extended / re-evaluate Kafka / reconfigure Kinesis as follows]

Time box: [X days]
Who builds it: [names/roles]
```

---

### Reference answer (review after completing)

<details>
<summary>Expand after you've written your own answer</summary>

**For Kinesis:**

**Riskiest assumption:** "We assumed a single Go worker can replay 90 days of order events from Kinesis within a 4-hour window (auditor SLA), at our projected data volume (~5k orders/day × 90 days = 450k events), without hitting Kinesis shard throughput limits or incurring prohibitive cost."

This is the right assumption to test because:
- Kinesis pricing is per-shard-hour + data retrieval. 90-day replay at volume might be expensive.
- Kinesis shard read limit is 2MB/s per shard. With 1 shard, 450k events at ~500 bytes/event = 225MB. Fine. But if events are larger or volume grows, sharding strategy matters.
- The Go worker doesn't exist yet for Kinesis. Integration complexity is unknown.

**PoC scope (minimal):**
- Produce 450,000 synthetic order events to a Kinesis stream (simulating 90 days of history)
- Consume all 450,000 events from the beginning using the Go worker
- Measure: total replay time, cost (Kinesis pricing calculator or actual AWS bill for test run), consumer throughput

**Success criterion:** Go worker completes full 90-day replay of 450,000 events in under 4 hours. AWS cost for one replay operation is under $X (define your budget threshold). Consumer produces correct audit output (verify record count and spot-check event content).

**Failure criterion:** If replay takes >4 hours or cost exceeds budget — examine whether adding shards reduces time proportionally (if yes: solvable by provisioning more shards; re-evaluate cost). If cost is prohibitive regardless of shards, this is a structural problem with the Kinesis pricing model for this use case — go back and re-evaluate S3-based archive replay.

**Time box:** 3 days. Day 1: set up Kinesis stream, write producer, load test data. Day 2: Go worker integration, run replay, measure. Day 3: analyze results, write PoC report.

</details>

---

## Evaluation Matrix Template

Copy this for any technology evaluation:

```markdown
## Technology Evaluation: [Decision Name]
Date: [date]
Decision owner: [name]

### Constraints (these eliminate options)
- [constraint 1]
- [constraint 2]

### Options considered
- Option A: [name] — [one-line description]
- Option B: [name] — [one-line description]
- Option C: [name] — [one-line description]

### Evaluation criteria

| Criterion | Weight (1–5) | Rationale |
|---|---|---|
| [criterion] | | |

### Scoring matrix

| Criterion | Wt | Option A | Score | Option B | Score | Option C | Score |
|---|---|---|---|---|---|---|---|
| [criterion] | | | | | | | |
| **Weighted total** | | | | | | | |

### Decision

We choose [option] because [primary criteria we're optimizing for].

Key tradeoffs accepted: [what we're sacrificing].

Re-evaluate if: [conditions that would change the decision].
```

---

## Checklist before moving on

- [ ] You can name the 6 steps of the evaluation framework in order without looking
- [ ] You can explain why "stay with current" must always be an option
- [ ] You know the primary decision driver for RabbitMQ vs Kafka vs cloud-native queues (replay + ops capacity)
- [ ] You can distinguish a PoC from a demo and state what a good PoC tests
- [ ] You can write a falsifiable success criterion for a PoC (measurable threshold, observable behavior)
- [ ] You can calculate a weighted score and use it to make a documented, reversible decision
