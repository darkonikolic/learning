# Unit 6 — Poison scenarios, replay, operational governance—not endless retry loops

**Poison message** caricature deterministic bug or schema mismatch causing infinite catastrophic failure churn—must graduate to segregated remediation path analogous DLQ philosophies yet broker-specific knobs differ.

Operational responsibilities:

```
bounded retries distinguishing transient infra vs poisonous semantic failure
replay tooling auditable respecting idempotency + legal duplication constraints consciously
prevent unsafe mass replays multiplying financial inconsistencies responsibly
```

## Kafka nuance teaser

Understand **offsets commit** interplay with poisonous partition stall—whole partition stuck if single bad record mishandled—contrasts naive queue acknowledging pattern assumptions.

Interview scenario: formulate policy table classifying retries vs skipping vs patching schema vs deploying fix-forward strategies.

