# Unit 4 — Memory Model: Slices, Maps, and Retention

## Concept

A slice header is three fields: a pointer to the backing array, a length, and a capacity. When you take a subslice (`s[0:10]`), the new slice shares the same backing array as the original. If the original was a 100 MB buffer, the subslice keeps all 100 MB alive in memory even though you only use 10 bytes. The fix is `copy`: allocate a new slice with exactly the size you need and copy the data in — the original backing array can then be garbage collected. This is a common, silent memory leak in code that processes large buffers.

## Code

```go
package main

import (
	"fmt"
	"runtime"
)

// LEAKY: subslice retains the entire backing array.
func firstTenLeaky(large []byte) []byte {
	return large[0:10] // shares backing array — all 100 MB retained
}

// FIXED: copy into a new, small slice — backing array can be GC'd.
func firstTenSafe(large []byte) []byte {
	result := make([]byte, 10)
	copy(result, large[0:10])
	return result
}

// Slice aliasing gotcha: modifying a subslice modifies the original.
func aliasDemo() {
	original := []int{1, 2, 3, 4, 5}
	sub := original[1:3] // sub = [2, 3], shares backing array
	sub[0] = 99
	fmt.Println(original) // [1 99 3 4 5] — original modified!

	// Fix: copy when you need an independent slice.
	safe := make([]int, 2)
	copy(safe, original[1:3])
	safe[0] = 42
	fmt.Println(original) // [1 99 3 4 5] — original unchanged
}

func memStats() uint64 {
	var ms runtime.MemStats
	runtime.GC()
	runtime.ReadMemStats(&ms)
	return ms.HeapAlloc
}

func main() {
	large := make([]byte, 100*1024*1024) // 100 MB

	before := memStats()

	leaky := firstTenLeaky(large)
	large = nil // clear original reference
	runtime.GC()
	afterLeaky := memStats()
	fmt.Printf("leaky:  heap after GC = %d MB (large array still alive)\n",
		afterLeaky/1024/1024)

	_ = leaky
	leaky = nil
	safe := firstTenSafe(make([]byte, 100*1024*1024))
	large = nil
	runtime.GC()
	afterSafe := memStats()
	fmt.Printf("safe:   heap after GC = %d MB (large array collected)\n",
		afterSafe/1024/1024)

	_ = safe
	_ = before
	aliasDemo()
}
```

## Exercise

**Build:** Write a benchmark that measures heap allocation for the leaky vs safe approach.
**Input:** A `large` buffer of 100 MB.
**Output:** `go test -benchmem` output showing allocation difference.
**Acceptance:** (1) `BenchmarkLeaky` retains ~100 MB after GC (verify with `runtime.ReadMemStats`). (2) `BenchmarkSafe` retains ~10 bytes after GC. (3) Modify a subslice and verify (with a test assertion) that the original is changed — then apply the `copy` fix and verify the original is not changed.

## Interview

- You extract a small prefix from a large buffer and store it in a cache. After 1000 requests, your heap is 10 GB. What is likely happening?
- What is the difference between `len` and `cap` of a slice?
- When does `append` allocate a new backing array vs reuse the existing one?
