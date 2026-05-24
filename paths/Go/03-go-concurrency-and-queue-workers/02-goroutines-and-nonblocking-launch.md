# Unit 2 — Goroutine thinking: cooperative scheduler intuition

## Learning outcome

Internalise **`go func()`** separates *launch scheduling* vs *completion witnessing* demands explicit synchronization primitives (`WaitGroup`, channel closure patterns, supervised errgroup patterns later—you choose minimal honest mechanism now).

Interpret Go mental model contrasts:

Bad oversimplification: “thread == goroutine simplistic manual lifecycle” → misleads newcomers.

Closer truth: goroutines multiplex atop runtime scheduler cooperating with cooperative blocking semantics at channel / syscall boundaries—study surface remains **logical concurrency clarity first**, internals second.

## Practice

Simulate “email/job dispatch”: fan out ~5 concurrently operating workers printing traceable IDs respecting ordering non-guarantees—observe nondeterministic interleaving deliberately.

Explain conversationally:

> Why **`go Process()`** does not block callers until you add coordination.

## Lab question (answer aloud)

Enumerate typical beginner bugs:

- orphaned goroutines,
- main exiting early,
- unbounded spawning spirals unrealistic production analogues.

## Interview prompts

Cheap creation ≠ cheap system load under pathological spawning.

Preemption evolution awareness (fine-grained preemption matured historically—don’t memorize timeline obsessively unless interviewing kernel teams).
