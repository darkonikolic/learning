# Unit 4 — Alignment, padding & false sharing (micro-architecture, measured)

Staff-level depth means you can name rare effects **and** stay honest about how often you really need them day to day.

## Alignment & padding

Different types have different alignment requirements; the compiler inserts **padding** so fields land on valid addresses. Occasionally this matters for compacting hot structs—but don’t turn this into cargo-cult reordering without evidence.

## False sharing

Independent goroutines mutate values that still share a **cache line**, causing cache-line “ping-pong” even though the variables are logically unrelated.

## Lab (benchmark-first)

1. Build two micro-benchmarks: **tight adjacent counters** vs **spacing/padding** variants.
2. Record results and noise caveats (thermal throttling, unrelated background load).
3. Write a short “would I ship this optimisation?” decision: only if tied to a measured production tail-latency/regression story—not because an interview question exists.

Interview prompt: how you’d distinguish false sharing from lock contention or allocator pressure using `pprof`/trace.
