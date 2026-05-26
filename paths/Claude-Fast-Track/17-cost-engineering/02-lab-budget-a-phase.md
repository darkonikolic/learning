# Lab — budget Phase 3 before running it

Before running plan for Phase 3 on task-api's PATCH endpoint, you will estimate token cost, build a context budget listing every file Claude will read and why, run the phase, compare estimated vs actual, and identify one context optimisation.

Estimated time: 45–60 minutes.

Prerequisites: task-api with Phase 2 complete (POST and GET /tasks working). `docs/` layout in place (project.md, state.md, specs/, plans/).

---

## Step 1 — Estimate token cost before running the phase

Use the workflow stage table to build an estimate before any command is run. Estimates are per-stage, not per-task.

**Token cost estimation template:**

| Stage | Files read | Estimated input tokens | Estimated output tokens | Total estimate |
|-------|-----------|----------------------|------------------------|---------------|
| frame 3 | `docs/plans/03-complete-task-context.md` | 500 | 800 | 1,300 |
| spec 3 | `docs/project.md`, prior SPEC sections | 2,500 | 2,000 | 4,500 |
| plan 3 | `docs/specs/complete-task.md`, `docs/project.md`, rules, prior plan sections | 5,000 | 3,000 | 8,000 |
| execute (6 tasks, wave 1 × 3 tasks) | `docs/plans/03-complete-task-plan.md` × 3, source files per task | 18,000 | 8,000 | 26,000 |
| execute (wave 2 × 3 tasks) | phase plan × 3, source files per task | 15,000 | 6,000 | 21,000 |
| verify | SPEC acceptance criteria, targeted output | 2,000 | 500 | 2,500 |
| code-review | Changed source files | 4,000 | 1,500 | 5,500 |
| **Phase 3 total estimate** | | | | **~68,800** |

**Soft ceiling:** 80,000 tokens. If you cross this, stop before starting the next wave and assess whether remaining tasks can be scoped more narrowly.

**Hard ceiling:** 110,000 tokens. Do not continue past this without replanning with narrower task scope.

Fill in your own numbers based on the actual files in your task-api. The table structure matters more than the exact numbers at this stage — you are building the estimation habit.

---

## Step 2 — Identify files that will be read during execute

Before running plan for Phase 3, list every file Claude will likely read during execute and classify each as required-for-every-task or required-for-some-tasks.

**Audit procedure:**

```bash
# List all source files in task-api
find /path/to/task-api -name "*.go" | sort

# Check Phase 2 plan to understand task structure
cat docs/plans/02-get-tasks-plan.md

# List your rules files
ls .claude/rules/

# Check CLAUDE.md for auto-loaded context
cat CLAUDE.md
```

Expected files for a Phase 3 PATCH /tasks/:id implementation:

| File | Type | Reason it will be read |
|------|------|----------------------|
| `docs/plans/03-patch-plan.md` | Planning | Task initialization — read at start of every task |
| `docs/specs/complete-task.md` | Planning | Acceptance criteria — read at start of every task |
| `internal/handler/task.go` | Source | Handler already exists — must read before modifying |
| `internal/store/store.go` | Source | Store interface — read to understand Update method |
| `internal/model/task.go` | Source | Task struct — read to verify fields for PATCH |
| `main.go` | Source | Router — read to confirm route registration pattern |
| `.claude/rules/stdlib-only.md` | Rules | Active rule — loaded per task |
| `.claude/rules/error-handling.md` | Rules | Active rule — loaded per task |

---

## Step 3 — Write the context budget

A context budget is not an estimate — it is a declaration of what you will allow Claude to read and why.

**Context budget format:**

```markdown
# Context budget — Phase 3 PATCH /tasks/:id

## Required for every task (always-on context)
| File | Estimated tokens | Justification |
|------|-----------------|---------------|
| `docs/plans/03-complete-task-plan.md` | 400 | Task definition — cannot be removed |
| `docs/specs/complete-task.md` | 600 | Acceptance criteria — cannot be removed |
| stdlib-only.md | 200 | Correctness rule — always required |
| error-handling.md | 150 | Correctness rule — always required |

## Required for specific tasks only (conditional context)
| File | Estimated tokens | Required for which tasks |
|------|-----------------|------------------------|
| internal/handler/task.go | 800 | Task 1 (add PATCH handler), Task 3 (integrate error response) |
| internal/store/store.go | 400 | Task 1 (add Update method), Task 2 (implement store logic) |
| internal/model/task.go | 200 | Task 1 only (verify struct fields) |
| main.go | 300 | Task 4 only (route registration) |

## Context that should NOT be passed
| File | Reason |
|------|--------|
| Full `docs/project.md` | Only milestone section is needed; pass milestone section only |
| Phase 1 and Phase 2 plan files | Historical — not relevant to Phase 3 execute |
| All prior conversation history | Carry forward only the last verification result |

## Per-task context ceiling
Soft: 12,000 tokens
Hard: 18,000 tokens
```

