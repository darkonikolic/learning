# Unit 1 — Scheduler: GMP, Preemption, and Syscall Blocking

## Concept

Go 1.14+ uses asynchronous preemption — signals interrupt even tight CPU loops, so other goroutines get CPU time without explicit yield points. Syscalls use a handoff protocol: the M parks, the P moves to another M, the syscall completes, the M tries to acquire a P. Network I/O uses the netpoller (epoll/kqueue) — a goroutine parks, the OS notifies the netpoller when the socket is ready, the goroutine is rescheduled.

## Code

```go
package main

import (
	"fmt"
	"runtime"
	"sync/atomic"
	"time"
)

func main() {
	runtime.GOMAXPROCS(1) // single P: demonstrates preemption

	var counter int64
	done := make(chan struct{})

	// Tight loop — no explicit yield. In Go 1.14+ this goroutine
	// is preempted by signals, allowing other goroutines to run.
	go func() {
		for {
			select {
			case <-done:
				return
			default:
				atomic.AddInt64(&counter, 1)
			}
		}
	}()

	// This goroutine can run even though the above loop never yields.
	// Without async preemption (Go <1.14 with GOMAXPROCS=1) this would starve.
	go func() {
		time.Sleep(100 * time.Millisecond)
		close(done)
	}()

	time.Sleep(200 * time.Millisecond)
	fmt.Printf("counter=%d (both goroutines ran despite tight loop)\n", atomic.LoadInt64(&counter))
}
```

## Exercise

**Build:** Run the program above with `GOMAXPROCS=1`. Add `runtime.Gosched()` inside the tight loop and measure if it makes any difference to scheduling fairness.
**Input:** Two goroutines on GOMAXPROCS=1 — one tight loop, one that sleeps 100ms then signals done
**Output:** Confirm the second goroutine's signal was received (the loop stopped). Compare counter values with and without `runtime.Gosched()`.
**Acceptance:** The program terminates in ~200ms with GOMAXPROCS=1, proving the tight loop goroutine was preempted. Document whether `Gosched()` changes the counter value significantly.

## Interview

- What is asynchronous preemption and which Go version introduced it?
- When a goroutine makes a blocking syscall, what happens to its P?
- What is the netpoller and why does it allow goroutines to park without blocking an OS thread?
