# Enterprise depth appendix (Faza 12)

Companion to **`01–08`**. Ownership still lives in weekly deliverables—this file is the **explicit syllabus critics wanted**: serious **test**, **distributed systems**, **observability**, **Go perf**, **Kubernetes production**, **database enterprise**, and **STRIDE** depth for the Payment Platform capstone.

**How to use:** skim once in Week 1; drill sections as each week assigns hooks (`01.*` cites this file). Maintain **living links** from your SPEC/architecture notebooks.

---

## 1. Test engineering (serious layering)

Goal: acceptance + NFR become **executable**—each line knows its proof class.

| Layer | What it guards | Typical failure modes if skipped |
| ----- | ------------- | -------------------------------- |
| **Unit** | Pure domain logic, deterministic branches | regressions disguised behind integration flake |
| **Integration** | ORM/repo + migrations + HTTP edges + broker client wiring | migrations break prod only |
| **Contract** | Stable consumer/provider schemas (REST/OpenAPI/async schema) | deploy order lottery |
| **Property-based** | Invariants (“no refunds exceed capture”, idempotent replays yield same outward effect class) | edge combinatorics missed |
| **Load** | Throughput/saturation envelopes, percentile latency | graceful degradation unknown |
| **Chaos / fault** | Behaviour under bounded real faults (paused broker TCP, flaky DNS) | folklore resilience |

### Contract testing posture

- Choose **producer-driven** (`schemathesis`, Pact provider) vs **consumer-driven** (classic Pact) deliberately. Payment edge often = **provider** strictness; PSP adapter might be consumer of external contract tests you don’t fully control — document **verification gaps**.

### Property testing intuition

Encode **generator + shrink** workflows for one scary invariant slice (replay storms, randomized partial saga completion). Prefer fewer properties with strong meaning over random fuzz noise.

### Load testing realism

Define **steady state**, **stress**, **soak**. Track **p95/p99** + error budget—not only average. Correlate saturation with worker pool + DB conn limits.

### Chaos testing guardrails

- Always **steady-state hypotheses** beforehand (“queue depth bounded”, “DLQ unchanged”, “0 money inconsistent states”). Abort when blast radius escapes sandbox.

### Test × chaos interplay with optimisation

After a performance change, re-run a **small chaos or load slice** (same harness as Week 3/7) to ensure optimisations did not widen retry storms, shrink bulkheads dangerously, or mask saturation. Treat “faster but flakier under fault” as a failed iteration.

Cross-links: Weeks **1** (plan classes), **3** (implement suites), **6–7** (observe + regress under change).

---

## 2. Distributed systems

### CAP (nuanced—not a vendor checkbox)

_partitions happen._ Document for **each critical path**:

- Availability vs consistency choice under partition **what user sees**. Example: PSP unreachable → degrade to **explicit failure** vs optimistic accept + reconciliation queue.

### Consistency models (name them honestly)

Examples to tag in architecture:

**Strong consistency** inside single MySQL transactional boundary  

**Sequential / linearizable** seldom across PSP + ledger—avoid claiming unless true  

**Causal / read-your-writes** for UX after mutate commands  

**Eventual** for analytics projections, notifications, non-money secondary reads—with **lag SLA** wording

### Outbox pattern (transaction + message alignment)

Classic fix for dual-write hallucination:

1. Business mutation + enqueue **same DB transaction** (outbox row).  

2. Publisher relay process ships to broker reliably.  

3. Consumer idempotency + dedupe keys correlate with ledger events.

Discuss **polling vs log-tailing relay**, ordering guarantees, backlog pressure ownership.

### Saga pattern

- **Choreography** (events bounce) vs **orchestration** (central saga brain). Ownership clarity often favours orchestrator for refunds/inventory choreography complexity—still document **every compensating action** + **timeouts**.

### Circuit breaker • bulkhead • rate limiting

**Circuit breaker** — fail fast downstream; beware half-open churn; align with retries + idempotent verbs only.  

**Bulkhead** — thread pools per dependency class (PSP vs internal query) isolation.  

**Rate limit** — edge protection vs fairness; distinguish **capacity shedding** vs **abuse mitigation**.

Related Week **2** architecture + **3** implementation (client middleware).

---

## 3. Observability (OpenTelemetry + Prometheus + Grafana + Jaeger)

### OpenTelemetry (OTel)

- Standard **traces + metrics + logs correlation** via context propagation.  

- Symfony: HTTP middleware + DB spans; Go: consumer spans per message.  

- Export to **OTLP** collector → fan-out to Prometheus/Jaeger stacks.

### Prometheus

- Counter/histogram naming discipline; exemplars (where supported) linking latency buckets to trace ids.  

