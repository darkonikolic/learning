# Unit 5 — Heap profiling growth hunting

Induce purposeful **steady memory ascent** caching slices incorrectly / retaining unintended references / global hoarding—even learning-scale acceptable.

Observe:

```
go tool pprof -http=:6060 heap.prof    // focussing alloc_space vs inuse_* semantics consciously
```

## Lab differentiation

Clarify in writing:

| Profile view | Typical question |
|--------------|------------------|
| `alloc_space` / `alloc_objects` | “What allocates a lot—even if transient?” |
| `inuse_space` / `inuse_objects` | “What stays alive unexpectedly?” |

Interview drill: differentiate **profiler evidence** from guesses when someone says “memory leak”—tie to goroutine/leak drills next units.