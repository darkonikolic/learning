# Unit 2 — Core practices: timeouts, retries, idempotency, inconsistency realism

## Timeout budgets across hops

Design a **tiered budget** edge → gateway → service → downstream → DB—not a uniform deep stack of identical long timeouts multiplying queue buildup.

Explain what happens socially when downstream DB spikes latency and budgets are dishonest upstream.

## Retries vs retry storms

List conditions when automated retries help vs harm (dependency already failing + amplified load). Tie to **bounded backoff + jitter + max attempts** motifs.

Explicitly anchor **financial / payment** ambiguity windows to idempotency keys (cross-link thinking to payment domains—no implementation mandate here).

## Duplicated events & ordering hotspots

Enumerate how duplicate **`OrderPaid`**, **`OrderCreated`**, retries at-least-once semantics surface—and how consumer design must reconcile (dedupe ledger / idempotent semantics / partitioning keys bridging Kafka-thinking forward areas).
