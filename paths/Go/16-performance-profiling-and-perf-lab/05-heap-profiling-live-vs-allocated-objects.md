# Unit 5 — Heap Profiling: Live vs Allocated Objects

## Concept

`inuse_objects` is what is alive right now. `alloc_objects` is total allocated since start — this measures GC pressure even if objects are collected quickly. Run `runtime.GC()` before taking a heap profile for a cleaner picture of what is actually live. A function that allocates a lot but GCs quickly is less harmful than one with long-lived allocations.

## Code

```go
package main

import (
	"net/http"
	"runtime"
	_ "net/http/pprof"
)

// Simulate a leak: allocating a large slice on every request and keeping
// a reference in a global slice prevents GC from collecting them.
var leak [][]byte

func leakyHandler(w http.ResponseWriter, r *http.Request) {
	buf := make([]byte, 1<<20) // 1 MB per request
	leak = append(leak, buf)   // retains reference — never collected
	w.WriteHeader(http.StatusOK)
}

// Non-leaky: allocate, use, let go — GC collects after each request.
func cleanHandler(w http.ResponseWriter, r *http.Request) {
	buf := make([]byte, 1<<20)
	_ = buf // used, then eligible for GC
	w.WriteHeader(http.StatusOK)
}

// Force GC then take a heap profile snapshot:
//   curl http://localhost:6060/debug/pprof/heap?gc=1 > heap1.prof
//   go tool pprof -http=:8081 heap1.prof
//
// Wait 10s, repeat:
//   curl http://localhost:6060/debug/pprof/heap?gc=1 > heap2.prof
//
// In the browser: switch between "inuse_space" and "alloc_space" views.
// inuse_space grows over time with leakyHandler but stays flat with cleanHandler.
```

## Exercise

**Build:** Add `leakyHandler` to a test server. Send 50 requests. Collect heap profiles 10s apart. Compare `inuse_objects` between the two profiles.
**Input:** 50 POST requests to `/leak`. Two heap profiles taken 10s apart.
**Output:** Profile 1 and Profile 2 `inuse_space` values. Show the growth. Then switch to `cleanHandler`, repeat — show `inuse_space` stays flat.
**Acceptance:** With `leakyHandler`: inuse_space in profile 2 is larger than in profile 1. With `cleanHandler`: inuse_space is approximately equal between profiles.

## Interview

- What is the difference between `inuse_objects` and `alloc_objects` in a heap profile?
- Why run `runtime.GC()` before taking a heap snapshot?
- A heap profile shows high `alloc_space` but low `inuse_space`. Is there a memory leak?
