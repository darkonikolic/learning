# Unit 11 — Incident triage: tie metrics, traces, and logs into one story

Synthetic incident:

```
CPU rising OR error rate rising OR latency rising (pick combo)
```

Your job is to narrate an investigation path:

```
Confirm user-visible symptom (dashboards / alerts)
Form hypotheses (dependency? GC? lock contention? retry storm? DB saturation?)
Validate with metrics first, then traces, then targeted logs
Apply fix with explicit trade-off note
```

## Deliverable

One-page **post-incident style note** (even fictional) with timeline + evidence links you would have collected.
