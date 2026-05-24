# Context thinking — framing

## Phase framing — Context Engineering (“Phase 11.5”)

**Units in this folder:** `01`–`06` (topic order only).

### Mindset pivot

| Weak | Strong |
|------|--------|
| “Give the model **more** context.” | Give the model **the right** context—**relevant**, **precise**, **minimal**. |

**Checkpoint mantra:** you **design context**—pipelines for retrieval, partitioning, hierarchy, compression, injection, validation—not **flood tokens** and hope.

### Theme map

**Context shaping** • **partitioning** • **hierarchy** • **compression** • **retrieval optimisation** • **long-context ownership**

Design goals: avoid **token flood**, **context pollution**, **SPEC loss**, unbounded stale narrative dominance.

### Context Engineering Template — per serious task

| Field | Holds |
|-------|-------|
| **GOAL** | What success means for this slice—one sharp sentence plus links. |
| **REQUIRED CONTEXT** | Bullet list of artefacts / facts/classes that must enter the window—nothing gratuitous. |
| **CONTEXT HIERARCHY** | L1 goal → L2 SPEC → L3 implementation detail → L4 operational/incident artefacts (adjust labels to your org). |
| **CONTEXT PARTITION** | Which bundles load together (Symfony DDD lane, Go worker lane, Ops infra lane—no undifferentiated blob). |
| **RETRIEVAL PLAN** | What to fetch, from where, in what order, with freshness checks. |
| **COMPRESSION** | What survives summarisation—and what **must remain verbatim** (numbers, identifiers, invariant lines). |
| **STALE CONTEXT RISK** | What might be outdated; how you verify before acting. |
| **VALIDATION** | Proof window matches task—MODEL + human spot checks tied to acceptance. |

Relationships: retrieval syllabus and memory layers remain **paired disciplines**—this phase unifies **how bounded text flows into the assistant**.

---

**Theme (this unit)**

**Symfony refund example**

Weak: paste “whole CQRS system.” Strong: **refund boundary** excerpt, **payment ownership**, **retry ownership**, linked SPEC ids only.

**Go worker timeout**

Weak: ambiguous dump. Strong: worker SPEC, queue contract snippet, failure-ownership bullets.

### LAB invariant

Before heavy prompting, write **required context list** standalone—reuse as onboarding discipline for collaborators.

### Checklist

- [ ] “Required context” cites **paths or doc ids**, not vibes like “team knows refunds.”  
