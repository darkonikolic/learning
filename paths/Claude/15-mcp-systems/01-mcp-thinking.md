# MCP thinking — tooling orchestration framing

## Phase framing — MCP Systems (“Phase 7”)

**Units in this folder:** `01`–`06` (topic order only).

### Shift in stance

Away from assistants that primarily **produce prose explanations** of problems. Toward assistants that **orchestrate capabilities**: choose tools, honour permissions, surface risk, validate outcomes—and accept **rollup** responsibilities when tools mis-fire.

Comfort target on a composite incident (Symfony bug → git → filesystem → DB → browser evidence): first reaction cites **which tool**, **ordering**, **permission posture**, **risk**—before a wall of unstructured narrative.

### Tool classes (conceptual MCP surfaces)

Typical MCP categories you wire deliberately:

**Filesystem MCP**  

**Git MCP**  

**Database MCP**  

**Browser MCP** (docs, changelog pages, reproducible UI states)  

**Terminal MCP** — shell access with policy (logs, Docker, Terraform, kubectl) — overlaps **security** heavily with your Sandbox phase.

Cross-cutting disciplines:

**Tool ownership**, **permission ownership**, **routing** (problem → capability → implementation path), **capability honesty** (“model cannot see X unless server exposes safely”), **security ownership** (scopes, leakage, audit).

### Core micro-workflow model

```
 PROBLEM surfaced
     → CAPABILITY selection (why this modality answers the question class)
           → concrete TOOL call(s)
                 → observable RESULT artefacts
                       → VALIDATION tying back to problem acceptance
```

Risk and rollback ride alongside—not afterthought footnotes.

### MCP Template — for every meaningful problem slice

| Field | Holds |
|-------|-------|
| **PROBLEM** | Symptoms, reproduction, scope (service / tenant / cluster). |
| **CAPABILITY** | Why filesystem vs git vs DB vs browser vs shell matters here. |
| **TOOL** | Named integration path plus sequence (minimal viable chain first). |
| **PERMISSION** | What identities / paths / DB roles / namespaces are reachable—explicit. |
| **VALIDATION** | Checks proving success—not vibes. |
| **RISK** | Blast radius when tool hallucinates filters or runs broad queries. |
| **ROLLBACK** | How you retreat from partial tool-driven changes (migration, infra, config). |

**Checkpoint mantra:** Claude stops behaving as solo explainer—you drive **controlled multi-tool choreography**.

Integration safety still follows your **sandbox / secret isolation** norms; MCP widens blast radius whenever permissions are careless.

---

**Theme (this unit — orchestrator mindset)**

Weak pattern: latent belief “the model intrinsically knows the repo truth.” Strong pattern: model **consumes anchored reads** sourced through scoped tools—not magical recall.

Practice vignettes sketch **plans before calls**:

Symfony bug → **git annotate / history** hypotheses → filesystem reads on ownership boundaries (`Order`, `Payment`, `Refund`) → constrained fix iteration.  

Go worker fault → aggregated logs (`terminal`/`log tool`) → filesystem hotspots → corrective diff.

LAB: Document a **tool plan** (bullet list with ordering + permission notes) **before** the model fires tools—reuse that habit when automation agents appear later.

### Checklist

- [ ] Problem statement distinguishes **facts already observed via tools** vs **assumptions**.  
