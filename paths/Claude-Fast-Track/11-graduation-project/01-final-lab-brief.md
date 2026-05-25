# Final lab brief — task-api graduation capstone

This is the end-to-end integration of everything in this track. You will complete Phase 2 (GET /tasks) and Phase 3 (PATCH /tasks/:id/complete) for task-api using the full Claude Code + GSD + spec-driven development workflow. No step-by-step handholding — use the reference map at the bottom of this file when you get stuck.

The graduation checklist at the end is the definition of done. Complete every item. If any item fails, go back and resolve it — do not skip.

---

## Starter Templates

Ten modules of structured guidance end here. The following templates give you the skeleton — you fill in the substance.

### CONTEXT.md template for Phase 2 (GET /tasks)

Create `.planning/phases/02-get-tasks/CONTEXT.md` with this as your starting point:

```markdown
## Goal

Implement GET /tasks endpoint that returns [fill in — what does it return? in what order?].

## Relevant files

- tasks/handler.go — add GetTasks handler here
- tasks/store.go — add List() method here
- main.go — register route here

## Acceptance criteria

- [ ] GET /tasks returns [fill in status code] with [fill in response shape]
- [ ] GET /tasks with no tasks returns [fill in — what status, what body?]
- [ ] Each task in the response has [fill in — which fields?]
- [ ] Response Content-Type is [fill in]
- [ ] [fill in — at least one more criterion]

## Out of scope

- Pagination
- Filtering or sorting
- Authentication
- [fill in any project-specific exclusions]

## Constraints

- stdlib only — no external packages
- [fill in — any data shape constraints from Phase 1?]
```

Do not proceed to `/gsd:plan-phase 2` until every `[fill in]` is replaced with a specific, verifiable claim.

---

### CONTEXT.md template for Phase 3 (POST /tasks — PATCH /tasks/:id/complete)

Create `.planning/phases/03-complete-task/CONTEXT.md`:

```markdown
## Goal

Implement PATCH /tasks/:id/complete endpoint that [fill in — what does it do to a task?].

## Relevant files

- tasks/handler.go — add Complete handler here
- tasks/store.go — add CompleteTask(id string) method here
- main.go — register route here

## Acceptance criteria

- [ ] PATCH /tasks/:id/complete with a valid id returns [fill in status + body]
- [ ] The response body contains [fill in — which fields?]
- [ ] PATCH on an already-complete task returns [fill in — idempotency behavior]
- [ ] PATCH with an unknown id returns [fill in status + body]
- [ ] [fill in — at least two more criteria]

## Out of scope

- Un-completing a task
- Bulk operations
- Authentication
- [fill in any project-specific exclusions]

## Constraints

- stdlib only
- Operation must be idempotent
- Must not modify any field except done
- [fill in any other constraints from your Phase 1/2 decisions]
```

---

### Command sequence reminder

Run these in order. Do not skip ahead.

```
1. /gsd:discuss-phase N       — generates CONTEXT.md draft; you edit it
2. /gsd:plan-phase N          — generates PLAN.md; you review it before approving
3. /gsd:execute-phase N       — runs the plan; you verify after each wave
4. /gsd:verify-work           — UAT against acceptance criteria
5. /gsd:code-review           — quality gate before PR
6. /gsd:pr-branch             — clean branch without .planning/ noise
7. /gsd:ship                  — PR creation + final ship step
```

The sequence is not optional. Skipping discuss means CONTEXT.md is missing and plan-phase will ask for it anyway. Skipping verify-work means you are shipping without evidence. Skipping code-review means you are shipping without a quality gate.

---

## Starting state

Before beginning, confirm this state is true:

- Phase 1 (POST /tasks) is implemented and compiles: `go build ./...` passes
- `.planning/` directory exists with PROJECT.md, REQUIREMENTS.md, ROADMAP.md
- CLAUDE.md exists at project root with stack constraints
- `.claude/settings.json` exists with allow/deny lists
- `.claude/rules/` has at minimum `spec-before-code.md` and `stdlib-only.md`
- REQ-001 status in REQUIREMENTS.md is "satisfied"

If any of these is false, return to the relevant module and complete it before proceeding.

---

## Phase 2: GET /tasks

If you completed the module 09 lab (`09-specification-first/04-lab-write-spec-for-feature.md`), you already have `docs/specs/get-tasks.md`. Skip Step 1 and use it as-is.

