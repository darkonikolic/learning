# Lab: write SPEC for GET /tasks and implement against it

This lab produces a complete SPEC for GET /tasks using the unified template, implements the feature against that SPEC, verifies all acceptance criteria, and runs the drift repair procedure on anything that fails. By the end, REQ-002 is updated in REQUIREMENTS.md.

Prerequisites: Phase 1 (POST /tasks) is complete. `docs/specs/` does not yet exist. Go project compiles with `go build ./...`.

---

## Step 1: create the docs/specs/ directory

```bash
mkdir -p docs/specs
```

Verify it exists:

```bash
ls docs/specs/
```

This is the permanent home for all feature SPECs in task-api. Do not put SPECs in `.planning/` for single-phase feature work — `.planning/` is for GSD phase-level SPECs. `docs/specs/` is for feature-level contracts.

---

## Step 2: write docs/specs/get-tasks.md

Create the file using the full template from `09-specification-first/01-spec-template-and-acceptance.md`. Fill every section. Do not leave any section empty. If a section truly does not apply, write "N/A — [reason]".

The content to write:

```markdown
# SPEC: get-tasks

## Problem
API consumers cannot retrieve existing tasks. Tasks created via POST /tasks are not accessible
after creation, making the API incomplete for any read-oriented workflow.

## Goal
GET /tasks returns all tasks stored in memory, in creation order (oldest first), each with
current completion status. Response is always 200 — never 404, never null.

## Out of scope
- Filtering by done/undone status
- Pagination
- Sorting by any field other than creation time
- Authentication or authorization
- Task search or substring matching

## Constraint
- Must use stdlib only (net/http, encoding/json, crypto/rand)
- Must not return 404 when task list is empty — 200 + [] is required
- store.List() must return a non-nil empty slice, not nil, when no tasks exist
  (json.Marshal(nil) produces null, not [])
- Must return Content-Type: application/json on all responses

## NFR
- Latency: p99 < 50ms for up to 100 tasks in memory (hypothesis — no benchmarks run)
- Empty state: GET /tasks with 0 tasks returns 200 and body [] (not null, not 404)
- Error format consistency: errors return {"error":"message"} JSON

## Boundary / ownership
- handler package: owns HTTP request parsing and JSON response writing; calls store.List()
- store package: owns in-memory task storage; exposes List() []domain.Task
- domain package: owns Task struct — handler never re-declares field names or types
- handler must not access store internals directly — must use injected interface

## Acceptance
- [ ] GET /tasks with no tasks returns HTTP 200 and body `[]`
- [ ] GET /tasks after creating two tasks returns HTTP 200 and a JSON array of length 2
- [ ] Tasks in response appear in creation order — first-created task is at index 0
- [ ] Each task object contains exactly: id (string), title (string), done (boolean), created_at (string)
- [ ] done field is JSON boolean type (verifiable with `jq '.[0].done | type'` = "boolean")
- [ ] Response Content-Type header is application/json

## Implementation strategy
1. Add List() []Task method to store package (returns copy of in-memory slice)
2. Add GET /tasks route in handler package
3. Handler calls store.List(), marshals result, writes 200 response
4. If store.List() returns empty non-nil slice, marshal produces []
No new packages required. No database changes.

## Tradeoff
Option A: return bare array `[{...}]`
  Pros: simpler, direct, standard REST convention for collection endpoints
  Cons: adding pagination metadata later requires a breaking response schema change

Option B: return object wrapper `{"tasks":[{...}], "count": N}`
  Pros: accommodates metadata without breaking schema change
  Cons: extra wrapping adds complexity with no current benefit; pagination is out of scope

Decision: Option A — pagination is explicitly out of scope. The extra wrapper adds overhead
for no current benefit. If pagination is added in a future phase, document as a breaking change.

## Risk
- store.List() returning nil causes json.Marshal to produce null instead of []
  Mitigation: explicit constraint above; unit test for empty list case
- Creation order not guaranteed if store uses map internally
  Mitigation: store must use ordered slice, not map, for task storage

## Rollback
Revert handler route registration and handler.GetTasks() function.
store.List() method stays — it is additive, no breaking change to existing behavior.
```

Write this to disk exactly as shown before any implementation begins. The SPEC is the contract. Implementation starts only after the SPEC file exists.

---

## Step 3: self-review the acceptance criteria

Before giving the SPEC to Claude, read each acceptance criterion and ask: "can I verify this in 60 seconds with only the criterion text and access to a running server?"

Work through each criterion:

**"GET /tasks with no tasks returns HTTP 200 and body `[]`"**
Verification: `curl -s -w "\n%{http_code}" localhost:8080/tasks` on a fresh server.
Expected: body = `[]`, status = `200`. Binary. Keep it.

**"GET /tasks after creating two tasks returns HTTP 200 and a JSON array of length 2"**
Verification: POST two tasks, then `curl localhost:8080/tasks | jq length`.
Expected: `2`. Binary. Keep it.

**"Tasks in response appear in creation order — first-created task is at index 0"**
Verification: POST task "A", POST task "B", GET, check `.[0].title == "A"`.
Binary. Keep it.

**"Each task object contains exactly: id (string), title (string), done (boolean), created_at (string)"**
This criterion has "exactly" which is stronger than "contains". The word "exactly" means no extra undocumented fields.
Verification: `curl ... | jq '.[0] | keys'` and compare.
Binary. Keep it — the word "exactly" is load-bearing.

