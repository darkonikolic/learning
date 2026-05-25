# Unit 12 — Profiling incident lab (synthetic): CPU pegged, memory climbing, workers stalling

Compose multi-signal chaos in `perf-lab/`:

```
CPU ~95% busy spin or pathological algorithm
memory growth via leak pattern(s)
worker pool starved or oversubscribed scenario mixing IO + CPU skew
```

You must:

```
profile (CPU + heap at minimum)
identify dominant contributors
patch with measured before/after bench/prof snapshot commentary
document trade-offs (readability loss? bounded buffers?)
```

Interview rehearsal: narrate investigation without opening laptop—prove muscle memory.
