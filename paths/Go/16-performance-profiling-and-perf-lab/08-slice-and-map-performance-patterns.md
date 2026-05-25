# Unit 8 — Slice & map performance: capacity, growth, bucket physics (high level)

Slice preallocation:

```go
s := make([]T, 0, 1000) // fewer reallocations vs blind append growth
```

Maps: growth & rehash events exist—avoid hot loops recreating maps unintentionally; pre-size when approximate cardinality known.

## Lab

Benchmark **prealloc vs naive append** and a **map heavy** micro workload; narrate `B/op` + allocs/op shifts.

## Interview prompts

When preallocation misleads (overalloc memory permanently for tiny inputs).

Map iteration order non-determinism unrelated but often adjacent confusion—don’t conflate with perf story unless relevant.
