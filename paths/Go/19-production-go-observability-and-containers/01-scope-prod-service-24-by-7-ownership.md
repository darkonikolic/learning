# Unit 1 — Scope: Production Service, 24/7 Ownership

## Concept

A service running in production needs more than working code. It needs a Docker image that builds deterministically, health probes so Kubernetes knows when to route traffic, graceful shutdown so in-flight requests complete before the process exits, structured logs so operators can search and correlate events, and distributed tracing so you can follow a request across services. This module takes your existing HTTP API and adds each of these layers. By the end, the service is deployable to Kubernetes with the observability stack a real team expects.

## Code

```go
// Production service checklist — each item maps to a unit in this module.
//
// [ ] Docker image
//     - Multi-stage build: builder (golang:1.23) → runtime (scratch/distroless)
//     - CGO_ENABLED=0 for static binary
//     - Non-root user in final image
//
// [ ] Health probes
//     GET /health/live  → 200 always (process is up)
//     GET /health/ready → 200 if deps reachable, 503 if not
//
// [ ] Graceful shutdown
//     - Catch SIGTERM
//     - Stop accepting new connections
//     - Drain in-flight requests (30s budget)
//     - Flush logs, close DB pool
//
// [ ] Structured logging
//     - slog with JSON handler in production
//     - Every request: method, path, status, latency, trace_id
//     - Never log PII
//
// [ ] OTel tracing
//     - initTracer with OTLP exporter
//     - Middleware creates one span per request
//     - Propagate trace context downstream (HTTP headers)
//
// [ ] Kubernetes deployment
//     - resources.requests and resources.limits set
//     - livenessProbe and readinessProbe configured
//     - terminationGracePeriodSeconds >= shutdown budget

package main

import "fmt"

func main() {
	fmt.Println("See units 02-05 for each item above.")
}
```

## Exercise

**Build:** Read through the checklist above and map each item to one of units 02-05 in this module.
**Input:** Your existing HTTP API service from a previous module.
**Output:** A written list: for each checklist item, which file you will change and what you expect to add.
**Acceptance:** You can explain to someone why each item matters in a production incident — what breaks if it is missing.

## Interview

- What is the difference between a liveness probe and a readiness probe? What goes wrong if you conflate them?
- Why does graceful shutdown matter in a rolling deployment?
- What does "structured logging" give you that plain text logs do not?
