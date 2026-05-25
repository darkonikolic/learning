# Lab: Bootstrap the .planning/ directory for task-api

This lab wires together the configuration concepts from Module 06. You will initialise a GSD project, populate the core files, and verify the structure is healthy before Phase 01 begins.

Estimated time: 30–45 minutes.

---

## Prerequisites

- Go 1.22+ installed: `go version`
- GSD installed: `npx get-shit-done-cc@latest`
- Claude Code running in your task-api directory

---

## Step 1: Create the task-api repo and run /gsd:new-project

```bash
mkdir task-api && cd task-api
git init
go mod init github.com/local/task-api
```

In Claude Code (with your working directory set to `task-api`):

```
/gsd:new-project
```

GSD will ask you for:
- Project name: `task-api`
- Brief description: `In-memory task manager REST API in Go`
- Stack: `Go 1.22, stdlib net/http, no external dependencies`

After it completes, verify the tree exists:

```bash
ls .planning/
# Expected: config.json  PROJECT.md  REQUIREMENTS.md  ROADMAP.md  STATE.md
```

---

## Step 2: Fill in PROJECT.md

Open `.planning/PROJECT.md`. Replace the scaffold with this content exactly:

```markdown
# task-api

## Vision
An in-memory HTTP task manager exposing three endpoints over a single Go binary.
The goal is demonstrating Go stdlib HTTP patterns without external dependencies.

## Goals
1. POST /tasks with valid JSON body returns 201 and a unique task ID within 10ms p99 under 50 concurrent clients.
2. GET /tasks returns all tasks in creation order, JSON-encoded, with correct id/title/status fields.
3. PATCH /tasks/:id/complete returns 200 for incomplete tasks, 404 for unknown IDs, 409 for already-complete tasks.

## Non-goals
- No authentication or authorization.
- No persistence — restart loses all data by design.
- No pagination, filtering, or search on GET /tasks.
- No metrics endpoint or distributed tracing in v1.
- No Docker or containerization in v1.

## Stack
- Language: Go 1.22
- HTTP: net/http stdlib (no external routers — no gorilla/mux, no gin, no chi)
- Storage: in-process (sync.Map or equivalent)
- Build: single `go build ./...` command
- Testing: go test stdlib only

## Key constraints
- Zero external dependencies: go.mod must have no `require` entries.
- No goroutine leaks: every spawned goroutine must be proven bounded.
- Binary start time < 100ms.

## Team
- Owner: solo learner
- Reviewer: Claude Code
```

Save the file. This is the authoritative project definition that every GSD command references.

---

## Step 3: Add requirements to REQUIREMENTS.md

Open `.planning/REQUIREMENTS.md`. Add these three requirements after any existing scaffold:

```markdown
## REQ-001: Create task
Status: open
Phase: 01-task-endpoints

### Description
POST /tasks accepts a JSON body and creates a task in memory.

### Acceptance criteria
- [ ] POST /tasks with `{"title":"Buy milk"}` returns HTTP 201
- [ ] Response body contains `id` field (unique per request)
- [ ] Response body contains `title` matching the submitted value
- [ ] Response body contains `status: "incomplete"`
- [ ] Two sequential POST requests return two distinct IDs

---

## REQ-002: List tasks
Status: open
Phase: 01-task-endpoints

### Description
GET /tasks returns all tasks in memory in creation order.

### Acceptance criteria
- [ ] GET /tasks with no tasks returns HTTP 200 with JSON `[]`
- [ ] GET /tasks after two POSTs returns both tasks in creation order
- [ ] Response is valid JSON array
- [ ] Each task object contains id, title, and status fields
- [ ] GET /tasks does not modify any task state

---

## REQ-003: Complete task
Status: open
Phase: 01-task-endpoints

### Description
PATCH /tasks/:id/complete marks a specific task as complete.

### Acceptance criteria
- [ ] PATCH /tasks/1/complete on an incomplete task returns HTTP 200
- [ ] After PATCH, GET /tasks shows that task with `status: "complete"`
- [ ] PATCH /tasks/999/complete (non-existent) returns HTTP 404
- [ ] PATCH /tasks/1/complete on an already-complete task returns HTTP 409
- [ ] PATCH does not modify tasks other than the targeted ID
```

---

## Step 4: Run /gsd:progress and read the output

```
/gsd:progress
```

GSD reads PROJECT.md, ROADMAP.md, STATE.md, and REQUIREMENTS.md and produces a status report. Read the entire output. It will show:

- Which requirements exist and their status
- Whether a phase is active
- What it recommends as the next step

Note what `/gsd:progress` says the next action should be. This is the command you would run to continue. Do not run it yet — you are still bootstrapping.

---

## Step 5: Inspect config.json

```bash
cat .planning/config.json
```

Find the model profile setting. It will be one of: `quality`, `balanced`, or `budget`. For this learning project, `balanced` or `budget` is appropriate.

If you want to switch to budget:

```
/gsd:config --profile budget
```

Diff config.json before and after:

```bash
git diff .planning/config.json
```

Observe which fields changed. Understand that the planner and executor model settings are what changed — not your Claude Code session model.

---

## Step 6: Run /gsd:health

```
/gsd:health
```

GSD validates that `.planning/` has the required structure, that config.json is parseable, that ROADMAP.md has at least one phase, and that STATE.md is consistent with ROADMAP.md phase statuses.

Expected output: "Health check passed" or a list of warnings. If you see warnings, read them carefully — they identify structural issues before they cause problems during execution.

Common warnings at this stage:
- "ROADMAP.md has no phases" — you may need to add the first phase: `/gsd:phase add`
- "STATE.md is empty" — normal after new-project, GSD initialises it on first command

---

## Step 7: Run /gsd:stats

```
/gsd:stats
```

GSD reads the full `.planning/` tree and produces metrics:

- Number of phases (planned/in-progress/completed)
- Number of requirements (open/satisfied)
- Number of plans
- Git commit count
- Days since project creation

At this point you should see:
- 3 requirements, all open
- 1 phase (if you ran `/gsd:phase add` in step 6), status: planned
- 0 plans (none written yet)

Record these numbers. After Phase 01 completes, run `/gsd:stats` again and compare — the delta shows exactly what one phase produced.

---

## Expected final state

After completing all steps, your `.planning/` tree should look like:

```
.planning/
├── config.json          ← model profile set, no hand-edits
├── PROJECT.md           ← vision, 3 measurable goals, 5 non-goals, stack, constraints
├── REQUIREMENTS.md      ← REQ-001, REQ-002, REQ-003 — all status: open
├── ROADMAP.md           ← phase 01-task-endpoints, status: planned
└── STATE.md             ← current phase: none, last step: project bootstrapped
```

---

## Checklist

- [ ] `/gsd:new-project` ran and created all five root `.planning/` files
- [ ] PROJECT.md contains a non-goals section with at least 5 items
- [ ] All three goals in PROJECT.md are measurable (pass/fail testable)
- [ ] REQUIREMENTS.md contains REQ-001, REQ-002, REQ-003 each with ≥5 acceptance criteria
- [ ] `/gsd:progress` ran and I read its recommended next action
- [ ] I found the model profile setting in config.json
- [ ] `/gsd:health` ran with no errors (warnings understood and accepted)
- [ ] `/gsd:stats` ran and I noted the baseline metrics (requirements open, phases planned)
