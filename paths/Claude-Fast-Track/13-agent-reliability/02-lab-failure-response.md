# Lab — failure response on task-api

This lab simulates a real execute failure: Claude adds out-of-scope filtering to `GET /tasks`. You classify the failure, run the recovery procedure, update `docs/state.md`, and verify. Estimated time: 30–40 minutes.

Prerequisites: task-api with a working `GET /tasks` endpoint, `docs/specs/get-tasks.md`, and `docs/plans/` with `02-get-tasks-plan.md` and `docs/state.md`.

---

## Setup — the simulated bad commit

You are going to create the bad state manually. This gives you a known starting point to recover from.

### Step 1 — Confirm your clean baseline

```bash
cd task-api
git log --oneline -5
go test ./...
```

Expected: tests pass. Note the current HEAD hash — you will return here if anything goes wrong.

```bash
git rev-parse HEAD
# Save this. Example: a3f9c12
```

### Step 2 — Simulate the bad commit

Add filtering support to your `GET /tasks` handler. Open `internal/handler/task.go` (or wherever your handler lives) and add query-param filtering:

```go
// Add this block inside your GET /tasks handler, before the json.Marshal call:
tasks := store.List()

// Out-of-scope: added filtering not in SPEC v0.1
if completed := r.URL.Query().Get("completed"); completed != "" {
    var filtered []Task
    for _, t := range tasks {
        if completed == "true" && t.Done {
            filtered = append(filtered, t)
        } else if completed == "false" && !t.Done {
            filtered = append(filtered, t)
        }
    }
    tasks = filtered
}
```

Commit it as if the agent did:

```bash
git add internal/handler/task.go
git commit -m "feat: implement GET /tasks with optional completed filter"
```

### Step 3 — Confirm the bad state

```bash
git log --oneline -5
```

Expected output (yours will differ by hash):

```
d7e4b91 feat: implement GET /tasks with optional completed filter
a3f9c12 feat: add POST /tasks handler
8b2c3f1 feat: add task store with in-memory implementation
5a1d0e4 chore: initialize task-api module
```

The top commit is the one you need to recover from.

---

## Part 1 — Classify the failure

### Step 4 — Fill the reliability template

Before touching anything, classify the failure.

Open a scratch file or just work through this mentally:

| Field | Your answer |
|-------|-------------|
| **FAILURE MODE** | Out-of-scope code — Claude added filtering not described in SPEC |
| **DETECTION SIGNAL** | Diff review of commit `d7e4b91` — `?completed=true` param handling not in SPEC |
| **CONFIDENCE LEVEL** | ? (fill this in after step 5) |
| **VERIFY STEP** | Check SPEC section for `GET /tasks`; run filtering request to confirm it responds |
| **RETRY DECISION** | No retry needed — the correct behavior is defined; this is a removal + replacement |
| **FALLBACK** | Current `GET /tasks` (with filter) still serves unfiltered requests correctly |
| **ESCALATION TRIGGER** | N/A — SPEC is clear, recovery path is straightforward |

### Step 5 — Apply the confidence rubric

Run your SPEC acceptance criteria for `GET /tasks`:

```bash
# Start the server
go run . &
SERVER_PID=$!

# Criterion: returns 200
curl -s -o /dev/null -w "%{http_code}" localhost:8080/tasks
# Expected: 200

# Criterion: returns JSON array
curl -s localhost:8080/tasks | jq 'type'
# Expected: "array"

# Criterion: no filtering (SPEC v0.1 out of scope)
# Create a task first
curl -s -X POST localhost:8080/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"test task"}' | jq '.id'

# Verify filtering is NOT happening (should return all tasks, not filter)
# With the bad commit: ?completed=false should return only incomplete tasks
TOTAL=$(curl -s localhost:8080/tasks | jq 'length')
FILTERED=$(curl -s "localhost:8080/tasks?completed=false" | jq 'length')
echo "Total: $TOTAL, Filtered: $FILTERED"
# If TOTAL != FILTERED: filtering IS active — scope violation confirmed

kill $SERVER_PID
```

**Confidence level for this output:** Medium. Core behavior (200, JSON array, data present) is correct. But the implementation violates a SPEC boundary. Classify: **scope violation at Medium confidence**. Do not advance to next wave.

---

## Part 2 — Hallucination recovery

### Step 6 — Identify the violation

Open your SPEC:

```bash
cat docs/specs/get-tasks.md
```

Find the `GET /tasks` section. It should contain something like:

```
## GET /tasks

Returns all tasks in the store.

### Acceptance criteria
- Returns HTTP 200
- Returns Content-Type: application/json
- Response body is a JSON array of task objects
- Returns empty array [] when no tasks exist
- Tasks returned in creation order (oldest first)

### Out of scope (v0.1)
- Filtering by status
- Sorting
- Pagination
```

Record the exact section that prohibits filtering. This is your authority. Everything in the recovery is grounded to this section.

### Step 7 — Isolate the violation

The bad code is in its own clean commit (`d7e4b91`). Use `git revert`:

```bash
# Replace d7e4b91 with your actual bad commit hash
git log --oneline -3   # confirm the hash
git revert <bad-commit-hash> --no-edit
```

Expected output:

```
[main e1f8a03] Revert "feat: implement GET /tasks with optional completed filter"
 1 file changed, 10 deletions(-)
```

Verify the revert removed the filtering code:

```bash
grep -n "completed" internal/handler/task.go
# Expected: no output (the filter block is gone)
```

### Step 8 — Verify the revert preserved correct behavior

