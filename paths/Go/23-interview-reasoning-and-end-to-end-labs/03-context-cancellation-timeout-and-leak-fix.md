# Unit 3 — Context Cancellation, Timeout, and Leak Fix

## Concept

A goroutine leak is a goroutine that blocks forever because no one reads from its channel or because it does not check `ctx.Done()`. Leaks accumulate silently — the goroutine count grows with every request and never falls. Use `runtime.NumGoroutine()` in tests to detect leaks: record the count before, run the operation, wait briefly, check the count after. The fix is always the same: every goroutine that blocks must select on `ctx.Done()` so it exits when the caller cancels.

## Code

```go
package main

import (
	"context"
	"fmt"
	"runtime"
	"time"
)

// LEAKY: goroutine blocks forever if ctx is cancelled before work completes.
func leakyWorker(ctx context.Context, jobs <-chan int) {
	go func() {
		for job := range jobs { // blocks here if jobs is never closed
			fmt.Println("processing", job)
		}
	}()
}

// FIXED: goroutine exits when ctx is cancelled.
func fixedWorker(ctx context.Context, jobs <-chan int) {
	go func() {
		for {
			select {
			case job, ok := <-jobs:
				if !ok {
					return // channel closed — exit cleanly
				}
				fmt.Println("processing", job)
			case <-ctx.Done():
				return // context cancelled — exit cleanly
			}
		}
	}()
}

// TestNoGoroutineLeak shows the test pattern.
// In a real test: use testing.T and a shorter wait.
func TestNoGoroutineLeak() {
	before := runtime.NumGoroutine()

	jobs := make(chan int, 10)
	ctx, cancel := context.WithCancel(context.Background())

	fixedWorker(ctx, jobs)
	jobs <- 1
	jobs <- 2

	// Cancel context — goroutine should exit.
	cancel()

	// Give goroutine time to exit.
	time.Sleep(10 * time.Millisecond)

	after := runtime.NumGoroutine()
	if after > before {
		fmt.Printf("LEAK: goroutine count went from %d to %d\n", before, after)
	} else {
		fmt.Println("OK: no goroutine leak")
	}
}

func main() {
	TestNoGoroutineLeak()
}
```

## Exercise

**Build:** Write a test that verifies your worker pool has no goroutine leak.
**Input:** Your worker pool implementation from a previous module.
**Output:** A `TestWorkerPoolNoLeak` test that passes with `go test -race`.
**Acceptance:** (1) Record goroutine count before starting the pool. (2) Start the pool, send 10 jobs, cancel the context. (3) `time.Sleep(100 * time.Millisecond)` to allow cleanup. (4) Assert goroutine count has returned to the baseline (±2 for test infrastructure). (5) The test must also pass with `go test -race` — no races during shutdown.

## Interview

- How do you detect a goroutine leak in a test?
- A goroutine is stuck waiting on a channel that will never receive. What are your two options for fixing this?
- Why does `context.WithTimeout` not guarantee the goroutine exits after the timeout?
