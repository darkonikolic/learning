# Evaluation thinking — multi-domain framing

## Phase framing — Claude Multi Domain Engineering (“Phase 10”)

**Units in this folder:** `01`–`08` (topic order only).

### Scope you integrate (examples—not exhaustive each week)

**PHP:** Symfony, **Laravel** when relevant  

**Go:** APIs, distributed patterns, performance discipline  

**Frontend:** **Vue**, **JavaScript** ecosystems you ship  

**DB:** **MySQL** as primary relational lens  

**Ops:** Docker, Terraform, Kubernetes  

**Security:** review cadence + hardening expectations

### Mindset pivot

Away from “it works.” Toward **measure → improve** loops across **engineering** and **AI-assisted workflow**.

**Checkpoint mantra:** you **design, measure, and evolve** large systems—including how Claude, agents, retrieval, and approval behave—not only application code.

### Claude Principal Template — large-system / principal view

| Pillar | Question it answers |
|--------|---------------------|
| **ARCHITECTURE** | What shapes the system end-to-end? |
| **OWNERSHIP** | Who decides and runs each slice? |
| **DEPENDENCY** | What depends on what—with what failure modes? |
| **FAILURE** | What breaks—how detected—how recovered? |
| **OBSERVABILITY** | Do we see truth before users do? |
| **COST** | Tokens, infra, brains, latency—priced honestly? |
| **OPTIMIZATION** | Targeted improvements with evidence—not vibes? |
| **EVOLUTION** | What changes in 6–24 months—planned? |
| **EVALUATION** | How do we score quality and regressions systematically? |

Use this alongside domain-specific specifics (Symfony DDD seams, Go concurrency contracts, Laravel conventions when that stack is active, Vue component boundaries, etc.).

---

**Theme (this unit): Evaluation thinking**

| Poor | Strong |
|------|--------|
| “Feels smooth in demo” | **Named metrics**, baseline, deltas after change |

Starter metric catalog (adapt weights):

**Claude / AI workflow**

Repair count  

Iteration count to acceptance  

SPEC drift incidence  

Hallucination or overconfidence misses caught  

Approval correctness versus matrix  

Retrieval grounding quality  

**Symfony / PHP services**

Ownership / boundary clarity scores  

Coupling hotspots  

Structural complexity heuristic (your rubric—not abstract magic numbers only)

**Go**

Concurrency correctness checkpoints  

Failure ownership clarity (timeouts, cancellations, retries)  

Latency envelopes vs simplicity tension

**Ops**

MTTR buckets  

Rollback rehearsal quality  

Incident narrative completeness (hypothesis, evidence, fix, follow-up)

### LAB invariant

Attach an **evaluation block** to every serious workflow run—even brief—so improvement has a spine.

### Checklist

- [ ] At least one metric is **automatable or semi-automated** over time (script, dashboard, CI gate)—not only subjective notes.  
