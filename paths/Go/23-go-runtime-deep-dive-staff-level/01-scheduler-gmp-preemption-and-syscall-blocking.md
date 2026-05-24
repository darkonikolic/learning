# Unit 1 — Scheduler at staff depth: G/M/P (evidence over folklore)

Build on Areas `03`, `15`, `16` with sharper runtime vocabulary:

## What staff-level clarity looks like

- Explain **why work stealing reduces idle `P`** under uneven goroutine churn—without pretending it removes all tail latency tails.
- State how **syscall blocking** can occupy an **`M`** and indirectly reduce CPU throughput for runnable goroutines (high-level mental model suffices; avoid OS-scheduler trivia unless you genuinely operate there).
- When discussing **preemption**, anchor claims to **current Go release/runtime documentation** rather than ageing blog summaries.

Interview drill:

- Differentiate scheduling pressure for **CPU-bound** vs **IO-bound** services.
- Name at least three observability signals (CPU profile, trace, scheduler metrics if available) you’d use to validate a scheduling hypothesis.
