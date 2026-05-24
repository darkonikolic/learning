# Optimization ownership

**Unit:** `07` (week 7)—production means **good enough under SLO**, then **measurable improvement.**

### Measure

**Cost** (tokens, infra, human time proxies)  

**Latency** end-to-end and hot segments  

**Quality** rubric adherence  

**Repair count** trend after changes

### Practice

Go **worker** throughput / contention tuning with proof (profiles, benchmarks).  

Go **performance engineering minimum bar**  

**pprof workflows** — CPU profile around hot handlers; `-http` profiling endpoint gated + auth  

**Heap / allocs profiling** — track allocation regressions comparing v2 vs v3 worker builds  

**Goroutine leak detection** — `goroutine` profile diff after soak; tie to forgotten receive channels / stuck ack loops  

**Block / mutex profiles** — when tail latency unexplained  

**Escape analysis intuition** — read `-gcflags=-m=2` sparingly where allocation surprise blocks budget; document one micro-case per iteration  

Symfony/PHP side optimisation stays bounded—this unit emphasises worker hot path realism. Canonical notes: **`09-enterprise-depth-appendix.md` § Go performance.**

**DB** slow-query remediation with `EXPLAIN`-class evidence (where policy allows).  

Replication / partitioning second-order tuning only after correctness proven—latency wins that violate the isolation story must be documented explicitly as regressions or accepted tradeoffs.  

**Ops**: deploy cadence, rollout strategy, warmup—optimise friction without skipping safety gates.

Repeat **Load** characterization from structured test harness—not only dashboards assuming traffic shape. Chaos micro-experiments may validate optimisation didn’t widen failure blast radius (**appendix § Test / Chaos interplay**).

### LAB

Ship **v1 → v2 → v3** of one slice with the **same acceptance** bar; chart metrics—reject “faster” that drops correctness.

### Checklist

- [ ] Each step documents **what regressed checks** guarded against—optimization without regression discipline is debt.  

- [ ] At least **one optimisation round** cites **before/after pprof** (or equiv) artefacts—not folklore speedups.  
