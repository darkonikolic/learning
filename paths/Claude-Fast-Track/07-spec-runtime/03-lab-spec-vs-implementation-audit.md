# Lab: spec vs implementation audit

This lab performs a full spec audit for task-api GET /tasks. You will run every acceptance criterion against the live implementation, record the results, find at least one piece of behavior the implementation has that the SPEC does not describe, make an explicit decision about it, run a test coverage check, and update both the SPEC and `docs/requirements.md` based on what you find.

Prerequisites: GET /tasks is implemented (from module 06 lab). `docs/specs/get-tasks.md` exists with ≥5 acceptance criteria. Server starts with `go run main.go` or equivalent.

---

## Step 1: read and list acceptance criteria

Open `docs/specs/get-tasks.md`. Write out every acceptance criterion as a numbered list. Do not work from memory.

If your SPEC has these six criteria from the module 06 lab:

```
1. GET /tasks with no tasks returns HTTP 200 and body []
2. GET /tasks after creating two tasks returns HTTP 200 and a JSON array of length 2
3. Tasks in response appear in creation order — first-created task is at index 0
4. Each task object contains exactly: id (string), title (string), done (boolean), created_at (string)
5. done field is JSON boolean type (jq '.[0].done | type' = "boolean")
6. Response Content-Type header is application/json
```

If your SPEC has different criteria, use those. The procedure is the same regardless of which criteria you have.

---

## Step 2: start the server

```bash
go run main.go
```

Note the port. Default is 8080. If your server uses a different port, substitute it in all commands below.

Verify the server is responding:

```bash
curl -s -o /dev/null -w "%{http_code}" localhost:8080/tasks
```

Expected: `200`. If you get a connection refused, the server is not running. If you get 404, the route is not registered.

---

## Step 3: run verification for each criterion

Work through each criterion with the specific command shown. Do not skip any. Record each result.

**Criterion 1: empty list**

Restart the server (or use a fresh server instance with no prior tasks):

```bash
curl -s localhost:8080/tasks
```

Expected: `[]`

```bash
curl -s -o /dev/null -w "%{http_code}" localhost:8080/tasks
```

Expected: `200`

If the body is `null` instead of `[]`: the store's List() method returns nil. Drift — code is wrong. store.List() must return an empty non-nil slice.

If the status is `404`: the route is not registered for empty state. Drift — code is wrong.

**Criterion 2: two tasks, array length 2**

```bash
curl -s -X POST localhost:8080/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"first task"}'

curl -s -X POST localhost:8080/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"second task"}'

curl -s localhost:8080/tasks | jq length
```

Expected: `2`

If you get `1`: the store is not persisting the first task before the second POST arrives. Possible race condition or overwrite bug.

If you get `0`: POST /tasks is not storing tasks in the same store that GET /tasks reads from. The store instances may not be shared.

**Criterion 3: creation order**

Continuing from the previous step (two tasks created):

```bash
curl -s localhost:8080/tasks | jq '.[0].title'
```

Expected: `"first task"`

```bash
curl -s localhost:8080/tasks | jq '.[1].title'
```

Expected: `"second task"`

If the order is reversed: the store is maintaining reverse insertion order (append vs prepend). Drift — code is wrong. Fix: append to slice, not prepend.

If the order is non-deterministic: the store is using a map. Maps in Go have non-deterministic iteration order. Drift — critical. The store must use a slice.

**Criterion 4: required fields**

```bash
curl -s localhost:8080/tasks | jq '.[0] | keys'
```

Expected: `["created_at","done","id","title"]` (jq sorts keys alphabetically)

If a field is missing: the domain.Task struct does not include it, or the json struct tag is missing/incorrect.

If extra fields appear: the response has fields not described in the SPEC. Record what they are — you will address them in Step 5.

**Criterion 5: done is boolean type**

```bash
curl -s localhost:8080/tasks | jq '.[0].done | type'
```

Expected: `"boolean"`

If the result is `"string"`: the done field is being serialized as a string. Likely cause: domain.Task defines `Done string` instead of `Done bool`, or there is a custom JSON marshaler converting it.

If the result is `"number"`: done is being serialized as 0/1. The field type in the struct is int. Fix: change to bool.

**Criterion 6: Content-Type header**

```bash
curl -sI localhost:8080/tasks | grep -i content-type
```

Expected output line containing: `application/json`

If the header is absent: handler is not calling `w.Header().Set("Content-Type", "application/json")` before writing the response body.

If it is `text/plain`: the handler uses `fmt.Fprintf(w, ...)` instead of `json.NewEncoder(w).Encode(...)`, and the default Content-Type detection runs on the first write.

---

## Step 4: record results in a table

Create this table with your actual results:

| # | Acceptance criterion | Verification command | Result | Notes |
|---|---------------------|---------------------|--------|-------|
| 1 | GET /tasks empty → 200 + [] | `curl -s localhost:8080/tasks` | | |
| 2 | Two tasks → array length 2 | `jq length` | | |
| 3 | Creation order | `jq '.[0].title'` | | |
| 4 | Required fields (exactly) | `jq '.[0] | keys'` | | |
| 5 | done is boolean | `jq '.[0].done | type'` | | |
| 6 | Content-Type: application/json | `curl -sI | grep content-type` | | |

Fill in PASS, FAIL, or CANNOT VERIFY for each.

CANNOT VERIFY means the verification command cannot tell you whether the criterion passes. It usually means the criterion is not binary. Rewrite the criterion if this happens.

