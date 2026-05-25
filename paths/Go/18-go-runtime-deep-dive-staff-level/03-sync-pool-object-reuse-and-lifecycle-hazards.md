# Unit 3 — sync.Pool: Object Reuse and Lifecycle Hazards

## Concept

`sync.Pool` reduces GC pressure by reusing allocated objects. Pool items may be collected any GC cycle — never use Pool for state that must persist across GC. Always `Reset` the object before use (it may contain data from a previous user). Never hold a reference to a pooled object after returning it with `Put`.

## Code

```go
package main

import (
	"bytes"
	"encoding/json"
	"sync"
)

var bufPool = sync.Pool{
	New: func() interface{} {
		return new(bytes.Buffer)
	},
}

// encode reuses a buffer from the pool instead of allocating per call.
func encode(v interface{}) ([]byte, error) {
	buf := bufPool.Get().(*bytes.Buffer)
	buf.Reset() // must reset — may contain data from previous use
	defer bufPool.Put(buf)

	if err := json.NewEncoder(buf).Encode(v); err != nil {
		return nil, err
	}
	// Copy before returning — buf goes back to pool, caller must not hold it.
	result := make([]byte, buf.Len())
	copy(result, buf.Bytes())
	return result, nil
}

// Hazard: do NOT do this — holding reference after Put.
func hazard(v interface{}) []byte {
	buf := bufPool.Get().(*bytes.Buffer)
	buf.Reset()
	json.NewEncoder(buf).Encode(v)
	bufPool.Put(buf)
	return buf.Bytes() // BUG: buf is back in pool — another goroutine may use it
}
```

## Exercise

**Build:** Benchmark JSON encoding with and without `sync.Pool` for `bytes.Buffer`. Use a struct with 10 fields. Run `-benchmem -count=3`.
**Input:** Benchmark both `json.Marshal` (allocates per call) and `encode` using the pool above
**Output:** allocs/op for each approach. Show that pool version has fewer allocations.
**Acceptance:** Pool version shows fewer allocs/op than `json.Marshal`. Use `-count=3` to verify the improvement is consistent across runs, not just a single lucky sample.

## Interview

- When does `sync.Pool` drop its objects?
- Why must you call `Reset()` on an object retrieved from a pool?
- A pool stores database connections. Is this correct use of `sync.Pool`? Why or why not?