If you did not complete the module 09 lab: write `docs/specs/get-tasks.md` now using the full template from `09-specification-first/01-spec-template-and-acceptance.md` before doing anything else. The SPEC is the PRD for plan-phase. Plan-phase cannot run without it.

---

### Phase 2, Step 1: review and finalize SPEC

Open `docs/specs/get-tasks.md`. Work through this checklist before running plan-phase:

**Problem section:**
- Is it one sentence? Does it state what is missing and why it matters now?
- If it says "improve" or "enhance": rewrite to state a specific missing behavior.

**Goal section:**
- Is it measurable? Can you observe it with a curl command?
- If it says "users can see tasks": rewrite to "GET /tasks returns all tasks in creation order with current completion status".

**Out of scope:**
- Does it list filtering, pagination, sorting, authentication?
- Missing exclusions become scope additions during execute.

**Constraint section:**
- Does it include "stdlib only"?
- Does it include "store.List() must return non-nil empty slice"?
- Are all items boolean (not "prefer" or "try to")?

**Acceptance section:**
- Are there ≥5 criteria?
- Is each binary — can you verify it with a command?
- Strike any criterion containing "correctly", "properly", "gracefully".
- For each remaining criterion: write the verification command next to it.

**Tradeoff section:**
- Does it present ≥2 options?
- Is the decision explicit with rationale?

**Rollback section:**
- Is it filled? "Revert handler.go" is acceptable.

If any section is incomplete or weak: fix it now. Do not run plan-phase against a weak SPEC.

---

### Phase 2, Step 2: run plan-phase

```
/gsd:plan-phase 2 --prd docs/specs/get-tasks.md
```

GSD reads the SPEC and produces a PLAN.md with a dependency graph (DAG) of implementation tasks.

**Review PLAN.md before approving:**

Open the generated PLAN.md. For each task, check:

| Question | Expected | If wrong |
|----------|----------|---------|
| Does the task name a specific file? | Yes — `store/store.go`, `handler/handler.go` | Reject — "update store" is too vague |
| Does the task match a SPEC acceptance criterion? | Yes or traces back to one | Flag — task may be out of scope |
| Is the dependency order correct? | store before handler before route registration | Reject — wrong order causes mid-wave failures |
| Does any task mention external packages? | No — stdlib only | Reject — violates SPEC constraint |
| Are tests a separate task after implementation? | Yes | Flag — tests mixed with implementation is harder to verify |

If PLAN.md is weak: ask for a revision. Use specific feedback:

```
Revise PLAN.md:
- Task 1 must name the specific file: store/store.go
- Task 3 must come before Task 4 (store.List() must exist before handler calls it)
- Remove Task 5 (integration test for pagination — pagination is out of scope per SPEC)
```

Do not proceed to execute with a PLAN.md that has vague task descriptions or wrong dependency order.

**Pre-execute checklist (apply before every execute-phase):**

- [ ] SPEC exists on disk and is referenced in PLAN.md
- [ ] PLAN.md has specific file names in every task
- [ ] Dependency order is correct (no task depends on a later task)
- [ ] No external packages referenced
- [ ] Out-of-scope behavior is not in any PLAN.md task
- [ ] `go build ./...` passes before execute (implementation baseline is clean)

---

### Phase 2, Step 3: execute and build-verify

```
/gsd:execute-phase 2
```

After execute completes:

```bash
go build ./...
```

This must pass before any other verification. A build failure means the implementation is incomplete. Do not proceed to verification with a broken build. Diagnose and fix before moving on.

```bash
go test ./...
```

Tests should pass. If tests fail: read the failure message. Is it a test written from a SPEC criterion (test is correct, code is wrong) or a test written from old behavior (code is correct, test needs updating)?

---

### Phase 2, Step 4: acceptance verification

Start the server:

```bash
go run main.go
```

Run each verification command from the SPEC acceptance criteria. Record results.

For the six criteria from the module 09 SPEC:

