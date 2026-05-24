# Unit 1 — Scope: distributed-first failure imagination

> **Suggested cadence (informational):** the source roadmap used ~twelve deepening blocks (~1 h/day). Folder order ≠ calendar.

Outcome shift (**Faza 2** source): evolve from **`"I finished an RPC"`** toward **`"I know what breaks when silence, slowness, or lies return"`**.

Vocabulary anchors (articulate distinctions, don’t meme patterns):

```
latency ceilings • cascading timeouts • retry policies & storms  
idempotency & dedupe realism • consistency boundaries • partition tolerance humility (CAP caricature responsibly)  
circuit breakers • bulkheads • saga/outbox choreography • duplicated events • ordering hotspots  
backpressure (& operator visibility of backlog age) • blast radius narration
```

## Practice spine topology (repeat deliberately)

Reuse exercise stack when relevant: **`Gateway → Symfony API → Redis queue/worker → Postgres → eventual Go-worker`**—adapt equivalent names consciously if your stack differs.

Cross-link voluntarily: parallels exist in **`paths/Go/12-*`**, **`paths/Go/14-*`** without duplicating full engineering depth repeatedly—this track stays **architecture reasoning**.
