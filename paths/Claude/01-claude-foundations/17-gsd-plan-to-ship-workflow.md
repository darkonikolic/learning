# GSD plan-to-ship workflow — discuss through merge

**Goal:** run **one phase** from intent → locked plan → executed code → verified outcome → shippable PR, including **mid-phase config updates** (STATE, CLAUDE.md/rules, GSD toggles).

**Commands reference:** `15-gsd-commands.md`. **`.planning/` layout:** `16-gsd-configuration.md`. **Single-session workflow:** `04-plan-to-execution-workflow.md`. **SPEC habit:** `05-specification-before-implementation.md`.

Numerical prefixes = concept order only.

---

## Workflow overview

```
discuss/spec → plan → (optional review) → execute → verify → ship
     │           │                              │        │
 CONTEXT.md   PLAN.md                      commits   UAT.md
 SPEC.md      RESEARCH.md                           PR
```

**Human gates:** approve CONTEXT before plan; approve PLAN before execute; approve verification before ship.

---

## Stage 1 — Frame the phase (discuss / spec)

### When to use which

| Situation | Command |
|-----------|---------|
| Fuzzy UX or architecture feel | `/gsd:discuss-phase <N> [--batch]` |
| WHAT is ambiguous (deliverables) | `/gsd:spec-phase <N>` first |
| PRD already written | `/gsd:plan-phase <N> --prd path` |
| ADRs already approved | `/gsd:plan-phase <N> --ingest path` |

**Output:** `CONTEXT.md` (and optionally `SPEC.md`) under `.planning/phases/XX-…/`.

**Your job:** edit CONTEXT — essentials, boundaries, non-goals. Delete model filler.

---

## Stage 2 — Plan (executable tasks)

```
/gsd:plan-phase <N> [--research] [--tdd] [--mvp]
```

**Output:** one or more `XX-YY-PLAN.md` files with:

- task breakdown and dependencies  
- wave groupings (for parallel execute)  
- verification criteria tied to REQUIREMENTS  

### Before execute — plan review checklist

- [ ] Every task maps to a **REQ-ID** or explicit out-of-scope note.  
- [ ] Files/services touched are **named**, not “refactor as needed”.  
- [ ] **Rollback** or feature-flag path exists for risky tasks.  
- [ ] Waves make sense — no hidden serial dependency inside a parallel wave.

Use **`/gsd:plan-review-convergence`** or **`/gsd:review`** if your install exposes peer review loops.

---

## Stage 3 — Execute

```
/gsd:execute-phase <N> [--wave W] [--gaps-only] [--tdd]
```

GSD spawns executor agents (often parallel per wave), commits atomically per plan conventions, updates:

- `STATE.md` — progress, blockers  
- `ROADMAP.md` — phase status  
- `REQUIREMENTS.md` — satisfied REQ markers  

### Manual Claude Code work during execute

Valid pattern:

1. GSD **PLAN.md** is source of truth for task bounds.  
2. In the same Claude Code session (or `/resume`), implement specific plan steps — message cites plan path + step numbers; use **`/plan`** if scope is unclear.  
3. Return to **`/gsd:execute-phase`** for manifest-aware commits when GSD manages git — **or** manual commits matching plan atomicity if hybrid.

**Invalid pattern:** off-plan implementation while GSD `STATE.md` still says phase X — drift guaranteed.

---

## Stage 4 — Verify

```
/gsd:verify-work
```

Conversational UAT against phase goal — produces tracking artefact (e.g. `{phase}-UAT.md`).

| Gap type | Follow-up command |
|----------|-------------------|
| Tests missing | `/gsd:validate-phase <N>` or `/gsd:add-tests` |
| Security concerns | `/gsd:secure-phase <N>` |
| UI issues | `/gsd:ui-review` |
| AI eval gaps | `/gsd:eval-review` |

Do not **`/gsd:ship`** until verification passes or waivers are explicit in STATE.

---

## Stage 5 — Ship

```
/gsd:ship
```

Push branch, open PR, optional review bots — bridge from local GSD completion to merged mainline.

For clean review branches without `.planning/` commit noise: **`/gsd:pr-branch`** first.

---

## Mid-flight changes (config in motion)

| Trigger | Update |
|---------|--------|
| Blocker discovered | `STATE.md` + chat; `/gsd:pause-work` if switching away |
| Plan wrong but code right | `/gsd:plan-phase <N> --gaps` — do not silently patch |
| Repeated agent mistake | **CLAUDE.md** or **`.claude/rules/`** + note in STATE |
| New integration needed | **`.mcp.json`** + document in PROJECT.md tooling section |
| Phase scope exploded | `/gsd:discuss-phase` again or split new phase in ROADMAP via `/gsd:phase` |

---

## When to stay on units `04`–`05` only

Skip full GSD loop for:

- single-session bugfix  
- one Markdown plan in `docs/plans/`  
- no REQ tracking  

Escalate to GSD when **phase boundaries**, **parallel waves**, or **REQUIREMENTS traceability** matter.

---

## Anti-patterns

| Anti-pattern | Consequence |
|--------------|-------------|
| Execute without approved PLAN | Untraceable scope |
| Edit PLAN.md by hand mid-execute without `--gaps` | Manifest / git desync |
| STATE.md stale | `/gsd:resume-work` hallucinates progress |
| Duplicate REQUIREMENTS in CLAUDE.md | Drift between `.planning/` and project memory |
| Ship without verify | Production surprises |

---

## Lab — one vertical slice phase

**Toy scope:** “Add health check endpoint + test + doc” (or equivalent in your stack).

| Step | Command / action |
|------|------------------|
| 1 | `/gsd:discuss-phase 1` — trim CONTEXT to essentials |
| 2 | `/gsd:plan-phase 1` — confirm one small PLAN |
| 3 | `/gsd:execute-phase 1` — full phase or `--wave 1` only |
| 4 | `/gsd:verify-work` — record pass/fail |
| 5 | Update **CLAUDE.md** or one rule referencing REQ or phase lesson |
| 6 | Optional: `/gsd:ship` on branch you can discard |

**Deliverable:** screenshot or log of `.planning/` tree + PR link or commit range.

---

## Checklist

- [ ] CONTEXT approved before plan; PLAN approved before execute.  
- [ ] `STATE.md` reflects reality after execute.  
- [ ] Verification artefact exists before ship.  
- [ ] CLAUDE.md / rules and GSD artefacts **cross-reference**, not duplicate.  
- [ ] I know when this phase should **not** have used GSD.  
