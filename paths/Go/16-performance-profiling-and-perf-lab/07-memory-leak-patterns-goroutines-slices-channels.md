# Unit 7 — Memory “leak” thinking in Go: goroutines, slices, channels

Go can **retain memory** without classic malloc/free leaks:

| Pattern | Symptom sketch |
|---------|----------------|
| **Goroutine leak** | forgotten `ctx` cancellation / blocked sends / waiting forever |
| **Slice backing array retention** | tiny visible slice holding giant underlying array alive |
| **Channel / map caches** | unbounded growth “feature” |

## Practice

Seed an intentional **goroutine leak** (ignore `Done` + blocking channel), observe process RSS climb / goroutine count via `pprof` goroutine profile or runtime metrics patterns.

Fix with cancellation + join discipline cross-linking Area `03/04`.

## Interview expectation

Differentiate **unreachable cycles** (GC reclaim) vs **reachable accidental retention** (profiler shows live objects still referenced).
