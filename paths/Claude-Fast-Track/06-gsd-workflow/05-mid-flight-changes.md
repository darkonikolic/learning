# Mid-flight changes

Plans break during execution. This is not a failure — it is information. The failure is silently patching around the break without updating the plan artifacts. That creates drift between what the plan says and what the code does, and that drift compounds.

---

## The "never silently patch" principle

When you discover the plan is wrong, fix the plan. When you discover the SPEC is wrong, fix the SPEC. When STATE.md is stale, repair it. Do not:

- Implement differently from the plan without updating the plan
- Accept that the SPEC acceptance criteria are wrong but build to them anyway
- Leave STATE.md showing tasks as complete when they are partial
- Change course in code and leave CONTEXT.md describing the old direction

Every silent patch creates a divergence between `.planning/` and reality. GSD commands read `.planning/`. When that data is wrong, every subsequent GSD action — resume-work, progress, health — operates on false premises.

---

## Decision table: what broke, what to do

| Trigger | Action |
|---------|--------|
| Blocker discovered mid-wave | Record in STATE.md blockers; pause and fix before continuing |
| Plan task is wrong, code direction is right | Edit PLAN.md task; run `/gsd:execute-phase N --gaps-only` |
| Plan task is right, code execution is wrong | Fix the code; state is correct, code needs repair |
| New dependency discovered | Add to go.mod; document in PROJECT.md tooling section; update CONTEXT.md constraints |
| Phase scope is too large to execute in one session | Split via `/gsd:phase` — create Phase N and Phase N+1; move overflow to N+1 |
| Implementation reveals SPEC acceptance criteria are wrong | Update SPEC.md first, re-approve, then continue or replan |
| CONTEXT.md contradicts what you are building | Stop. Reconcile CONTEXT.md with reality before any more execution. |
| Repeated agent mistake on same issue | Update the PLAN.md task description; add a rule to `.claude/rules/` |
| Feature not in PLAN.md needed urgently | Do not implement outside plan; add to CONTEXT.md, update plan with `--gaps` |

---

## Handling a mid-wave blocker

Scenario: execute-phase is running. Wave 2 task 01-03 fails because it tries to import from `internal/store` but that package has a compile error introduced in Wave 1.

**Wrong response:** Continue, manually patch the compile error, and let the rest of execute proceed without updating anything.

**Right response:**

1. Stop the session if execute is still running. Check STATE.md for current wave and task status.
2. Find the compile error in git log — which commit introduced it?
3. Fix the compile error, commit the fix manually with a message: "fix: compile error in internal/store (blocker for 01-03)"
4. Update STATE.md if needed: remove the compile error from blockers, note the fix commit.
5. Run `/gsd:execute-phase N --wave 2` to restart Wave 2 from scratch, or `--gaps-only` to run only failed tasks.

---

## Scope changes during execute

The most common mid-flight change: you discover the feature needs something extra.

**Scenario:** During execute of POST /tasks, you realize the test requires a `CreatedAt` timestamp in the response, but CONTEXT.md did not specify it.

Options:

| Option | When appropriate |
|--------|-----------------|
| Update CONTEXT.md, add acceptance criterion, replan with `--gaps` | CreatedAt is in scope — it is a real requirement that was missed |
| Add to CONTEXT.md non-goals explicitly | CreatedAt is genuinely out of scope for this phase — defer to Phase 2 |
| Create a follow-up task in STATE.md | Known gap to fix after verify-work as a validation finding |

Do not: silently add the `CreatedAt` field, have tests pass, and never update CONTEXT.md. The verification step will check against CONTEXT.md acceptance criteria. If `CreatedAt` is not listed there, its presence is accidental and unreviewable.

---

## When SPEC acceptance criteria are wrong

Scenario: SPEC.md says "POST /tasks returns 201 with `{id, title, done: false}`" but during execution you realize the task needs `createdAt` to be useful to clients.

