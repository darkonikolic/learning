# Unit 11 — Latency ownership: triage CPU / memory / GC / DB / network systematically

Synthetic production scenario:

You receive “this API is slow.” Forbidden answer: random micro-optimisation gut feelings.

## Checklist mental walkthrough

| Layer | Quick honest probes |
|-------|---------------------|
| CPU | profile hot functions |
| Alloc/GC | `-benchmem`, heap profile, alloc pressure |
| DB | query plans / connection pool waits (cross Area `08`) |
| Network | timeouts, retries storm, payload bloat |
| Queues | backlog age / consumer lag (Areas `12`/`14`) |

## Practice

Introduce intentional slow dependency (sleeping fake client) AND independent CPU hog path—prove you can separate symptoms using tools rather than story-telling.

## Deliverable

Short **incident note template**: symptom → hypothesis → validation evidence → fix → trade-off.
