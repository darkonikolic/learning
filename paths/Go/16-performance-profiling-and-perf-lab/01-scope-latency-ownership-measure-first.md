# Unit 1 — Scope: Latency Ownership — Measure First

## Concept

This module profiles a slow HTTP handler, finds the bottleneck, and fixes it with evidence. You will write benchmarks, collect pprof CPU and heap profiles, and make changes guided by data instead of intuition. The rule is: measure first, optimize second — the bottleneck is almost never where you think it is.

## Code

```go
// What you will build across this module:
//
// slowHandler (provided)
//   - An HTTP handler with multiple inefficiencies built in
//   - Unnecessary allocations in the hot path
//   - A blocking call where none is needed
//   - Redundant JSON encoding
//
// Your job, unit by unit:
//   1. Write benchmarks — establish a baseline ns/op and allocs/op
//   2. Add pprof — collect a CPU profile under load with hey or wrk
//   3. Read the flame graph — find the widest frame that is your code
//   4. Fix the top bottleneck — measure again to confirm improvement
//   5. Repeat for heap profile — find inuse_objects growth, fix it
//
// Target: reduce p99 latency by at least 40% using only profiling evidence

package perf // placeholder — each unit fills this in
```

## Exercise

**Build:** Nothing yet. Read the scope and answer: what is the difference between a benchmark and a pprof profile? When do you need each?
**Input:** Your reasoning
**Output:** Write two sentences: (1) what a benchmark tells you that a profile does not, (2) what a profile tells you that a benchmark does not
**Acceptance:** You can explain: benchmark = reproducible measurement of a specific code path; profile = where real CPU time goes during a realistic workload

## Interview

- What does `-benchmem` show that `-bench` alone does not?
- Why should you never optimize code you haven't benchmarked first?
- Name two tools in the Go standard toolchain for measuring performance.
