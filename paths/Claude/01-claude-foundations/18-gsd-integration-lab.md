# GSD integration lab — one phase end-to-end

**Purpose:** capstone for **Claude foundations + GSD** — prove you can run GSD workflow (`15`–`17`) on a real or toy repo.

**Prerequisites:** GSD installed; units `02`–`05`, `09`–`13`, and `15`–`16` at least once. Optional warm-up: `14-foundation-integration-lab.md` (single-session).

Numerical prefixes = concept order only.

---

## Choose lab track

| Track | Repo | Scope |
|-------|------|-------|
| **A — Greenfield toy** | Empty or sample app | One phase, 3–5 tasks max |
| **B — Brownfield slice** | Repo you maintain | `/gsd:map-codebase` first, one constrained phase |
| **C — Hybrid** | Active project with `.planning/` | Resume via `/gsd:progress`, complete **next** incomplete phase slice |

Pick **one** track — do not merge tracks in one lab run.

---

## Required artefacts (submit to yourself)

After the lab, you should have:

| Artefact | Evidence |
|----------|----------|
| `.planning/PROJECT.md` | Vision matches what you actually built |
| `.planning/ROADMAP.md` | Phase 1 (or N) status updated |
| `.planning/STATE.md` | Blockers empty or honestly listed |
| Phase `CONTEXT.md` | Boundaries you enforced during execute |
| At least one `*-PLAN.md` | Tasks you can map to commits |
| Verification note | From `/gsd:verify-work` or written UAT |
| One Claude config delta | CLAUDE.md, rule, MCP, or permission patch |

---

## Playbook

| Step | Action | Stop if |
|------|--------|---------|
| 0 | `/gsd:progress` or `/gsd:new-project` | No `.planning/` and you skipped bootstrap |
| 1 | Discuss or spec phase | CONTEXT contradicts PROJECT |
| 2 | `/gsd:plan-phase <N>` | PLAN tasks are vague — edit before execute |
| 3 | Optional: `/plan` on hardest task slice | — |
| 4 | `/gsd:execute-phase <N>` or `--wave 1` | Scope creep — fix STATE, narrow plan |
| 5 | `/gsd:verify-work` | Failures unaddressed |
| 6 | Capture: STATE + CLAUDE.md or rule patch | — |
| 7 (optional) | `/gsd:ship` or `/gsd:pr-branch` | — |

---

## Measurement grid

| Measure | Notes |
|---------|-------|
| Commands invoked blindly vs via `--do` | Router literacy |
| Plan iterations before execute | discuss/spec quality |
| Execute waves used | parallelization comfort |
| Manual `/plan` used mid-phase? | hybrid workflow |
| Verification failures | spec vs implementation gap |
| Time in `STATE.md` repair | honesty of session memory |

---

## Post-run journal

- Which **`/gsd:*`** command you reached for first incorrectly  
- Whether **PLAN.md** or chat was source of truth during manual edits  
- One thing that belongs in **CLAUDE.md** vs **STATE.md** vs **PROJECT.md**  
- Update GSD (`/gsd:update`) needed?  

---

## Relationship to unit `14`

| Unit `14` (single-session lab) | Unit `18` (this lab) |
|--------------------------------|----------------------|
| Plan or SPEC in `docs/` | `.planning/phases/*` |
| Claude Code commands & MCP | `/gsd:execute-phase`, verify |
| No REQ-IDs | REQUIREMENTS traceability |

Complete **`14` first** for Claude Code + SPEC literacy; **`18`** when you adopt GSD for multi-phase work.

---

## Checklist

- [ ] Lab track chosen and recorded.  
- [ ] All **required artefacts** exist on disk.  
- [ ] Verification ran before optional ship.  
- [ ] Config capture (CLAUDE.md, rule, or equivalent) applied.  
- [ ] `/gsd:help` version noted in journal for future drift checks.  
