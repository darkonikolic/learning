# Unit 5 — Race detector + profiling combined incident

Scenario:

```
CPU pegged + memory rising + workers “slow”
```

Use:

```
go test -race / go run -race on representative paths
pprof CPU + heap (and goroutine profile if suspect leaks)
```

## Deliverable

Incident write-up: hypothesis list ordered by likelihood, evidence collected, fix, verification, trade-offs.
