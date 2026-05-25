# Lab: full phase end-to-end on task-api

Run one complete GSD phase cycle on the task-api toy project. You enter with a `.planning/` directory and CONTEXT.md for Phase 1. You exit with a working POST /tasks endpoint, a verification artifact, and a code review result.

---

## Prerequisites

Complete the module 04 lab first. After that lab you have:
- `task-api/` directory with `git init`
- `.planning/` directory with PROJECT.md, REQUIREMENTS.md, ROADMAP.md, STATE.md, config.json
- `.planning/phases/01-post-tasks/CONTEXT.md` — edited by you

If any of these are missing, run the module 04 lab setup first.

---

## Phase 1 scope

POST /tasks endpoint:
- Accepts JSON body: `{"title": "string"}`
- Returns 201 with `{"id": 1, "title": "buy milk", "done": false}`
- Returns 400 with `{"error": "title is required"}` if title is absent or empty
- IDs are sequential integers starting at 1
- In-memory storage, stdlib only

---

## Step 1: Verify CONTEXT.md is ready for planning

Open `.planning/phases/01-post-tasks/CONTEXT.md`. Apply the approval gate:

- [ ] Goal is one sentence
- [ ] Goal is verifiable with a curl command
- [ ] Non-goals section exists with at least 2 entries
- [ ] Acceptance criteria exist and are all checkable
- [ ] Open questions section is empty

If any item fails: edit CONTEXT.md now. Do not proceed to plan-phase with a CONTEXT.md that fails this gate.

Goal should read approximately: "POST /tasks accepts a JSON body with a required title field and returns 201 with the created task object."

If it reads: "The endpoint should handle task creation with proper validation", that is not ready. Rewrite it.

---

## Step 2: Run plan-phase

```
/gsd:plan-phase 1
```

Wait for PLAN.md to be generated. Then open `.planning/phases/01-post-tasks/01-01-PLAN.md`.

Apply the pre-execute checklist to every task:

| Check | Pass? |
|-------|-------|
| Every task names a specific file path | |
| Every task has a concrete action (not "improve" or "add") | |
| Every task references REQ-001 | |
| Wave grouping makes sense (dependencies between waves, not within) | |
| Verification criteria exist per task | |

Count the tasks. Write the count in your notes.

If any task fails the checklist: edit it in PLAN.md before proceeding. Example fix:

Before: "Add handler for POST /tasks"
After: "File: internal/handler/tasks.go — implement CreateTask(store TaskStore) http.HandlerFunc that parses JSON body, validates title, calls store.Create, returns 201 with JSON"

---

## Step 3: Run execute-phase

```
/gsd:execute-phase 1
```

Watch STATE.md update as waves complete. After execute finishes:

```bash
# Check that code compiles
go build ./...

# Check that tests pass
go test ./...

# See what was committed
git log --oneline -10
```

Expected outcome: all commands pass. If `go build` fails, find the bad commit in git log, fix the compile error, and re-run `--gaps-only`.

Count the commits in git log that correspond to PLAN.md tasks. Does the count match your task count from Step 2?

---

## Step 4: Manual verification — run the server

```bash
# Start the server
go run main.go &

# Verify POST /tasks with valid input
curl -s -X POST localhost:8080/tasks \
  -H 'Content-Type: application/json' \
  -d '{"title":"buy milk"}' | jq .
# Expected: {"id":1,"title":"buy milk","done":false}

# Verify HTTP status
curl -s -o /dev/null -w '%{http_code}' -X POST localhost:8080/tasks \
  -H 'Content-Type: application/json' \
  -d '{"title":"buy milk"}'
# Expected: 201

# Verify missing title returns 400
curl -s -X POST localhost:8080/tasks \
  -H 'Content-Type: application/json' \
  -d '{}' | jq .
# Expected: {"error":"title is required"}

# Verify empty title returns 400
curl -s -X POST localhost:8080/tasks \
  -H 'Content-Type: application/json' \
  -d '{"title":""}' | jq .
# Expected: {"error":"title is required"}

# Verify second task has id:2
curl -s -X POST localhost:8080/tasks \
  -H 'Content-Type: application/json' \
  -d '{"title":"read book"}' | jq .
# Expected: {"id":2,"title":"read book","done":false}

# Stop server
kill %1
```

Record each check as PASS or FAIL. Any FAIL needs resolution before moving on.

