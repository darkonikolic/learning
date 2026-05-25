# Unit 4 — Benchmarks, Load Tests, and Fuzz Hooks

## Concept

Benchmarks measure performance using `BenchmarkX(b *testing.B)` — the test runner calls your function `b.N` times and adjusts N until timing stabilizes. Use `-benchmem` to show allocations per operation, which is often more important than raw speed. Fuzz tests (`FuzzX`) generate random inputs to find panics and crashes in parsing and decoding code. Both are standard library features — no external tools needed.

## Code

```go
package serialization_test

import (
	"bytes"
	"encoding/json"
	"strings"
	"testing"

	"github.com/example/app/domain"
)

var order = domain.Order{
	ID:     "ord_123",
	UserID: "usr_456",
	Status: "pending",
}

// BenchmarkJSONMarshal measures allocation cost of json.Marshal.
func BenchmarkJSONMarshal(b *testing.B) {
	b.ReportAllocs()
	for i := 0; i < b.N; i++ {
		_, _ = json.Marshal(order)
	}
}

// BenchmarkJSONMarshalWithBuffer reuses a buffer to reduce allocations.
func BenchmarkJSONMarshalWithBuffer(b *testing.B) {
	b.ReportAllocs()
	var buf bytes.Buffer
	enc := json.NewEncoder(&buf)
	for i := 0; i < b.N; i++ {
		buf.Reset()
		_ = enc.Encode(order)
	}
}

// BenchmarkStringConcat vs Builder — classic allocation demo.
func BenchmarkStringConcat(b *testing.B) {
	b.ReportAllocs()
	for i := 0; i < b.N; i++ {
		s := ""
		for j := 0; j < 10; j++ {
			s += "word "
		}
		_ = s
	}
}

func BenchmarkStringBuilder(b *testing.B) {
	b.ReportAllocs()
	for i := 0; i < b.N; i++ {
		var sb strings.Builder
		for j := 0; j < 10; j++ {
			sb.WriteString("word ")
		}
		_ = sb.String()
	}
}

// FuzzParseOrderID finds crashes in order ID parsing.
func FuzzParseOrderID(f *testing.F) {
	// Seed corpus
	f.Add("ord_123")
	f.Add("")
	f.Add("ord_" + strings.Repeat("x", 1000))

	f.Fuzz(func(t *testing.T, input string) {
		// Must not panic for any input
		_, _ = parseOrderID(input)
	})
}
```

## Exercise

**Build:** Benchmarks for JSON marshal/unmarshal of an Order struct with 6 fields.
**Input:** Benchmark 1: `json.Marshal` with no buffer reuse. Benchmark 2: `json.NewEncoder` with a `bytes.Buffer` reset between iterations.
**Output:** Run `go test -bench=. -benchmem -benchtime=3s ./...`. Show output with `ns/op`, `B/op`, `allocs/op` for both benchmarks.
**Acceptance:** The buffer-reuse benchmark shows fewer `allocs/op` than the plain marshal benchmark. Document the difference in a comment. Run with `-benchtime=10x` (10 iterations fixed) to understand the flags.

## Interview

- What does `allocs/op` tell you that `ns/op` does not?
- Why does resetting a `bytes.Buffer` reduce allocations compared to calling `json.Marshal` directly?
- When would you use a fuzz test over a table-driven test?
