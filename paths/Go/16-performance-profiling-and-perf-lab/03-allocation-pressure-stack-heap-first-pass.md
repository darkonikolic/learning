# Unit 3 — Allocation Pressure: Stack, Heap, First Pass

## Concept

Stack allocations are free — they are just a pointer move. Heap allocations require GC. A variable escapes to heap when it outlives its function (returned as pointer, captured in closure, stored in interface). Use `-gcflags="-m"` to see which variables escape and why. The goal is to keep hot-path variables on the stack.

## Code

```go
package main

// Case 1: returns int — stays on stack, no allocation.
func stackInt() int {
	x := 42
	return x // value copied out, x does not escape
}

// Case 2: returns *int — x escapes to heap.
// go build -gcflags="-m" prints: "moved to heap: x"
func heapPointer() *int {
	x := 42
	return &x // x must outlive the function — escapes
}

// Case 3: stored in interface{} — value is boxed on heap.
// go build -gcflags="-m" prints: "42 escapes to heap"
func interfaceBox() interface{} {
	return 42 // integer boxed into interface{} header — heap allocation
}

// Case 4: closure captures variable — captured vars escape to heap.
func closureCapture() func() int {
	x := 42
	return func() int { return x } // x captured, escapes to heap
}

func main() {
	_ = stackInt()
	_ = heapPointer()
	_ = interfaceBox()
	_ = closureCapture()
}

// Run: go build -gcflags="-m" ./...
// Look for lines containing "escapes to heap" or "moved to heap"
```

## Exercise

**Build:** Run `go build -gcflags="-m" ./...` on your e-commerce service (or any service from a prior module). Find 3 variables that escape to heap. For one of them, rewrite the code to avoid the escape. Verify with `-benchmem` that `allocs/op` decreased.
**Input:** Existing service code
**Output:** Three escape analysis findings from the compiler output. Before/after benchmark showing allocs/op for the function you fixed.
**Acceptance:** The rewritten function shows fewer allocs/op in the benchmark. You can explain the reason for each of the three escapes you found.

## Interview

- What is escape analysis and who performs it in Go?
- Name three things that cause a variable to escape from stack to heap.
- Why does storing a value in an `interface{}` cause a heap allocation?