Procedure:
1. Stop implementation on the affected task
2. Update SPEC.md — add `createdAt` to the acceptance criterion
3. Update CONTEXT.md — add `createdAt` to the goal line
4. Update REQUIREMENTS.md — add `createdAt` to REQ-001 acceptance criteria
5. Re-approve (read the updated criteria; are they still achievable in this phase?)
6. Continue or rerun the affected task with `--gaps-only`

Do not update SPEC.md after the task is already implemented without also verifying that the implementation actually matches. The SPEC change is only meaningful if the code catches up.

---

## STATE.md honesty rules

**Anti-pattern: marking tasks "completed" when they partially work.**

Task 01-03 (POST /tasks handler) exists as a file, compiles, and returns 201 for valid input. But validation (400 for empty title) is not yet implemented.

Wrong STATE.md entry:
```
- 01-03: POST /tasks handler — commit ghi789 ✓
```

Correct STATE.md entry:
```
- 01-03: POST /tasks handler — PARTIAL. Handler created and compiles.
  Validation (400 for empty title) not yet implemented. Do not mark complete.
```

**Consequence of false completion:** `/gsd:resume-work` reads STATE.md and reports Phase 1 execution complete. Verify-work then finds the gap. But now you have lost the context of which specific task was incomplete, making the fix harder to locate.

**Consequence chain:**
1. Partial task marked complete in STATE.md
2. Execute-phase `--gaps-only` skips the partial task (STATE.md says it is done)
3. Verify-work finds the missing validation
4. You cannot rerun just that task without manually editing STATE.md
5. Time lost reconstructing what "01-03 partial" means

Keeping STATE.md honest costs 30 seconds. Repairing the consequences costs 30 minutes.

---

## `/gsd:pause-work`

Ends a session mid-phase cleanly. Writes a structured checkpoint to STATE.md:

```markdown
## Pause checkpoint — 2026-05-25

### Status at pause
Phase 01 in progress. Wave 2 complete (01-01, 01-02, 01-03 done). Wave 3 not started.

### Next action
Run /gsd:execute-phase 1 --wave 3 — task 01-04: wire routes and write tests.

### Context to restore
- Decided to use sequential integers (not UUIDs) — see 01-02
- main.go not yet created — that is Wave 3's job

### Blockers
None
```

Always run `/gsd:pause-work` before:
- Ending a session with an in-progress phase
- Switching to a different project
- Taking a break of more than a few hours

Do not let the session end naturally with a mid-phase STATE.md. The next session's `/gsd:resume-work` reads the pause checkpoint to reconstruct context. Without it, resume has to guess.

---

## `/gsd:resume-work`

Reads STATE.md, the active PLAN.md, and recent git log to reconstruct working memory after a session break or `/compact`.

After resume completes, verify the summary it produces:
- Does the current phase match what you expect?
- Does the "next action" align with where you stopped?
- Is the list of completed tasks accurate against git log?

If any of these are wrong, repair STATE.md manually before continuing. Running execute-phase or verify-work on a false resume leads to incorrect automation.

**Common cause of wrong resume:** STATE.md pause checkpoint is stale (written from a previous session, not the most recent one). If you ran manual commits between pause and resume, git log will have commits that STATE.md does not reflect. Repair procedure: cross-reference git log with STATE.md tasks, update completed task list, update status.

---

## Concrete before/after: adding pagination mid-flight

**Scenario:** You are mid-execution on task-api Phase 2 (GET /tasks). The PLAN.md calls for returning all tasks. Wave 1 (store.List) is complete. Wave 2 (handler) is in progress. Halfway through, you realize the API will be unusable if the task list grows large — you need pagination via `limit` and `offset` query params.

---

### CONTEXT.md before the change

```markdown
## Goal

Implement GET /tasks endpoint that returns all tasks in creation order.

## Acceptance criteria

- GET /tasks returns 200 with JSON array of all tasks
- Empty task list returns 200 with []
- Each task has id, title, done, created_at fields
- Response Content-Type is application/json

## Out of scope

- Filtering by status
- Sorting options
- Authentication
```

