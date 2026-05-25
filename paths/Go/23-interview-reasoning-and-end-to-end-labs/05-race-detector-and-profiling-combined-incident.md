# Unit 5 — Race Detector and Profiling: Combined Incident

## Concept

Real incidents combine multiple issues. A slow endpoint under load triggers both a data race and a memory spike. Fix the race first — a race is a correctness bug and can produce data corruption or crashes. Then address the allocation — a performance problem. The race detector (`-race`) finds races at runtime by instrumenting memory accesses. The benchmark `-benchmem` flag shows allocations per operation. Fix the race with a mutex or channel. Fix the allocation by reusing objects or reducing copies.

## Code

```go
package main

import (
	"net/http"
	"sync"
)

// BUGGY handler: shared map with no lock — DATA RACE.
// Also allocates a new map on every request — UNNECESSARY ALLOCATION.

var requestCounts map[string]int // shared, unprotected

func countHandler(w http.ResponseWriter, r *http.Request) {
	requestCounts[r.URL.Path]++ // RACE: concurrent reads and writes
	w.WriteHeader(http.StatusOK)
}

// FIXED handler: mutex protects the map, same map reused across requests.

type Counter struct {
	mu     sync.Mutex
	counts map[string]int
}

func NewCounter() *Counter {
	return &Counter{counts: make(map[string]int)}
}

func (c *Counter) Handler(w http.ResponseWriter, r *http.Request) {
	c.mu.Lock()
	c.counts[r.URL.Path]++
	c.mu.Unlock()
	w.WriteHeader(http.StatusOK)
}

// To reproduce the race:
//   go test -race -count=100 -run TestCountHandler
//
// The race detector will report:
//   WARNING: DATA RACE
//   Write at 0x... by goroutine N:
//   Previous read at 0x... by goroutine M:
//
// To find the allocation hot spot:
//   go test -bench=BenchmarkCountHandler -benchmem
//   Look for allocs/op > 0 in the hot path.
//
// After fixing:
//   go test -race -count=100 -run TestCountHandler   → no race reported
//   go test -bench=BenchmarkCountHandler -benchmem   → allocs/op should drop

func main() {
	requestCounts = make(map[string]int)

	counter := NewCounter()

	mux := http.NewServeMux()
	mux.HandleFunc("/buggy", countHandler)         // has race
	mux.HandleFunc("/fixed", counter.Handler)      // race-free

	http.ListenAndServe(":8080", mux)
}
```

## Exercise

**Build:** Reproduce the data race in `countHandler`, fix it, then find and fix the allocation hot spot.
**Input:** The buggy `countHandler` above.
**Output:** A fixed handler that passes `go test -race -count=100` and shows reduced `allocs/op` in benchmarks.
**Acceptance:** (1) Write a test that sends 100 concurrent requests to `countHandler`. Run with `-race` — the race detector must fire. (2) Apply the `Counter` fix. Run with `-race` again — no race reported. (3) Write a benchmark for the fixed handler. Run with `-benchmem`. Identify if there are unnecessary allocations in the hot path and eliminate them. (4) Final state: `-race` clean, `allocs/op` is 0 or minimized in the benchmark.

## Interview

- The race detector does not find all races. What kind of race does it miss?
- You see `allocs/op: 48` in a benchmark for a simple counter increment. What are the likely causes?
- A race causes a map to panic with "concurrent map read and map write" in production. The race detector was not enabled. How do you reproduce and confirm the fix before deploying?
