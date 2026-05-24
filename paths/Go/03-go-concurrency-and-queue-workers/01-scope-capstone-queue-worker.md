# Unit 1 — Concurrency mindset and spine project (`queue-worker/`)

> **Suggested informational cadence:** ten thematic segments originally paired roughly with daily ~1–1.5 h pacing—**topic order preserved**, not timetable enforcement.

## Learning outcome trajectory

Discard vague “threads scary” folklore for **purposeful parallelism mental model**:

| Primitive | Operational meaning |
|-----------|---------------------|
| **goroutine** | lightweight logically concurrent function execution scheduled cooperatively—not free infinite scaling token |
| **channel** | communicate to share memory (idiom reversal from classical locks-first habits) |
| **mutex** | explicit shared-structure protection discipline |
| **select** | readiness multiplexing—not busy polling camouflage |
| **`context`** | cooperative cancellation propagation—again—not magic globals |

Understand **ownership of shutdown**: leaking goroutines is a correctness defect—even if demos “appear fine” briefly.

Final Area `03` capstone (**Unit 11**): integrate **producer**, **bounded buffer/channel**, **worker pool**, **`select`** coordination (timeout/cancel readiness), graceful **shutdown** narrative, intentional **fault injection** arcs (later repaired).

Interview consolidation later must cover:

goroutine distinctions vs OS threads coarse mental model • channel buffering trade-offs • **`select`** patterns • **`context`** cancellation propagation • **`sync.Mutex`** under contention • **`go run -race`** signalling data races • worker pool structuring.

## Spine repository

Maintain **`queue-worker/`** codebase (no frameworks, no mandatory HTTP)—pure concurrency educational laboratory across Units 2–11.

Acceptance ethos: reproducible behavioural commentary plus code—not mystical “trust me parallelism” assertions.
