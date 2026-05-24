# Approval thinking — human loop framing

## Phase framing — Approval Workflow (“Phase 8.9”)

**Units in this folder:** `01`–`05` (topic order only).

### Why this exists

An architect or multi-agent workflow **without an approval model is incomplete**: high-energy changes need **human verification**, **alignment**, and explicit **authorization**—not “model said so.”

Target operating shape:

```
 Agent / AI produces PROPOSAL + confidence signal
         → HUMAN or delegated role REVIEWS against risk & specs
                    → APPROVAL captured where policy demands
                           → EXECUTION under scoped credentials
                                   → POST REVIEW / rollback ownership if reality diverges
```

### Theme map

**Human approval** tiers • **dangerous action** gating • **rollback ownership** • **verification ownership** (who signs that checks happened) • **deployment approval** • **human correction ownership** • **feedback integration** • **iterative alignment** with Rules/Skills evolution

### Claude Human Loop Template — serious tasks

| Field | Holds |
|-------|-------|
| **TASK** | Goal slice, constraints, links to SPEC/RULE ids. |
| **CONFIDENCE** | High / medium / low—with reason; triggers escalation when below threshold. |
| **REVIEW** | What reviewers must check (diff, plan, migration phases, blast radius). |
| **FEEDBACK** | Corrections from humans; must be integrated, not ignored on next turn. |
| **ALIGNMENT** | Agreements updated (wording, diagrams, acceptance); loop until match. |
| **APPROVAL** | Who approved what class of action; timestamp or ticket id. |
| **EXECUTION** | What ran, under which environment, with what observability. |
| **POST REVIEW** | Reality vs expectation; rollback trigger conditions; verification sign-off. |

**Verification ownership** sits with whoever attests post-deploy checks—not the model alone. **Rollback ownership** names who can initiate retreat and in what order.

**Checkpoint mantra:** you stop equating “assistant output” with truth; you run **AI + human as one system**.

Sandbox / security syllabus expectations still apply: approval is part of **least privilege**, not optional politeness.

---

### Approval matrix — starting point (adapt to your org)

| Level | Examples | Typical gate |
|-------|----------|--------------|
| **Safe** | Read docs, read non-secret logs, explain code | Usually no formal approval—still log high-risk reads if policy says so. |
| **Review** | Refactors, schema/migration plans, infra diffs | Peer or role review before merge/run. |
| **Approval** | `terraform apply`, DB migration execution, `kubectl apply` to shared clusters | Explicit approver + often change window / plan artifact. |
| **Human-only** | Credential rotation, destructive prod deletes, “destroy” class operations | Restricted identities; often two-person rule; assistants must not execute. |

**LAB invariant:** For each task rehearsal, assign an **approval level** from this matrix before work expands.

**Dangerous actions** (apply, migrate, kubectl to shared env, destroy-class) always map to **Review** or higher—never **Safe**.

### Checklist

- [ ] “Approved” implies a **recoverable artefact trail**—ticket, immutable log, or signed CI record—not only chat agreement.  
