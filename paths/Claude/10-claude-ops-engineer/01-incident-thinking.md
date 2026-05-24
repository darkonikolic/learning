# Incident thinking — ops framing

## Phase framing — Claude Ops Engineer (“Phase 6”)

**Units in this folder:** `01`–`08` (topic order only).

### Theme stack — delivery + observability + ownership

**Ops tooling:** Docker • Kubernetes • Terraform • Helm • **IaC**  

**Observability:** logs • traces • metrics • **incident ownership**

Failure practice lenses: **DB** • **worker** • **K8s** • **network** (rotate through drills).

### Response evolution

**Discard:** visible outage → mute panic → random restart roulette.  

**Adopt:**

```
 Incident  →  Hypothesis set  →  Logs / metrics / traces  →  VALIDATION gates  →  Fix  →  Rollback doorway
                                                           →  Recovery narrative
```

“Claude gives a fix immediately” bows to “Claude **shepherds** incident process with evidence cadence.”

### Claude Incident Template — use for Go / Symfony / Ops / IaC slices

| Field | Holds |
|-------|-------|
| **SYMPTOM** | User-visible or SLO-bearing deviation—in plain operational language + scope (which env / cluster / tenant lane). |
| **HYPOTHESIS** | Ranked guesses **before** deep fix coding—explicit disproof paths. |
| **LOGS** | Which selectors, timestamps, anchors (`request_id`, `trace_id`, pod uid, deploy revision). |
| **METRICS** | Signals vs noise hypotheses—dashboards/queries—not vibes. |
| **TRACE** | Span graph expectations; known gaps instrumented vs blind zones. |
| **VALIDATION** | Experiments disproving hypotheses or confirming culprit class without production thrash where avoidable. |
| **FIX** | Minimal corrective change respecting blast radius budgeting. |
| **ROLLBACK** | Ordering; irreversible leaps named; parity with infra state snapshots. |
| **RECOVERY** | Health restoration proof; backlog drain; customer comms placeholders if SLA breach feared. |

---

**Theme (this unit):** **Evidence before thrash.** Do not brainstorm random toggles—“What am I **proving / disproving**?”

Structured micro-workflow tying to investigations:

```
 problem statement  →  crisp symptom taxonomy  →  hypothesis forest  →  validation ladder  →  mitigating fix hypothesis
```

### Practice vignettes mapping

| Stack | Stress idea |
|-------|--------------|
| **Go** | **Slow worker** — saturation vs blocking IO vs contention. |
| **Symfony** | **Queue backlog** growth — enqueue faster than drains? poison? external dependency stutter? |
| **DB / MySQL** | **Escalating query latency** — plan regression vs lock contention vs saturation. |

### LAB invariant (**unit 01** onward)

Facing any synthetic outage write **≥ five hypotheses** ranked with **cheap→expensive** disqualification sequencing **before** a fix PR description grows.

### Checklist

- [ ] Incident doc states **baseline vs deviation window** anchored to revision / deploy artefact—not “sometime slower.”  
