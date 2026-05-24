# Unit 1 — Scope: edge caches & CDN as first-class architectural surfaces

Edge decisions change **routing, consistency, purge operations, TLS termination adjacency**, and **operator runbooks**.

## Architectural concerns (answer each for your sketch system)

```
What is cacheable vs must stay dynamic—and why spoofing CDN headers is hostile?
How do you version static assets safely (immutable URLs / fingerprint builds)?
Purging correctness vs TTL-only simplicity trade spectrum (risk of stale embargoed content…)  
Regional edges & sovereignty / latency trade-offs (conceptual—not legal briefing)  
Interactions with gateways/WAF/API abuse controls (overlap with **`14-*`** & **`21-*`** later)
Observability: hit ratios miss alone insufficient—tail latency & error envelope matters
```

## Practice spine

Take Symfony-style app: separate **static vs dynamic** responsibility split with explicit edge failure mode (CDN degrades—what still works?).

