# Unit 4 — Execution Trace Overview: go tool trace

## Concept

Execution trace records goroutine scheduling, GC events, and syscall timings with microsecond precision. It is more detailed than pprof — it shows blocking events and goroutine lifecycle, not just where CPU time goes. It is expensive to collect — use it for specific problem investigations (goroutine starvation, unexpected blocking, GC pause spikes), not as always-on instrumentation.

## Code

```go
package main

import (
	"os"
	"runtime/trace"
)

func main() {
	f, _ := os.Create("trace.out")
	defer f.Close()

	trace.Start(f)
	defer trace.Stop()

	// Your work here — the trace captures everything that happens.
	doWork()
}

// Open the trace in the browser:
//   go tool trace trace.out
//
// Navigate to:
//   "Goroutine analysis" — see per-goroutine blocking time
//   "View trace"         — timeline of all goroutines, GC events, syscalls
//   "Stop-the-world"     — GC pause durations
//
// For HTTP services, collect trace via pprof endpoint:
//   curl http://localhost:6060/debug/pprof/trace?seconds=5 > trace.out
//   go tool trace trace.out
```

## Exercise

**Build:** Add trace collection to your API service. Send 100 requests while collecting a 5s trace. Open it in the browser.
**Input:** 100 HTTP requests against the running service. 5s trace collected via the pprof endpoint.
**Output:** Find and record: (1) how long the longest GC stop-the-world pause is, (2) which goroutines block the longest, (3) how many goroutines are active at peak load.
**Acceptance:** You can navigate to "Goroutine analysis" and identify the top blocking goroutine. You can find at least one GC event in the timeline view and read its pause duration.

## Interview

- What is the difference between a pprof CPU profile and an execution trace?
- Why is trace collection more expensive than pprof profiling?
- Name two events visible in an execution trace that are not visible in a CPU profile.