**"done field is JSON boolean type (verifiable with `jq '.[0].done | type'` = "boolean")"**
Verification: `curl localhost:8080/tasks | jq '.[0].done | type'`.
Expected: `"boolean"`. Binary. The jq command is already in the criterion — no interpretation needed.

**"Response Content-Type header is application/json"**
Verification: `curl -s -I localhost:8080/tasks | grep Content-Type`.
Expected: `Content-Type: application/json`. Binary. Keep it.

All six pass the self-review. Strike any criterion that required rewriting to make binary. The SPEC should reflect the revised criterion, not the original.

---

## Step 4: implement against the SPEC

Give Claude this exact message:

```
Implement GET /tasks per docs/specs/get-tasks.md.
Acceptance section is the contract.
Stop after implementation — no tests, no additional behavior.
Do not add anything not described in the SPEC.
```

The file path reference is not optional. Claude reads the file. Do not paraphrase the SPEC in the message.

What to expect:
- A new `List()` method added to the store package
- A new route handler for GET /tasks
- Route registration in the server setup

What to reject if it appears:
- Filtering parameters (`?done=true`)
- Pagination parameters (`?limit=10`)
- A response wrapper object (`{"tasks":[...]}`)
- External package imports

If Claude adds anything not in the SPEC, stop the session before the next turn and check for drift.

---

## Step 5: verify each acceptance criterion

Start the server:

```bash
go run main.go
```

Or whatever your server start command is. Then run each verification:

**Criterion 1: empty list**
```bash
curl -s localhost:8080/tasks
# Expected: []
curl -s -o /dev/null -w "%{http_code}" localhost:8080/tasks
# Expected: 200
```

**Criterion 2: two tasks, length 2**
```bash
curl -s -X POST localhost:8080/tasks -H "Content-Type: application/json" -d '{"title":"first task"}'
curl -s -X POST localhost:8080/tasks -H "Content-Type: application/json" -d '{"title":"second task"}'
curl -s localhost:8080/tasks | jq length
# Expected: 2
```

**Criterion 3: creation order**
```bash
curl -s localhost:8080/tasks | jq '.[0].title'
# Expected: "first task" (created first, so index 0)
```

**Criterion 4: required fields**
```bash
curl -s localhost:8080/tasks | jq '.[0] | keys'
# Expected: ["created_at","done","id","title"] (jq sorts keys alphabetically)
```

**Criterion 5: done is boolean type**
```bash
curl -s localhost:8080/tasks | jq '.[0].done | type'
# Expected: "boolean"
```

**Criterion 6: Content-Type header**
```bash
curl -s -I localhost:8080/tasks | grep -i content-type
# Expected line containing: application/json
```

Record each result in the SPEC file. Update each `- [ ]` to `- [x]` for PASS. Mark FAIL for anything that does not match. Mark CANNOT VERIFY if the verification step itself is unclear.

---

## Step 6: apply drift repair if any FAIL

For each FAIL, run the three-case decision:

**Is the code right?**
- Does the implementation behavior make sense given the Problem and Goal?
- Is the SPEC criterion describing the wrong thing?
- If yes: update the SPEC criterion (spec evolution). Write one sentence explaining why.

**Is the SPEC right?**
- Does the acceptance criterion describe the intended behavior?
- Did the implementation diverge from intent?
- If yes: fix the code. Re-run the verification.

**Are both wrong?**
- Is the criterion ambiguous enough that both interpretations are defensible?
- If yes: rewrite the criterion from the Problem statement. Get to a binary criterion. Then fix code or SPEC to match.

Common failures and their typical resolutions:

| Failure | Likely cause | Resolution |
|---------|-------------|------------|
| GET /tasks returns null instead of [] | store.List() returns nil | Code wrong — fix List() to return empty slice |
| Tasks in wrong order | Store uses map instead of slice | Code wrong — fix store to preserve insertion order |
| done field is "false" string, not boolean false | json.Marshal config or field type | Code wrong — fix domain.Task done field type |
| Extra field in response | Claude added field not in SPEC | Drift — is it desirable? If yes: add to SPEC. If no: remove from code. |

---

## Step 7: update REQUIREMENTS.md

Open REQUIREMENTS.md. Find REQ-002.

If all acceptance criteria pass: update status to `satisfied`.

If any criterion failed and was resolved: update status to `satisfied` with a note: "drifted during implementation, resolved via spec repair on [date]".

If any criterion is still failing: update status to `in-progress` with a note on what remains.

The REQUIREMENTS.md is the phase-level record. The SPEC is the feature-level contract. Both must reflect reality.

---

## Checklist

- [ ] `docs/specs/get-tasks.md` written with all template sections filled before implementation
- [ ] ≥5 acceptance criteria, all binary — each passes the "60-second verification" test
- [ ] Tradeoff section has ≥2 options and explicit decision with rationale
- [ ] SPEC on disk before implementation message sent
- [ ] Implementation message references `docs/specs/get-tasks.md` by file path
- [ ] All six verification commands run against the live server
- [ ] Results recorded in SPEC — each criterion marked PASS, FAIL, or CANNOT VERIFY
- [ ] Any FAIL resolved: drift repair procedure applied, explicit decision on which party was wrong
- [ ] Any CANNOT VERIFY rewritten as a binary criterion
- [ ] REQ-002 status updated in REQUIREMENTS.md
