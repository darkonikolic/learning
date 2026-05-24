# Unit 13 — Capstone: `payment-platform/` as a production-shaped mini system

Compose (even partially stubbed honesty permitted if documented boundaries) **`payment-platform/`** with coherent services skeleton:

```
api
payment
inventory
worker (+ queue bridging earlier distributed/event areas lightly)
```

## Must embed production primitives

Docker (multi-stage by default unless justified)  

Metrics (Prometheus style)  

Tracing (OpenTelemetry end-to-end at least api→one hop)  

Structured logging correlation  

`/health` + `/ready` split policy  

Graceful shutdown  

Synthetic chaos again (timeouts/failures) with evidence-driven fixes echoing Units 11–12

Interview checklist consolidation:

```
Docker multi-stage
graceful shutdown
metrics
tracing (spans propagation)
structured logging correlation ids
health vs readiness distinctions
OpenTelemetry vocabulary vs hand-wavy “we have traces” fluff debunk ethically
```

