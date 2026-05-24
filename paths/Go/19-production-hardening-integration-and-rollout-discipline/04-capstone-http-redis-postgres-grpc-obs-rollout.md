# Unit 4 — Capstone: hardened stack rehearsal (HTTP + Redis + Postgres + gRPC + metrics/trace + shutdown)

Assemble **one runnable slice** exercising previously separated concerns together—scope honesty permitted via stubs if each boundary labelled clearly (`// STUB:` with behaviour contract).

Mandatory integration checklist:

| Capability | Requirement |
|-----------|--------------|
| HTTP API edge | timeouts + graceful shutdown hooked |
| Redis | caching / rate-limit backend / ephemeral lock illustrative—pick one purposeful use |
| Postgres | real query path OR documented stubbed interface bridging Area 08 |
| gRPC collaborator | unary call respecting deadlines |
| Metrics | Prometheus scrape endpoint or pull exporter pattern |
| Tracing | OTEL exporting stub acceptable if propagation proven locally |
| Probes | `/health` + `/ready` policy written down |
| Docs | WHY certain toggles/timeouts chosen—not code-only submission |

Produce a concise **risk note**: what fails first under load spike and what signals prove it.

