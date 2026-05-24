# Unit 4 — Outbox pattern: never “successful DB txn + forgotten publish”

Problem class: transactional success commits but message publish crashes—downstream ignorance permanent.

## Canonical pattern

Persist **desired publication records** atomically beside domain writes (same DB transaction ideally), asynchronously relayed safely to Kafka/Rabbit with **publisher confirm / retry / DLQ bridging** interplay.

Articulate transactional boundaries honestly:

```
BEGIN
 mutate domain aggregates
 INSERT outbox_events (payload, routing metadata, ...)
COMMIT

background relay reads outbox ⇒ publishes ⇒ marks dispatched (or transactional delete variant—design choice with trade-offs)
```

## Practice angle

Implement minimal table + relay loop teaching—even SQLite acceptable—contrasting transactional honesty vs heroic “dual write” folklore.

Interview prompt: reconcile outbox duplication risk & idempotent publisher behaviour.
