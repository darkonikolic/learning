# Unit 2 — Worker Pool: Fan-Out and Fan-In

## Concept

Fan-out means distributing work across N workers via a shared input channel — each worker takes jobs as fast as it can. Fan-in means collecting results from N workers back into a single output channel. A bounded worker pool (fixed N goroutines) prevents goroutine explosion: without a bound, you could spawn 10,000 goroutines for 10,000 jobs and exhaust memory. The pattern: close the jobs channel when all work is submitted, use a WaitGroup to know when all workers are done, then close the results channel so the collector can use `range`.

## Code

```go
package main

import (
	"fmt"
	"sync"
	"time"
)

type Job struct {
	ID   int
	Size int // simulated image size in KB
}

type Result struct {
	JobID     int
	OutputSize int
	Duration  time.Duration
}

// worker reads jobs, simulates resize, writes results.
func worker(id int, jobs <-chan Job, results chan<- Result, wg *sync.WaitGroup) {
	defer wg.Done()
	for job := range jobs { // exits when jobs is closed and drained
		start := time.Now()
		time.Sleep(10 * time.Millisecond) // simulate resize work
		results <- Result{
			JobID:     job.ID,
			OutputSize: job.Size / 2,
			Duration:  time.Since(start),
		}
	}
}

func main() {
	const numWorkers = 4
	const numJobs = 20

	jobs := make(chan Job, numJobs)
	results := make(chan Result, numJobs)

	// Launch fixed-size worker pool.
	var wg sync.WaitGroup
	for w := 1; w <= numWorkers; w++ {
		wg.Add(1)
		go worker(w, jobs, results, &wg)
	}

	// Feed all jobs.
	start := time.Now()
	for j := 1; j <= numJobs; j++ {
		jobs <- Job{ID: j, Size: 1024}
	}
	close(jobs) // signal workers: no more jobs

	// Close results once all workers are done — in a separate goroutine
	// to avoid deadlock (results is buffered but could fill if collector is slow).
	go func() {
		wg.Wait()
		close(results)
	}()

	// Collect all results (fan-in).
	var processed int
	for r := range results {
		processed++
		_ = r
	}

	fmt.Printf("processed %d jobs with %d workers in %v\n",
		processed, numWorkers, time.Since(start).Round(time.Millisecond))
	// ~4 workers * 10ms = 50ms for 20 jobs (vs 200ms with 1 worker)
}
```

## Exercise

**Build:** An image resize simulator: 20 "images" with random sizes (100–2000 KB). Run with 4 workers first, then 1 worker. Each "resize" takes 10ms.

**Input:** 20 jobs, configurable worker count.

**Output:** `processed 20 jobs with 4 workers in ~50ms`. With 1 worker: `~200ms`.

**Acceptance:** The results channel must be closed properly — the collector must use `range` with no goroutine leaks. Run with `go test -race`. Write a benchmark (`BenchmarkPool`) that measures 4-worker vs 1-worker throughput.

## Interview

- Why close the jobs channel from the sender rather than sending a "poison pill" sentinel value?
- What happens if you forget to close the results channel? How does the collector get stuck?
- A pool of 100 workers on a machine with 4 cores — is this wasteful for CPU-bound work? For I/O-bound work?
