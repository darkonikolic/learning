# Unit 2 — Stacks, Heaps, and Escape Analysis Instincts

## Concept

Stack: per-goroutine, automatic, fast — allocating is a pointer move. Heap: GC-managed, slower — used when a value must outlive its function. Escape analysis decides where each variable lives at compile time. You can see every decision with `go build -gcflags="-m"`. The goal: keep hot-path variables on the stack.

## Code

```go
package main

// stackReturn: value copied out — x stays on stack.
// -gcflags="-m": no escape message
func stackReturn() int {
	x := 42
	return x
}

// heapReturn: pointer returned — x escapes to heap.
// -gcflags="-m": "moved to heap: x"
func heapReturn() *int {
	x := 42
	return &x
}

// interfaceEscape: integer stored in interface{} — boxed on heap.
// -gcflags="-m": "42 escapes to heap"
func interfaceEscape() interface{} {
	return 42
}

// closureEscape: captured variable escapes to heap.
// -gcflags="-m": "moved to heap: x"
func closureEscape() func() int {
	x := 42
	return func() int { return x }
}

// sliceGrowth: append may move slice to heap if it grows.
func sliceGrowth() []int {
	s := make([]int, 0, 10)
	for i := 0; i < 100; i++ {
		s = append(s, i) // grows beyond cap=10 → heap
	}
	return s
}

// Run: go build -gcflags="-m" ./...
// Each escape is explained by one of the patterns above.
```

## Exercise

**Build:** Write 5 functions with different escape patterns. Before running `-gcflags="-m"`, predict which variables escape for each function.
**Input:** 5 functions: one returning int, one returning *int, one accepting interface{}, one using a closure, one returning a slice from a function
**Output:** Your predictions vs the actual `-gcflags="-m"` output for each function
**Acceptance:** Your predictions are correct for at least 4 of 5. For any wrong prediction, write one sentence explaining why the compiler made a different decision.

## Interview

- Why is returning a pointer from a function sufficient to cause a heap allocation?
- Does every interface conversion cause a heap allocation? Give a counterexample.
- A goroutine's stack starts at 2KB. What happens when it grows beyond that?
