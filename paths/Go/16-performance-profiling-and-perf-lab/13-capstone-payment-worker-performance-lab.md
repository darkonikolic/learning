# Unit 13 — Capstone: `payment-worker/` performance integration

Build (or extend) **`payment-worker/`** exercising:

```
worker pool + queue consumption + retry + timeout discipline (bridge Areas 12/14 concepts lightly)
```

Then inject **deliberate pathologies**:

```
allocation / GC pressure scenario
goroutine leak scenario
memory retention via slice backing array trick (educational)
```

Use **`pprof` + benchmarks** to detect and fix—document **WHY** fixes work structurally.

Interview consolidation checklist (must speak smoothly):

```
pprof CPU/heap
benchmark discipline
GC / allocation pressure intuition
leak classes
slice prealloc trade-offs
stack vs heap first-pass literacy (deepening Area 16/23)
```
