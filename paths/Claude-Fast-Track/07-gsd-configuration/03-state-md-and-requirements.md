# STATE.md and REQUIREMENTS.md

These two files are the project's honest memory. STATE.md tracks where you are right now. REQUIREMENTS.md tracks what you must deliver and whether you have delivered it. Together, they are the ground truth that `/gsd:resume-work` and `/gsd:progress` read to reconstruct context across sessions.

---

## STATE.md — the honest memory

STATE.md records the current position in the workflow without optimism. It is a machine-readable + human-readable status file that GSD updates after every significant step.

### What STATE.md contains

```markdown
# State

## Current phase
01-task-endpoints

## Current step
plan-phase completed; execute-phase not yet started

## Last action
2026-05-25: plan-phase completed. PLAN.md written at phases/01-task-endpoints/01-01-PLAN.md.
Wave 1 contains tasks 1.1 (POST handler), 1.2 (GET handler), 1.3 (PATCH handler).

## Active blockers
None.

## In-flight decisions
- Chose sync.Map over mutex+map for storage. Rationale: simpler API, no lock management.
- Chose flat JSON response (no envelope) for v1. Rationale: non-goal to add wrappers until clients exist.

## Next action
Run /gsd:execute-phase for phase 01-task-endpoints, wave 1.
```

### What each field does

| Field | Purpose | Staleness consequence |
|-------|---------|----------------------|
| Current phase | Points resume-work to the right phase dir | Wrong phase loaded on resume |
| Current step | Prevents re-running completed steps | Double-execution, drift |
| Last action | Timestamped breadcrumb trail | Misleading when investigating failures |
| Active blockers | Surfaces why phase is stuck | Unblocked issue missed; phase stays in `blocked` |
| In-flight decisions | Records choices made mid-phase | Contradictory choices next session |
| Next action | Single unambiguous next command | Paralysis or wrong command on resume |

---

## STATE.md anti-patterns

The most dangerous STATE.md failure is optimistic state — recording "completed" when work is actually broken.

| Anti-pattern | What happens |
|-------------|-------------|
| "phase: completed" when UAT failed | `/gsd:resume-work` loads next phase; broken code never fixed |
| "blockers: none" with a known issue | Issue never surfaced to planning; compounds |
| Missing in-flight decisions | Claude makes contradictory choice next session |
| "next action: continue" | Ambiguous — resume-work may pick wrong command |
| Stale timestamp | Cannot tell if state is from this week or last month |

---

## How /gsd:resume-work uses STATE.md

`/gsd:resume-work` reads this chain in order:

1. STATE.md current phase → loads that phase directory
2. STATE.md current step → determines what to skip vs re-run
3. Phase CONTEXT.md → restores your original goal
4. Phase PLAN.md → finds the remaining tasks
5. STATE.md blockers → surfaces issues before you continue

If STATE.md says "execute-phase completed" but UAT.md does not exist, resume-work detects the inconsistency and asks you to clarify. This detection only works if STATE.md is accurate.

---

## STATE.md repair procedure

Run this when STATE.md is stale after a bad execute:

1. Read the actual state: check git log, UAT.md (if it exists), and the phase PLAN.md
2. Determine what truly completed vs what only started
3. Set `current step` to the last confirmed-complete step
4. Set `active blockers` to any known failures
5. Set `next action` to the first incomplete step
6. Timestamp the repair entry: "2026-05-25: STATE manually repaired after partial execute"

Never delete STATE.md and start fresh — the history of decisions and blockers is valuable forensic data.

---

## REQUIREMENTS.md — REQ-IDs as traceability anchors

REQUIREMENTS.md gives every requirement a stable identifier. Tasks in PLAN.md reference REQ-IDs. This lets you trace: task → requirement → acceptance criterion.

### Format

