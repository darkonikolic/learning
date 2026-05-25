# Unit 3 — Channels: Share by Communicating

## Concept

A channel transfers ownership of a value from one goroutine to another — no shared memory, no locks needed for the transfer itself. An unbuffered channel forces a rendezvous: the sender blocks until a receiver is ready, and the receiver blocks until a sender sends. Use directional channel types in function signatures (`chan<- int` for send-only, `<-chan int` for receive-only) — they document intent and the compiler enforces them. Close a channel from the sender side when there are no more values; receivers use `range` to drain it cleanly.

## Code

```go
package main

import (
	"fmt"
	"sync"
)

// producer sends job IDs on a send-only channel, then closes it.
// Closing signals to consumers: no more jobs are coming.
func producer(jobs chan<- int, count int) {
	for i := 1; i <= count; i++ {
		jobs <- i // blocks until a consumer is ready (unbuffered channel)
	}
	close(jobs) // sender closes, never the receiver
}

// consumer reads from a receive-only channel until it is closed and drained.
func consumer(id int, jobs <-chan int, wg *sync.WaitGroup) {
	defer wg.Done()
	for job := range jobs { // range exits when channel is closed AND empty
		fmt.Printf("consumer %d: processed job %d\n", id, job)
	}
}

func main() {
	jobs := make(chan int) // unbuffered: every send blocks until a receive is ready
	var wg sync.WaitGroup

	// Start 2 consumers — they race to receive from the same channel.
	wg.Add(2)
	go consumer(1, jobs, &wg)
	go consumer(2, jobs, &wg)

	// Producer runs concurrently; it will block on each send until a consumer picks up.
	go producer(jobs, 6)

	wg.Wait()
	fmt.Println("pipeline complete — 6 jobs processed by 2 consumers")
}
```

## Exercise

**Build:** A two-stage pipeline: `generate(n int) <-chan int` produces integers 1 through n, `square(in <-chan int) <-chan int` reads from the first channel and sends each value squared. Chain them and print the results in main.

**Input:** `n = 5`

**Output:**
```
1
4
9
16
25
```

**Acceptance:** Both `generate` and `square` must close their output channels when done. Main must drain the final channel with `range` — no `WaitGroup` needed. Run `go test -race ./...` — no race conditions.

## Interview

- Why must only the sender close a channel? What happens if a receiver closes it?
- What is the difference between `for v := range ch` and `for { v := <-ch }`?
- How do directional channel types (`chan<-`, `<-chan`) improve code clarity and safety?
