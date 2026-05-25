# Unit 4 — Goroutine Leaks, Deadlocks, and Unblocking Drills

## Concept

A goroutine leak is a goroutine that never exits. It silently consumes memory and scheduler capacity — the runtime does not tell you about it. Deadlock is different: two goroutines each waiting for the other. Go's runtime detects full deadlocks immediately and panics with `all goroutines are asleep — deadlock!`. Partial deadlocks (some goroutines stuck, others running) are silent. Use `runtime.NumGoroutine()` in tests to catch leaks, and `go test -race` to catch data races that can hide underlying leak conditions.

## Code

```go
package main

import (
	"context"
	"fmt"
	"runtime"
	"time"
)

// LEAK 1: goroutine sends to unbuffered channel with no receiver.
// The goroutine blocks forever because nobody reads from ch.
func leakyNoReceiver() {
	ch := make(chan int) // unbuffered
	go func() {
		ch <- 42 // blocks forever — nobody reads
		fmt.Println("this never prints")
	}()
	// ch goes out of scope but the goroutine is still blocked.
}

// FIX 1: use a buffered channel, or ensure a receiver exists, or use select with done.
func fixedNoReceiver() {
	ch := make(chan int, 1) // buffered: send does not block
	go func() {
		ch <- 42
	}()
	<-ch // drain it
}

// LEAK 2: goroutine ranges over a channel that is never closed.
// range blocks waiting for more values indefinitely.
func leakyNeverClosed() {
	ch := make(chan int, 5)
	go func() {
		for v := range ch { // blocks forever — channel never closed
			_ = v
		}
	}()
	ch <- 1
	ch <- 2
	// forgot to close(ch)
}

// FIX 2: always close the channel when the sender is done.
func fixedNeverClosed() {
	ch := make(chan int, 5)
	go func() {
		for v := range ch {
			_ = v
		}
	}()
	ch <- 1
	ch <- 2
	close(ch) // goroutine exits cleanly
	time.Sleep(time.Millisecond) // give it a moment to exit
}

// LEAK 3: goroutine ignores ctx.Done() and runs forever.
func leakyIgnoresContext(ctx context.Context) {
	go func() {
		for {
			time.Sleep(10 * time.Millisecond) // does work
			// never checks ctx.Done() — runs after context is cancelled
		}
	}()
}

// FIX 3: always check ctx.Done() in long-running goroutines.
func fixedWithContext(ctx context.Context) {
	go func() {
		for {
			select {
			case <-ctx.Done():
				fmt.Println("goroutine exiting via context")
				return
			case <-time.After(10 * time.Millisecond):
				// do work
			}
		}
	}()
}

func main() {
	baseline := runtime.NumGoroutine()
	fmt.Println("baseline goroutines:", baseline)

	leakyNoReceiver()
	time.Sleep(10 * time.Millisecond)
	fmt.Println("after leak 1:", runtime.NumGoroutine(), "(should be baseline+1)")

	fixedNoReceiver()
	time.Sleep(10 * time.Millisecond)
	fmt.Println("after fix 1:", runtime.NumGoroutine(), "(should be back to baseline)")

	ctx, cancel := context.WithTimeout(context.Background(), 50*time.Millisecond)
	defer cancel()
	fixedWithContext(ctx)
	time.Sleep(100 * time.Millisecond) // wait for context to expire and goroutine to exit
	fmt.Println("after context fix:", runtime.NumGoroutine(), "(should be back to baseline)")
}
```

## Exercise

**Build:** Three isolated functions, each containing one of the bugs above. Write a test for each that:
1. Records `runtime.NumGoroutine()` before calling the buggy function.
2. Calls the function.
3. Waits 100ms.
4. Asserts goroutine count has not increased (leak) or that the program did not deadlock.

**Input:** The three buggy functions in this file.

**Output:** Tests fail for buggy versions, pass after applying fixes.

**Acceptance:** Run `go test -race -v ./...`. All three "fixed" versions show goroutine count returning to baseline within 100ms. Goroutine counts for leaky versions are clearly higher.

## Interview

- How do you detect a goroutine leak in production without adding code to the binary?
- What is the difference between a full deadlock (runtime panics) and a partial deadlock?
- A goroutine is blocked on `<-ch` and the channel will never be written to. Is this a deadlock or a leak?
