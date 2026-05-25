# Go Learning Path

23 modules from fundamentals to staff-level runtime. Practically oriented — each module has a `00-quick-reference.md` cheatsheet and code anchors in unit files.

## Module Map

| # | Module | Focus | Project |
|---|--------|-------|---------|
| 01 | go-fundamentals-and-cli-thinking | Structs, interfaces, pointers, errors | `go-lab/` |
| 02 | go-tooling-engineering-workflow | go toolchain, Delve, Makefile | — |
| 03 | go-concurrency-and-queue-workers | goroutines, channels, select | `go-lab/` |
| 04 | go-concurrency-advanced-labs | sync, errgroup, worker pool | `go-lab/` |
| 05 | http-apis-service-ownership-and-chi | HTTP handlers, chi, DTOs, validation | `api-service/` |
| 06 | grpc-protobuf-and-service-contracts | proto3, gRPC, streaming, interceptors | `api-service/` |
| 07 | serialization-http-grpc-tradeoffs | JSON, protobuf, decision matrix | — |
| 08 | persistence-sql-postgresql-and-sqlx | sqlx, repository pattern, transactions | `api-service/` |
| 09 | testing-engineering-go-services | table-driven, testcontainers, gomock, benchmarks | all |
| 10 | testing-advanced-contracts-integration-and-mocks | subtests, contract testing, flake hygiene | all |
| 11 | caching-redis-and-invalidations | go-redis, cache-aside, singleflight | `api-service/` |
| 12 | backend-architecture-ownership-and-design | packages, clean arch, DI, DDD | `api-service/` |
| 13 | distributed-systems-resilience-and-messaging | timeouts, retries, idempotency | `api-service/` |
| 14 | workflow-durable-execution-and-temporal-concepts | Temporal Go SDK, signals, retries | `workflow-service/` |
| 15 | messaging-advanced-kafka-and-event-ownership | kafka-go, consumer groups, outbox/inbox | `event-service/` |
| 16 | performance-profiling-and-perf-lab | benchmarks, pprof, allocation pressure | all |
| 17 | go-runtime-internals-foundations-for-profilers | GMP, escape analysis, GC, trace | — |
| 18 | go-runtime-deep-dive-staff-level | sync.Pool, false sharing, preemption | — |
| 19 | production-go-observability-and-containers | Docker, health probes, graceful shutdown | `prod-service/` |
| 20 | kubernetes-backend-advanced-placement-and-ingress | HPA, resources, rolling deploy, ingress | — |
| 21 | production-hardening-integration-and-rollout-discipline | OTel, slog, config, govulncheck | `prod-service/` |
| 22 | backend-security-authn-authz-and-abuse | JWT, RBAC, rate limiting, OWASP | `api-service/` |
| 23 | interview-reasoning-and-end-to-end-labs | Gotchas, drills, end-to-end scenarios | all |

## Projects used across modules
- `go-lab/` — fundamentals practice, grows through modules 01-04
- `api-service/` — HTTP/gRPC service, grows through modules 05-13, 22
- `workflow-service/` — Temporal workflows, module 14
- `event-service/` — Kafka producer/consumer, module 15
- `prod-service/` — production hardening target, modules 19, 21
