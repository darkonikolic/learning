# Unit 3 — Channel idioms: “Don’t communicate by sharing memory blindly” orientation

## Learning outcome

Adopt proverb directionally—even if nuanced later—for teaching clarity:

Prefer **ownership passing** idioms leveraging **`chan`** over ad-hoc global maps protected casually.

Starter pattern:

```go
jobs := make(chan int)
```

Produce **producer** fabricating simulated tasks; consumers drain executing slower operations (sleep mocking latency).

Understand **blocking semantics** zero-buffer channels: synchronization rendezvous pairwise readiness.

## Practice tasks

Implement minimal pipeline:

```
task creator goroutine → channel → executor goroutine
```

Articulate buffering absence consequences on throughput vs deterministic handoff choreography.

## Lab

Contrast readability / failure surface vs unstructured shared structs mutated under `time.Sleep`-based gambles—not production patterns.

## Interview prompts

Directed channel types (**send-only**, **receive-only**) in function signatures signalling intent cleanly.
