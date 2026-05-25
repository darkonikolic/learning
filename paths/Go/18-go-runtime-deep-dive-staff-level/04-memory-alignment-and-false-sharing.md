# Unit 4 — Memory Alignment and False Sharing

## Concept

CPUs read and write in cache lines (64 bytes). If two goroutines write different fields that share a cache line, they contend for the same line — this is false sharing, and it serializes what should be parallel work. Fix by padding structs so each hot field occupies its own cache line. Field ordering also affects struct size: put the largest fields first to minimize padding between them.

## Code

```go
package main

import (
	"fmt"
	"sync"
	"testing"
	"unsafe"
)

// Unpadded: both counters share a cache line — false sharing under parallel writes.
type UnpaddedCounters struct {
	a int64
	b int64
}

// Padded: each counter has its own cache line.
type PaddedCounter struct {
	value   int64
	_       [56]byte // pad to 64 bytes (cache line size)
}

type PaddedCounters struct {
	a PaddedCounter
	b PaddedCounter
}

func benchFalseSharing(b *testing.B) {
	var c UnpaddedCounters
	var wg sync.WaitGroup
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		wg.Add(2)
		go func() { defer wg.Done(); for j := 0; j < 1000; j++ { c.a++ } }()
		go func() { defer wg.Done(); for j := 0; j < 1000; j++ { c.b++ } }()
		wg.Wait()
	}
}

func main() {
	fmt.Printf("UnpaddedCounters size: %d bytes\n", unsafe.Sizeof(UnpaddedCounters{}))
	fmt.Printf("PaddedCounters size:   %d bytes\n", unsafe.Sizeof(PaddedCounters{}))
	// Run: go test -bench=. -benchmem -count=3
}
```

## Exercise

**Build:** Benchmark a counter array where N goroutines each increment their own counter: (a) `[]int64` (unpadded, likely shares cache lines), (b) `[]PaddedCounter` (each counter on its own cache line). Use N = number of CPUs.
**Input:** N goroutines each doing 1M increments on their assigned counter. Two implementations: unpadded array and padded array.
**Output:** ns/op for both implementations with `-count=3`. On a multi-core machine, padded version should be faster.
**Acceptance:** Padded version is measurably faster on multi-core (2× or more speedup is common). The unpadded version's performance degrades as CPU count increases; padded version scales better.

## Interview

- What is a cache line and how large is it on modern x86?
- Describe false sharing with a concrete example using two goroutines.
- Why does padding fix false sharing but increase memory usage? When is the tradeoff worth it?
