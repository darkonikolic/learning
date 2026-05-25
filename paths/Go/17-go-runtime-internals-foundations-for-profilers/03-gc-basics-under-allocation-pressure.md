# Unit 3 — GC Basics Under Allocation Pressure

## Concept

Go's GC is concurrent — it runs alongside your program with short stop-the-world pauses. GC triggers when the heap grows to 2× live data (GOGC=100). `GOMEMLIMIT` (Go 1.19+) sets a hard memory ceiling — when approached, GC runs more frequently regardless of GOGC. High allocation rate = frequent GC = latency spikes.

## Code

```go
package main

import (
	"fmt"
	"runtime"
)

func printMemStats(label string) {
	var m runtime.MemStats
	runtime.ReadMemStats(&m)
	fmt.Printf("%s: HeapAlloc=%dKB NumGC=%d PauseTotalNs=%dms\n",
		label,
		m.HeapAlloc/1024,
		m.NumGC,
		m.PauseTotalNs/1e6,
	)
}

func allocate(n int) {
	for i := 0; i < n; i++ {
		_ = make([]byte, 1024) // 1KB per iteration
	}
}

func main() {
	printMemStats("before")
	allocate(100_000)
	printMemStats("after")
	runtime.GC()
	printMemStats("after GC")
}

// Experiment with environment variables:
//   GOGC=100    (default) — GC when heap doubles
//   GOGC=200    — GC less often, more memory used, fewer pauses
//   GOGC=off    — no GC — maximum throughput, unbounded memory
//   GOMEMLIMIT=128MiB — hard ceiling — GC runs aggressively when approaching limit
//
// Run:
//   GOGC=off   go run main.go
//   GOGC=100   go run main.go
//   GOGC=off GOMEMLIMIT=64MiB go run main.go
```

## Exercise

**Build:** Write a benchmark that allocates 1KB slices in a tight loop (`b.N` iterations). Run it three ways and record throughput (ns/op).
**Input:** `go test -bench=. -count=3` with GOGC=100, GOGC=off, and GOGC=off GOMEMLIMIT=64MiB
**Output:** ns/op for each configuration. Which is fastest? What happens with GOMEMLIMIT when you allocate more than the limit?
**Acceptance:** GOGC=off is fastest (no GC pauses). GOGC=off with GOMEMLIMIT shows GC kicking in once memory approaches the limit, raising ns/op. You can explain why.

## Interview

- What does GOGC=100 mean in plain English?
- Why might GOGC=off in production be dangerous without GOMEMLIMIT?
- What is a stop-the-world GC pause and how long are typical Go GC pauses?