```bash
# Criterion 1: empty list
curl -s localhost:8080/tasks
# Expected: []
curl -s -o /dev/null -w "%{http_code}" localhost:8080/tasks
# Expected: 200

# Criterion 2: length after two POSTs
curl -s -X POST localhost:8080/tasks -H "Content-Type: application/json" -d '{"title":"alpha"}'
curl -s -X POST localhost:8080/tasks -H "Content-Type: application/json" -d '{"title":"beta"}'
curl -s localhost:8080/tasks | jq length
# Expected: 2

# Criterion 3: creation order
curl -s localhost:8080/tasks | jq '.[0].title'
# Expected: "alpha"

# Criterion 4: required fields
curl -s localhost:8080/tasks | jq '.[0] | keys'
# Expected: ["created_at","done","id","title"]

# Criterion 5: done is boolean
curl -s localhost:8080/tasks | jq '.[0].done | type'
# Expected: "boolean"

# Criterion 6: Content-Type
curl -sI localhost:8080/tasks | grep -i content-type
# Expected line containing: application/json
```

Mark each PASS or FAIL.

For any FAIL: apply the drift repair procedure from `09-specification-first/03-spec-drift-and-repair.md`. Decide which is wrong (code or SPEC). Fix the wrong party. Re-verify.

---

### Phase 2, Step 5: quality and ship

```
/gsd:code-review
```

Read REVIEW.md. Address any HIGH findings. Decide on MEDIUM findings — not all require immediate action, but each requires a decision.

```
/gsd:pr-branch
```

This creates a branch with only phase implementation commits (excludes .planning/ commits). Review the diff on that branch before merging.

Update STATE.md for Phase 2: mark as completed.

Update REQUIREMENTS.md: REQ-002 status = satisfied.

---

## Phase 3: PATCH /tasks/:id/complete

No SPEC exists yet for Phase 3. Write it from scratch before running any GSD commands.

---

### Phase 3, Step 1: write docs/specs/complete-task.md

Create the file using the full template. Every section must be filled. Work through each section below.

**Problem:**
"API consumers cannot mark tasks as complete. Tasks created via POST /tasks have no mechanism to update their completion status, making the API incomplete for task management workflows."

**Goal:**
"PATCH /tasks/:id/complete sets the task's done field to true and returns the updated task. The operation is idempotent — repeated calls return the same 200 response."

**Out of scope:**
- Un-completing a task (setting done back to false)
- Bulk complete operations
- Authentication or authorization
- Partial updates via PATCH (only completion is supported, not title updates)
- Soft delete or archiving completed tasks

**Constraint:**
- Must use stdlib only
- Operation must be idempotent (multiple PATCH calls to the same valid ID must all return 200)
- Must not change any other task field (title, created_at remain unchanged)
- Must not affect other tasks (completing task A must not modify task B)

**NFR:**
- Latency: p99 < 10ms for valid requests (hypothesis — in-memory store, no benchmarks)
- Idempotency: second call to PATCH /tasks/:id/complete returns same 200 with same body
- Error format: 404 response body is `{"error":"task not found"}` JSON

**Boundary / ownership:**
- handler package: owns HTTP routing (extract :id from path), response writing
- store package: owns CompleteTask(id string) (domain.Task, error) — returns updated task or error
- domain package: owns Task struct — done field is the only field CompleteTask modifies

**Acceptance (write your own — minimum 5 are required):**

Think through the surface before writing:
- What happens on a valid ID? (Status, body)
- What happens on an unknown ID? (Status, body)
- What happens if the task is already complete? (Idempotency)
- What does the response body contain? (Schema)
- What fields are unchanged? (Constraint verification)
- Is the done field now true? (State verification)

Example acceptance criteria:
```markdown
- [ ] PATCH /tasks/:id/complete with a valid task id returns HTTP 200
- [ ] Response body for a valid request contains the updated task with done=true
- [ ] Response body includes id, title, done, created_at fields
- [ ] title field in the response is unchanged from the original POST
- [ ] PATCH /tasks/:id/complete on an already-complete task returns HTTP 200 (idempotent)
- [ ] PATCH /tasks/:id/complete with an unknown id returns HTTP 404
- [ ] 404 response body is {"error":"task not found"}
```

Seven criteria — each binary and verifiable with a curl command.

**Tradeoff:**

Option A: return 200 with updated task body
- Pros: client sees current state without a subsequent GET; confirms completion applied correctly
- Cons: slightly more work to marshal response

Option B: return 204 No Content
- Pros: simpler handler (no response body)
- Cons: client must issue a GET to confirm the state change; more network round trips

Decision: Option A — returning the updated task eliminates a required follow-up GET. The extra serialization is negligible for in-memory store. If clients need to display the completed task, they have it immediately.

**Risk:**
- Concurrent requests completing the same task simultaneously
  Mitigation: Go net/http server is single-threaded per-handler by default — lock around store mutation if using goroutines; document as out of scope for current implementation
