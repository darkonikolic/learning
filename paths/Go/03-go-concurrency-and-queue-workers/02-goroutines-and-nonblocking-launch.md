# Unit 2 — Goroutines and Non-Blocking Launch

## Concept

`go f()` schedules `f` to run concurrently and returns immediately — it does not wait for `f` to finish. This means if `main()` exits before your goroutines are done, they are killed mid-execution with no cleanup. `sync.WaitGroup` is the standard solution: call `wg.Add(1)` before launching, `wg.Done()` (via `defer`) inside the goroutine, and `wg.Wait()` in main. The print order of goroutines is non-deterministic — the scheduler decides, and that is intentional.

## Code

```go
package main

import (
	"fmt"
	"sync"
	"time"
)

// processEmail simulates sending one email.
// In production this would be an SMTP call or API request.
func processEmail(workerID, emailID int, wg *sync.WaitGroup) {
	defer wg.Done() // always called, even if the function panics

	time.Sleep(50 * time.Millisecond) // simulate network latency
	fmt.Printf("worker %d: sent email %d\n", workerID, emailID)
}

func main() {
	const workers = 5
	const emailsPerWorker = 3

	var wg sync.WaitGroup

	for w := 1; w <= workers; w++ {
		for e := 1; e <= emailsPerWorker; e++ {
			wg.Add(1) // increment BEFORE launching the goroutine
			go processEmail(w, e, &wg)
		}
	}

	// Blocks here until all 15 goroutines call wg.Done().
	wg.Wait()
	fmt.Println("all 15 emails sent")

	// Without wg.Wait(), main would exit after ~0ms and 0 emails would print.
	// That is the classic "goroutine orphan" bug.
}
```

## Exercise

**Build:** An email dispatcher that launches 5 workers, each processing 3 emails. Each "send" takes 50ms (use `time.Sleep`). Print `worker W: sent email E` for each.

**Input:** No user input — hardcoded workers=5, emails=3.

**Output:** All 15 `worker X: sent email Y` lines printed before `all 15 emails sent`. Print order can vary — that is expected.

**Acceptance:** Move `wg.Wait()` to a comment and observe that many lines are missing when you run without it. Put it back. Add a test using `runtime.NumGoroutine()` — assert that goroutine count returns to baseline after `wg.Wait()`.

## Interview

- Why does `go f()` return immediately instead of waiting for `f` to finish?
- What is the difference between a goroutine leak and a goroutine that exits too early?
- What happens to a goroutine if the function that launched it returns?
