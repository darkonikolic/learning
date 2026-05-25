# Unit 5 — Capstone: Slow Service to Evidence Fix

## Concept

Debugging performance = hypothesis → measure → fix → measure again. Never guess. The fix that seems obvious is often not the bottleneck. This capstone gives you a deliberately slow handler with multiple inefficiencies — your job is to find each one with profiling evidence before touching the code.

## Code

```go
package main

import (
	"encoding/json"
	"net/http"
	"strings"
	_ "net/http/pprof"
)

type Item struct {
	ID    int    `json:"id"`
	Name  string `json:"name"`
	Price int    `json:"price"`
}

// slowHandler has three intentional inefficiencies.
// Your job is to find them with pprof before fixing them.
func slowHandler(w http.ResponseWriter, r *http.Request) {
	// Inefficiency 1: string concatenation in a loop (allocates N times)
	var names string
	for i := 0; i < 100; i++ {
		names += fmt.Sprintf("item-%d,", i)
	}

	// Inefficiency 2: redundant JSON encode (result discarded)
	items := make([]Item, 100)
	for i := range items {
		items[i] = Item{ID: i, Name: fmt.Sprintf("item-%d", i), Price: i * 10}
	}
	_, _ = json.Marshal(items) // encoded but discarded — wasted work

	// Inefficiency 3: allocates new encoder on every request instead of reusing
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(items)
}

func main() {
	go http.ListenAndServe(":6060", nil) // pprof
	http.HandleFunc("/items", slowHandler)
	http.ListenAndServe(":8080", nil)
}
```

## Exercise

**Build:** Use pprof to identify the top 3 bottlenecks in `slowHandler`. Fix each one. Show before/after benchmark numbers.
**Input:** `slowHandler` as written above. Load from `hey -n 5000 -c 20 http://localhost:8080/items`.
**Output:** For each bottleneck: (1) which pprof frame pointed to it, (2) what the fix is, (3) before/after ns/op and allocs/op from the benchmark.
**Acceptance:** After all 3 fixes: allocs/op is reduced by at least 50% and ns/op improves by at least 30% compared to the original. Each fix is backed by a before/after benchmark — no guessing.

## Interview

- How do you benchmark an HTTP handler in Go without starting a real server?
- What does `httptest.NewRecorder()` give you?
- If a CPU profile shows most time in `runtime.mallocgc`, what does that tell you?