- :id extraction from URL path using stdlib (no chi, no gorilla)
  Mitigation: use r.URL.Path splitting or strings.TrimPrefix; document approach in implementation strategy

**Rollback:**
Revert handler Complete() method and route registration.
store.CompleteTask() stays — additive change, no breaking effect on existing behavior.

---

### Phase 3, Step 2: self-review the SPEC

Before handing to GSD, audit your SPEC:

**Acceptance criterion audit:**

For each criterion, ask: "can I verify this in 60 seconds with only the criterion text and access to a running server?"

Run through the example seven criteria:

"PATCH /tasks/:id/complete with a valid task id returns HTTP 200"
Verification: `curl -s -o /dev/null -w "%{http_code}" -X PATCH localhost:8080/tasks/$ID/complete` = `200`
Binary. Keep.

"Response body contains the updated task with done=true"
Verification: `curl -s -X PATCH localhost:8080/tasks/$ID/complete | jq '.done'` = `true`
Binary. Keep.

"title field is unchanged"
Verification: compare `.title` before and after PATCH.
Binary. Keep — the "before" value is known from the POST response.

"Already-complete returns 200"
Verification: PATCH twice, check both return 200.
Binary. Keep.

"Unknown id returns 404"
Verification: `curl -o/dev/null -w "%{http_code}" -X PATCH localhost:8080/tasks/nonexistent/complete` = `404`
Binary. Keep.

"404 body is `{"error":"task not found"}`"
Verification: `curl -s -X PATCH localhost:8080/tasks/nonexistent/complete | jq '.error'` = `"task not found"`
Binary. Keep.

All pass. If any failed the audit, rewrite before proceeding.

---

### Phase 3, Step 3: run plan-phase

```
/gsd:plan-phase 3 --prd docs/specs/complete-task.md
```

Review PLAN.md for Phase 3:

| Check | What to look for |
|-------|-----------------|
| store task before handler task | CompleteTask(id) must exist before handler calls it |
| specific file names | `store/store.go` not "update store" |
| no external router | stdlib path parsing only |
| idempotency task present | store.CompleteTask must handle already-complete case |
| 404 error handling task | handler must return correct error response |

The DAG for Phase 3 should look approximately like:

```
Task 1: add CompleteTask(id string) (Task, error) to store/store.go
  → Task 2: add PATCH /tasks/:id/complete route handler to handler/handler.go
    → Task 3: register route in server setup
      → Task 4: write tests for CompleteTask behavior
```

If the DAG has handler before store: reject PLAN.md, request revision with correct order.

---

### Phase 3, Step 4: execute

```
/gsd:execute-phase 3
```

Post-execute build check:

```bash
go build ./...
go test ./...
```

Both must pass. If build fails: the implementation is incomplete or has a syntax error. Read the error, locate the file, fix the issue. Do not run verification until the build passes.

---

### Phase 3, Step 5: full verification

Start the server:

```bash
go run main.go
```

Run all seven acceptance verifications:

```bash
# Create a task to work with
ID=$(curl -s -X POST localhost:8080/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"test task for completion"}' | jq -r '.id')

echo "Task ID: $ID"

# Criterion 1: 200 on valid id
curl -s -o /dev/null -w "%{http_code}" -X PATCH localhost:8080/tasks/$ID/complete
# Expected: 200

# Criterion 2: done=true in response
curl -s -X PATCH localhost:8080/tasks/$ID/complete | jq '.done'
# Expected: true

# Criterion 3: response contains all required fields
curl -s -X PATCH localhost:8080/tasks/$ID/complete | jq 'keys'
# Expected: ["created_at","done","id","title"]

# Criterion 4: title unchanged
ORIGINAL_TITLE=$(curl -s localhost:8080/tasks | jq -r '.[0].title')
RESPONSE_TITLE=$(curl -s -X PATCH localhost:8080/tasks/$ID/complete | jq -r '.title')
echo "Original: $ORIGINAL_TITLE, Response: $RESPONSE_TITLE"
# Expected: both are "test task for completion"

# Criterion 5: idempotent — second PATCH returns 200
curl -s -o /dev/null -w "%{http_code}" -X PATCH localhost:8080/tasks/$ID/complete
# Expected: 200 (same as first call)

# Criterion 6: unknown id returns 404
curl -s -o /dev/null -w "%{http_code}" -X PATCH localhost:8080/tasks/nonexistent-id/complete
# Expected: 404

# Criterion 7: 404 body is correct
curl -s -X PATCH localhost:8080/tasks/nonexistent-id/complete | jq '.error'
# Expected: "task not found"
```

