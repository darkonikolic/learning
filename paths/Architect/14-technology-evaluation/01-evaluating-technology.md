# Evaluating Technology

Technology decisions outlast the people who made them. A bad choice compounds for years — migration costs, expertise gaps, operational toil, and the slow drag of a system that wasn't designed for the problem it's solving. "It's popular" and "we used it before" are not evaluation criteria. Neither is "the team wants to learn it."

---

## The Evaluation Framework

### Step 1: Define constraints first

Constraints eliminate options before you compare. They are non-negotiable: things that cannot change regardless of how good a technology looks on paper.

Common constraints:
- **Team skills** — if no one on the team knows Kafka, operational complexity of Kafka is dramatically higher than its paper complexity
- **Existing stack** — switching databases mid-product is a migration project, not a technology evaluation
- **Compliance and security** — data residency requirements eliminate cloud-native options in some regions
- **Ops maturity** — a 4-person team cannot operate Kafka, Elasticsearch, Cassandra, and Kubernetes simultaneously
- **Budget** — fully managed services cost more in hosting but less in engineering time; make this tradeoff explicit

List your constraints. Anything that violates a constraint is eliminated. Don't evaluate eliminated options — it wastes time and creates false debate.

### Step 2: Define selection criteria with weights

Criteria are what you're optimizing for. They vary by decision.

| Criterion | Weight (1–5) | Notes |
|---|---|---|
| Throughput | | Matters for message queues, not for admin dashboards |
| Operational complexity | | Higher weight for small teams |
| Ecosystem maturity | | Client libraries, community answers, known failure modes |
| Cost (TCO) | | Hosting + engineering time + migration |
| Learning curve | | Time before team is productive |
| Feature fit | | Does it actually solve the problem without workarounds |

Weight them. If you don't weight, every criterion has equal weight, which is almost never true. A team of 4 should weight operational complexity at 5; a platform team of 20 can afford to weight it lower.

### Step 3: Generate at least 3 options including "stay with current"

"Stay with current" is always an option. It has known failure modes, known operational cost, and zero migration cost. If you can't articulate why it's insufficient for the new requirement, you shouldn't switch.

### Step 4: Score each option per criterion

Not "Kafka is better." Score: Kafka scores 5/5 on throughput, 2/5 on operational complexity for a team of 4, 4/5 on ecosystem maturity, 2/5 on TCO for self-hosted.

Scoring forces honest comparison. It surfaces tradeoffs explicitly rather than letting the loudest voice win.

### Step 5: State what you're optimizing for

The decision is only good given your current priorities. Document: "We chose X because we weighted operational simplicity at 5 (team of 4, no dedicated ops) and throughput at 2 (current volume doesn't require it). If volume grows to >50k/msg/s or team grows to include a dedicated platform engineer, re-evaluate."

This is what allows future teams to re-evaluate correctly rather than cargo-culting the original decision.

### Step 6: Total cost of ownership

Don't compare licensing costs. Compare:
- Migration cost (how much work to move from current to new)
- Learning curve (time before team is productive — not just "get it running" but "debug it at 2am")
- Ongoing ops (patching, upgrades, capacity planning, incident response)
- Tooling (monitoring, alerting, backup, restore)
- Debugging when it breaks (how hard is it to find root cause in production)

---

## Common Evaluations Architects Face

### Message Queue: RabbitMQ vs Kafka vs Cloud-native (SQS/Pub-Sub)

| Criterion | RabbitMQ | Kafka | SQS/Cloud-native |
|---|---|---|---|
| Throughput | Medium (tens of thousands/s) | High (millions/s) | Medium — managed ceiling |
| Message replay | No (messages consumed = gone) | Yes — consumers can re-read from offset | No (SQS) / Limited (Pub-Sub) |
| Ops complexity | Low-medium — manageable for small team | High — requires Kafka expertise | Minimal — managed service |
| Routing flexibility | High — exchanges, bindings, dead-letter | Limited — topics and consumer groups | Simple FIFO / fan-out |
| Vendor lock-in | None | None | Yes — cloud vendor |
| Good for | Task queues, RPC, complex routing, <10k msg/s | Event streaming, audit log, analytics, replay | Cloud-native teams, simple queues, don't want ops |

**Decision driver:** Do you need replay? If yes, Kafka (or cloud event streams like AWS Kinesis). Do you have ops capacity for Kafka? If no, Kafka is the wrong answer regardless of throughput. RabbitMQ is underrated — it solves most task queue problems with far less operational overhead.

