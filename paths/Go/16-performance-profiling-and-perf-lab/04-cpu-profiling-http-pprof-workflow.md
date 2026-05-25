# Unit 4 — CPU Profiling: HTTP pprof Workflow

## Concept

The pprof HTTP endpoint exposes CPU, heap, goroutine, and mutex profiles. Collect a 30s CPU profile under load with `go tool pprof`. The flame graph shows where CPU time is spent — the widest frame at the top is where time is consumed most. Optimize the widest frame that is your code, not the standard library.

## Code

```go
package main

import (
	"log"
	"net/http"
	_ "net/http/pprof" // registers /debug/pprof/* handlers on DefaultServeMux
)

func main() {
	// Debug server — expose on a separate port, never on the public port.
	go func() {
		log.Println(http.ListenAndServe(":6060", nil))
	}()

	// Your application server.
	mux := http.NewServeMux()
	mux.HandleFunc("/", yourHandler)
	log.Fatal(http.ListenAndServe(":8080", mux))
}

// Collect a 30s CPU profile:
//   go tool pprof http://localhost:6060/debug/pprof/profile?seconds=30
//
// Open interactive browser UI:
//   go tool pprof -http=:8081 http://localhost:6060/debug/pprof/profile?seconds=30
//
// Generate load while collecting (use hey or wrk):
//   hey -n 10000 -c 50 http://localhost:8080/
//
// In the browser: View > Flame Graph
// The widest frame at the top is where your CPU time goes.
```

## Exercise

**Build:** Add pprof to your API service from a prior module. Send 1000 requests with `hey` while collecting a 30s CPU profile. Open the profile in the browser flame graph.
**Input:** 1000 HTTP requests against your running service. CPU profile collected during the load.
**Output:** A flame graph showing the top CPU consumer. Write down: what is the widest frame that belongs to your code (not `runtime` or `net/http`)?
**Acceptance:** You can point to a specific function in the flame graph and explain why it consumes CPU. If the top consumer is framework overhead, document that finding — that is a valid result.

## Interview

- What is the pprof endpoint URL for a CPU profile?
- Why should the debug server run on a different port from the application server?
- What does a wide frame in a CPU flame graph mean?
