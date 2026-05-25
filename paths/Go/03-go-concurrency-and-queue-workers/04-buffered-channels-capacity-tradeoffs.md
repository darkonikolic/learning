# Unit 4 — Buffered Channels: Capacity and Tradeoffs

## Concept

A buffered channel (`make(chan T, N)`) lets the sender proceed without a receiver until the buffer is full. Once full, the sender blocks — just like an unbuffered channel. This is useful for absorbing short bursts: a producer can send N items before it has to wait. But buffering hides backpressure: if you buffer too much, your system accepts more work than it can handle and you get memory growth instead of a clear "slow down" signal. Choose buffer size based on expected burst, not as a way to avoid thinking about flow control.

## Code

```go
package main

import (
	"fmt"
	"time"
)

func main() {
	// Unbuffered: every send blocks until someone receives.
	unbuffered := make(chan int)
	go func() {
		start := time.Now()
		for i := 1; i <= 3; i++ {
			unbuffered <- i
			fmt.Printf("unbuffered: sent %d after %v\n", i, time.Since(start).Round(time.Millisecond))
		}
		close(unbuffered)
	}()
	for v := range unbuffered {
		time.Sleep(20 * time.Millisecond) // slow consumer
		fmt.Printf("unbuffered: received %d\n", v)
	}

	fmt.Println()

	// Buffered: sender can put up to 3 items without blocking.
	buffered := make(chan int, 3)
	start := time.Now()
	buffered <- 1 // does not block — buffer has room
	buffered <- 2
	buffered <- 3
	fmt.Printf("buffered: all 3 sent in %v (no receiver yet)\n", time.Since(start).Round(time.Millisecond))

	// Fourth send would block because buffer is full.
	// buffered <- 4  // deadlock if uncommented here with no receiver

	close(buffered)
	for v := range buffered {
		fmt.Printf("buffered: received %d\n", v)
	}

	// Measure producer wait time when buffer fills up.
	bursty := make(chan int, 5)
	go func() {
		for i := 1; i <= 10; i++ {
			t := time.Now()
			bursty <- i
			waited := time.Since(t)
			if waited > time.Millisecond {
				fmt.Printf("producer blocked on item %d for %v (buffer full)\n", i, waited.Round(time.Millisecond))
			}
		}
		close(bursty)
	}()
	for v := range bursty {
		time.Sleep(15 * time.Millisecond) // consumer slower than producer
		_ = v
	}
}
```

## Exercise

**Build:** A rate-limited batch processor. Producer sends 20 jobs into a buffered channel of size 5. Consumer processes each job in 10ms. Use `time.Now()` to measure how long the producer is blocked each time the buffer fills.

**Input:** 20 jobs, buffer size 5, consumer 10ms per job.

**Output:** Print which job number caused the producer to block and for how long.

**Acceptance:** The total runtime should be roughly `20 * 10ms / 1 consumer = 200ms` (not 0ms, which would indicate buffering masked all wait). Run `go test -race ./...`.

## Interview

- A buffered channel of size 100 never blocks the producer. Is this a good thing?
- What is the observable difference between a buffer-full block and a deadlock?
- When would you use an unbuffered channel even when you know the sender is faster than the receiver?