Record results. For any FAIL: apply drift repair. Resolve before proceeding to quality gates.

---

### Phase 3, Step 6: validate and secure

```
/gsd:validate-phase 3
```

Read the coverage table. Write tests for any acceptance criteria with no corresponding test.

```
/gsd:secure-phase 3
```

For task-api Phase 3, expected security findings:
- No SQL injection risk (in-memory, no SQL)
- Input validation: :id extracted from URL is not validated as a positive integer (acceptable — store returns 404 on unknown ID regardless)
- No authentication (explicit scope exclusion)

Read the output. For any security finding not addressed: document as accepted risk or fix.

---

### Phase 3, Step 7: ship

```
/gsd:code-review
```

Read REVIEW.md. Address HIGH findings.

```
/gsd:pr-branch
/gsd:ship
```

Update STATE.md: Phase 3 completed.
Update REQUIREMENTS.md: REQ-003 status = satisfied.
Update ROADMAP.md: all three phases marked completed.

---

## Graduation checklist

Complete every item. If any fails, return to the module indicated and resolve it before marking done.

---

### Claude Code configuration

- [ ] `CLAUDE.md` exists at project root containing: project name, stack (Go, stdlib, net/http), and at least 2 constraints (e.g., "stdlib only", "no global state")
- [ ] `.claude/settings.json` exists with an allow list for Go commands (`go build`, `go test`, `go run`) and a deny list for destructive commands (`git push --force`, `rm -rf`)
- [ ] `.claude/rules/spec-before-code.md` exists and instructs Claude to refuse implementation without a SPEC on disk (module 04)
- [ ] `.claude/rules/stdlib-only.md` exists and instructs Claude to refuse external package imports (module 04)
- [ ] `.mcp.json` exists with at least one server configured (module 03)

---

### GSD setup

- [ ] `.planning/PROJECT.md` exists with: project vision, 3 measurable goals, explicit non-goals
- [ ] `.planning/REQUIREMENTS.md` exists with REQ-001, REQ-002, REQ-003 each having acceptance criteria
- [ ] `.planning/config.json` has `auto_approve: false` (module 05)
- [ ] `.planning/ROADMAP.md` exists with all 3 phases listed

---

### Phase 2: GET /tasks

- [ ] `docs/specs/get-tasks.md` exists with all template sections filled
- [ ] SPEC has ≥5 binary acceptance criteria
- [ ] Tradeoff section has ≥2 options with explicit decision
- [ ] SPEC was on disk before any implementation message was sent
- [ ] `/gsd:plan-phase 2 --prd docs/specs/get-tasks.md` was run
- [ ] PLAN.md was reviewed: every task names specific files
- [ ] Pre-execute checklist was applied before execute
- [ ] `/gsd:execute-phase 2` completed
- [ ] `go build ./...` passes after execute
- [ ] `go test ./...` passes after execute
- [ ] All acceptance criteria verified with specific commands
- [ ] Results recorded: every criterion is PASS (or drift was resolved)
- [ ] `/gsd:verify-work` run: verification artifact exists in .planning/
- [ ] `/gsd:code-review` run: REVIEW.md exists
- [ ] STATE.md shows Phase 2 completed
- [ ] REQ-002 in REQUIREMENTS.md: status = satisfied

---

### Phase 3: PATCH /tasks/:id/complete

- [ ] `docs/specs/complete-task.md` exists with all template sections filled
- [ ] SPEC has ≥5 binary acceptance criteria (ideally ≥7 covering idempotency and error cases)
- [ ] Tradeoff section: ≥2 options, explicit decision with rationale for return-body vs 204
- [ ] Constraint section: idempotency is a named constraint
- [ ] SPEC was on disk before any implementation message was sent
- [ ] `/gsd:plan-phase 3` run with SPEC as PRD
- [ ] PLAN.md reviewed: store task before handler task
- [ ] `/gsd:execute-phase 3` completed
- [ ] `go build ./...` passes
- [ ] `go test ./...` passes
- [ ] All acceptance criteria verified with specific commands
- [ ] Idempotency verified: second PATCH call checked explicitly
- [ ] Unknown ID 404 verified explicitly
- [ ] Drift check completed
- [ ] `/gsd:validate-phase 3` run: coverage table read, gaps addressed
- [ ] `/gsd:secure-phase 3` run: findings addressed or documented
- [ ] `/gsd:code-review` run
- [ ] STATE.md shows Phase 3 completed
- [ ] REQ-003 in REQUIREMENTS.md: status = satisfied
- [ ] ROADMAP.md: all 3 phases marked completed

