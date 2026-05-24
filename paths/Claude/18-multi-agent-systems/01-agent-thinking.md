# Agent thinking — multi-role framing

## Phase framing — Agents (“Phase 8”)

**Units in this folder:** `01`–`06` (topic order only).

### Mindset pivot

Away from **one assistant doing everything contiguously.** Toward a **composed system**: distinct roles with clear **ownership**, handoff artefacts, and review gates—even when physically one model instance plays multiple hats sequentially via explicit prompts.

Target stack familiarity: Symfony, Go, database work, Terraform, Kubernetes—agents partition concerns instead of collapsing them.

### Role catalogue (minimal set for serious tasks)

| Role | Owns |
|------|------|
| **Planner** | Goals, task graph, dependency ordering, priority—**not implementation code**. |
| **Architect** | Boundaries (DDD seams, CQRS), tradeoffs, risk register, scalability / failure posture—“**why before how**”. |
| **Implementer** | Code/config changes realising the architecture slice—no silent scope creep into approval territory. |
| **QA** | Validation vs frozen acceptance: drift detection, risky gaps, constraint violations **before** trusting merge. |
| **Ops** | Runtime / containers / cluster / Terraform paths, observable signals, rollout + **rollback**. |
| **Reviewer** | Cross-cutting quality: security-sensitive patterns, maintainability, diff risk narration—orthogonal to QA’s behavioural checking. |

You may compose fewer roles on tiny tasks—but **substantial** deliveries should consciously touch this template.

### Claude Agent Template — for substantial work

Structured handoff scaffolding (adapt naming to your orchestration tooling):

```
 PLANNER artefact …
 ARCHITECT artefact …
 IMPLEMENTER artefact …
 QA artefact …
 OPS artefact …
 REVIEWER artefact …
```

Each section states: **ownership**, **inputs consumed**, **outputs produced**, **explicit non-goals** (what that role refuses to own this round).

Checkpoint mantra: Claude stops behaving as lone problem solver—problem solving becomes **multi-agent choreography** whether simulated or wired.

Integrity note: aligns with Sandbox / MCP / Retrieval habits—narrow permissions per role persona where automation exists.

---

**LAB (unit 1)**  

Symfony **refund flow** tabletop: write “**who owns what**” table before any code—Planner graph, Architect boundary/tradeoffs, Implementer edits, QA checks, Ops deploy hooks if applicable, Reviewer critique slots.

Go variant analogous on payment worker refactor planning.

### Checklist

- [ ] Every role section lists **dependence on prior artefacts**—no orphaned implementation without architecturally frozen slice.  
