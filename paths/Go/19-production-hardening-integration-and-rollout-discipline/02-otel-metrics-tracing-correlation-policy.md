# Unit 2 — OTEL + metrics + correlation policies (instrumentation without harming the service)

Treat observability rollout as engineering work with trade-offs:

- **Metrics**: naming consistency, cardinality discipline, sane histogram buckets.
- **Tracing**: propagate context across at least HTTP + any internal call you own; validate with a scripted multi-hop request.
- **Logs**: reuse the same correlation identifiers consistently (Areas `06/08` plus this hardening lens).

## Lab

Instrument a tiny service upgrade path documenting **before vs after**:

- allocations / latency micro-benchmark snippet OR a short “pprof/quick bench” rationale if full bench impractical locally,
- a checklist verifying sensitive fields are redacted (`Authorization`, tokens),
- `/debug/pprof` never exposed unintentionally on public ingress (verify current security posture).