```markdown
# Requirements

## REQ-001: Create task via POST /tasks
Status: open
Phase: 01-task-endpoints

### Description
The API must accept a POST request to /tasks with a JSON body and create a new task.

### Acceptance criteria
- [ ] POST /tasks with `{"title": "Buy milk"}` returns HTTP 201
- [ ] Response body contains an `id` field (string or integer, consistent)
- [ ] Response body contains `title` matching the submitted value
- [ ] Response body contains `status: "incomplete"`
- [ ] Two sequential POST requests produce two tasks with distinct IDs

---

## REQ-002: List tasks via GET /tasks
Status: open
Phase: 01-task-endpoints

### Description
The API must return all tasks currently in memory in creation order.

### Acceptance criteria
- [ ] GET /tasks with no tasks returns HTTP 200 with `[]`
- [ ] GET /tasks after two POST /tasks returns both tasks in creation order
- [ ] Response body is valid JSON array
- [ ] Each task object contains `id`, `title`, and `status` fields
- [ ] GET /tasks does not mutate any task state

---

## REQ-003: Complete task via PATCH /tasks/:id/complete
Status: open
Phase: 01-task-endpoints

### Description
The API must mark a specific task as complete given its ID.

### Acceptance criteria
- [ ] PATCH /tasks/1/complete on an existing incomplete task returns HTTP 200
- [ ] After PATCH, GET /tasks shows that task with `status: "complete"`
- [ ] PATCH /tasks/999/complete on a non-existent task returns HTTP 404
- [ ] PATCH /tasks/1/complete on an already-complete task returns HTTP 409
- [ ] PATCH does not modify tasks other than the targeted ID

---

## REQ-004: Input validation on POST /tasks
Status: open
Phase: 02-validation

### Description
POST /tasks must reject invalid input with structured error responses.

### Acceptance criteria
- [ ] POST /tasks with missing `title` field returns HTTP 400
- [ ] POST /tasks with empty string `title` returns HTTP 400
- [ ] POST /tasks with `title` exceeding 255 characters returns HTTP 400
- [ ] Error response body is JSON with an `error` field containing a human-readable message
- [ ] Valid POST /tasks is unaffected by validation additions

---

## REQ-005: Concurrent safety
Status: open
Phase: 03-concurrent-safety

### Description
All endpoints must be safe under concurrent access without data races.

### Acceptance criteria
- [ ] `go test -race` passes with concurrent POST + GET + PATCH goroutines
- [ ] No deadlock under 50 concurrent clients sending mixed requests
- [ ] go vet reports no issues
- [ ] Benchmark baseline recorded: throughput at 50 concurrent clients
- [ ] No goroutine leak detected after server receives and handles 1000 requests
```

---

## Why REQ-IDs matter

Without REQ-IDs, requirements are prose scattered across PROJECT.md, chat history, and PLAN.md comments. With REQ-IDs:

| Without REQ-IDs | With REQ-IDs |
|-----------------|-------------|
| "we need validation" somewhere | REQ-004: Phase 02, specific acceptance criteria |
| Plan tasks with no traceability | Every task in PLAN.md references REQ-001..REQ-005 |
| Unknown if requirement was met | `Status: satisfied` after execute-phase |
| Duplicate requirements discovered late | Single source in REQUIREMENTS.md |

A PLAN.md task that references a REQ-ID looks like:

```markdown
## Task 1.1 — Implement POST /tasks handler
Satisfies: REQ-001
...
```

This link is how `/gsd:audit-uat` and `/gsd:validate-phase` find gaps — they check every REQ-ID for a corresponding satisfied task.

---

## How requirements get satisfied

1. PLAN.md task references REQ-ID
2. execute-phase runs the task
3. verify-work checks acceptance criteria
4. UAT.md records pass/fail per criterion
5. REQUIREMENTS.md `Status` field updated to `satisfied` or `partial`

If a requirement is `partial`, the next phase must include a task addressing the gap. Never close a requirement with untested acceptance criteria.

---

## Checklist

- [ ] STATE.md has all six fields: current phase, current step, last action, blockers, in-flight decisions, next action
- [ ] STATE.md is pessimistic — if something is broken, it says so
- [ ] I know what /gsd:resume-work reads and in what order
- [ ] I know the STATE.md repair procedure (5 steps)
- [ ] Each REQ in REQUIREMENTS.md has a status field and phase mapping
- [ ] Each REQ has ≥5 binary acceptance criteria
- [ ] Every task in PLAN.md references at least one REQ-ID
- [ ] I know the difference between `open`, `partial`, and `satisfied` REQ status
