# Unit 1 — Concurrency Interview Drill and QA Cards

## Concept

Concurrency interview questions test whether you understand goroutine lifecycle, race conditions, and channel semantics — not just syntax. The most common mistakes are: capturing a loop variable by reference (all goroutines see the last value), writing to a map from multiple goroutines without a lock, sending to a closed channel (panic), and acquiring two mutexes in opposite order in two goroutines (deadlock). Predict the behavior before running. Then verify with `-race`.

## Code

```go
package main

import (
	"fmt"
	"sync"
)

// Gotcha 1: loop variable capture.
// What does this print?
func gotcha1() {
	for i := 0; i < 3; i++ {
		go func() { fmt.Println(i) }() // BUG: all goroutines print 3
	}
	// Fix: pass i as argument
	for i := 0; i < 3; i++ {
		go func(n int) { fmt.Println(n) }(i) // prints 0, 1, 2 (any order)
	}
}

// Gotcha 2: concurrent map write — DATA RACE.
// Does this race?
func gotcha2() {
	m := map[string]int{}
	var wg sync.WaitGroup
	for i := 0; i < 10; i++ {
		wg.Add(1)
		go func(n int) {
			defer wg.Done()
			m["key"] = n // RACE: multiple goroutines write concurrently
		}(i)
	}
	wg.Wait()
	// Fix: use sync.Mutex or sync.Map
}

// Gotcha 3: send to closed channel — PANIC.
// What happens?
func gotcha3() {
	ch := make(chan int, 1)
	close(ch)
	ch <- 1 // panic: send on closed channel
	// Fix: only the sender closes; close after all sends are done.
}

// Gotcha 4: deadlock from lock ordering.
// mu1 then mu2 in one goroutine; mu2 then mu1 in another.
func gotcha4() {
	var mu1, mu2 sync.Mutex
	go func() { mu1.Lock(); mu2.Lock(); mu2.Unlock(); mu1.Unlock() }()
	go func() { mu2.Lock(); mu1.Lock(); mu1.Unlock(); mu2.Unlock() }() // DEADLOCK
	// Fix: always acquire locks in the same order everywhere.
}

func main() {}
```

## Exercise

**Build:** For each of the four gotchas above, predict the output or behavior BEFORE running the code.
**Input:** Each snippet run with `go run -race .` or `go test -race -count=100`.
**Output:** Your written prediction for each, then the actual result.
**Acceptance:** (1) Gotcha 1: explain why the loop-variable version prints 3 three times, not 0, 1, 2. (2) Gotcha 2: `go test -race` must report a data race. Fix it and verify the race disappears. (3) Gotcha 3: reproduce the panic, then fix the code so it never panics. (4) Gotcha 4: reproduce the deadlock, then fix it by enforcing lock order. All four fixes must pass `-race`.

## Interview

- In Go, is it safe to read a map from multiple goroutines if no goroutine writes?
- What is the rule for who should close a channel?
- Two goroutines each hold one lock and wait for the other. What is the name of this condition and what is the standard prevention technique?
