# Diff ownership

## Phase framing — Diff / Refactor Ownership (“Phase 5.5”)

**Units in this folder:** `01`–`06` (topic order only).

### Themes

**Incremental refactor** • **diff ownership** • **migration ownership** • **safe change workflow** • **architectural evolution**

Mindset shift: the architect-assisted workflow spends more time **changing what exists** than minting greenfield blobs. Claude should default to **controlled evolution**.

### Reaction you want on a legacy system

First artefacts lean **diff**, **risk**, **migration**, **rollback**, **safe evolution** — not an instinctive **full rewrite**.

### Claude Refactor Template (Symfony / Go / DB / Ops)

| Heading | Holds |
|---------|-------|
| **CURRENT STATE** | What runs today — paths, behaviours, coupling you must not hallucinate away. |
| **TARGET STATE** | Observable end state for *this slice* — small enough to validate in one rollout window. |
| **DIFF** | Concrete edits: files/contracts/data/infra deltas (before → after mentally explicit). |
| **RISK** | Blast radius, partial failure modes, ambiguity in boundaries. |
| **MIGRATION** | Ordered steps bridging current → target — including compat layers and sunset flags. |
| **ROLLBACK** | Preconditions, ordering, irreversible forks called out honestly. |
| **VALIDATION** | Proof ladder: automated checks plus targeted manual / shadow traffic if needed. |
| **DEPLOY STRATEGY** | Blue/green, canary, feature flags, expand/contract migrations — whichever matches your stack policy. |

Use this whenever the task touches **running** behaviour—not only Application code (`Symfony`/`Go`) but schema, queues, caches, Terraform/Helm, feature toggles.

---

**Theme (this unit):** **Diff ownership** — “What am I changing?” before “What am I inventing?”

### Narrative rhythm

```
before (baseline truth)
    → after (minimal target intent)
        → named diff chunks (reviews land per chunk)
```

#### Example cue

Existing `OrderService` gains **clear refund ownership** at the boundary: who commands, who queries, where idempotency lives — **DIFF** spells that out module-by-module rather than rewriting the tree.

### Practice rotations

| Stack | Drill |
|-------|-------|
| **Symfony** | **CQRS-on-existing flow** — carve command/query seams without bulldozing the legacy service façade first. |
| **Go** | **Worker queue** touchpoint — one consumer path / one ACK semantics change defended in **DIFF+RISK**. |

### Lab invariant

Every task through this syllabus: Claude (or any assistant output you accept) delivers **CHANGE** × **IMPACT** × **RISK** before implementation paragraphs sprawl — map them to template columns loosely if that keeps you honest.

### Checklist

- [ ] **Baseline** cites actual symbols / paths / behavioural contracts—not a generic diagram.  