```bash
go build ./...
# Expected: no errors

go test ./...
# Expected: all tests pass

go run . &
SERVER_PID=$!

# Core behavior still works
curl -s -o /dev/null -w "%{http_code}" localhost:8080/tasks
# Expected: 200

curl -s localhost:8080/tasks | jq 'type'
# Expected: "array"

# Filtering param is now silently ignored (no filtering behavior)
curl -s "localhost:8080/tasks?completed=true" | jq 'length'
curl -s localhost:8080/tasks | jq 'length'
# Expected: same count — param is ignored

kill $SERVER_PID
```

### Step 9 — Replace with correct implementation (if needed)

The revert restored the original `GET /tasks` handler. If that handler already satisfied all acceptance criteria before the bad commit, no replacement is needed — the revert IS the fix.

If the original handler was also incomplete (missing fields, wrong status codes), now is the time to implement correctly. Prompt Claude with the specific gap and an explicit scope constraint:

```
Implement GET /tasks as specified in docs/specs/get-tasks.md.

The handler must satisfy these acceptance criteria:
- Returns HTTP 200
- Returns Content-Type: application/json
- Response body is a JSON array of task objects
- Returns empty array [] when no tasks exist

Do NOT add filtering, sorting, or pagination — these are explicitly out of scope for v0.1.
The SPEC section "Out of scope (v0.1)" lists these exclusions.
```

---

## Part 3 — Update docs/state.md

### Step 10 — Record the incident in docs/state.md

Open `docs/state.md`.

Find the entry for the `GET /tasks` task (it may show `status: complete` from the bad execute run). Update it to record what happened:

```yaml
tasks:
  - id: implement-get-tasks
    status: complete
    wave: 1
    commit: e1f8a03
    note: |
      Wave 1 execution added out-of-scope query filtering (?completed=true).
      Violation: SPEC v0.1 section "Out of scope" explicitly excludes filtering.
      Recovery: reverted commit d7e4b91 (git revert). Filtering removed.
      Verification: GET /tasks returns 200 + full array regardless of query params.
      Wave rerun: not required — revert restored correct behavior.
      Date: 2026-05-25
```

If docs/state.md does not have a `note` field in its schema, add the incident as a comment below the task entry:

```yaml
  - id: implement-get-tasks
    status: complete
    wave: 1
    commit: e1f8a03
    # INCIDENT: reverted d7e4b91 — out-of-scope filtering removed 2026-05-25
```

Commit the docs/state.md update:

```bash
git add docs/state.md
git commit -m "docs: record scope-creep incident and recovery for GET /tasks"
```

---

## Part 4 — Final verification

### Step 11 — Full acceptance criteria pass

Run every acceptance criterion from the SPEC. Do not skip any.

```bash
go run . &
SERVER_PID=$!

# AC1: 200 on empty store
curl -s -o /dev/null -w "AC1 status: %{http_code}\n" localhost:8080/tasks

# AC2: Content-Type header
curl -sI localhost:8080/tasks | grep -i content-type
# Expected: application/json

# AC3: empty array on fresh server
curl -s localhost:8080/tasks
# Expected: []

# AC4: tasks present after POST
curl -s -X POST localhost:8080/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"first task"}' > /dev/null
curl -s -X POST localhost:8080/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"second task"}' > /dev/null
curl -s localhost:8080/tasks | jq 'length'
# Expected: 2

# AC5: creation order (oldest first)
curl -s localhost:8080/tasks | jq '.[0].title'
# Expected: "first task"

# AC6: scope boundary — filtering param has no effect
FULL=$(curl -s localhost:8080/tasks | jq 'length')
WITH_PARAM=$(curl -s "localhost:8080/tasks?completed=false" | jq 'length')
echo "Full: $FULL, With param: $WITH_PARAM"
# Expected: same number — filtering is not implemented

kill $SERVER_PID
```

### Step 12 — Run the test suite

```bash
go test ./...
# Expected: PASS on all packages
```

### Step 13 — Confirm git log shows clean recovery

```bash
git log --oneline -8
```

Expected shape:

```
f2a9d14 docs: record scope-creep incident and recovery for GET /tasks
e1f8a03 Revert "feat: implement GET /tasks with optional completed filter"
d7e4b91 feat: implement GET /tasks with optional completed filter
a3f9c12 feat: add POST /tasks handler
...
```

The history is honest: you can see the bad commit, the revert, and the docs/state.md update. No force-push, no squash. The revert is the record.

---

## Reference — docs/state.md incident format

Use this format for any execute incident you record in docs/state.md:

```yaml
# INCIDENT LOG
# Task: <task-id>
# Date: YYYY-MM-DD
# Failure mode: [scope-creep | acceptance-mismatch | loop | timeout]
# Bad commit: <hash> — <one-line description of what was wrong>
# Recovery: [git revert <hash> | manual removal | replan]
# Rerun required: [yes | no]
# Verification: <what you ran to confirm recovery succeeded>
```

---

## Checklist

- [ ] I created the simulated bad commit and confirmed filtering was active.
- [ ] I filled the reliability template (all seven fields) before starting recovery.
- [ ] I assigned confidence level (Medium — core correct, scope violated) before touching code.
- [ ] I identified the exact SPEC section that the implementation violated.
- [ ] I used `git revert` for the clean single-commit isolation (not `git reset --hard`).
- [ ] I verified the revert removed filtering AND preserved correct behavior.
- [ ] I confirmed the scope boundary: `?completed=true` param is now silently ignored.
- [ ] I updated docs/state.md with the incident log entry and committed it.
- [ ] All six acceptance criteria from the SPEC pass after recovery.
- [ ] `go test ./...` passes after recovery.
- [ ] `git log` shows the revert commit and the docs/state.md update commit.
