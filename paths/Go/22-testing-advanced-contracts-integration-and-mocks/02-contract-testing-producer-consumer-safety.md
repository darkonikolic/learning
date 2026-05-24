# Unit 2 — Contract testing between services (producer/consumer safety net)

Consumers and producers deploy independently—schema drift hurts before integration tests notice if you only rely on “we run both in staging sometimes.”

## Conceptual toolkit

```
Consumer-driven contracts / consumer expectations
Provider verification in CI
Versioned API contracts (OpenAPI / proto compatibility rules) as complementary guardrails
```

## Deliverable

Pick one API boundary you own (even fake) and write:

- a contract scenario list (happy + breaking changes),
- how you’d fail CI when the provider regresses,
- what you still **cannot** catch (operational partial failures, performance)—state limits honestly.
