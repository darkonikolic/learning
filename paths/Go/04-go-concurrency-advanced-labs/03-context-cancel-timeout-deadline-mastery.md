# Unit 3 — Context: Cancel, Timeout, and Deadline

## Concept

`context` is how Go propagates cancellation, deadlines, and request-scoped values across goroutines and function calls. Always pass `ctx` as the first argument to functions that do I/O, sleep, or call other services. Always check `ctx.Done()` in loops and before blocking operations. The critical mistake is spawning a fresh `context.Background()` inside a function — this severs the cancellation chain and the child operation runs even after the caller has given up. Use `errors.Is(err, context.DeadlineExceeded)` to check for timeout — never string matching.

## Code

```go
package main

import (
	"context"
	"errors"
	"fmt"
	"time"
)

// fetchURL simulates an HTTP call that takes ~50ms.
// It respects context cancellation.
func fetchURL(ctx context.Context, url string) (string, error) {
	select {
	case <-time.After(50 * time.Millisecond): // simulated latency
		return "body:" + url, nil
	case <-ctx.Done():
		return "", fmt.Errorf("fetchURL %s: %w", url, ctx.Err())
	}
}

// dbQuery simulates a database call that takes ~30ms.
func dbQuery(ctx context.Context, query string) (string, error) {
	select {
	case <-time.After(30 * time.Millisecond):
		return "row:" + query, nil
	case <-ctx.Done():
		return "", fmt.Errorf("dbQuery: %w", ctx.Err())
	}
}

// processRequest simulates an HTTP handler with a 100ms total budget.
// It calls dbQuery then a downstream service.
func processRequest(requestID string) {
	// Outer timeout: the whole request must complete in 100ms.
	ctx, cancel := context.WithTimeout(context.Background(), 100*time.Millisecond)
	defer cancel() // always defer cancel to release resources

	// Step 1: database call (30ms — fits in budget).
	row, err := dbQuery(ctx, "SELECT user WHERE id=1")
	if err != nil {
		fmt.Printf("[%s] db error: %v\n", requestID, err)
		return
	}
	fmt.Printf("[%s] db result: %s\n", requestID, row)

	// Step 2: downstream service with a tighter per-call deadline.
	// Give the downstream service only 40ms of the remaining budget.
	callCtx, callCancel := context.WithTimeout(ctx, 40*time.Millisecond)
	defer callCancel()

	result, err := fetchURL(callCtx, "https://api.example.com/enrich")
	if err != nil {
		if errors.Is(err, context.DeadlineExceeded) {
			fmt.Printf("[%s] downstream timed out\n", requestID)
		} else if errors.Is(err, context.Canceled) {
			fmt.Printf("[%s] request was cancelled\n", requestID)
		} else {
			fmt.Printf("[%s] downstream error: %v\n", requestID, err)
		}
		return
	}
	fmt.Printf("[%s] enriched: %s\n", requestID, result)
}

func main() {
	// req-1: db takes 30ms, downstream takes 50ms but only has 40ms — times out.
	processRequest("req-1")

	fmt.Println()

	// Demonstrate WithCancel: manual cancellation from another goroutine.
	ctx, cancel := context.WithCancel(context.Background())
	go func() {
		time.Sleep(20 * time.Millisecond)
		cancel() // cancel from outside after 20ms
	}()

	_, err := fetchURL(ctx, "https://slow.example.com")
	fmt.Println("manual cancel:", err)
}
```

## Exercise

**Build:** Fetch 10 "URLs" concurrently (simulate each with `time.Sleep` of a random 20–80ms duration). Set a 300ms total context timeout. Launch all 10 as goroutines; collect results into a slice.

**Input:** 10 URLs, 300ms total deadline.

**Output:** Print which URLs succeeded and which were cancelled. The number of successes depends on timing — that is expected.

**Acceptance:** All 10 goroutines must exit cleanly when context expires — no goroutine leak. Use `errors.Is(err, context.DeadlineExceeded)` to categorize results. Run `go test -race ./...`.

## Interview

- Why is creating a new `context.Background()` inside a function a correctness bug?
- What is the difference between `context.WithTimeout` and `context.WithDeadline`?
- How do you check if a context error is a deadline versus a cancellation?
