# Unit 1 — Data Races, sync.Mutex, and sync.Map

## Concept

A regular Go map is not goroutine-safe. If two goroutines write to the same map concurrently — even to different keys — the runtime panics or silently corrupts data. The race detector (`go test -race`) catches this and reports the exact goroutine and line numbers. The fix is `sync.Mutex` (exclusive lock for all operations) or `sync.RWMutex` (shared lock for reads, exclusive for writes). Use `sync.Map` when keys are written once and read many times, or when different goroutines work on disjoint key sets — it is not a general replacement for a mutex-protected map.

## Code

```go
package main

import (
	"fmt"
	"sync"
)

// UnsafeCache demonstrates the race — DO NOT use this in production.
// Run with: go run -race . to see the data race report.
type UnsafeCache struct {
	store map[string]string
}

// Cache is a goroutine-safe in-memory store protected by RWMutex.
type Cache struct {
	mu    sync.RWMutex
	store map[string]string
}

func NewCache() *Cache {
	return &Cache{store: make(map[string]string)}
}

// Set acquires an exclusive write lock — blocks all readers and writers.
func (c *Cache) Set(key, value string) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.store[key] = value
}

// Get acquires a shared read lock — multiple readers can proceed concurrently.
func (c *Cache) Get(key string) (string, bool) {
	c.mu.RLock()
	defer c.mu.RUnlock()
	v, ok := c.store[key]
	return v, ok
}

// Delete acquires an exclusive write lock.
func (c *Cache) Delete(key string) {
	c.mu.Lock()
	defer c.mu.Unlock()
	delete(c.store, key)
}

func main() {
	cache := NewCache()
	var wg sync.WaitGroup

	// 10 concurrent writers
	for i := 0; i < 10; i++ {
		wg.Add(1)
		go func(n int) {
			defer wg.Done()
			cache.Set(fmt.Sprintf("user:%d", n), fmt.Sprintf("Alice-%d", n))
		}(i)
	}

	// 10 concurrent readers — safe alongside other readers
	for i := 0; i < 10; i++ {
		wg.Add(1)
		go func(n int) {
			defer wg.Done()
			v, ok := cache.Get(fmt.Sprintf("user:%d", n))
			if ok {
				_ = v // use the value
			}
		}(i)
	}

	wg.Wait()
	fmt.Println("no races — all goroutines complete")
	// Verify: go test -race ./...
}
```

## Exercise

**Build:** A thread-safe `Cache` with `Set(key, value string)`, `Get(key string) (string, bool)`, and `Delete(key string)`. Use `sync.RWMutex`.

**Input:** 20 goroutines writing, 20 goroutines reading, running simultaneously.

**Output:** No race detector errors. All written values are readable by readers.

**Acceptance:** Write a test that uses `go test -race`. First make the test fail by removing the mutex (comment it out). Then restore the mutex — test must pass with `-race`. Also write a test that verifies `Get` on a missing key returns `("", false)`.

## Interview

- What is a data race, and how is it different from a race condition?
- When would you choose `sync.RWMutex` over `sync.Mutex`?
- What are the tradeoffs of `sync.Map` vs a mutex-protected `map`?
