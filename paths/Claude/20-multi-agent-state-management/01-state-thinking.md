# State thinking — durable handoff framing

## Phase framing — Multi Agent State Management (“Phase 8.6”)

**Units in this folder:** `01`–`06` (topic order only).

### Mindset pivot

Stop accepting “**next agent starts from zero**.” Start designing **continuity**: what must survive every hop so **spec**, **boundaries**, **ownership**, **risk**, and **history** do not evaporate when personas change.

Target surfaces: Symfony domains, Go workers, relational schemas, Terraform stacks, Kubernetes manifests, **incident** threads, **deploy** arcs—state threads stay coherent across the chain.

Operating chain (minimum intent):

```
 Agent n produces durable state delta
        → explicit HANDOFF contract consumed by agent n+1
                → optional CHECKPOINT for recovery
                           → CONSISTENCY CHECK before irreversible steps
```

Themes here: **shared state**, **synchronisation**, **memory ownership** (who curates shared truth), **state / context propagation**, **state recovery**, **handoff ownership**.

### Claude State Template — for serious multi-agent workflows

| Field | Holds |
|-------|-------|
| **SHARED STATE** | Authoritative artefacts visible to all relevant agents (project context, RULES references, architecture digest, SPEC anchors, NFR). |
| **LOCAL STATE** | Persona-private scratch (Planner task graph draft, Architect tradeoff workbook, QA scenario list) that must not silently replace shared truth. |
| **STATE CONTRACT** | Mandatory fields that **must** cross a given edge (goal, constraints, boundary, risk snapshot, open questions). |
| **HANDOFF** | Named producer → consumer, artefact pointers, version or commit id where applicable. |
| **RECOVERY** | How to resume after failure (which checkpoint, what to discard, who re-approves). |
| **CONSISTENCY CHECK** | Validation that local views match shared truth before act (e.g. “Redis” vs “memory cache” divergence). |
| **CHECKPOINT** | Immutable or versioned savepoint of shared state after a stable hop (ticket, ADR bump, tagged doc revision). |

**Checkpoint mantra:** you move from counting agents to running a **durable AI workflow** with explicit state discipline.

This complements **agent orchestration** (routing / approval): here the emphasis is **what persists** across those routes.

---

**Theme (this unit)**  

Weak pipeline: Planner → Architect → Implementer with **implicit** assumptions. Strong pipeline: each hop carries **minimal shared payload**: **goal**, **constraints**, **risk**, **ownership**—nothing “understood verbally only.”

**LAB invariant:** for **every handoff** in rehearsals, write **what must cross next** — one-line minimum per field above you use.

### Checklist

- [ ] No handoff lacks a **STATE CONTRACT** block—even if abbreviated—before downstream work expands.  
