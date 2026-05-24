# Metrics thinking — evaluation framing

## Phase framing — Evaluation Systems (“Phase 11.6”)

**Units in this folder:** `01`–`05` (topic order only).

### Mindset pivot

| Weak | Strong |
|------|--------|
| “It feels fine.” | “**I measured** and can compare runs.” |

### Theme map

**Benchmark ownership**, **quality metrics**, **hallucination proxies**, **latency**, **cost (tokens/time)**, **golden datasets**, **regression benchmarks**, **evaluation suites**, **baseline ownership**, **quality drift** detection.

### Operating workflow (reuse every optimisation or model/tool change)

```
 MEASURE (same rubric each time)
           → COMPARE versus baseline snapshot
                                         → OPTIMISE deliberately—then re-measure honestly
```

### Lightweight evaluation run record (append to notebooks or CI artefacts)

| Field | Holds |
|-------|-------|
| **BASELINE REF** | Version id (Rules/Skills/date/commit). |
| **TASK / PROMPT SIGNATURE** | Stable id so reruns stay comparable. |
| **METRICS** | Numeric + short notes—see below. |
| **DIFF VS BASELINE** | What got better/worse—not vibes. |
| **DECISION** | Keep regression, rollback policy change, widen dataset, etc. |

### Starter metric buckets

**Quality**  

Specification adherence completeness  

Maintainability posture  

Structural / **DDD correctness** (Symfony-heavy tracks)  

**Security** heuristic score where applicable  

**Go** auxiliary: creeping **complexity**, **performance-risk** smells, observable **SPEC drift**

**Latency**  

Wall clock to usable answer—not only model raw tokens.

**Cost**  

Token counts where available; optionally human calibration minutes.

**Hallucination / grounding**  

Fabricated APIs, inverted ownership facts, unsubstantiated infra claims—tally severity.

---

**LAB — scoring dimensions (illustrative 0–10 rubric)**

**Symfony CQRS aggregate task** authored by Claude or trainee—rate:

SPEC adherence  

Maintainability  

Security sensitivity handling  

DDD / boundary correctness coherence

**Go worker retry subsystem** artefact suite—track:

SPEC drift occurrences vs authoritative doc  

Structural complexity heuristic you define  

Latency / amplification risk narration quality

Iterate until rubric explanations stay **consistent** scorer-to-scorer—even if subjective initially.

### Checklist

- [ ] At least one dimension each run can be scored **cold** by a second person using only the written rubric—repeatability beats private intuition.