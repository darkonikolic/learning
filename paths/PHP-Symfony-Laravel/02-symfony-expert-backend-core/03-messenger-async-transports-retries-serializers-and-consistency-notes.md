# Unit 3 — Messenger professional transport design

Goals

- **Handler idempotency** across redelivery horizons—timeouts vs logical duplicates.
- **Serialization boundaries**: class-based vs DTO payloads; upgrade compatibility when renaming message classes responsibly.
- **Failure queues / DLQ thinking**: distinguishing poison messages vs infra blips versus partial commit hazards.
- **Transactional integration**: aligning DB commit horizons with enqueue visibility (bridge to transactional outbox later).

Symfony-specific angle

Know when **sync vs async** transports change failure semantics subtly (kernel vs worker process boundaries).
