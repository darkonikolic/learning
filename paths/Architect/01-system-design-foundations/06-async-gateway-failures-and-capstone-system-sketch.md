# Unit 6 — Sync vs async, gateway boundaries, failure thinking, integration lab

## Sync vs async

Contrast **request/response** paths vs **queue-mediated** side effects (email, analytics). Address timeout ownership, user-visible vs background responsibilities.

## API gateway & ownership

Gateway responsibilities (auth termination, routing, rate limits, WAF adjacency) vs domain services owning business rules—avoid “smart gateway / dumb services” vs “dumb gateway / duplicated auth mess” extremes without conscious policy.

## Failure thinking (non-optional)

For each dependency (Redis, DB, DNS latency, third-party HTTP), document:

```
detection signal
degradation / fallback options
recovery window expectations
cost of being wrong
```

## Capstone diagram (source Faza 1 integracioni lab)

Sketch end-to-end:

```
Frontend → Gateway → Symfony API → Go worker → Redis → Postgres
```

For each labelled concern, write **≥1 concrete sentence** (not a word on a slide):

- **Scale** — which component hits ceiling first under your assumptions.
- **Failure** — one plausible outage and observable symptom.
- **Monitoring** — the minimum signal proving health vs user pain.
- **Backup / restore** — RPO/RTO statement (even qualitative).
- **Security** — one trust-boundary assertion.
- **Deployment** — one rollback / rollout constraint you accept.
