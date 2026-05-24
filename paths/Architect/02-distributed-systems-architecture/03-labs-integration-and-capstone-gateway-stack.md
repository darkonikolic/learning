# Unit 3 — Labs & integration capstone (distributed systems area)

Produce **three** short failure drills (diagram + bullets each):

1. **Queue/worker disappearance** — queue age metrics, UX degradation posture, remediation ownership.
2. **Database slowdown** — pool exhaustion story, cascading timeout propagation.
3. **Ambiguous payment RPC** — idempotency keys + reconciliation—not hope.

## Capstone topology (reuse source stack)

Sketch & narrate:

```
Gateway → Symfony API → Redis queue/stream surface → Go worker → Postgres
```

Annotate **`retry`** / **`timeout`** / **`monitoring`** / **`failure recovery`** / **`consistency realism`** consciously—not slide-only labels without sentences.

## Interview rehearsal

Five sceptical questions you’d ask **before** “we need microservices to fix outages.”
