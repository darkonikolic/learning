# Unit 3 — `sync.Pool`: reuse without lying to yourself about safety

`sync.Pool` trades **allocation rate** against **risk** if pooled objects retain stale mutable state accidentally.

## Rules of thumb

- Pool **allocation-heavy** ephemeral buffers / scratch structs—not long-lived authoritative domain records.
- Reset pooled objects meticulously before reuse; document invariants fiercely.
- Expect pooled objects **may disappear** anytime between GC cycles—never treat pooled storage as dependable cache correctness.

Practice: micro-benchmark pooling `[]byte` buffers for serialization hot path contrasting naive `make` churn—articulate concurrency hazards if pools cross goroutines wrongly.

Interview: summarise when pooling is ethically cancelled because correctness risk outweighs micro wins.
