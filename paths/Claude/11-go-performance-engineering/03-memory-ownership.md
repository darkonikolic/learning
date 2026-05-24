# Memory ownership

**Theme:** Understand **growth vs steady churn**, allocation pressure driving **GC cost**, dormant **goroutine ladders**, and creeping heap footprints.

### Artefacts

`-memprofile`, `runtime.MemStats` semantics (during incidents and labs), goroutine dumps (`/debug/pprof/goroutine`).

### Typical failure classes

Unbounded slice or buffer growth  

Caches without eviction discipline  

Misused `sync.Pool` assumptions  

Escaping pointers retaining large graphs unintentionally  

**Goroutine leak** signals: workers stuck waiting on never-closed channels, unbounded fan-out retries, orphaned `select` loops.

Tie optimisations to **allocation profiles + benchmarks**, not anecdotes.

GC pressure intuition: allocation **rate**, object **lifetimes**, pointer density / write barriers—articulate qualitatively, prove with heap diffs.

### LAB — goroutine-heavy worker

Induce controlled leak or runaway concurrency; correlate goroutine dump growth with queue backlog and throughput collapse.

### Checklist

- [ ] Post-change heap profile shows **dominant allocations** shifted or reduced—not only `ns/op` improvement.  