Write this file at `docs/plans/03-complete-task-context-budget.md`.

---

## Step 4 — Run the phase and compare

Run the phase stages and record actual token usage at each stage.

**Recording actual usage:**

Claude Code displays token usage in the session header or after each response. Record it after each command:

```bash
# Frame (optional if SPEC is clear)
# Write or skim docs/plans/03-complete-task-context.md

# Tighten docs/specs/complete-task.md if needed
# Record tokens used: ___________

# /plan for phase 3
# Record tokens used: ___________

# bounded execution
# Bounded execution for phase 3
# Record tokens used after wave 1: ___________
# Record tokens used after wave 2: ___________

# Run verify
# verify step 3
# Record tokens used: ___________
```

**Comparison table — fill in after running:**

| Stage | Estimated tokens | Actual tokens | Delta | Over/under |
|-------|-----------------|---------------|-------|-----------|
| spec 3 | 4,500 | ___ | ___ | ___ |
| plan 3 | 8,000 | ___ | ___ | ___ |
| execute wave 1 | 26,000 | ___ | ___ | ___ |
| execute wave 2 | 21,000 | ___ | ___ | ___ |
| verify | 2,500 | ___ | ___ | ___ |
| **Total** | **68,800** | ___ | ___ | ___ |

If actual > estimated by more than 30%, identify which stage overran and why before running the next phase.

---

## Step 5 — Identify one context optimisation

After the phase runs, review what was actually read vs what needed to be read. Find one file that was included in every task's context but was only required for a subset of tasks.

**Optimisation decision table:**

| File | Included in how many tasks | Required for how many tasks | Potential saving (tokens × unnecessary tasks) | Action |
|------|--------------------------|---------------------------|----------------------------------------------|--------|
| `internal/model/task.go` | All 6 tasks | 1–2 tasks | 200 tokens × 4 tasks = 800 tokens | Pass only to tasks that modify the struct |
| `main.go` | All 6 tasks | 1 task | 300 tokens × 5 tasks = 1,500 tokens | Pass only to the route-registration task |
| Full feature SPEC | All 6 tasks | All tasks | 0 — required | Keep |
| Full `docs/project.md` | All 6 tasks | 0–1 tasks | 2,000 tokens × 5 tasks = 10,000 tokens | Pass milestone section only |

**The single optimisation to implement:** identify the highest-saving row in your table and write a note in `docs/plans/03-complete-task-context-budget.md` specifying which tasks should receive that file and which should not.

Example note:

```markdown
## Optimisation identified — 2026-05-25

File: main.go (estimated 300 tokens)
Included in: all 6 tasks during Phase 3 execute
Actually needed for: Task 6 only (route registration)
Saving: ~1,500 tokens over Phase 3 execute

Action for Phase 4: add task-level context annotation in the phase plan:
  - Tasks 1–5: do not pass main.go
  - Task 6 (route registration): pass main.go

How to enforce: in the task description in `docs/plans/<phase>-plan.md`, explicitly note
"context: do not read main.go — only internal/handler/ is in scope"
```

---

## Token cost estimation template (reusable)

Copy this for every phase you budget before running:

```markdown
# Token cost estimate — Phase N: <name>

## Soft ceiling: _______ tokens
## Hard ceiling: _______ tokens

| Stage | Files read | Est. input tokens | Est. output tokens | Total |
|-------|-----------|------------------|--------------------|-------|
| frame | — | | | |
| spec | | | | |
| plan | | | | |
| execute (wave 1) | | | | |
| execute (wave 2) | | | | |
| verify | | | | |
| code-review | | | | |
| **Total** | | | | |

## Notes
- Dominant cost driver: ___________
- Highest-risk overrun: ___________
- Optimisation from last phase applied: ___________
```

---

## Context budget format (reusable)

```markdown
# Context budget — Phase N: <name>

## Required for every task (always-on)
| File | Est. tokens | Justification |

## Required for specific tasks only
| File | Est. tokens | Required for tasks |

## Excluded context
| File | Reason |

## Per-task ceilings
Soft: _______ tokens
Hard: _______ tokens

## Optimisations carried forward from previous phase
(list any file-scoping decisions made from prior phase analysis)
```

---

## Checklist

- [ ] I completed the token cost estimation template before running any phase command.
- [ ] I set a soft ceiling and a hard ceiling for Phase 3.
- [ ] I listed every file Claude will read during execute and classified each as always-on or conditional.
- [ ] I wrote `docs/plans/03-complete-task-context-budget.md` before running.
- [ ] I recorded actual token usage at each stage and filled the comparison table.
- [ ] I identified at least one file that was included in more tasks than it needed to be.
- [ ] I wrote an optimisation note in the context budget file specifying how to scope that file in Phase 4.
- [ ] My actual total spend came within 40% of my estimate (or I know specifically why it did not).
- [ ] I know which stage dominated cost in Phase 3.
