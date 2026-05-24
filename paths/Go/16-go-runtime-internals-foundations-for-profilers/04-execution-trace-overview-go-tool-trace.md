# Unit 4 — Execution trace alongside `pprof` (when wall-clock latency hides CPU-only blind spots)

Use `go tool trace` over a bounded window when:

- CPU profiles look fine but latency tails are bad (scheduling/blocking blindness),
- you suspect goroutine coordination or syscall waits dominate wall time.

Traces grow large quickly—capture short, representative workloads and delete artefacts you do not need.
