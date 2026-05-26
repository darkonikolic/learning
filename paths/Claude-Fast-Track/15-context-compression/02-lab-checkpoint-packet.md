# Lab: checkpoint packet

**Prerequisites:** task-api Phase 1 complete. POST /tasks and GET /tasks/:id implemented and tests passing.

**Duration:** 40 minutes.

**What you will practice:** writing a session-level checkpoint packet, using it to survive `/compact`, and verifying fidelity against three target questions.

---

## Setup

You need:
- task-api Phase 1 complete (all five acceptance criteria passing)
- An active Claude Code session that has been running for this phase
- docs/specs/get-tasks.md open for reference

Do not use `docs/state.md` as your checkpoint source. This lab trains manual checkpoint writing — the skill that makes `docs/state.md` comprehensible when you read it back.

---

## Step 1: Write the checkpoint packet

Before running `/compact`, write the checkpoint in a new file: `task-api/docs/checkpoints/phase1.md`.

Use this exact format — do not abbreviate, paraphrase, or summarise protected zones:

```markdown
## Checkpoint — Phase 1: task store + CRUD — [date]

### Verified state

| AC | Description | Result |
|---|---|---|
| AC-01 | POST /tasks with valid body returns 201 and task JSON including generated id | PASS / FAIL |
| AC-02 | POST /tasks with missing title returns 400 and `{"error":"title is required"}` | PASS / FAIL |
| AC-03 | POST /tasks with title > 200 chars returns 400 and `{"error":"title too long"}` | PASS / FAIL |
| AC-04 | GET /tasks/:id with valid id returns 200 and task JSON | PASS / FAIL |
| AC-05 | GET /tasks/:id with unknown id returns 404 and `{"error":"not found"}` | PASS / FAIL |

### Open decisions

- **ID type:** integer, auto-increment starting at 1. Selected because SPEC says "integer IDs." Not UUID.
- **title validation location:** enforced in handler (tasks.go), not in store layer.
- **Persistence:** in-memory only. No database. Reset on restart. Explicitly out of scope for Phase 1.
- **Router:** [chi / stdlib mux / gorilla — fill in what you used and why]

### Next action

Implement Phase 2: PATCH /tasks/:id partial update. Load docs/specs/get-tasks.md Phase 2 section before starting. Do not begin until SPEC is in context.

### File paths that matter

- `internal/store/store.go` — Task struct, Store interface, MemStore implementation
- `internal/handlers/tasks.go` — POST /tasks and GET /tasks/:id handlers
- `main.go` — router initialisation, server start
- `docs/specs/get-tasks.md` — ground truth; load Phase 2 section for next session
- `task-api_test.go` (or `internal/handlers/tasks_test.go`) — integration tests for AC-01 through AC-05
```

**Fill in your actual values.** AC results must be PASS or FAIL, not "probably passing" or "looks good." Run `go test ./...` and record the actual output.

**Time box:** 10 minutes. If writing the checkpoint reveals you cannot state the AC conditions verbatim, that is a finding — open docs/specs/get-tasks.md and copy the text exactly.

---

## Step 2: Run /compact

In your Claude Code session, run:
```
/compact
```

Claude will summarise the session. The summary will compress or lose:
- Exact error response bodies
- The reasoning behind the ID type choice
- Which file contains which function
- The specific test that was hardest to pass

It will likely preserve:
- General flow of what was built
- File names (sometimes)
- That Phase 1 is "done" (without specifics)

Do not add anything to context after `/compact`. Move directly to Step 3.

---

## Step 3: Resume using only the checkpoint

Load the checkpoint packet as Claude's context for the next step. Do not load any source files, do not paste test output, do not summarise what you remember. Load only:

```
Read task-api/docs/checkpoints/phase1.md
```

Then say: "Resume from this checkpoint. We are about to begin Phase 2."

Observe what Claude says back. A good checkpoint produces a coherent restatement of Phase 1 state. A bad checkpoint produces vagueness or questions that the packet should have answered.

---

## Step 4: The three test questions

With only the checkpoint in context, ask Claude each question separately. Record the answer.

**Q1 — ID type:**
```
What type is the task ID in this API, and what determines the value of a new task's id?
```

Expected answer: integer, auto-incremented from 1, assigned by the store. If Claude says "string" or "UUID" or "I'm not sure," the checkpoint failed to protect this decision.

**Q2 — POST /tasks validation failure:**
```
What does POST /tasks return when the title field is missing from the request body?
Status code and exact response body.
```

Expected answer: 400, `{"error":"title is required"}`. If Claude says "an error response" or "400 with an error message," the checkpoint lost the protected verbatim zone.

**Q3 — Entry point:**
```
What file initialises the HTTP router and starts the server?
```

