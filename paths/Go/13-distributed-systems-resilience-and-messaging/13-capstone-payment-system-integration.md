# Unit 13 — Capstone: resilient `payment-system/` checkout choreography

Compose an end-to-end story (code depth proportionate honest to your sandbox):

```
checkout
  → payment
  → inventory reservation / adjustment choreography
  → queue-backed notification acknowledgement path
```

## Must deliberately exercise earlier motifs

timeouts • bounded retries • idempotency keys • RabbitMQ-ish queue semantics pragmatically • delivery honesty • DLQ emergence • saga/compensation narration • correlation identifiers propagation minimally • backpressure narrative when workers insufficient capacity honesty

## Fault replay notebook

Enumerate duplicate requests, ambiguous timeouts (“did payment land?”), poison messages, flaky workers—recover with written rationale bridging **delivery semantics**, **handler idempotency**, and **human-runbook** pointers where automation cannot ethically replace judgement.

Interview rehearsal: summarise the system aloud as if onboarding a sceptical teammate—prioritise correctness arguments over toolchain trivia.
