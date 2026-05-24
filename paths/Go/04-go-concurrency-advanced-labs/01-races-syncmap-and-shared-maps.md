# Unit 1 — Shared-map turbulence: practise mutex, `RWMutex`, and `sync.Map` trade-offs

> **Bridging informational cadence:** conceptual block sequence originally mapped to roughly four deepening “weeks”; treat numbering as deepening order.

## Practice scaffolding

Stress **shared map** concurrent writes until runtime panics or races manifest—observe failures differ under `-race` harness vs naive runs.

Remediation ladder:

| Stage | Tooling | Commentary |
|-------|---------|-----------|
| 1 | `sync.Mutex` around every mutating structural access | straightforward baseline |
| 2 | **`sync.RWMutex`** distinguishing dominant read-heavy profile | amortise contention when truly read skewed—not cargo-cult prematurely |
| 3 | **`sync.Map`** exploratory fits specialized dynamic key churn / cache-ish patterns—not drop-in synonym for careless global map substitution |

Articulate drawbacks: coarse lock serialisation vs fine-grained design complexity trade spectrum.

Cross-reference eventually **PostgreSQL concurrency** grounding truth—prefer DB invariants authoritative when domain demands durability—not heroic in-memory map warfare.

Deliverable expectation: reproducible storyline + metrics-free qualitative latency commentary permissible now.
