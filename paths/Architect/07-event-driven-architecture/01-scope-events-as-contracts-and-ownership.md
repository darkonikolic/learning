# Unit 1 — Scope: event-driven architecture as ownership of consequences

**Framing:** events are **contracts** with evolution, consumer burden, and operational visibility—not “fire JSON into void hope.”

Core architectural lenses:

```
event naming & versioning discipline (additive evolution default)  
publisher vs consumer ownership of idempotency & ordering guarantees realistic honesty  
synchronous thin command path vs fat async fan-out responsibilities explicitly carved  
poison / DLQ / replay governance preview (deepened in streaming area)  
observability: lag, consumer health, dead-letter growth expectations  
compensation choreography intersection with reliability / sagas later areas
```

## Practice spine

Relate Symfony command path to **domain events** crossing Go workers / notification fan-out—sketch **who must never lose money or stock truth** when async.

