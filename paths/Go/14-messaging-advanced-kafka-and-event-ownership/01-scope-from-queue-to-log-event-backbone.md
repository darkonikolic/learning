# Unit 1 — From “we have a queue” to durable event backbone thinking

You already practise **broker-backed work decoupling** (RabbitMQ-style paths in Area `12`). This area stretches into **Kafka-shaped event streaming** semantics and **ownership patterns** (outbox/inbox) that staff engineers defend in payment and inventory pipelines.

## Outcomes

- Place **Kafka** conceptually alongside RabbitMQ—not “Kafka everywhere,” but knowing its partition + consumer-group + ordering guarantees story.
- Name **replay**, **ordering**, **poison** handling, **event-driven boundaries** crisply—not only happy-path enqueue/dequeue instincts.

> **Suggested cadence (informational only):** this area often lands as several deep blocks (~1–1.5 h/day authoring pace)—folder numbering is ordering, not a calendar.

## Practice spine (conceptual sketch)

Maintain the narrative **`payment → event emission → inventory`**, where **`event`** carries explicit contract versioning and deterministic consumer behaviour under duplicates.

## Interview cornerstone

Articulate **`RabbitMQ vs Kafka`** responsibilities: workload shape, throughput, replay model, retention, ordering primitives, ops surface—reject absolutist slogans.

