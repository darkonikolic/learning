# Quality, review, and debug commands

These commands are not part of the core loop by default. They are invoked when verification reveals gaps, when you want peer review before execute, or when something breaks. Knowing which command fits which situation is the skill.

---

## Code review commands

### `/gsd:code-review`

**Purpose:** Reviews all files changed during the current phase for bugs, security issues, and code quality problems. Scoped to phase diff by default.

**When to run:** After execute-phase, before verify-work. Catches implementation problems before conversational UAT misses them.

**Output:** Inline findings with severity labels (HIGH / MEDIUM / LOW) and suggested fixes.

**Flags:**

| Flag | Effect |
|------|--------|
| `--fix` | Applies suggested fixes automatically. Review the diff before committing. |

**Task-api example:** After implementing POST /tasks, run code-review to catch missing error returns, unhandled edge cases in validation, or incorrect HTTP status codes before verify-work.

### `/gsd:secure-phase <N>`

**Purpose:** Threat model verification — checks that security mitigations present in PLAN.md or CONTEXT.md are actually implemented in the code.

**When to run:** Any phase that touches authentication, authorization, input validation, or external integrations. For the task-api, run before ship if CONTEXT.md lists "validate input" as a requirement.

**Output:** Gap report: mitigations listed vs mitigations found in code. PASS / FAIL per threat.

**Not a substitute for code-review** — secure-phase is threat-tracing, not general quality review.

---

## Validation commands

### `/gsd:validate-phase <N>`

**Purpose:** Retroactively fills test and validation gaps after execute. If execute-phase ran without `--tdd` and tests are sparse, this command adds them.

**When to run:** Verify-work reveals missing test coverage. You shipped a working feature but have no automated regression protection.

**Output:** New test files or additions to existing test files, matched to PLAN.md task list.

**Difference from add-tests:** validate-phase operates at phase scope; add-tests operates at UAT scope.

### `/gsd:add-tests`

**Purpose:** Generates tests based on UAT criteria from the verification artifact. Narrower than validate-phase — traces directly to UAT pass/fail items.

**When to run:** After verify-work, when specific UAT items lack automated test coverage.

**Task-api example:** verify-work confirms POST /tasks returns 201 manually via curl. add-tests generates a Go test function that asserts the same behavior programmatically.

### `/gsd:verify-work`

Already covered in core loop (`01-core-loop-commands.md`). It belongs here too because it is the trigger for every other quality command in this file. Run it first; let the results route you to the right follow-up.

---

## Specialized review commands

### `/gsd:ui-review`

**Purpose:** 6-pillar visual audit of implemented frontend code. Produces UI-REVIEW.md with scored findings.

**6 pillars:** Layout correctness, Typography, Color and contrast, Spacing, Interaction states (hover, focus, disabled), Accessibility.

**When to run:** After implementing any UI. Before ship if the phase includes frontend changes.

**Not applicable to task-api** — the toy project has no frontend.

### `/gsd:eval-review`

**Purpose:** Retroactive audit of AI evaluation coverage for phases that call LLMs, use embeddings, or build agent pipelines.

**When to run:** After executing an AI integration phase, before ship. Answers: "Did we actually evaluate this AI behavior, or did we just ship and hope?"

**Output:** EVAL-REVIEW.md — COVERED / PARTIAL / MISSING per evaluation dimension (correctness, latency, safety, cost, regression).

**Not applicable to task-api** — the toy project has no LLM calls.

---

## Debug command

### `/gsd:debug`

**Purpose:** Systematic bug investigation using scientific method. Maintains state across context resets. Spawns debugger agents for parallel hypothesis testing.

**When to run:** Bug in executed code that is not immediately obvious. Especially useful when the bug survives a first-pass read of the code.

**How it works:**
1. You describe the symptom and what you have already tried.
2. `/gsd:debug` establishes a hypothesis checkpoint in STATE.md.
3. Each investigation cycle tests one hypothesis, records result, advances or eliminates the hypothesis.
4. State persists through `/compact` and session restarts — you do not lose investigation progress.

**Multi-cycle pattern:** Run debug, test the hypothesis, `/compact`, run `/gsd:resume-work`, continue from checkpoint.

**Task-api example:** POST /tasks returns 500 unexpectedly. Run `/gsd:debug`, describe: "POST /tasks returns 500 on valid input. No panic in logs. Suspecting nil map write." Debug tracks hypothesis, tests, and outcome.

---

## Maintenance commands

### `/gsd:health`

**Purpose:** `.planning/` directory integrity check. Detects: missing required files, STATE.md / ROADMAP.md desync, orphaned phase folders with no PLAN.md, corrupt config.json.

**When to run:** Before starting a new session on an existing project. After any manual `.planning/` edits. When something feels off with routing.

**Output:** GREEN / YELLOW / RED per check. YELLOW means warning (functional but messy). RED means blocking (GSD cannot operate correctly).

### `/gsd:stats`

**Purpose:** Project metrics dashboard.

**Shows:**
- Total phases, completed vs in-progress
- Number of requirements, satisfied vs open
- Git commit count for current milestone
- Estimated timeline based on phase velocity
- Plan file count and task count

**When to run:** Before a milestone retrospective. When estimating scope for a new milestone.

### `/gsd:update`

**Purpose:** Upgrade GSD package to latest version.

**After running:** Run `/gsd:help` immediately. Command names, flags, and behavior change across versions. Do not assume last month's knowledge is still accurate.

**Before running:** Note your current version (`/gsd:help` shows it). If updating during an active phase, finish the phase first — mid-phase updates can cause manifest desync.

### `/gsd:undo`

**Purpose:** Safe revert using the phase execution manifest. Rolls back commits associated with a specific plan step or phase.

**Why safer than `git reset`:** `undo` reads the phase manifest to identify exactly which commits belong to the plan step. It does not blindly revert N commits — it reverts the specific change set.

**When to run:** Execute produced bad output you want to undo before attempting a replan. You discover a completed task introduced a regression.

**Flags include dependency checking:** If task B depends on task A, undoing A will warn you about B.

---

## Decision table: which quality command when

| Situation | Command |
|-----------|---------|
| After execute, want code quality check | `/gsd:code-review` |
| After execute, tests are missing | `/gsd:validate-phase N` or `/gsd:add-tests` |
| UAT item lacks automated test | `/gsd:add-tests` |
| Security concern before ship | `/gsd:secure-phase N` |
| Bug in executed code | `/gsd:debug` |
| Frontend implemented, check UI | `/gsd:ui-review` |
| AI phase shipped, check evals | `/gsd:eval-review` |
| `.planning/` feels corrupt or inconsistent | `/gsd:health` |
| Want cross-AI peer review of plan | `/gsd:review` |
| Need to revert a specific plan step | `/gsd:undo` |

---

## Peer review loop: `/gsd:review`

Not a code review — a plan review. Sends your PLAN.md to an external AI reviewer (if configured) and returns structured feedback before execute. Use before executing high-risk or high-complexity phases.

**`/gsd:plan-review-convergence`:** Extended loop — replan with review feedback until no HIGH-severity concerns remain. More expensive; use for phases where failure cost is high.

---

## Checklist

- [ ] I know the difference between code-review and secure-phase.
- [ ] I know when to run validate-phase vs add-tests.
- [ ] I understand that /gsd:debug maintains state across context resets.
- [ ] I know what /gsd:health checks and when to run it.
- [ ] I would run /gsd:update and then /gsd:help immediately after.
- [ ] I know /gsd:undo is safer than git reset because it uses the phase manifest.
- [ ] I can fill the decision table from memory for the five most common situations.
