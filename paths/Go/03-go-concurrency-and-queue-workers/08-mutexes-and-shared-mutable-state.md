# Unit 8 — Mutex & shared mutation: pessimistic guarding when purity cracks

Bad habit anti-pattern caricature:

> “Just share maps across goroutines because map writes feel easy.” → **crash / data race chaos**.

Responsible pattern:

Synchronize with **`sync.Mutex`** guarding invariants—not sprinkling blindly after-the-fact when `-race` yells louder than design.

## Practice

Increment shared counter pressured by ~100 concurrent goroutines.

1. Demonstrate flaky wrong results without instrumentation (may appear “fine” sporadically—never trust nondeterministic green runs).
2. Re-run enforcing **`-race`** highlighting data races vividly.
3. Serialize increments via mutex concluding determinism reproducibly—also measure coarse latency inflation qualitatively (not microseconds wars yet).

## Lab written reflection

Enumerate ** Mutex vs channels** decision heuristics: linear ownership pipelines vs shared counter-style hotspot needing lock.

Discuss **ordering deadlocks**: acquiring multiple locks inconsistently lethal pattern—sketch hypothetical cross-lock scenario resolved by consistent acquisition partial ordering conventions.

## Interview prompts

Contrast **optimistic concurrency** glimpses forward (defer Area `08` DB depth) layering mental hooks.
