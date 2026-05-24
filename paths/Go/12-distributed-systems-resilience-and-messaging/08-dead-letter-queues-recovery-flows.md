# Unit 8 — Dead-letter queues: escape infinite poisonous retry traps

Operational story: a malformed message or a deterministic bug retries forever—burning CPU, harming shared brokers, burying legitimate traffic.

Define a humane policy:

- bounded retries while errors look transient / unknown,
- then route poison messages into a **dead-letter queue** path (conceptual name varies by broker) for isolated inspection/replay tooling.

Document what operators need: payloads, timestamps, correlation headers, replay procedure that does not blindly double-charge (link idempotency, Unit 5).

## Interview prompts

Difference between DLQ as “junk drawer” versus an operational cockpit with alerting and replay runbooks tied to compensation logic.