---

## Step 5: find behavior not in the SPEC

Read `handler/handler.go` (or wherever the GET /tasks handler lives). Look for:

- Any response field not listed in the SPEC's acceptance criteria or boundary section
- Any HTTP header set that is not mentioned in the SPEC
- Any query parameter handling not mentioned in the SPEC
- Any error response path not described in the SPEC
- Any logging, metrics, or tracing behavior not described in the SPEC

Common findings in task-api GET /tasks implementations:

**Extra response field:** some implementations add an `updated_at` field to the Task struct for Phase 3 completeness. If this field appears in GET /tasks response and is not in the SPEC, it is excess behavior.

**Extra Content-Type charset:** `Content-Type: application/json; charset=utf-8`. The SPEC says `application/json`. The charset addition is technically correct but not specified. Is this excess behavior? Decision: add to SPEC as evolution ("Content-Type: application/json; charset=utf-8 is acceptable") or add a constraint ("Content-Type must be exactly application/json without charset suffix"). Make the decision explicit.

**Request ID header:** some implementations add `X-Request-ID` to all responses. Not in SPEC. Decision: if you want it, add it to the SPEC. If you do not want it for task-api, remove it.

**What to do with each finding:**

Ask: was this intentional? Can you trace a decision that led to this behavior?

If intentional and desirable: spec evolution. Update SPEC to document it. Write one sentence explaining why it was added.

If unintentional or not wanted: remove from code. Revert the specific change.

If you are not sure: remove from code. Easier to add intentionally later than to remove something that has become relied upon.

---

## Step 6: drift repair for any FAIL

For each FAIL in your results table, apply the three-case decision:

**FAIL: tasks in wrong order**

Case: SPEC says creation order (oldest first). Code returns newest first.
Decision: SPEC right, code wrong. The SPEC was explicit.
Fix:
```go
// In store package, ensure append (not prepend):
func (s *InMemoryStore) Add(task domain.Task) domain.Task {
    s.mu.Lock()
    defer s.mu.Unlock()
    s.tasks = append(s.tasks, task) // append preserves insertion order
    return task
}
```
Re-verify Criterion 3 after fix.

**FAIL: done field is string "false" not boolean false**

Case: SPEC says boolean. Code returns string.
Decision: SPEC right, code wrong.
Fix: check domain.Task struct:
```go
type Task struct {
    ID        string    `json:"id"`
    Title     string    `json:"title"`
    Done      bool      `json:"done"`      // must be bool, not string
    CreatedAt time.Time `json:"created_at"`
}
```
Re-verify Criterion 5 after fix.

**FAIL: empty list returns null**

Case: SPEC says []. Code returns null.
Decision: SPEC right, code wrong.
Fix: ensure store.List() returns an initialized empty slice:
```go
func (s *InMemoryStore) List() []domain.Task {
    s.mu.RLock()
    defer s.mu.RUnlock()
    if s.tasks == nil {
        return []domain.Task{} // non-nil empty slice, marshals to []
    }
    return s.tasks
}
```
Re-verify Criterion 1 after fix.

After all fixes: re-run the full verification table. Confirm all items are PASS before proceeding.

---

## Step 7: run test coverage check

Run the test suite and map each test name against the SPEC acceptance criteria:

```bash
go test ./... -v | grep -E "^(=== RUN|--- PASS|--- FAIL)"
```

Count tests against acceptance criteria. For each acceptance criterion, there should be a corresponding test. A gap means a criterion has no automated verification.

For each gap: write the missing test. The test name should be derived from the criterion text. If you used spec-driven TDD (empty test stubs first), you may have stubs that need implementation.

---

## Step 8: update docs/specs/get-tasks.md

Based on what you found:

1. Mark passing acceptance criteria with `[x]` (or keep a record of pass/fail state)
2. If you found excess behavior and decided it is evolution: add the new acceptance criteria
3. If you rewrote any CANNOT VERIFY criteria: update the SPEC with the rewritten version
4. If the Constraint section was missing the nil-slice constraint: add it

Do not delete acceptance criteria that are now satisfied. The SPEC is a living document, not just a pre-implementation checklist. The criteria remain as the contract definition.

---

## Step 9: update docs/requirements.md

Open `docs/requirements.md`. Find REQ-002.

If all acceptance criteria are now PASS and the SPEC is updated:
```markdown
REQ-002: GET /tasks
Status: satisfied
Verified: [date]
Notes: drift found in criterion 3 (creation order) — resolved via code fix
```

If any criteria remain FAIL:
```markdown
REQ-002: GET /tasks
Status: in-progress
Blocked: criterion 3 (creation order) — fix in progress
```

The status in `docs/requirements.md` must reflect reality. An optimistic "satisfied" on a failing criterion creates false confidence for the next phase.

---

## Checklist

- [ ] All acceptance criteria verified with concrete commands, results recorded in a table
- [ ] Not one criterion marked "checked manually" without a specific command
- [ ] Excess behavior identified — at least one implementation feature examined and decision made
- [ ] All FAIL items resolved: either code fixed or SPEC updated with rationale
- [ ] CANNOT VERIFY items rewritten as binary criteria
- [ ] Test coverage check run — coverage gaps noted
- [ ] Missing tests written for any gaps found
- [ ] docs/specs/get-tasks.md updated: evolved criteria, nil-slice constraint, verification state
- [ ] `docs/requirements.md` REQ-002 status reflects verified state
