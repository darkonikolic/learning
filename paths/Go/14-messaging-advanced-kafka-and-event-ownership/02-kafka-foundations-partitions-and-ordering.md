# Unit 2 — Kafka conceptually: topics, partitions, offsets, replay

Kafka is marketed as “log,” behaved like **append-only segments** with scalable fan-out—not a mailbox that deletes after acknowledgement.

Core vocabulary you must wield:

| Concept | Operational meaning |
|---------|-----------------------|
| **Topic** | named stream grouping related events (`payment.events.v1`). |
| **Partition** | unit of parallelism; ordering is **partition-scoped**, not globally magic. |
| **Offset** | per-partition consumption progress pointer; rewind/replay rewinds offsets intentionally. |
| **Retention** | events may remain readable historically—replay becomes a deliberate tool, also a GDPR/PII headache if ignored.

## Ordering reality

Kafka gives **total order inside one partition**. Across partitions ordering is meaningless—never assume global ordering without pinning keys.

Practice question: **`PaymentCaptured` ordering vs `InventoryReserved` causal expectations** — which saga step must serialize on the same partitioning key?

## Lab

Compose two alternate partition key schemes for `payment → inventory` choreography and critique **skew** (single hot key) versus **incoherent ordering**.

## Interview focus

Contrast **“message queue delivery” folklore** versus **replayable log semantics** succinctly—not vendor trivia.

