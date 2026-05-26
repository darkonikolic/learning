# Refactor ownership

For diff review on every change (not only refactors), see `12-diff-refactor/03-diff-review-discipline.md`. For edit anchors, allowed zones, and minimal-diff discipline, see `12-diff-refactor/04-idempotent-refactoring-discipline.md`.

Refactoring without a template fails the same way every time: you tell Claude "make it cleaner" and it rewrites three files, renames four symbols, and changes error handling in a way you did not ask for. Tests break. You do not know which change broke them. You roll back everything and lose the work that was actually good. The cause is a vague instruction that gave Claude no target state, no scope, and no success criterion.

The fix is a template you fill before you type a single instruction to Claude.

---

## The refactor template

Fill every field. Skipping a field means you do not yet understand the refactor well enough to start.

| Field | What it holds |
|-------|--------------|
| **CURRENT STATE** | Exact files, types, and coupling that exist today. No invented abstractions. |
| **TARGET STATE** | The observable end state for this slice only. One reviewable step. |
| **DIFF** | Concrete file-level changes: what moves, what is created, what is deleted, what signatures change. |
| **RISK** | What breaks if any step goes wrong. Which callers are affected. |
| **MIGRATION STEPS** | Ordered steps from current to target. Each step compiles and passes tests. |
| **ROLLBACK** | How to undo. Which steps are irreversible — named honestly. |
| **VALIDATION** | Proof the refactor is complete: `go build`, `go test ./...`, manual smoke test if needed. |

Save this as a file (e.g., `docs/refactor-store-extraction.md`) and reference it by path in your Claude message. This is not optional ceremony — it is the contract that keeps scope bounded.

---

## The forbidden anti-pattern

The most common senior mistake: "rewrite everything from scratch."

It is always wrong for the same reasons:

- Rewrites throw away knowledge encoded in the existing code that no one can fully articulate before seeing it disappear.
- Rewrites expand scope invisibly. "While I'm in here" decisions accumulate. The blast radius is unknown until tests run.
- Rewrites eliminate the feedback loop. You cannot validate a half-complete rewrite because it does not compile until it is done.
- Rewrites destroy git bisect. When something breaks, "was it always broken or did we just introduce it" cannot be answered.

The correct instinct for any system with running behaviour: diff, not rewrite. Relocate responsibilities one seam at a time. The system stays deployable at every step.

When Claude proposes a full rewrite in response to a refactor request, stop. Ask: "what is the smallest extractable change that moves toward the target state and leaves everything else working?"

---

## The incremental sequencing rule

Each step in the migration must independently satisfy:

1. `go build ./...` exits 0
2. `go test ./...` exits 0
3. The HTTP API behaviour is unchanged (existing callers still work)

If a step breaks tests, triage before moving forward. Moving to step N+1 on a broken step N means you now have two sources of breakage. Diagnosing becomes exponentially harder.

This is not caution for its own sake. It means every intermediate commit is a valid rollback point. You can stop the refactor at any step and the system still works. That property is worth more than finishing faster.

---

## How to instruct Claude for safe refactoring

The message structure that works:

```
Refactor: [one-line description]

Template: docs/refactor-store-extraction.md

Execute step [N] only. Stop after step [N] is complete.

After step [N]: run `go build ./...` and `go test ./...` and report the results.
Do not proceed to step [N+1] until I confirm.
```

The critical constraints in that message:
- Reference the template by file path so Claude reads your target state, not its own inference.
- Specify exactly which step to execute. Claude will naturally want to do the whole thing.
- Explicit stop point. "Stop after step N is complete" is not implicit in "execute step N."
- Verification before continuation. Claude reports results; you decide to proceed.

Weak instruction: "Refactor the store out of main.go."
Strong instruction: "Execute step 1 of docs/refactor-store-extraction.md only. Stop when done. Run go build ./... and go test ./... and report results."

---

## task-api example: extracting the in-memory store

Current state of `task-api`: all store logic lives inside `handler.go`. The handler struct holds the slice, the mutex, and the ID counter directly. Every handler method reaches directly into those fields. There is no seam between HTTP handling and data management.

The target: a `store/store.go` package with a `Store` type that owns the slice, mutex, and ID counter. `handler.go` depends on `store.Store` via its interface. The HTTP behaviour is identical.

### Filled template

```
CURRENT STATE
  File: handler.go
  Type: Handler struct {
    mu      sync.Mutex
    tasks   []Task
    nextID  int
  }
  Methods on Handler: CreateTask, ListTasks, CompleteTask
  All data access: direct field access inside method bodies
  Package: main

TARGET STATE
  New file: store/store.go
  New type: store.Store with methods: Add(title string) Task, List() []Task, Complete(id int) (Task, bool)
  handler.go: Handler struct holds *store.Store, not the raw fields
  HTTP behaviour: identical — same status codes, same JSON shapes, same paths
  Package: main unchanged; new internal package: store

DIFF
  CREATE: store/store.go — Task type, Store struct, Add/List/Complete methods
  MODIFY: handler.go — remove mu/tasks/nextID fields; add Store *store.Store field
  MODIFY: main.go — instantiate store.NewStore(), pass to handler
  DELETE: nothing

RISK
  If store.Task and main.Task diverge in field names, JSON output changes.
  If mutex is not moved to store.Store correctly, race detector fires.
  Callers of handler methods are HTTP mux only — blast radius is contained.

MIGRATION STEPS
  Step 1: Create store/store.go with Task type and Store struct (Add/List/Complete).
          Do not touch handler.go yet. Confirm: go build ./... passes.
  Step 2: Modify handler.go to use store.Store instead of direct fields.
          Update main.go to pass store.NewStore() to handler.
          Confirm: go build ./... and go test ./... pass.
  Step 3: Remove Task type from main package (now lives in store).
          Update any references. Confirm: go build ./... and go test ./... pass.

ROLLBACK
  Each step is a git commit. Roll back is: git revert <commit>.
  No step is irreversible. No external state is touched.
  Step 3 (type removal) has the most coupling risk — verify step 2 fully before proceeding.

VALIDATION
  go build ./...
  go test ./...
  curl -s -X POST localhost:8080/tasks -d '{"title":"test"}' | jq .
  curl -s localhost:8080/tasks | jq .
  curl -s -X PATCH localhost:8080/tasks/1/complete | jq .
```

This template is saved to disk before any Claude message is sent. The Claude instruction references it by path.

---

## Why this sequence is safe

Step 1 creates the new code without touching the existing code. If step 1 fails to compile, nothing is broken — you are adding, not modifying. Step 2 is the seam-crossing step: the one place where coupling changes. Step 3 is cleanup after the coupling is confirmed stable. The sequence preserves deployability at every commit.

The same logic applies to any Go refactor: add the new abstraction first, migrate callers second, delete the old code third. Never delete before the migration is confirmed.

---

## Checklist

- [ ] I filled the refactor template before writing any Claude message.
- [ ] My TARGET STATE describes observable behaviour, not abstract architecture.
- [ ] My MIGRATION STEPS each independently satisfy go build and go test.
- [ ] My Claude message references the template file by path.
- [ ] My Claude message names exactly one step to execute before stopping.
- [ ] I know what "irreversible" means for each step in this refactor.
- [ ] I can describe the blast radius if step 2 goes wrong.
- [ ] I have the rollback command ready before I start step 1.
