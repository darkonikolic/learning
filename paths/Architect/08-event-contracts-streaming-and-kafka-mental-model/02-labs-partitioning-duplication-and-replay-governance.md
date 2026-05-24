# Unit 2 — Labs: partitioning keys, duplication, replay governance

## Lab A — partition key rationale

Sketch `payment` events vs `inventory` events keying schemes and argue skew vs coherence trade-offs.

## Lab B — duplication drill

Enumerate three duplicate deliveries of `PaymentCaptured`; document idempotent sinks preventing double ledger effects honestly.

## Lab C — replay policy

Produce written policy: who authorises rewind, safeguards against double-money effects, auditing expectations.

Cross-reference enrichment optional: parallels with **`paths/Go/14-*`** (outbox/inbox mental hooks) without re-implementing here.

