# Unit 3 — Allocation thinking: pressure, escapes, observable growth

Loops that allocate per iteration pressure **GC**—sometimes dominating wall time more than naive Big-O guesses.

Practice:

Craft **`append`** / string concatenation pitfalls vs efficient patterns—observe **allocation count** deltas using `-benchmem`.

Relate intuitively:

| Question | Probe |
|---------|-------|
| stack vs heap | not always predictable without tooling—use profiler + escapes where confused |
| value copying | slicing big structs unknowingly allocates / copies bridging earlier fundamentals |

## Lab essay

“When allocation rate rises disproportionately versus CPU hotspots” diagnostic steps—mention `go tool pprof` heap sample preview forward units.

Interview focus: articulate **difference algorithmic complexity vs allocator chatter** verbally crisp.

