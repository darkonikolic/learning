# Orchestration thinking — conductor framing

## Phase framing — Agent Orchestration (“Phase 8.5”)

**Units in this folder:** `01`–`07` (topic order only).

### Mindset pivot

Multiple agents cease being **sequential chatter chaos** once an **orchestration layer** exists: deliberate **routing**, **ownership**, **approval**, and **recovery**—not naive “Planner → Architect → Implementer forever” for every twitch.

Comfort target spanning Symfony, Go, MySQL evolution, Terraform, Kubernetes manifests, and **deploy choreography**: behaviour reads **system**, not improvised role-play.

### Theme map

**Orchestration ownership** — who runs the playbook end-to-end.  

**Routing ownership** — which capability answers which task class (**can** vs **should** discipline).  

**Task delegation / capability routing** — mapping problem surfaces to personas + tools cleanly.  

**Topology** — pipelines, forks, escalation loops, parallelism—drawn consciously.

Canonical macro-workflow (**adapt per incident vs feature strand**):

```
 Requirement clarification
       → PLANNER decomposition wave
               → ARCHITECTURAL freeze slice
                       → IMPLEMENTER execution corridor
                                     → QA validation gate
                                              → REVIEWER quality / security overlays
                                                               → OPS / APPROVED DEPLOY choreography
```

**Ops incident** shorthand may compress earlier roles or reorder (**Ops → Reviewer → human approval**)—orchestration decides case-by-case.

### Claude Orchestration Template — substantial tasks minimum

| Field | Holds |
|-------|-------|
| **ORCHESTRATOR** | Named controlling pattern (human you? automation graph?) invoking transitions. |
| **ROUTING** | Which agents activate, **why**, exit criteria per hop. |
| **CONTEXT** | Required payloads each hop receives (SPEC excerpt, diagrams, infra delta scope). |
| **STATE** | Shared artefacts authoritative vs ephemeral; mutability & owners. |
| **APPROVAL** | Classification of actions needing reviewer / ops / human release sign-off. |
| **FALLBACK** | Degraded modalities when prerequisite agent blocked (skip? retry? escalate?). |
| **RECOVERY** | Repair loops sequencing after QA/reviewer rejection or infra partial apply. |
| **VALIDATION** | Cross-cutting checks asserting orchestrated output still matches acceptance story. |

**Checkpoint mantra:** artefacts shift from boasting “many agents assembled” toward transparent **AI system choreography** reproducible deliberately.

Relationships: builds atop **per-role ownership** once you have defined agent personas—this area composes how they are **invoked and coordinated**.

Integrity: keep **sandbox**, **MCP**, and **retrieval** habits in mind when wiring automation—permissions and evidence still apply.

---

**LAB invariant (unit onward)**  

For each task tabletop: annotate **exactly why chosen agent activates**—not generic capability listing.

Example slices:

Symfony **refund defect** exploratory chain likely engages Planner discovery → Architecture boundary narrowing → Implement + QA iterative ring.  

**Ops incident:** likely opens at Ops telemetry triage funnel → Reviewer on risky infra diff → gated approval—not full planning fanfare blindly.

### Checklist

- [ ] Topology diagram—even ASCII—captures branching & escalation realistically once tasks exceed trivial linear fairy tales.  
