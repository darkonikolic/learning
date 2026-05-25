# Compression and checkpoints

## The four context levels

Every serious task has four tiers of context. Load the wrong tier and Claude either lacks what it needs or drowns in noise.

| Level | Name | Contents | Load when |
|---|---|---|---|
| L1 | Goal | One sentence: what success means for this slice. Phase name, SPEC link, key constraint. | Always. First thing in any session. |
| L2 | SPEC | Acceptance criteria (verbatim IDs + text), boundaries, out-of-scope list, non-functional requirements. | At session start and after any `/compact`. |
| L3 | Implementation | Relevant file sections: struct definitions, interface signatures, handler stubs. Not whole files. | When Claude must read or write code. Scoped to the function under work. |
| L4 | Operational | Test output, error messages, failing assertion text, log lines. Evidence for a specific debug or verify step. | Only when diagnosing a failure. Remove after resolved. |

Wrong tier mistakes:
- **L3 without L2**: Claude writes code that compiles but violates acceptance criteria because it never saw them.
- **L4 flooding L2**: error logs from a prior session push SPEC text off the attention stack. Claude references a stale failure.
- **L1 missing**: Claude executes correctly but solves the wrong problem because success was never defined.

### task-api examples

L1 — "Implement Phase 1: CRUD task store (task-api). Success = AC-01 through AC-05 passing."

L2 — The SPEC.md section for Phase 1: field list, ID type (integer, auto-increment), POST /tasks contract, error shapes.

L3 — `internal/store/store.go` lines 1–40: `Task` struct and `Store` interface only. Not `internal/handlers/`.

L4 — `go test ./... -run TestCreateTask` output after a red run. Load it; fix it; drop it before the next task.

---

## Protected verbatim zones

Compression destroys drift-prone text safely: narrative, rationale, chat. It must never touch:

| Protected class | Examples in task-api | Why paraphrase kills you |
|---|---|---|
| Acceptance criteria IDs | `AC-01`, `AC-03` | Summaries say "validates input" — which field? Which status code? The ID + verbatim text is the ground truth. |
| Exact field names | `title`, `status`, `created_at` | "The title field" vs `title` — one is a description, one is a JSON key. Drift corrupts tests, serialisation, and client contracts. |
| Error codes and shapes | `400`, `{"error":"title is required"}` | "Returns an error" tells Claude nothing. The exact body is the contract. |
| Constraint rules | title max 200 chars, status ∈ {open, done} | "Validate title length" loses the bound. Claude picks 255 or 100. Both are wrong. |
| File paths that matter | `internal/store/store.go`, `main.go` | "The store file" requires inference. The path is load-bearing. |

**Rule:** before compressing anything, write out every protected field as a named list. Do not summarise those items. Everything else can be condensed.

### How paraphrase introduces drift

Original AC-02: "POST /tasks returns 201 with the created task JSON on success."

Paraphrased: "Endpoint creates tasks and responds with task data."

What Claude infers from the paraphrase:
- Status could be 200 or 201 — ambiguous.
- "Task data" — does it include the generated `id`? Maybe.
- "JSON" — implied but not guaranteed.

One paraphrase, three potential drift points. In a CRUD API that is three failing tests.

---

## Checkpoint packets

A checkpoint packet is a structured context reset written at a stable milestone. It replaces the accumulated session narrative as the authoritative state of truth.

**Write one when:**
- An execute wave completes (all tasks in a PLAN.md wave are done and verified).
- Before running `/compact` — the packet survives; the chat does not.
- Before handing off to another session or another agent.
- When context has grown past 60% full and you are switching sub-problems.

### Checkpoint packet format

```
## Checkpoint — [phase name] — [timestamp or commit]

### Verified state
- [AC-01] POST /tasks → 201 + task JSON: PASS
- [AC-02] POST /tasks missing title → 400 + {"error":"title is required"}: PASS
- [AC-03] GET /tasks/:id → 200 + task JSON: PASS
- [AC-04] GET /tasks/:id unknown id → 404 + {"error":"not found"}: PASS
- [AC-05] Store is in-memory; no persistence required: PASS

### Open decisions
- ID type: integer (auto-increment from 1). Chosen per SPEC constraint. Not UUID.
- title max 200 chars enforced in handler, not store layer.
- No authentication — explicitly out of scope for Phase 1.

### Next action
Implement Phase 2: PATCH /tasks/:id (partial update). Load SPEC section 2 before starting.

### File paths that matter
- internal/store/store.go — Task struct, Store interface, in-memory implementation
- internal/handlers/tasks.go — POST and GET handlers
- main.go — router setup (chi)
- SPEC.md — ground truth for all phases
```

