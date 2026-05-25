# Unit 6 — Garbage collector thinking: allocation pressure & pause awareness

Go’s GC is **non-magical**: more allocation churn generally means more GC work (CPU + latency variance), even if individual pauses are often short relative to classic stop-the-world horror stories.

## Practice

Allocate ~100k short-lived objects in tight loops under bench harness—watch **GC-related cost** indirectly via:

```
-benchmem
cpu + heap profiles (previous units)
optional GODEBUG=gctrace=1 textual logs (interpret qualitatively; don’t overfit local laptop numbers)
```

## Lab

Explain in prose what **allocation pressure** means for tail latency at API scale—not average-only dashboards delusions.

## Interview prompts

Generational GC myths misapplied to Go—stay factual with current runtime docs when disputing trivia.

Trade-off: micro-alloc elimination vs readability—optimise only with evidence (Area intent).
