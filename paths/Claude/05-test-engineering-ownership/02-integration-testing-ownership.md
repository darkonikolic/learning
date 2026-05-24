# Integration testing ownership

**Theme:** Confidence where **pieces actually meet wiring** — not mocked away.

**Bridges to prove in exercises:**

```
Symfony ⇄ persistence (DB fixture / transaction strategy you trust)

Go ⇄ RabbitMQ ⇄ authoritative database path
```

### Lab scaffold

Scenario path:

```
worker publishes/consumes  →  queue semantics hold  →  database reflects expected saga / idempotency
```

Compose **narrow** slices: one unhappy path plus one sunny path beats ten shallow happy paths.

### Concept tags

**Integration ownership** — you say which dependencies are **in-scope real** versus test doubles today.  

**Dependency verification** — assert observable effects at seams (queued message shape, persisted row mutations, transactional boundaries).

### Checklist

- [ ] Test names state **boundary under proof** (“after ack, ledger row uniqueness holds”).  
- [ ] Fixtures stay **minimal** — avoid copying production dumps wholesale.  
