# Experiment thinking — large codebase + AI framing

## Phase framing — Large Codebase AI Engineering (“Phase 10.5”)

**Units in this folder:** `01`–`05` (topic order only).

### Why this phase exists

You are **not optimising toy CRUD repos**. Typical surfaces:

**Frontend**, **backend** (e.g. Symfony), **workers** (e.g. Go), **Terraform**, **shared libraries**—possibly **monorepo** or **polyrepo** with brittle cross-repo links.

AI assistance must cope with **huge ambiguity surface**: dependency graphs, SPEC sprawl, and retrieval that either floods context or misses the truth.

### Large-codebase theme map

**Monorepo vs polyrepo** tradeoffs for AI + humans  

**Dependency ownership** (who guarantees API stability across packages)  

**Cross-project context** discipline  

**Incremental context loading** — slice-by-slice; add the next artefact only when dependency graph or retrieval proves it needed—not whole-repo paste.  

**Context partitioning** — which services, packages, or SPEC ids may sit in one assistant window together.  

**SPEC partitioning** — one authoritative doc per bounded capability; cross-links instead of megadoc entropy.

### Mindset pivot

| Weak | Strong |
|------|--------|
| “I changed something—hope it’s better.” | **Hypothesis → controlled change → metric → conclusion → guarded rollback** |

**Checkpoint mantra:** you **proved** impact—not only **performed** a change.

### Experiment Template — serious optimisation or workflow tweak

| Field | Holds |
|-------|-------|
| **PROBLEM** | Measurable pain (latency, coupling, retrieval miss rate, tokens, incidents). |
| **HYPOTHESIS** | If we change X, we expect Y on metric Z—because … |
| **CHANGE** | Minimal diff describing what actually moved (Rules, Skills, chunking, code). |
| **KPI** | Primary + secondary metrics—declared before the run. |
| **A/B TEST** | How A vs B run (sequential with reset, shadow traffic, branch pair—be honest about limits). |
| **RESULT** | Numbers + qualitative notes; confidence level. |
| **REGRESSION CHECK** | What else could have broken—explicitly checked. |
| **DECISION** | Adopt, iterate, revert, or schedule follow-up experiment. |

---

**Theme (this unit): Experiment thinking**

Example hypotheses (illustrative):

**Claude workflow:** smaller retained context → fewer tokens → **same answer quality** on task class T (verify with rubric).

**Symfony:** sharpening **ownership boundaries** hypothesised to cut cross-module churn / coupling smell.

**Go:** resizing worker concurrency (e.g. pool hypotheses) hypothesised to move **latency** or **saturation**—measure before believing.

### LAB invariant

Every optimisation—or retrieval / Skills / topology change—is invalid without a logged **hypothesis**.

### Checklist

- [ ] Experiments touching **production paths** honour **approval** and **sandbox** norms—staging or flags first where needed.  