**What makes a packet valid:**
- Every acceptance criterion has a named pass/fail status.
- Every open decision is explicit — no "we decided something earlier in chat."
- Next action is a single concrete step, not a list of possibilities.
- File paths are absolute or repo-relative — not descriptions.

---

## Stale context risk

Context that is true at session start can become false by session end. Three patterns:

**1. Structural drift** — you refactored `Store` interface mid-session. A reference to it loaded at session start is now wrong. Claude writes code against the old signature.

**2. Decision drift** — you changed ID type from UUID to integer halfway through a session, but the SPEC excerpt in context still says UUID. Claude generates UUIDs for three more functions before you notice.

**3. Status drift** — AC-03 was failing at the start of the session. You fixed it. But context still contains the failure log. Claude treats it as still broken and attempts a second fix that reverts the first.

### How GSD STATE.md reduces stale context risk

STATE.md is a checkpoint packet on disk. GSD writes it after each execute wave. At session start you load STATE.md as L2 context — it reflects the current verified state, not what was true yesterday.

Without STATE.md: you reconstruct current state from git log, chat history, and memory. All three are stale context risks.

With STATE.md: one file, one load. The checkpoint is always at the most recent verified milestone.

**Still your responsibility:** STATE.md does not capture decisions made in chat. Open decisions — ID type, error shape choices, constraint interpretations — belong in your checkpoint packet or in SPEC.md. STATE.md tracks completion status, not design rationale.

---

## Compression validation

After compressing context (via `/compact` or manual summarisation), verify the compression did not destroy the protected verbatim zones.

**Three-question test:**
1. Can Claude state each acceptance criterion ID and its exact success condition?
2. Can Claude state the exact error body for each validation failure?
3. Can Claude name the correct field names, types, and constraints from SPEC?

If Claude answers with paraphrases ("the endpoint validates required fields"), the compression failed. The acceptance criteria are no longer intact.

**How to run it:**

After `/compact`, before resuming execution work, ask:
```
What does AC-02 require exactly — status code and response body?
```

If the answer is "400 with an error message," that is paraphrase. Stop. Reload SPEC.md before continuing. Running an execute task on degraded SPEC context produces drift.

If the answer is "400 with body `{\"error\":\"title is required\"}`," the checkpoint is intact.

---

## The compression pipeline in practice

For task-api, the full pipeline at the end of Phase 1 looks like this:

**1. Retrieve** — identify what is currently in context: session chat, SPEC.md excerpt, store.go, handlers/tasks.go, test output.

**2. List protected zones** — before touching anything, write out: AC-01 through AC-05 exact text, field names (`title`, `status`, `created_at`, `id`), error bodies, constraint values (title max 200, status enum).

**3. Write checkpoint packet** — record verified state, open decisions, next action, file paths. No prose. No narrative. This is the distillate.

**4. Validate** — ask the three questions. If any answer is paraphrase, the checkpoint is incomplete. Fix it before running `/compact`.

**5. Inject consciously** — in the new session, load the checkpoint first, then load only the files needed for the next task. Do not reload all of Phase 1 context. The checkpoint replaces it.

**What the pipeline prevents:**

| Skipped step | Failure mode |
|---|---|
| No protected zone list | AC-02 error body gets paraphrased away. Claude writes wrong response body in Phase 2 handler. |
| No checkpoint before /compact | Open decision (ID type) is lost. Phase 2 generates UUID IDs, breaking Phase 1 tests. |
| No validation | Compression looks fine but AC conditions are degraded. Only discovered when Phase 2 tests fail against Phase 1 contract. |
| Stealth re-injection | Phase 1 L4 debug logs reloaded with Phase 2 context. Claude reasons about old failures as current state. |

---

## Checklist

- [ ] I can name which context level (L1–L4) each item in my window belongs to.
- [ ] Before compressing, I listed every protected verbatim item (AC IDs, field names, error shapes, constraint values).
- [ ] My checkpoint packet contains verified state, open decisions, next action, and file paths — nothing else.
- [ ] I write a checkpoint packet before running `/compact` on a session with completed work.
- [ ] I loaded the checkpoint packet (not session history) to resume the session after `/compact`.
- [ ] I ran the three-question compression validation before resuming execution work.
- [ ] My open decisions in the checkpoint are explicit — not references to "what we decided earlier."
- [ ] I know that GSD STATE.md tracks completion, not design decisions — those go in the checkpoint.