---

### Final integration checks

- [ ] End-to-end workflow works without restarting server: POST → GET → PATCH → GET

  ```bash
  # Create task
  ID=$(curl -s -X POST localhost:8080/tasks \
    -H "Content-Type: application/json" \
    -d '{"title":"graduation task"}' | jq -r '.id')
  
  # Verify in list
  curl -s localhost:8080/tasks | jq '.[0].title'
  # Expected: "graduation task"
  
  # Complete task
  curl -s -X PATCH localhost:8080/tasks/$ID/complete | jq '.done'
  # Expected: true
  
  # Verify completion reflected in list
  curl -s localhost:8080/tasks | jq '.[0].done'
  # Expected: true
  ```

- [ ] `/gsd:health` passes — no structural issues in .planning/ directory
- [ ] `/gsd:stats` run — metrics are coherent: 3 phases, 3 requirements, all satisfied
- [ ] `docs/specs/` contains at minimum: `get-tasks.md` and `complete-task.md`

---

### Conceptual check

These cannot be auto-verified with commands. Answer each in your own words before marking done.

- [ ] You can describe the SPEC → DAG → wave → verify flow without looking at notes
- [ ] You can explain why "tasks pass" does not guarantee SPEC satisfaction (the derivation chain)
- [ ] You can name the three drift repair cases and when each applies
- [ ] You can state the difference between spec evolution and spec drift
- [ ] You can describe what a boundary section does that constraints and NFR do not
- [ ] You can explain why out-of-scope exclusions prevent scope creep during execute

---

## Reference map

Use this when stuck. Module numbers match the directory names in this track.

| Stuck on | Module | File |
|----------|--------|------|
| Which GSD command to use | 05 | 01-core-loop-commands.md |
| PLAN.md tasks are vague | 06 | 02-plan-phase-and-approval-gates.md |
| Execute failed mid-wave | 06 | 05-mid-flight-changes.md |
| STATE.md is stale | 07 | 03-state-md-and-requirements.md |
| Acceptance criteria not binary | 09 | 01-spec-template-and-acceptance.md |
| NFR or Boundary section unclear | 09 | 02-boundaries-nfr-and-constraints.md |
| SPEC and code diverged | 09 | 03-spec-drift-and-repair.md |
| Lab for GET /tasks SPEC | 09 | 04-lab-write-spec-for-feature.md |
| Executable verification | 10 | 01-executable-spec-thinking.md |
| Drift detection procedure | 10 | 02-drift-detection.md |
| Spec audit lab | 10 | 03-lab-spec-vs-implementation-audit.md |
| Context window polluted | 02 | 03-context-ownership.md |
| Need to add a rule | 04 | 04-rules-and-skills-authoring.md |
| Agent produced wrong output | 08 | 08-trust-but-verify.md |
| Two agents conflicting | 08 | 06-partial-failure-and-recovery.md |
| .planning/ feels broken | 05 | 03-quality-review-and-debug-commands.md |
| Don't know what artifact file does | 07 | 01-planning-directory-layout.md |

---

## What comes next

If you completed all checklist items, you have demonstrated:

- Claude Code configuration: CLAUDE.md, settings.json, rules that enforce SPEC-first behavior
- Context management: SPEC on disk, file path references in implementation messages
- GSD loop: discuss → plan → execute → verify → ship for two phases
- Spec engineering: full template with problem, acceptance, NFR, constraints, boundaries, tradeoff, risk, rollback
- Drift detection and repair: acceptance verification with specific commands, three-case triage
- Executable specs: verification mapping from criterion to command or test

The next level of complexity: multiple concurrent phases with shared types, external services (queues, databases), and multi-developer contexts where boundary ownership prevents silent scope violations. The same workflow applies — the SPEC artefact scales with the complexity of what it describes.

The track is a permanent reference. When you encounter GSD commands not covered here or Claude Code behaviors not explained, find the nearest module and add a note. The reference map grows as the system expands.