Expected answer: `main.go`. If Claude says "one of the Go files" or cannot name it, the checkpoint's file paths section was incomplete.

---

## Step 5: Identify what was preserved and what was lost

After the three questions, compare:

| Item | In checkpoint? | Survived /compact? | Notes |
|---|---|---|---|
| AC-01 exact status code and body | Yes (if you filled it in) | Depends on summary quality | |
| AC-02 exact error body | Yes | Often lost in summary | |
| ID type decision | Yes (open decisions) | Often lost or paraphrased | |
| File: tasks.go location | Yes (file paths) | Sometimes preserved | |
| Which test was hardest to pass | No | Lost | Not a checkpoint item — operational detail |
| Rationale for router choice | If included | Usually compressed | |
| Next action | Yes | Preserved if checkpoint was loaded | |

**Finding to record:** Which questions could Claude answer from the checkpoint that it could *not* answer from the `/compact` summary alone? That delta is the value the checkpoint added.

---

## Evaluation criteria

### A passing checkpoint packet

- All five AC rows filled with exact verbatim status code + body text, not descriptions.
- Open decisions list at least: ID type, validation location, persistence scope.
- Next action is a single concrete step — not "continue Phase 2" but "load SPEC Phase 2 and implement PATCH /tasks/:id."
- File paths section contains at minimum: the store file, the handler file, and main.go — with repo-relative paths.

### A failing checkpoint packet

Any of:
- AC conditions described rather than quoted: "validates required fields" instead of `{"error":"title is required"}`.
- Open decisions missing: no mention of ID type, or "we discussed this earlier."
- File paths are descriptions: "the store implementation" instead of `internal/store/store.go`.
- Status column says "done" or "working" instead of PASS/FAIL against a run of `go test`.

### Grading the three test questions

| Score | Criteria |
|---|---|
| 3/3 | Checkpoint is production quality. Use this format for all future phases. |
| 2/3 | One protected zone was lost. Review the failing question, identify which section of the packet was incomplete, repair the format. |
| 1/3 | Checkpoint was mostly description. Rewrite the AC table with verbatim text from docs/specs/get-tasks.md and repeat the test. |
| 0/3 | The checkpoint was not loaded, or was loaded alongside session history. Repeat with only the checkpoint in context. |

---

## What good looks like: reference checkpoint

This is a complete, passing checkpoint for task-api Phase 1. Use it as a template if you are unsure whether yours meets the standard.

```markdown
## Checkpoint — Phase 1: task store + CRUD — 2026-05-25

### Verified state

| AC | Description | Result |
|---|---|---|
| AC-01 | POST /tasks with valid body returns 201 and task JSON including generated id | PASS |
| AC-02 | POST /tasks with missing title returns 400 and `{"error":"title is required"}` | PASS |
| AC-03 | POST /tasks with title > 200 chars returns 400 and `{"error":"title too long"}` | PASS |
| AC-04 | GET /tasks/:id with valid id returns 200 and task JSON | PASS |
| AC-05 | GET /tasks/:id with unknown id returns 404 and `{"error":"not found"}` | PASS |

### Open decisions

- **ID type:** integer, auto-increment starting at 1. Selected per SPEC constraint "integer IDs." Not UUID.
- **title validation location:** enforced in handler (tasks.go HandleCreate), not in store layer.
- **Persistence:** in-memory MemStore. No database. Resets on restart. Phase 1 scope.
- **Router:** chi v5. Chosen for clean URL params (:id). No other reason.

### Next action

Implement Phase 2: PATCH /tasks/:id partial update. Load docs/specs/get-tasks.md lines for Phase 2 before writing any code.

### File paths that matter

- `internal/store/store.go` — Task struct, Store interface, MemStore
- `internal/handlers/tasks.go` — HandleCreate (POST), HandleGet (GET)
- `main.go` — chi router setup, ListenAndServe on :8080
- `docs/specs/get-tasks.md` — load Phase 2 section next
- `internal/handlers/tasks_test.go` — AC-01 through AC-05 integration tests
```

---

## Checklist

- [ ] I ran `go test ./...` and recorded actual PASS/FAIL for each AC — not inferred status.
- [ ] Every AC row contains exact status code and exact response body text, not descriptions.
- [ ] Open decisions names the ID type explicitly (integer, not "the type we chose").
- [ ] File paths section contains at least three concrete repo-relative paths.
- [ ] I ran `/compact` before loading the checkpoint — not after.
- [ ] I loaded only the checkpoint file before asking the three test questions.
- [ ] I scored 3/3 on the test questions, or identified and repaired the failing section.
- [ ] I recorded which context was lost by `/compact` and which was preserved by the checkpoint.
