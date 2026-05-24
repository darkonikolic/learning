# Unit 7 — Cache layers Doctrine & HTTP coherence

Goals

- Distinguish **application cache adapters** versus **Doctrine result / query caching** semantics (staleness horizons differ).
- **HTTP cache layering** interplay (ETag negotiation, surrogate keys conceptually)—even API-only backends may emit conditional semantics thoughtfully.
- **Invalidation choreography** aligning domain events versus brute TTL-only strategies.

Interview

Enumerate **failure classes** introducing ghost reads after deployments if cache layers misaligned schema evolution.
