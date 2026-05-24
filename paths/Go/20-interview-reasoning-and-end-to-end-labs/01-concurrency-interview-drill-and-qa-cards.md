# Unit 1 — Concurrency interview lab: races, synchronisation, channels

## Prompt A (classic)

```go
counter := 0
for i := 0; i < 1000; i++ {
    go func() { counter++ }()
}
```

Explain data race, why results fluctuate, and fix using **`sync.Mutex`** or **`atomic`** with trade-off clarity (when atomics sufficient vs mutex clarity for invariants).

## Prompt B (channels)

Given `jobs := make(chan int)` vs buffered variants—explain blocking semantics, suitable use-cases, dangers (forgotten readers, leaks).

## Deliverable

Author **20 short Q&A cards** (even bullet form) covering mutex/channel/`select`/worker pool reasoning—your own words, not copy-paste trivia lists.
