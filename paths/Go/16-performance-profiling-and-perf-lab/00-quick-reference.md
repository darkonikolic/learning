# Quick Reference — Performance Profiling

## Benchmark flags
```
go test -bench=.              # run all benchmarks
go test -bench=BenchmarkFoo   # specific
go test -benchmem             # show allocations
go test -count=3              # run N times (check variance)
go test -cpuprofile cpu.out   # save CPU profile
go test -memprofile mem.out   # save memory profile
```

## pprof HTTP endpoint
```go
import _ "net/http/pprof"
go http.ListenAndServe("localhost:6060", nil)
```

```
# collect 30s CPU profile
go tool pprof http://localhost:6060/debug/pprof/profile?seconds=30
# heap
go tool pprof http://localhost:6060/debug/pprof/heap
```

## pprof commands
```
(pprof) top10           # top 10 by CPU/alloc
(pprof) web             # flame graph (needs graphviz)
(pprof) list funcName   # annotate source
(pprof) peek funcName   # callers + callees
```

## Reading -benchmem output
```
BenchmarkFoo  1000000  1234 ns/op  128 B/op  3 allocs/op
                               ↑           ↑        ↑
                          nanosec   bytes/call  alloc count
```

## Allocation reduction
```
strings.Builder > string concat in loop
sync.Pool for frequently allocated objects
preallocate slices: make([]T, 0, knownCap)
```
