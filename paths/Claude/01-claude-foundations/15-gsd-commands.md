# GSD commands — slash reference and when to use each

**Goal:** navigate **Get Shit Done (GSD)** in Claude Code without memorizing the entire command tree — know the **core loop**, the **smart router**, and where to look up the rest.

**Part of Claude foundations** — GSD is the structured layer on top of bare Claude Code (`02`–`05`, `09`–`13`). Config: `16`. Workflow: `17`. Lab: `18`.

**Product:** **Claude Code** with GSD installed (`npx get-shit-done-cc@latest` or global install). GSD commands are **`/gsd:…`** slash commands in the Claude Code session.

**Verify:** run **`/gsd:help`** (or `/gsd-help` per your install) after every GSD update — command names and flags evolve.

Numerical prefixes = concept order only.

---

## Core loop (memorize this)

```
/gsd:new-project  →  /gsd:discuss-phase N  →  /gsd:plan-phase N  →  /gsd:execute-phase N  →  /gsd:verify-work
         ↑__________________________________________|__________________________________________|
                              repeat per phase; /gsd:progress when unsure
```

| Stage | Command | Creates / updates |
|-------|---------|-------------------|
| Bootstrap | `/gsd:new-project` | `.planning/PROJECT.md`, `REQUIREMENTS.md`, `ROADMAP.md`, `STATE.md`, `config.json` |
| Brownfield map | `/gsd:map-codebase` | `.planning/codebase/*` |
| Phase intent | `/gsd:discuss-phase <N>` | `CONTEXT.md` under phase folder |
| Phase plan | `/gsd:plan-phase <N>` | `XX-YY-PLAN.md` under `.planning/phases/` |
| Phase build | `/gsd:execute-phase <N>` | Code + manifest commits; updates STATE/ROADMAP |
| Phase proof | `/gsd:verify-work` | UAT / verification artefacts |

---

## Smart router — when you do not know the command

| Command | Behavior |
|---------|----------|
| **`/gsd:progress`** | Situational report + suggested next step (default) |
| **`/gsd:progress --next`** | Auto-advance to next logical workflow step |
| **`/gsd:progress --do "…"`** | Natural language → best matching `/gsd:*` command (dispatcher only) |
| **`/gsd:help`** | Full reference dump |

**Lab habit:** when tempted to freestyle a long prompt, try **`/gsd:progress --do "your intent in one sentence"`** first.

---

## Project lifecycle commands

| Command | Use when |
|---------|----------|
| `/gsd:new-project` | Greenfield — idea → requirements → roadmap |
| `/gsd:new-milestone` | New version cycle after shipping v1 |
| `/gsd:map-codebase [--fast] [--focus area]` | Existing repo — intelligence before planning |
| `/gsd:import --from …` | Pull external plan into `.planning/` |
| `/gsd:resume-work` | Restore context after pause / new session |
| `/gsd:pause-work` | Handoff checkpoint mid-phase |

---

## Phase workflow commands

| Command | Use when |
|---------|----------|
| `/gsd:discuss-phase <N> [--batch]` | You have vision but no CONTEXT.md yet |
| `/gsd:spec-phase <N>` | Clarify WHAT before discuss (produces SPEC.md) |
| `/gsd:plan-phase <N> [--research] [--tdd] [--mvp]` | Ready for executable PLAN.md files |
| `/gsd:plan-phase --research-phase <N>` | Research only → RESEARCH.md |
| `/gsd:mvp-phase <N>` | Vertical slice — user story → plan |
| `/gsd:execute-phase <N> [--wave W]` | Run plans (parallel waves inside phase) |
| `/gsd:verify-work` | Conversational UAT after execution |
| `/gsd:validate-phase <N>` | Fill validation / test gaps retroactively |

**Express paths (skip discuss):**

- `/gsd:plan-phase <N> --prd path/to/prd.md`  
- `/gsd:plan-phase <N> --ingest path/to/adr.md`

---

## Quality, review, and ship

| Command | Use when |
|---------|----------|
| `/gsd:code-review [--fix]` | Review phase changes; optional auto-fix |
| `/gsd:secure-phase <N>` | Threat model vs implementation |
| `/gsd:ui-review` | Frontend visual audit |
| `/gsd:eval-review` | AI eval coverage audit |
| `/gsd:ship` | PR creation after verification |
| `/gsd:pr-branch` | Clean branch without `.planning/` noise for review |

---

## Debug, undo, and housekeeping

| Command | Use when |
|---------|----------|
| `/gsd:debug` | Systematic bug investigation with checkpoints |
| `/gsd:undo` | Safe revert using phase manifest |
| `/gsd:health` | `.planning/` integrity check |
| `/gsd:stats` | Project metrics |
| `/gsd:update` | Upgrade GSD package |

---

## AI-specific phase commands

When a phase builds LLM features:

| Command | Output |
|---------|--------|
| `/gsd:ai-integration-phase <N>` | AI-SPEC.md |
| `/gsd:ui-phase <N>` | UI-SPEC.md (frontend) |

---

## Workstreams and threads (parallel work)

| Command | Use when |
|---------|----------|
| `/gsd:workstreams create/list/switch …` | Parallel tracks inside one repo |
| `/gsd:thread …` | Cross-session persistent context threads |

Use when single-session workflow (`04`) is insufficient for **parallel ownership**.

---

## How GSD relates to earlier foundation units

| Foundation unit | GSD equivalent |
|-----------------|----------------|
| `05` SPEC in `docs/specs/` | `.planning/phases/…/SPEC.md` |
| `04` plan file in `docs/plans/` | `.planning/phases/…/PLAN.md` |
| `/plan` + bounded execute | `/gsd:execute-phase` |
| `12` CLAUDE.md / `09` rules capture | Update `.planning/STATE.md` + CLAUDE.md |
| `/gsd:progress --do` | Smart dispatch vs manual `/gsd:*` |

Use **Claude Code** for daily edits inside a phase; use **GSD** for **phase lifecycle** and `.planning/` truth.

Scenario → first command:

| Scenario | Start with |
|----------|------------|
| Brand-new repo idea | `/gsd:new-project` |
| Existing codebase, no `.planning/` | `/gsd:map-codebase` then `/gsd:new-project` |
| Phase 3 planned, ready to code | `/gsd:execute-phase 3` |
| “Where am I?” | `/gsd:progress` |
| “Add auth but I don’t know GSD verb” | `/gsd:progress --do "add OAuth login phase"` |
| Plan feels wrong after code spike | `/gsd:discuss-phase N` or `/gsd:plan-phase N --gaps` |

---

## Lab — command map from your project

If you have `.planning/` in any repo:

1. Run **`/gsd:progress`** — paste ROADMAP phase summary into notes.  
2. Run **`/gsd:progress --next`** (dry run mindset) — record which command it would invoke.  
3. Pick one phase folder — list every artefact file (`CONTEXT.md`, `PLAN.md`, …).  
4. Run **`/gsd:help`** — bookmark where full reference lives on your machine.

If no project yet, run **`/gsd:new-project`** on a **toy repo** and stop after roadmap — still complete steps 1–4.

---

## Command selection drill

- [ ] I can recite the **core loop** without looking.  
- [ ] I know **`/gsd:progress --do`** exists and when to prefer it.  
- [ ] I ran **`/gsd:help`** on my installed version this month.  
- [ ] I can point to **one phase folder** and name its artefact files.  
