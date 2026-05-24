# Unit 1 — Performance mindset shift for `perf-lab/`

> **Informative cadence:** historically ~twelve deepening blocks aligning ~1–1.5 h/day authoring intent—**folder order only**.

Reject vague “slow” emotions. Acquire **measurable evidence** distinguishing:

```
CPU hotspots vs allocation pressure/GC chatter vs contention vs IO/database/network culprits
```

Spine codebase: **`perf-lab/`** housing micro workloads you benchmark & profile—not production microservices yet.

Signature tooling internalisation:

```
go test -bench=. / select benches
go test -bench=. -benchmem
go tool pprof (CPU / heap endpoints or profile files)
net/http/pprof hooking practise eventually (next units)
```

