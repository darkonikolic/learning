# Unit 9 — Concurrency performance: more goroutines ≠ faster

Measure:

```
worker pool sizes: 5 vs 50 vs 500
```

on **CPU-bound** vs **IO-bound** toy workloads—observe contention, scheduling overhead, and throughput collapse when oversubscribed CPU work.

## Lab deliverable

Plot a small qualitative table of outcomes (even handwritten) and explain how they relate to coarse parallel speedup intuition (CPU-bound saturation vs IO-bound overlap)—without treating a laptop benchmark like a mathematical proof.
