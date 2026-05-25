# Lab: Build Context for a Task

## The Task

```
Add PATCH /tasks/:id/complete endpoint to task-api
Language: Go, stdlib only, in-memory store
```

This is the raw task. It is under-specified. Your job is to build the context that makes it executable.

---

## Step 1 — Identify What Context Is Required

Work through the three required elements.

**Relevant files** — what does this task touch?

The handler file. The router where routes are registered. The store if the handler calls it. The Task model if CompletedAt needs to be added.

```
internal/api/tasks.go     — handler goes here
internal/api/router.go    — route registration
internal/store/memory.go  — in-memory store (read to understand Update interface)
internal/models/task.go   — Task struct (does it have CompletedAt?)
```

Do not include: `main.go`, `go.mod`, test files, config files.

**Constraint** — what rules apply?

From workspace config (CLAUDE.md):
- stdlib only, no third-party packages
- errors: `fmt.Errorf("operation: %w", err)`
- JSON responses include a `"status"` field

Specific to this task:
- do not modify the store interface signature — add methods if needed, don't change existing ones
- in-memory store only, no persistence

**Done condition** — what does success look like?

```
PATCH /tasks/:id/complete
- 200 + updated Task JSON if successful
- 404 + {"status": "error", "error": "task not found"} if id not in store
- 409 + {"status": "error", "error": "already complete"} if Task.CompletedAt != zero
- Task.CompletedAt set to time.Now() on success
```

---

## Step 2 — Identify What to Exclude and Why

| File | Include? | Reason |
|------|----------|--------|
| internal/api/tasks.go | Yes | Handler lives here |
| internal/api/router.go | Yes | Route must be registered |
| internal/store/memory.go | Yes | Handler calls into store |
| internal/models/task.go | Yes | Need to verify Task struct has CompletedAt |
| internal/api/tasks_test.go | No | Not writing tests this turn |
| main.go | No | Not touched by this task |
| go.mod | No | Not touched; no new dependencies |
| internal/middleware/ | No | Not called by this endpoint |
| .env / config.go | No | No config changes |

Rule applied: every included file has a direct reason. Every excluded file has no direct connection to the task.

---

## Step 3 — Write the Context Message

### [Claude] Context Message

```
Read these files before we start:
- internal/api/tasks.go
- internal/api/router.go
- internal/store/memory.go
- internal/models/task.go

Task: Add PATCH /tasks/:id/complete handler.

Constraints (also in CLAUDE.md):
- stdlib only, no third-party packages
- errors wrapped: fmt.Errorf("operation: %w", err)
- all JSON responses include a "status" field

Acceptance criteria:
- 200 + updated Task on success, CompletedAt set to time.Now()
- 404 + {"status":"error","error":"task not found"} if id not in store
- 409 + {"status":"error","error":"already complete"} if CompletedAt already set
- Route registered in router.go

Do not modify the store interface. Add a CompleteTask(id string) method if needed.
Do not create or modify test files.
```

### [Cursor] Composer Setup

```
@tasks.go @router.go @memory.go @task.go

Add PATCH /tasks/:id/complete handler.

Constraints:
- stdlib only
- errors: fmt.Errorf("operation: %w", err)
- all JSON includes "status" field

Done:
- 200 + Task on success, CompletedAt = time.Now()
- 404 if not found, 409 if already complete
- Route registered in router.go
- Do not modify store interface
```

Note: Cursor's composer context is smaller. Keep the spec tighter. The `@file` references pull current file state — do not paste code.

---

## Step 4 — After 3 Turns, Write a Checkpoint

Assume 3 turns have happened:
- Turn 1: model read files, proposed the handler
- Turn 2: you asked for a fix to the 409 condition
- Turn 3: route was registered in router.go

### Checkpoint Message

```
## Checkpoint — PATCH /tasks/:id/complete

### Verified state
- Handler implemented in internal/api/tasks.go (CompleteTask)
- Store method CompleteTask(id string) added to internal/store/memory.go
- Route registered: PATCH /tasks/{id}/complete in internal/api/router.go
- Task.CompletedAt field confirmed present in internal/models/task.go
- Manual test:
  curl -X PATCH localhost:8080/tasks/1/complete → 200 + Task JSON ✓
  curl -X PATCH localhost:8080/tasks/999/complete → 404 ✓
  curl -X PATCH localhost:8080/tasks/1/complete (again) → 409 ✓

### Active constraints
- stdlib only, no third-party packages
- errors: fmt.Errorf("operation: %w", err)
- JSON responses include "status" field
- Store interface: add methods only, do not modify existing signatures

### Files modified this session
- internal/api/tasks.go (added CompleteTask handler)
- internal/store/memory.go (added CompleteTask method)
- internal/api/router.go (registered PATCH route)

### Files NOT modified (confirmed unchanged)
- internal/models/task.go
- main.go

### Next action
Implement POST /tasks — see SPEC.md under "POST /tasks" for request/response spec
```

---

## Step 5 — Evaluate the Checkpoint

Ask: can a fresh session pick up where this left off using only the checkpoint?

**Evaluation criteria:**

- [ ] Verified state is specific — says what was built and what was tested, not just "it works"
- [ ] Test results are concrete — actual curl commands with actual responses, not "tests pass"
- [ ] Constraints are fully restated — a fresh session doesn't need CLAUDE.md to be read to know the rules
- [ ] All modified files are listed — nothing to hunt for
- [ ] Files confirmed unchanged are listed — prevents re-applying work
- [ ] Next action is unambiguous — "see SPEC.md under POST /tasks" is better than "do the next endpoint"
- [ ] No reference to "what we discussed" — the checkpoint is self-contained

**The test**: paste only the checkpoint into a new session and ask the model to implement the next endpoint. If it asks clarifying questions that the checkpoint should have answered, the checkpoint is incomplete.

---

## Reference: Checkpoint Template

```
## Checkpoint — [task name]

### Verified state
- [what was built, file-level]
- [manual test: command → result]

### Active constraints
- [list, restated fully]

### Files modified this session
- [file] ([what changed])

### Files NOT modified
- [file]

### Next action
[specific next task + pointer to spec]
```

---

## Checklist

- [ ] Identified the three required context elements: files, constraints, done condition
- [ ] Justified every included file with a direct reason
- [ ] Justified every excluded file
- [ ] Claude context message: files listed for reading, constraints stated, acceptance criteria specific
- [ ] Cursor composer: @file references used, no pasted code, spec is tight
- [ ] Checkpoint written after 3 turns, not after session ends
- [ ] Checkpoint contains verified state with concrete test evidence
- [ ] Checkpoint contains fully restated constraints (not "see CLAUDE.md")
- [ ] Checkpoint passes the fresh-session test: paste it and the session can continue
- [ ] Next action in checkpoint is specific and points to a spec
