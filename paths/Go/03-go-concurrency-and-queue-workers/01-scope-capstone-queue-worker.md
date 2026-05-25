# Unit 1 — Module Scope: queue-worker/

## What You Will Build

A job queue with concurrent workers — the `queue-worker/` codebase. A producer generates jobs and sends them to a shared channel. A pool of N workers drains the channel concurrently. A `select` loop handles both incoming jobs and shutdown signals. The whole system shuts down cleanly when a context is cancelled.

No frameworks, no HTTP. Pure Go concurrency primitives from the standard library.

## What You Will Know by the End

- **Goroutines:** launch with `go f()`, understand that launch and completion are separate — you must synchronize explicitly
- **Channels:** pass data ownership between goroutines; close to signal completion; use directional types in function signatures
- **Buffered channels:** sender does not block until the buffer is full; useful for absorbing bursts
- **select:** wait on multiple channels simultaneously; integrate context cancellation cleanly
- **WaitGroup:** wait for a known set of goroutines to finish
- **Race detector:** `go test -race` catches concurrent map writes and other data races before they hit production

## Spine Project: queue-worker/

Carry this structure through units 2–11:

```
queue-worker/
  main.go          — wires producer + workers + shutdown
  job.go           — Job type
  worker.go        — worker function
  producer.go      — producer function
  pool.go          — (added later) bounded worker pool
```

Capstone (Unit 11): producer generates 50 jobs, 5 workers process them concurrently, a 2-second context timeout cancels remaining work, and the program reports how many jobs completed versus were cancelled.

## Mental Model

Go's concurrency motto is "share memory by communicating." Instead of a shared variable that multiple goroutines write to (and a mutex to protect it), pass the data through a channel. The goroutine that owns the channel is the only one writing to it. This eliminates entire classes of race conditions.

A goroutine is not a thread — it is multiplexed onto OS threads by the Go runtime. You can have tens of thousands of goroutines. You cannot have tens of thousands of OS threads. The cost of spawning a goroutine is ~2KB of stack and a scheduler entry, not a kernel syscall.
