# Plan-phase and approval gates

PLAN.md is the contract between you and the executor agents. Every task in it is an instruction to a machine. Vague instructions produce vague results. The approval gate before execute is the moment to catch that.

---

## What plan-phase does

`/gsd:plan-phase N` reads the approved CONTEXT.md and produces one or more PLAN.md files. The planner:

1. Reads CONTEXT.md for goals, constraints, and acceptance criteria
2. Reads REQUIREMENTS.md for relevant REQ-IDs
3. Breaks work into tasks
4. Groups tasks into waves (parallel batches)
5. Assigns dependencies between waves
6. Writes verification criteria for each task

Output location: `.planning/phases/XX-phase-name/XX-YY-PLAN.md`

Multiple PLAN.md files can exist per phase (when a phase is split). The naming convention `XX-01-PLAN.md`, `XX-02-PLAN.md` tells GSD the execution order.

---

## What a good PLAN.md looks like

Full example for task-api Phase 1:

```markdown
# Phase 01: POST /tasks endpoint

## Context
- Goal: POST /tasks returns 201 with created task
- REQs: REQ-001
- Constraints: stdlib only, sequential integer IDs

---

## Wave 1 (parallel)

### Task 01-01: Define task domain model
- File: internal/domain/task.go
- Action: Define Task struct with fields: ID int, Title string, Done bool, CreatedAt time.Time. Export all fields. Add constructor NewTask(id int, title string) Task.
- REQ: REQ-001
- Verification: go build ./internal/domain/...

### Task 01-02: Create in-memory task store
- File: internal/store/memory.go
- Action: Define TaskStore interface with Create(title string) (Task, error) and List() []Task methods. Implement MemoryStore struct with []domain.Task field. Create method appends to slice and returns the created task. List returns a copy.
- REQ: REQ-001, REQ-002, REQ-003
- Verification: go build ./internal/store/...

---

## Wave 2 (after Wave 1 completes)

### Task 01-03: Implement POST /tasks handler
- File: internal/handler/tasks.go
- Action: Define CreateTask(store store.TaskStore) http.HandlerFunc. Parse JSON body into struct{Title string `json:"title"`}. Validate: return 400 with {error:"title is required"} if title empty. Call store.Create(title). Encode result as JSON. Write 201 status.
- REQ: REQ-001
- Depends on: 01-01, 01-02
- Verification: go build ./internal/handler/...

---

## Wave 3 (after Wave 2 completes)

### Task 01-04: Wire routes and write integration tests
- Files: main.go, internal/handler/tasks_test.go
- Action: In main.go, create MemoryStore, register POST /tasks with http.HandleFunc, listen on :8080. In tasks_test.go, write table-driven test with httptest: valid body → 201 + id:1, empty body → 400, missing title key → 400.
- REQ: REQ-001
- Depends on: 01-03
- Verification: go test ./...
```

---

## What a bad PLAN.md looks like

Bad task examples:

```markdown
### Task: Add the POST /tasks handler
- Action: Implement the handler for creating tasks
- Verification: should work

### Task: Add validation
- Action: Validate the input

### Task: Wire everything up
- Action: Connect the pieces and make sure it runs
```

Problems:
- No file paths — executor has no address for the change
- No action spec — "implement" and "validate" are intentions, not instructions
- No verification — "should work" is not a check
- All in one wave — no parallelism, no dependency reasoning

---

## Pre-execute approval checklist

Apply this to every task before approving the plan:

| Check | Pass condition | Fail action |
|-------|---------------|-------------|
| File named | Task specifies exact file path | Edit task to add file path |
| Action is concrete | A junior dev could execute without asking questions | Rewrite the action line |
| REQ-ID mapped | Task references a REQ-ID or has explicit note why it does not | Add REQ reference or out-of-scope note |
| Verification is checkable | Command or assertion that proves the task is done | Replace with `go build` or `go test` or specific curl |
| Wave makes sense | Tasks in the same wave have no dependency between them | Move dependent task to next wave |
| Rollback path exists | For destructive tasks (data migration, infra change), there is a revert step | Add rollback task or note |

For the task-api, the rollback check is easy: in-memory storage means nothing to roll back. For a database migration, this check is critical.

**Human gate rule:** YOU approve PLAN.md before execute. If plan-phase produces a plan you have not reviewed line by line, do not run execute-phase. The gate is yours to hold.

---

## Editing tasks in PLAN.md

You can and should edit PLAN.md before execute. Changes that are always acceptable:
- Adding specific file paths to vague tasks
- Replacing "refactor as needed" with named actions
- Adding missing REQ-ID references
- Splitting a task that is too large into two
- Moving a task to a different wave after noticing a dependency

Changes to avoid without replanning:
- Removing tasks (use `--gaps` flag instead)
- Changing wave frontmatter structure
- Adding entirely new features not in CONTEXT.md (add them to CONTEXT.md first, then replan)

If you find yourself making large structural changes to PLAN.md, stop and run `/gsd:plan-phase N` again — the plan was not ready.

---

## Plan flags that change task structure

The flag you choose at plan-time shapes every task in the output:

| Flag | Task structure | Best for |
|------|---------------|----------|
| (none) | Standard tasks with action + file + verification | Most phases |
| `--tdd` | TEST task followed by IMPL task for each feature | When test coverage is contractual |
| `--mvp` | Tasks scoped to minimum viable slice only | First iteration of a new feature |
| `--research` | Produces RESEARCH.md first; planner uses it | Unfamiliar domain or library |

Decide at plan-phase time. Using `--tdd` at execute-phase time without a `--tdd` plan structure is less reliable. The plan and execute flags should match.

---

## When to replan: `/gsd:plan-phase N --gaps`

`--gaps` reruns planning only for tasks not marked complete in STATE.md. Use it when:
- Execute-phase stopped mid-run due to a blocker
- You fixed the root cause and want to continue
- Some tasks completed successfully and you do not want to re-execute them

Do not use `--gaps` to add features that were never in the original plan. That is scope creep disguised as a gap fill. Add new scope by updating CONTEXT.md and running a full replan or creating a new phase.

---

## Wave structure and parallelism

Waves are batches of tasks that execute in parallel. Wave 2 starts only after all Wave 1 tasks are complete. The executor spawns one agent per task within a wave.

Good wave grouping:
```
Wave 1: domain model (01-01), in-memory store (01-02)   ← no dependency between them
Wave 2: handler (01-03)                                  ← depends on 01-01 and 01-02
Wave 3: wiring + tests (01-04)                           ← depends on 01-03
```

Bad wave grouping:
```
Wave 1: domain model (01-01), handler (01-02)            ← 01-02 depends on 01-01, not parallel
Wave 2: tests (01-03)
```

If two tasks in the same wave have a dependency between them, one agent will fail waiting for the other. Move the dependent task to the next wave.

---

## Checklist

- [ ] I can write a PLAN.md task that names the file, action, REQ-ID, and verification.
- [ ] I know what "all in one wave" means and why it is a bad sign.
- [ ] I can apply the pre-execute checklist to a plan and find at least one issue.
- [ ] I understand when to use --gaps vs a full replan.
- [ ] I know that --tdd at plan-phase changes task structure for the entire plan.
- [ ] I would never run /gsd:execute-phase on a plan I have not read line by line.
- [ ] I can explain why "refactor as needed" is an invalid task action.
- [ ] I understand why the human gate before execute exists.
