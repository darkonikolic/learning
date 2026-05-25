# Unit 5 — select: Multi-Case Coordination

## Concept

`select` waits on multiple channels simultaneously and proceeds on whichever becomes ready first. If multiple cases are ready at the same time, Go picks one at random — never rely on ordering. The most important use of `select` is combining a work channel with `ctx.Done()`: when the context is cancelled, the goroutine exits cleanly instead of being stuck waiting for work that will never come. Never add a `default` case unless you explicitly want non-blocking polling — a `default` in a loop becomes a busy-spin that pegs the CPU.

## Code

```go
package main

import (
	"context"
	"fmt"
	"time"
)

// worker processes jobs until the channel is closed or the context is done.
func worker(ctx context.Context, id int, jobs <-chan int) {
	for {
		select {
		case job, ok := <-jobs:
			if !ok {
				fmt.Printf("worker %d: jobs channel closed, exiting\n", id)
				return
			}
			fmt.Printf("worker %d: processing job %d\n", id, job)
			time.Sleep(30 * time.Millisecond) // simulate work

		case <-ctx.Done():
			// Context timed out or was cancelled — stop accepting new work.
			fmt.Printf("worker %d: context done (%v), exiting\n", id, ctx.Err())
			return

			// No default case: without it, select blocks until one case is ready.
			// A default here would spin the CPU when both channels are empty.
		}
	}
}

func main() {
	// Give the whole operation 200ms.
	ctx, cancel := context.WithTimeout(context.Background(), 200*time.Millisecond)
	defer cancel()

	jobs := make(chan int, 10)

	// Send 8 jobs spaced 30ms apart — total 240ms, which exceeds the 200ms deadline.
	go func() {
		for i := 1; i <= 8; i++ {
			select {
			case jobs <- i:
				fmt.Printf("sent job %d\n", i)
				time.Sleep(30 * time.Millisecond)
			case <-ctx.Done():
				fmt.Println("producer cancelled, closing jobs channel")
				close(jobs)
				return
			}
		}
		close(jobs)
	}()

	worker(ctx, 1, jobs)
	fmt.Println("done")
}
```

## Exercise

**Build:** A worker that processes jobs but stops after 200ms (use `context.WithTimeout`). Jobs take 30ms each. The producer sends one job every 25ms for as long as the context is alive.

**Input:** 200ms timeout, 30ms per job, jobs arriving every 25ms.

**Output:** Print each job processed. When the timeout fires, print how many jobs were processed.

**Acceptance:** The program must exit cleanly — no goroutine leak (verify with `runtime.NumGoroutine()` at the end). In-flight job must complete before the worker exits. Run `go test -race ./...`.

## Interview

- What happens when multiple `select` cases are ready simultaneously?
- Why is adding a `default` case to a `select` loop dangerous?
- How does `select` on `ctx.Done()` differ from `select` on a dedicated `quit chan struct{}`?