---

## Step 5: Run `/gsd:verify-work`

```
/gsd:verify-work
```

GSD will walk through the Phase 1 acceptance criteria. For each criterion, confirm pass or fail based on your Step 4 results.

After verify-work completes, check that a verification artifact was created. Look for:
- UAT.md in the phase folder
- Or a verification section appended to STATE.md

If any acceptance criterion is FAIL:
- Minor gap (e.g., error message text differs): decide: fix now or create explicit waiver in STATE.md
- Major gap (e.g., validation not implemented at all): fix the code, re-run the affected test, update STATE.md

---

## Step 6: Check STATE.md accuracy

Read STATE.md. Verify:
- Phase 01 status is "execution complete" or "completed"
- All four tasks (01-01, 01-02, 01-03, 01-04) are listed as completed
- Blockers section is empty or contains only explicitly deferred items
- Decisions made this session are recorded (e.g., "sequential integer IDs, not UUIDs")

If STATE.md does not match reality (missing completed tasks, stale status): repair it manually. Cross-reference with `git log --oneline -10`.

---

## Step 7: Run `/gsd:code-review`

```
/gsd:code-review
```

Read the output. Classify each finding:
- HIGH/CRITICAL: fix before ship
- MEDIUM: decide — fix now or defer with waiver
- LOW: note for later; defer acceptable for toy project

For task-api, common findings might include:
- Missing error return in JSON encoder
- No limit on request body size (standard finding for HTTP handlers)
- `sync.Mutex` missing on shared in-memory store (valid concern even for toy project)

For each HIGH finding: fix it, commit the fix, note it in STATE.md as "post-review fix — task 01-03".

---

## Step 8: Ship or pr-branch

For a learning exercise, either option works:

```
# Option A: clean PR branch (recommended for real projects)
/gsd:pr-branch

# Option B: ship directly
/gsd:ship
```

If using `/gsd:pr-branch`: verify the new branch exists and contains only code changes (no .planning/ commits).

If using `/gsd:ship`: confirm the PR is created with a description that references Phase 01 and the verification artifact.

---

## What you should have after this lab

| Artifact | Expected state |
|----------|---------------|
| `internal/domain/task.go` | Task struct defined |
| `internal/store/memory.go` | MemoryStore with Create and List methods |
| `internal/handler/tasks.go` | CreateTask handler with validation |
| `main.go` | Route registration, server start on :8080 |
| `internal/handler/tasks_test.go` | Table-driven tests: 201 for valid, 400 for invalid |
| `.planning/STATE.md` | Phase 01 completed, all tasks listed |
| `.planning/phases/01-post-tasks/UAT.md` | Verification artifact from verify-work |
| `go build ./...` | Passes |
| `go test ./...` | Passes |

---

## Measurement grid

Record these after the lab. They tell you where you spent extra time.

| Measure | Count / Notes |
|---------|--------------|
| PLAN.md task edits before execute | How many vague tasks did you fix? |
| Execute waves re-run | Did any wave need --wave or --gaps-only? |
| FAIL items in verify-work | How many acceptance criteria needed fixing? |
| FAIL items in code-review | How many code issues found? |
| STATE.md repairs needed | Was STATE.md honest after execute? |
| Total sessions | Did you need /gsd:pause-work and /gsd:resume-work? |

A clean run: 0 task edits, 0 wave reruns, 0 verify fails, 0 STATE.md repairs. That means your CONTEXT.md and PLAN.md were solid before execute. That is the target.

---

## Checklist

- [ ] CONTEXT.md reviewed and approved before plan-phase
- [ ] CONTEXT.md goal is one verifiable sentence
- [ ] CONTEXT.md has at least two non-goals
- [ ] /gsd:plan-phase 1 run — PLAN.md exists
- [ ] Every task in PLAN.md names a specific file
- [ ] Pre-execute checklist applied — no vague tasks remain
- [ ] /gsd:execute-phase 1 completed
- [ ] go build ./... passes
- [ ] go test ./... passes
- [ ] All five curl checks in Step 4 pass
- [ ] /gsd:verify-work run — verification artifact exists
- [ ] STATE.md shows Phase 01 as completed with all tasks listed
- [ ] /gsd:code-review run — all HIGH findings addressed
- [ ] /gsd:ship or /gsd:pr-branch run
