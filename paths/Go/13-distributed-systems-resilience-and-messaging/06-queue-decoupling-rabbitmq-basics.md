# Unit 6 — RabbitMQ queue decoupling: move work off the critical path ethically

Contrast overloaded synchronous fan-out caricature pushing email/analytics/notifications inline until checkout latency becomes user-facing hostage situation.

Responsible outline:

```
checkout critical path ⇒ enqueue durable intent message ⇒ worker draining asynchronously respecting consumers operational realities acknowledging new tail latency failure classes appearing honestly
```

## Practice

Wire a modest publisher/consumer with explicit ack/nack reasoning—understand poison messages preview next DLQ discussions.

Interview expectation: verbally contrast queue introduction tax (operability, duplication handling) vs latency wins / blast-radius containment virtues balanced non-absolutism.
