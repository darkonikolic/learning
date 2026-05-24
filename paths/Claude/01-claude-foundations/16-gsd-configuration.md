# GSD configuration — `.planning/` and workflow toggles

**Goal:** understand **where GSD state lives**, how **`config.json`** shapes behavior, and how GSD config relates to **Claude Code** project config (`CLAUDE.md`, `.claude/`, `.mcp.json`) — without duplicating two sources of truth.

**Part of Claude foundations.** Commands: `15`. Workflow: `17`. Lab: `18`. Claude config map: `03`. SPEC habit: `05`.

**Product:** Claude Code + GSD. Install/update: `npx get-shit-done-cc@latest`.

Numerical prefixes = concept order only.

---

## `.planning/` directory map

After `/gsd:new-project`, expect a hierarchy like:

| Path | Role |
|------|------|
| `.planning/PROJECT.md` | Vision, constraints, stack — north star |
| `.planning/REQUIREMENTS.md` | REQ-IDs, v1/v2/out-of-scope |
| `.planning/ROADMAP.md` | Phases, goals, requirement mapping |
| `.planning/STATE.md` | **Session memory** — current phase, blockers, decisions |
| `.planning/config.json` | Workflow mode and toggles |
| `.planning/research/` | Domain research from new-project |
| `.planning/codebase/` | Brownfield maps from `map-codebase` |
| `.planning/phases/XX-name/` | Per-phase artefacts |
| `.planning/phases/XX-name/CONTEXT.md` | Your vision from discuss-phase |
| `.planning/phases/XX-name/SPEC.md` | What the phase delivers (from spec-phase) |
| `.planning/phases/XX-name/RESEARCH.md` | Plan research (optional) |
| `.planning/phases/XX-name/*-PLAN.md` | Executable plans |
| `.planning/phases/XX-name/VERIFICATION.md` | Post-execute proof |
| `.planning/intel/` | Codebase intelligence index (query via map/intel flows) |

**Checkpoint:** if a decision matters next week, it belongs in **STATE.md**, **PROJECT.md**, or a **phase artefact** — not only in chat scrollback.

---

## Phase folder conventions

Phase directories use **`XX-kebab-name`** prefixes aligned with ROADMAP ordering.

Plans inside a phase: **`XX-YY-PLAN.md`** (multiple plans per phase allowed).

Wave execution (`execute-phase --wave N`) reads **wave frontmatter** inside plans — do not hand-edit waves without understanding planner output.

---

## `config.json` — workflow mode

Created at project bootstrap. Typical fields (exact schema varies by GSD version — inspect your file):

| Concept | Meaning |
|---------|---------|
| **Interactive vs yolo mode** | How often GSD stops for confirmation |
| **Research toggles** | Whether plan-phase spawns researchers |
| **Verifier / plan_check** | Quality gates before/after planning |
| **Branching strategy** | Git branch naming for phase work |

### Configure interactively

| Command | Scope |
|---------|-------|
| **`/gsd:config`** | Common toggles (model profile, research, verifier…) |
| **`/gsd:config --advanced`** | Timeouts, branch templates, cross-AI execution |
| **`/gsd:config --integrations`** | API keys, external review CLIs, agent skills injection |
| **`/gsd:config --profile quality\|balanced\|budget`** | Model profile shortcut |

**Lab:** run `/gsd:config` on a toy project — record which toggles changed `config.json`.

---

## GSD vs Claude Code project config

| Concern | GSD owns | Claude Code owns |
|---------|----------|------------------|
| Phase plans & roadmap | `.planning/*` | — |
| Session coding policy | — | `CLAUDE.md`, `.claude/rules/` |
| Tool access (browser, DB) | — | `.mcp.json`, `~/.claude.json` |
| Lifecycle hooks | — | `hooks` in `.claude/settings.json` |
| Long-running project memory | `STATE.md`, REQUIREMENTS | CLAUDE.md + auto memory (pointers OK) |

**Integration pattern:**

- **PROJECT.md** states stack and boundaries.  
- **CLAUDE.md / rules** encode day-to-day must/must-not while executing plans.  
- **STATE.md** links to active phase + blockers — do not duplicate full rule text.

Avoid pasting entire REQUIREMENTS into CLAUDE.md — **reference REQ-IDs** instead.

---

## Workstreams and workspaces (optional scale-out)

| Feature | Purpose |
|---------|---------|
| **`/gsd:workstreams`** | Parallel tracks (e.g. frontend vs backend) sharing one `.planning/` |
| **`/gsd:workspace`** | Isolated GSD workspace environments on disk |

Use when a single ROADMAP lane cannot represent concurrent ownership.

---

## Model profile and cost

`/gsd:config --profile …` switches quality/cost posture for **GSD-orchestrated agents** (planner, executor, verifier).

This is **orthogonal** to **`/model`** and **`/effort`** in Claude Code — align GSD profile with session model choices or costs drift.

---

## Updating GSD itself

```bash
npx get-shit-done-cc@latest
```

Or **`/gsd:update`** — read changelog; breaking changes often affect command flags.

After update, re-run **`/gsd:health`** on active projects.

---

## Configuration lab

On a **throwaway repo**:

| Step | Action |
|------|--------|
| 1 | `/gsd:new-project` — stop after roadmap exists |
| 2 | Draw `.planning/` tree on paper — label each file’s job |
| 3 | `/gsd:config` — change one toggle; diff `config.json` |
| 4 | Add one **CLAUDE.md** bullet pointing agents at `.planning/PROJECT.md` for stack context |
| 5 | Write three lines in `STATE.md` — simulate resume after weekend |

**Pass:** another person (or future you) can read `.planning/` only and know what phase is active.

---

## Security and secrets

- API keys for research integrations → `/gsd:config --integrations`, not committed `.env` in plans.  
- `.planning/` may contain **architecture secrets** — treat repo visibility like production code.  
- MCP credentials stay in `.mcp.json` / local env — not duplicated into PLAN.md.

---

## Checklist

- [ ] I can name **five** `.planning/` files and their roles.  
- [ ] I know where **`config.json`** lives and how to change it safely.  
- [ ] Rules **reference** GSD artefacts instead of duplicating them.  
- [ ] I ran **`/gsd:health`** after changing GSD version.  
