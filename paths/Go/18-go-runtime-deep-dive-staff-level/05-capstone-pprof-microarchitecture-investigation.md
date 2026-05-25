# Unit 5 — Capstone: pprof and Microarchitecture Investigation

## Concept

Staff-level performance work combines runtime knowledge with profiling evidence. You need to know what the profile is telling you — "allocations in `sync.Pool.Get`" means your pool objects are being GC'd too fast, not that Pool is broken. Distinguish between allocation pressure, false sharing, and escape analysis issues by reading the profile before reading the code.

## Code

```go
package main

import (
	"encoding/json"
	"fmt"
	"sync"
	"sync/atomic"
)

// Item has fields in suboptimal order — causes internal padding waste.
type Item struct {
	Active bool    // 1 byte + 7 bytes padding before Price
	Price  float64 // 8 bytes
	ID     int32   // 4 bytes + 4 bytes padding before Name pointer
	Name   string  // 16 bytes (pointer + len)
}

// SharedState has two hot fields on the same cache line — false sharing.
type SharedState struct {
	readCount  int64 // written by reader goroutines
	writeCount int64 // written by writer goroutines — shares cache line with readCount
}

// processItems has three issues:
//  1. allocates a new encoder per call (escape to heap each time)
//  2. Item struct layout wastes padding bytes
//  3. SharedState.readCount and writeCount share a cache line
func processItems(state *SharedState, items []Item) ([]byte, error) {
	atomic.AddInt64(&state.readCount, 1)

	// Issue 1: new bytes.Buffer per call — should use sync.Pool
	var buf []byte
	for _, item := range items {
		b, err := json.Marshal(item) // allocates per item
		if err != nil {
			return nil, err
		}
		buf = append(buf, b...)
	}
	atomic.AddInt64(&state.writeCount, 1)
	return buf, nil
}

func main() {
	state := &SharedState{}
	items := make([]Item, 100)
	for i := range items {
		items[i] = Item{ID: int32(i), Name: fmt.Sprintf("item-%d", i), Price: float64(i) * 1.5, Active: true}
	}

	var wg sync.WaitGroup
	for i := 0; i < 8; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for j := 0; j < 10_000; j++ {
				processItems(state, items)
			}
		}()
	}
	wg.Wait()
	fmt.Printf("reads=%d writes=%d\n", state.readCount, state.writeCount)
}
```

## Exercise

**Build:** Profile `processItems` under load. Identify: (1) what escapes to heap unnecessarily, (2) whether `SharedState` has false sharing, (3) the top allocation hot spot. Fix each one. Target: reduce `allocs/op` by 50% and improve throughput.
**Input:** 8 goroutines each calling `processItems` 10K times. CPU and heap profile collected via pprof.
**Output:** For each of the 3 issues: (a) which profile frame pointed to it, (b) the fix applied, (c) before/after benchmark numbers (ns/op, allocs/op).
**Acceptance:** After all fixes: allocs/op reduced by ≥50% vs original. Each fix is backed by a before/after benchmark. `SharedState` padded so reads and writes are on separate cache lines. You can explain what `-gcflags="-m"` shows before and after the escape fix.

## Interview

- What does pprof output `sync.Pool.Get` in the allocation profile tell you?
- Describe the steps you take when a service has high p99 latency but normal CPU usage.
- A colleague claims padding structs is premature optimization. When is it and when is it not?
