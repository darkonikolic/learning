# Unit 1 — Production mindset & `prod-service/` spine

> **Informative cadence:** historically ~twelve deepening blocks aligning ~1–1.5 h/day authoring intent—**ordering only**.

## Outcome metamorphosis

Stop celebrating “runs on my laptop.” Pursue artefacts proving **survivability 24/7**:

```
Structured logs with correlation identifiers
metrics (Prometheus exposition patterns ideologically—even if scraping infra stubbed mentally)
tracing (OpenTelemetry bridging multi-hop flows)
containers (Docker reproducibility—not hero builds)
graceful degradation signals (health vs readiness distinctions)
conceptual Kubernetes awareness (pods/deployments/services) without pretending admin mastery prematurely unless your role demands deepening elsewhere intentionally
```

Spine codebase: **`prod-service/`** (HTTP/gRPC hybrids acceptable if bounded—avoid scope explosion uncontrolled ethically warn learners responsibly).
