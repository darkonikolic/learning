# Unit 2 — Benchmark discipline: interpreting `go test -bench`

## Outcomes

- Write meaningful benchmarks (**string parse variants**, **`encoding/json`** decode workloads, **`map`** lookup micro shapes).
- Compare **Implementations A/B** without cargo-cult `B/op` fantasies—you still reason about compiler optimisations / dead-store elimination pitfalls.

Starter patterns:

```
go test -bench=.
go test -bench=. -benchmem
go test -bench=. -benchtime=… (when smoothing noise conscientiously—avoid benchmarking forever chasing ghosts)
```

## Lab

Pick two parsing strategies (regex vs hand-rolled tokenizer mini, or `strconv` variants) and document **which metric moved** (ns/op, allocs/op) and **why** you trust the comparison setup (same CPU governor awareness high-level okay).

## Interview prompts

Micro-benchmark traps: compiler eliding work, unrealistic tiny inputs, no `-benchmem` blind spots.
