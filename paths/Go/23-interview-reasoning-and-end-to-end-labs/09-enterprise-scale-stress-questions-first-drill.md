# Unit 9 — Enterprise-scale scenario drill (qualitative “100M orders” stress)

Given stylised scale signals:

```
worker slow, queue backlog growing, latency rising, memory rising
stack includes Go API + Redis + Postgres + queue
```

You must **ask questions first** (data shape, traffic pattern, hot keys, DB indexes, consumer lag, GC, retry storms) before proposing fixes.

Deliverable: structured Q&A + ranked hypotheses + measurement plan. No “rewrite the whole platform” without stating what evidence would justify it.