Pagination is not mentioned. It is not in scope. The plan has no pagination task.

---

### The decision point

You are mid-execution. Do you:

1. Silently add `limit` and `offset` to the handler without updating any artifact?
2. Stop, update CONTEXT.md, rerun plan-phase with `--gaps`?
3. Stop, add pagination to CONTEXT.md, decide whether it's in scope for this phase?

Option 1 is the failure mode. The handler will implement behavior not described in CONTEXT.md. Verify-work will not check for it. STATE.md will not reflect it. The next developer (or the next session) will not know pagination exists.

---

### Decision rule: when to re-plan vs when to update CONTEXT.md and continue

**Re-run `/gsd:plan-phase N --gaps` when:**
- The change adds new tasks (e.g., pagination requires a new store method, a new handler parameter, new tests)
- The change affects the dependency structure (e.g., the new task must run before the existing handler task)
- The scope change is substantial enough that the current PLAN.md is misleading without revision

**Update CONTEXT.md and continue (no re-plan) when:**
- The change is a clarification of an existing task, not a new task
- The change does not affect wave order or task dependencies
- The change is a constraint tightening (e.g., "return at most 100 tasks" with no new code structure needed)

For pagination: this is a re-plan case. Adding `limit` and `offset` requires new logic in the store's List method, new query param parsing in the handler, and new tests. The current PLAN.md does not cover any of this.

---

### What to add to CONTEXT.md mid-flight

Stop execution. Update CONTEXT.md:

```markdown
## Goal

Implement GET /tasks endpoint that returns tasks in creation order with optional pagination.

## Acceptance criteria

- GET /tasks returns 200 with JSON array of all tasks (when no pagination params given)
- GET /tasks?limit=10 returns the first 10 tasks
- GET /tasks?offset=5&limit=10 returns tasks 6–15
- Invalid limit or offset values return 400
- Empty task list returns 200 with []
- Each task has id, title, done, created_at fields
- Response Content-Type is application/json

## Out of scope

- Filtering by status
- Sorting options
- Authentication
- Cursor-based pagination (limit+offset only)

## Mid-flight change note

Pagination (limit + offset query params) added after Wave 1 completed. This change
requires replanning — new store method signature and handler parameter parsing tasks
were not in the original PLAN.md.
```

Then replan:

```
/gsd:plan-phase 2 --gaps
```

The `--gaps` flag tells plan-phase to extend the existing plan, not replace it. Wave 1 (store.List) is already complete and will not be regenerated. The planner adds new tasks for pagination logic.

---

### After the re-plan

Review the updated PLAN.md. Verify:
- store.List() now accepts `limit int, offset int` parameters (or pagination is a separate method)
- The handler task covers query param parsing and validation
- Tests cover the new boundary conditions (invalid params, offset beyond list length)
- Wave order is still correct (store changes before handler changes)

The mid-flight change cost 15 minutes of re-planning. The alternative — silently adding pagination — would have cost 2 hours when verify-work found behavior not described in CONTEXT.md, plus more time to reconstruct what was intentionally added versus accidentally included.

---

## Checklist

- [ ] I can explain the "never silently patch" principle and why it matters.
- [ ] I know what to do when a blocker is discovered mid-wave.
- [ ] I understand the difference between "plan task wrong, code right" and "plan task right, code wrong".
- [ ] I know the procedure for updating SPEC.md when acceptance criteria are wrong.
- [ ] I can explain why marking partial tasks as complete in STATE.md creates problems.
- [ ] I would run /gsd:pause-work before ending a session mid-phase.
- [ ] I know that /gsd:resume-work can be wrong and how to verify it.
- [ ] I can write a STATE.md partial task entry that is honest and useful.
- [ ] I know when a mid-flight change requires re-planning vs a CONTEXT.md update only.
- [ ] I can apply the decision rule: scope additions that create new tasks → re-plan; clarifications that don't → update and continue.