- Alert on **golden signals adapted** — not “CPU high” orphan alerts.

### Grafana

- Dashboard-as-code mindset; overlays for deploy annotations.  

- Use **recording rules** sparingly—clarity beats cleverness early.

### Jaeger / tracing practically

Practice drill:

1. Take **trace id** from slow payment.  

2. Jump to PSP callback span boundaries.  

3. Correlate log fields (`payment_id`)—assert single coherent story within SLO budgets.

Incident Week **6** demands this—not optional gloss.

---

## 4. Go performance engineering

Minimal production literacy:

| Technique | Typical question answered |
| --------- | ------------------------- |
| `go test -bench` | micro hot path regressions |
| `pprof` CPU | where time goes under load |
| `pprof` heap/allocs | unexpected allocation churn |
| `pprof` goroutine | leaks / stuck concurrency |
| `pprof` block/mutex | scheduling / lock contention |
| Escape analysis (`-gcflags=-m=2`) | surprise heap escapes from hot tiny helpers |

Always pair profiles with **correctness tests**—faster wrong ledgers are worse.

---

## 5. Kubernetes production controls

| Concern | Why it matters for payments |
| ------- | --------------------------- |
| **Ingress** | stable external API + TLS story |
| **NetworkPolicy** | blast radius to metadata/PSP endpoints |
| **Service mesh (conceptual)** | uniform mTLS, traffic policy, retries vs idempotency hazards—**optional** but understand tradeoffs |
| **PodDisruptionBudget** | voluntary disruption safety during drain/rollout |
| **Affinity / anti-affinity** | AZ spread, noisy neighbour isolation |
| **Taints / tolerations** | dedicated pools (GPU unlikely here; maybe spot vs on-demand simulation) |

Mesh adoption is **not required**—but you must write **one paragraph** why adopt or defer with risk acceptance.

---

## 6. Database enterprise (MySQL-flavoured)

### Transaction isolation

Know differences at least between **READ COMMITTED** vs **REPEATABLE READ** (MySQL/InnoDB specifics: gap locks, phantom risks). Map chosen levels to **payment vs reporting** paths.

### Deadlock analysis

Practice reading deadlock graph output: lock order inversion across refund + inventory updates. Mitigations: consistent lock ordering, smaller transactions, optimistic paths.

### Replication

**Async replica lag** → stale read risks. Document which reads may hit replicas vs must stay on primary.

### Partitioning / sharding (future you)

Capture **hot partition key** risk now even if unsharded—prevents surprise scale rewrite.

### Locking strategies

**Optimistic** — version column / compare-and-swap; fewer long locks; requires conflict UX.  

**Pessimistic** — `SELECT … FOR UPDATE`; stronger immediate consistency; deadlock sensitivity.

---

## 7. Threat modeling — STRIDE & attack surface

### STRIDE quick map

| Class | Example payment concern |
| ----- | ----------------------- |
| **Spoofing** | forged webhooks, stolen tokens |
| **Tampering** | altered callback payloads, message replays |
| **Repudiation** | missing audit correlation on money movement |
| **Information disclosure** | verbose errors leaking PAN metadata, log PII |
| **Denial of service** | webhook floods, queue stuffing |
| **Elevation of privilege** | worker creds over-scoped to DB rows |

### Attack surface modeling

Enumerate **entrypoints** (public API, admin, queue consumers, CI agents, assistant tool scopes). For each: trust boundary, data carried, blast radius, reduction options.

Store STRIDE tables **versioned** next to architecture—update when flows change.

---

## 8. Cross-week lab ideas (pick 2–3 total if time-constrained)

1. **Outbox relay failure** — pause relay; verify lag metrics + no money inconsistency; recovery path.  

2. **Contract break** — introduce incompatible event field; ensure pipeline surfaces before prod.  

3. **Jaeger-led incident** — remove logging clue; navigate via trace spans only until hypothesis.  

4. **Deadlock rehearsal** — contrived concurrent refund/inventory locking; document ordering fix + test.  

5. **NetworkPolicy accidental deny** — break egress; practise triage dashboards vs blind restart.

---

### Appendix checklist (merge into Week 8 rubric selectively)

- [ ] STRIDE artefacts updated ≥ once after architectural change  

- [ ] Contract/schema tests enforced in CI for published edges  

- [ ] OTel propagation verified cross Symfony ↔ Go boundaries  

- [ ] Load profile reproduced from scripts—not anecdotal dashboards  

- [ ] PDB + NetworkPolicy rationales documented with rollback paths  

- [ ] Known isolation/deadlock story for concurrency hot path written down  

- [ ] pprof before/after saved for at least one optimisation cycle  
