# Unit 2 — Benchmark Thinking and Microbenchmark Hygiene

## Concept

Benchmarks run until time stabilizes (`b.N` iterations, chosen by the test runner). `-benchmem` shows bytes/op and allocs/op — often more important than ns/op because allocations drive GC pauses. Run `-count=3` to check variance. A 10% difference with high variance is noise; a 3× difference with low variance is real.

## Code

```go
package bench_test

import (
	"strings"
	"testing"
)

// Slow: + operator creates a new string on every iteration.
func concatPlus(parts []string) string {
	result := ""
	for _, p := range parts {
		result += p
	}
	return result
}

// Fast: strings.Builder pre-allocates and appends in place.
func concatBuilder(parts []string) string {
	var b strings.Builder
	b.Grow(len(parts) * 10) // hint: avoids re-growth
	for _, p := range parts {
		b.WriteString(p)
	}
	return b.String()
}

var parts = make([]string, 100)

func init() {
	for i := range parts {
		parts[i] = "word"
	}
}

func BenchmarkConcatPlus(b *testing.B) {
	for i := 0; i < b.N; i++ {
		_ = concatPlus(parts)
	}
}

func BenchmarkConcatBuilder(b *testing.B) {
	for i := 0; i < b.N; i++ {
		_ = concatBuilder(parts)
	}
}

// Run: go test -bench=. -benchmem -count=3
// Expected output:
// BenchmarkConcatPlus-8     50000    24000 ns/op   45000 B/op   99 allocs/op
// BenchmarkConcatBuilder-8  500000   2400 ns/op     1024 B/op    2 allocs/op
```

## Exercise

**Build:** Benchmark `json.Marshal` for a struct with 10 fields. Then encode the same struct using a pre-allocated `bytes.Buffer` and `json.NewEncoder`.
**Input:** A struct with 10 string/int fields. Benchmark both approaches with `-benchmem -count=3`.
**Output:** Two benchmark results showing ns/op, B/op, allocs/op for each approach.
**Acceptance:** The `json.NewEncoder` with pre-allocated buffer shows fewer allocs/op than `json.Marshal`. Explain why: `Marshal` allocates a new `[]byte`; `NewEncoder` writes into your buffer.

## Interview

- What does `b.N` represent in a Go benchmark?
- Why run with `-count=3` instead of just `-count=1`?
- A benchmark shows 5000 ns/op and 20 allocs/op. Which should you optimize first for a high-QPS service?
