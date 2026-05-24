# Unit 2 — Escape analysis: when the compiler sends work to the heap

## Outcomes

- Use **escape diagnostics** (`go build -gcflags="-m"`) as a *hinting* tool, not a religion—profiles still win for hot paths.
- Predict common escape drivers: **interface boxing**, **variable captured by closure returned**, **slice/map elements referenced beyond stack lifetime**, **unsized values** passed through interfaces.
- Relate escapes to **GC pressure** and tail latency (Areas `15`/`16`).

## Lab

Take one hot function from `perf-lab/` and:

1. capture `alloc_space` / `allocs/op` signal,
2. inspect escape report for that function,
3. attempt a *small* change that reduces allocations,
4. re-measure and document whether latency improved or readability regressed.

Interview prompt: “When would you ignore escape reports and trust `pprof` instead?”
