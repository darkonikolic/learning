# Unit 2 — Labs: choreography vs orchestration sketch, failure containment

## Lab A — event storm

Producer spikes 10×: enumerate backpressure & operator signals (queue depth, processing lag, shed policy).

## Lab B — schema evolution

Add optional field to `OrderCreated` event—document dual-read window & deployment ordering constraints.

## Lab C — ownership argument

Debate **choreography** (many listeners react) vs **orchestrator** (central saga brain) for `Order → Payment → Inventory` with explicit trade-off bullets.

## Review checklist

| Question | Your answer must include |
|----------|--------------------------|
| Duplicate delivery tolerated? | Dedupe/idempotency plan |
| Global ordering illusion? | Partition key realism |
| Consistency proof | Observable compensations paths |