### Database: Postgres vs MySQL vs Managed

| Criterion | Postgres (self-hosted) | MySQL (self-hosted) | Managed (RDS/CloudSQL) |
|---|---|---|---|
| JSON support | Excellent (JSONB, indexable) | Adequate | Depends on engine |
| Feature set | Richer (window functions, CTEs, PostGIS) | Adequate | Depends on engine |
| Replication | Logical + streaming | Binary log | Handled by provider |
| Ops overhead | Requires DBA attention for tuning | Similar | Low — provider handles backups, failover, patching |
| Cost | Hosting only | Hosting only | Higher hosting, lower engineering |
| Choose when | You have DBA capacity and specific tuning needs | Migrating from MySQL or ecosystem requirement | Team doesn't want to operate databases |

**Default choice for new systems: managed Postgres.** The managed overhead is worth it for most teams. Choose self-hosted only if you have a DBA and specific performance requirements that managed services can't accommodate.

### Cache: Redis vs Memcached

| Criterion | Redis | Memcached |
|---|---|---|
| Data structures | Strings, hashes, lists, sets, sorted sets, streams | Strings only |
| Pub/sub | Yes | No |
| Persistence | Optional (RDB, AOF) | No |
| Clustering | Redis Cluster | Built-in sharding |
| Ops complexity | Moderate | Lower |
| Choose when | Almost always — default choice | Pure key-value at extreme scale with nothing else needed |

**Default choice: Redis.** Memcached is marginally faster for pure get/set at very high throughput. In practice, the operational simplicity of having one cache system that also handles sessions, rate limiting, and pub/sub outweighs the throughput difference.

---

## Avoiding Evaluation Theater

**The tell:** "We evaluated 5 options and chose Kafka" with no documented criteria, no scoring, no tradeoffs stated. This is post-hoc rationalization — the decision was made before the evaluation started.

**PoC before decision for high-risk choices.** A PoC is not a demo. It tests the riskiest assumption — the thing that, if wrong, invalidates the decision. If you're evaluating Kafka for replay: your PoC should test whether your consumer can replay 90 days of messages at your projected volume within your SLA window. Not whether Kafka starts and a message flows through it.

**Time-box the evaluation:**
- Low-risk (mature technology, reversible choice): 3–5 days
- High-risk (new technology, expensive to reverse): 1–2 weeks
- Evaluations that drag on produce analysis paralysis, not better decisions

---

## Anti-Patterns

**Choosing based on job posting trends** — "Kafka is on all the job listings" tells you the market is using Kafka. It tells you nothing about whether your system needs Kafka. Trend-following is not evaluation.

**Choosing based on what the team wants to learn** — valid input, not the primary criterion. "We want to learn Kafka" belongs in the learning curve row of the evaluation matrix, not in the decision driver.

**Not including "stay with current" as an option** — if your current solution is excluded from comparison, the evaluation is biased toward switching. Include it. If it loses, the case for switching is stronger.

**PoC that tests only the happy path** — testing that Kafka receives and delivers a message proves nothing. The happy path always works. Test: what happens when a consumer crashes mid-batch, when a topic is full, when the consumer group falls behind, when the broker restarts.

**TCO calculation that excludes migration** — a new technology that's cheaper to run but costs 6 months of engineering time to migrate to is not cheaper. Include the migration in the cost column.

**Evaluating without weights** — every criterion having equal weight means operational complexity ties with throughput. That's almost never the right call. Weight explicitly.

---

## Šta da pitaš AI

- "We need to choose between [A] and [B] for [specific use case]. Our constraints are [list]. Our weighted criteria are [list with weights]. Evaluate each option per criterion — score 1–5 and explain the score. Do not give a recommendation, just compare."
- "We're considering adopting [technology]. What are the operational failure modes at [our scale and team size]? What expertise does the team need to operate it safely in production?"
- "We chose [technology] 2 years ago. Our situation has changed: [describe changes]. Re-evaluate that decision against [alternatives] given the new context."
- "Build a comparison table: [A] vs [B] vs [C] on these criteria: [list]. Don't recommend — just compare so I can apply our weights."
- "Design a PoC for evaluating [technology] for [use case]. What is the riskiest assumption we need to test? What does pass look like? What does fail tell us?"
