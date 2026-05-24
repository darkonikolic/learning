# Unit 5 — Inbox pattern: consumers survive duplicates & replays elegantly

Symmetric consumer-side companion to duplicates arriving under **>=1 delivery**:

Record message IDs consumed / processed transitions idempotently to avoid doubling side effects adjusting inventory dangerously.

Minimal mental model sketch:

```
BEGIN
 INSERT inbox_seen (consumer_group, producer_event_id UNIQUE)
 IF conflict → ack & skip gracefully
ELSE
 apply domain mutations
COMMIT
```

Articulate distinctions:

- deterministic idempotency keys vs brute dedupe ledger,
- long retention vs compaction nuances high-level—not broker admin depth requirement here.

Interview lens: summarise **difference outbox publishes vs inbox dedupes ingestion** verbally crisp staff expectation.

