# Unit 2 — Escape Analysis and Allocation Tradeoffs (Deep)

## Concept

Interface boxing always allocates when the stored value is a non-pointer type. Closures that capture variables cause those variables to escape to heap. Returning a pointer from a function causes the pointed-to value to escape. In hot paths, replace interface parameters with generics (Go 1.18+) or concrete types to eliminate boxing allocations.

## Code

```go
package main

// Pattern 1: interface boxing — allocates per call for non-pointer types.
// -gcflags="-m": "42 escapes to heap"
func withInterface(v interface{}) int {
	return v.(int) + 1
}

// Pattern 2: generic function — no boxing, no allocation for value types.
// -gcflags="-m": no escape for the value
func withGeneric[T int | int64 | float64](v T) T {
	return v + 1
}

// Pattern 3: concrete type — fastest, zero allocation.
func withConcrete(v int) int {
	return v + 1
}

// Pattern 4: closure captures x — x escapes to heap.
// -gcflags="-m": "moved to heap: x"
func makeAdder(x int) func(int) int {
	return func(n int) int { return n + x }
}

// Run: go build -gcflags="-m" ./...
// See which patterns cause "escapes to heap" and which do not.
```

## Exercise

**Build:** In a hot path (1M iterations), benchmark three implementations of `add(v int) int`: (a) takes `interface{}`, (b) generic `[T int]`, (c) concrete `int`. Use `-benchmem -count=3`.
**Input:** Three benchmark functions each calling their implementation 1M times in `b.N` iterations
**Output:** ns/op and allocs/op for all three. Show the allocation difference between (a) and (b)/(c).
**Acceptance:** (a) interface version has allocs/op > 0; (b) generic and (c) concrete have allocs/op = 0. You can explain why generics avoid boxing while interfaces do not.

## Interview

- Why does storing an `int` in `interface{}` allocate but storing a `*int` does not always?
- What is the cost of interface dispatch compared to a direct function call?
- When would you choose a generic function over an interface in a performance-critical path?
