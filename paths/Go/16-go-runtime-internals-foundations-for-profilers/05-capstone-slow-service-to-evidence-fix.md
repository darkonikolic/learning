# Unit 5 — Capstone drill: synthetic slow service → profiler → tracer → guarded optimisation

Compose **one** knowingly flawed service binary in `perf-lab/` exhibiting:

```
CPU bottleneck branch AND subtle blocking wait concurrently (mix signals)
potential memory retention OR goroutine buildup optional accent
```

You must traverse:

```
CPU pprof → hypothesis
go tool trace (optional) → validate scheduling / wait suspicion
Heap / goroutine profile if retention suspected
implement smallest effective change with before/after evidence
reject readability-destroying micro-optimisations without measured wins
```
