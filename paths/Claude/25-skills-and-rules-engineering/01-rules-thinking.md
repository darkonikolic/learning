# Rules thinking — engineering defaults

## Phase framing — Skills + Rules Engineering (“Phase 9”)

**Units in this folder:** `01`–`08` (topic order only).

### Mindset pivot

Stop retyping the same constraints every session. Encode **how you work** in **Rules** (persistent policy) and **what you run** in **Skills** (repeatable workflows with clear inputs/outputs). The assistant should load **your** Symfony, Go, ops, review, security, and architecture style—not a blank tabula rasa.

### Theme map

**Rules:** architecture • security • coding • review (and anything else you want always-on).  

**Skills:** domain packs (e.g. Symfony architect, Go backend, ops debug, Terraform review, MySQL review).  

Cross-cutting: **reusable workflows**, **reusable prompt shapes**, **reusable validation** hooks.

### Claude Engineering Template — per serious project or workspace

| Pillar | Role |
|--------|------|
| **RULES** | Non-negotiables and defaults (style, safety, review bar). |
| **SKILLS** | Procedure blueprints: inputs → steps → outputs. |
| **MEMORY** | Where durable context lives (SPECs, ADRs, runbooks)—not chat. |
| **RETRIEVAL** | How facts are pulled into working context safely. |
| **AGENTS** | Role boundaries when you use multi-step automation. |
| **SECURITY** | Approval, secrets, injection resistance—wired to Rules. |
| **APPROVAL** | Human gates for high-energy changes. |
| **EVALUATION** | Rubrics so you improve Rules/Skills deliberately. |

**Checkpoint mantra:** you move from “using Claude” to owning a **Claude engineering platform**—Rules and Skills are the load-bearing walls.

Where files live depends on your editor (e.g. Cursor typically uses **Rules** under `.cursor/rules/` and **Skills** as `SKILL.md` trees)—mirror your product docs; paths in labs are placeholders.

---

**Theme (this unit): Rules thinking**

Contrast:

| Weak | Strong |
|------|--------|
| Every session: “use CQRS, DDD, small interfaces…” | **`go-rules`** / **`symfony-rules`** / **`ops-rules`** fragments stating defaults once |

Illustrative **Go** Rule bullets you might codify:

Prefer **composition**; **small interfaces**; **explicit errors**  

Default data access stance (e.g. **sqlx**-style clarity vs ORM only when justified in your codebase)

Illustrative **Symfony** Rule bullets:

**DDD** seams; **CQRS** honesty; **ownership first**  

**Transaction boundaries** explicit; avoid **god service** blobs

Illustrative **Ops** Rule bullets:

**Rollback path** before hero fixes  

Structured **logs/evidence before restart**  

**Hypothesis** before shotgun changes

### LAB

Author three artefacts (names illustrative—use your real Rule filenames / formats):

`go-rules` • `symfony-rules` • `ops-rules`

Each lists **prioritised bullets**—short, enforceable, not essays.

### Checklist

- [ ] Rules say **what to refuse** as well as what to prefer (security/approval hooks).  
