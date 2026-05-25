# Unit 1 — GMP Scheduler Model and Blocking Intuition

## Concept

G = goroutine (user-space, starts at 2KB stack, grows as needed). M = OS thread (managed by the runtime). P = logical processor (GOMAXPROCS, default = number of CPUs). When a goroutine blocks on I/O, its M is released and another goroutine takes over the P. CPU-bound goroutines must yield cooperatively — in Go 1.14+, the runtime preempts them with signals so other goroutines still get CPU time.

## Code

```go
package main

import (
	"fmt"
	"runtime"
	"sync"
	"time"
)

func cpuBound(id int, wg *sync.WaitGroup) {
	defer wg.Done()
	start := time.Now()
	sum := 0
	for i := 0; i < 100_000_000; i++ {
		sum += i
	}
	fmt.Printf("goroutine %d done in %v (sum=%d)\n", id, time.Since(start), sum)
}

func main() {
	const n = 4

	for _, procs := range []int{1, n} {
		runtime.GOMAXPROCS(procs)
		var wg sync.WaitGroup
		start := time.Now()
		for i := 0; i < n; i++ {
			wg.Add(1)
			go cpuBound(i, &wg)
		}
		wg.Wait()
		fmt.Printf("GOMAXPROCS=%d total time: %v\n\n", procs, time.Since(start))
	}
}
```

## Exercise

**Build:** Run the program above. Set `GOMAXPROCS=1`, then `GOMAXPROCS=4` (or match your CPU count). Run 4 CPU-bound goroutines each doing 100 million iterations.
**Input:** 4 goroutines, each doing 100M additions
**Output:** Total wall time for each GOMAXPROCS setting
**Acceptance:** With GOMAXPROCS=4, total time is approximately 4× faster than GOMAXPROCS=1. The speedup confirms the work is CPU-bound and parallel.

## Interview

- What is a P in the GMP model and why does its count matter for CPU-bound work?
- What happens to the M (OS thread) when a goroutine blocks on a network read?
- A program has GOMAXPROCS=2 and 100 goroutines. How many goroutines run simultaneously?
