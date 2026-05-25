# Unit 4 — Capstone: HTTP + Redis + Postgres + gRPC + Observability + Rollout

## Concept

A production-ready service is not one feature — it is the combination of all concerns working together without conflict. Graceful shutdown must flush the OTel exporter before closing. The readiness probe must check all dependencies the service actively uses. Resource limits must be set before HPA is configured. Structured logs must include the trace ID so you can correlate a log line with the trace in Jaeger. This capstone wires everything together.

## Code

```go
// Production readiness checklist — verify each item before calling a service production-ready.
//
// BINARY AND IMAGE
// [ ] Multi-stage Dockerfile, scratch or distroless final base
// [ ] CGO_ENABLED=0, static binary
// [ ] Image size < 20 MB
// [ ] Non-root user in container
//
// HEALTH
// [ ] GET /health/live  returns 200 always
// [ ] GET /health/ready returns 503 when DB or cache unavailable
// [ ] Readiness check uses 2s timeout per dependency
//
// SHUTDOWN
// [ ] Catches SIGTERM via signal.Notify
// [ ] http.Server.Shutdown called with context
// [ ] Shutdown budget (25s) < terminationGracePeriodSeconds (35s)
// [ ] OTel provider flushed in shutdown sequence
// [ ] DB pool closed after server.Shutdown returns
//
// OBSERVABILITY
// [ ] slog with JSON handler in production
// [ ] Every request logged: method, path, status, latency_ms, trace_id
// [ ] OTel tracing: one span per request, child spans for DB and Redis calls
// [ ] trace_id injected into log fields from span context
//
// KUBERNETES
// [ ] resources.requests and resources.limits set on all containers
// [ ] livenessProbe configured (path, initialDelay, period, failureThreshold)
// [ ] readinessProbe configured (path, initialDelay, period, failureThreshold)
// [ ] terminationGracePeriodSeconds set
// [ ] HPA configured with minReplicas >= 2
// [ ] Ingress configured with TLS
//
// CONFIG
// [ ] All config from env vars
// [ ] Missing required vars cause fail-fast exit at startup
// [ ] No secrets in code or Docker image layers
```

## Exercise

**Build:** Deploy your complete e-commerce API service to a local Kubernetes cluster (minikube or kind) with all items on the checklist above.
**Input:** Your API service with PostgreSQL, Redis, and at least two endpoints.
**Output:** A running service in Kubernetes with Jaeger for traces and structured logs.
**Acceptance:** (1) Run `hey -z 30s -c 20 http://<ingress-ip>/api/v1/products`. (2) Open Jaeger UI — traces must appear for each request with DB and Redis spans. (3) Check pod logs — each log line must be JSON with a `trace_id` field. (4) Run `kubectl get hpa -w` — observe scale-up under load. (5) Trigger a rolling update — zero 5xx errors during the rollout.

## Interview

- During shutdown, in what order should you close resources: HTTP server, OTel exporter, DB pool, log flush?
- A trace shows a request took 800 ms but your logs show 200 ms latency. What would explain the discrepancy?
- What breaks first if you deploy without setting `resources.requests`?
