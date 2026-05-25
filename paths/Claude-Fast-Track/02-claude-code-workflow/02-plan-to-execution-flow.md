# Plan-to-execution flow

Every implementation failure is a planning failure. Not a Claude failure. Not a tool failure. The work degraded before execution started.

The flow enforces a checkpoint between understanding and action. Skipping it produces output that is locally correct and systemically wrong.

---

## The flow

```
FRAME -> DECOMPOSE -> SPEC/PLAN -> EXECUTE -> VERIFY
  you      you        you+Claude    Claude      you
  alone    alone      together      bounded     alone
```

Claude is active in exactly two phases: plan refinement and bounded execution. You own all other phases. This is not a collaboration style preference — it is the mechanical reason why sessions produce reliable output.

---

## Phase 1: Frame

One sentence. Specific. Grounded in the actual codebase.

Frame = problem statement + out-of-scope declaration.

| Bad frame | Good frame |
|---|---|
| "Build the task API" | "Add POST /tasks to task-api: validate title, store in-memory, return 201 JSON" |
| "Fix the bug in handlers" | "Fix nil pointer in tasks.go:47 when title is empty string" |
| "Make the tests pass" | "Make TestPostTask pass without modifying the test file" |
| "Clean up the code" | "Remove the three dead code blocks flagged by staticcheck in internal/store" |

A bad frame produces a session without a finish line. You cannot verify "build the task API" is done. You can verify "POST /tasks returns 201 with correct JSON body."

---

## Phase 2: Decompose

You write 3–7 steps in your own words before sending anything to Claude.

This is not for Claude. It is for you. Decomposition forces you to discover scope you missed, dependencies you didn't account for, and questions you need answered before execution starts.

For the POST /tasks endpoint:

1. Define Task struct: id (uuid), title (string), completed (bool), created_at (time.Time)
2. Create in-memory store: slice with mutex
3. Write handler: parse JSON body, validate title, store task, return 201
4. Register route in main.go
5. Write TestPostTask: happy path + missing title 400 + oversized title 400

If you cannot write these steps, you do not understand the problem well enough to execute it. Go back to framing.

---

## Phase 3: Spec/Plan

The /plan gate separates sessions that drift from sessions that ship.

### When to use /plan

| Situation | Use /plan? |
|---|---|
| Change touches 2+ files | Yes |
| Rollback concern exists | Yes |
| You are unsure what files are involved | Yes |
| Acceptance criteria require multiple verifications | Yes |
| Single-file bounded edit with obvious scope | No |
| Debugging a known specific issue | No |

### How to invoke /plan

```
/plan Add POST /tasks endpoint — no implementation yet.
Files: main.go, internal/handlers/tasks.go, internal/store/store.go
Constraints: in-memory only, no database, no auth
```

The "no implementation yet" is critical. Without it, Claude may start writing code inside the plan response.

### Plan approval: you decide scope, Claude does not

Claude produces a plan. You read it. You edit it. You approve it.

Plan approval checklist before you proceed:
- Does each step match your decomposition?
- Are all acceptance items objectively verifiable?
- Is the scope bounded to the files you expected?
- Is there a rollback step if needed?
- Are there steps you did not ask for? Remove them.

Claude does not decide scope. If the plan includes a step you did not request, remove it before approving. "Claude suggested it" is not a justification for scope expansion.

---

## Phase 4: Execute

Execution is bounded by the approved plan. Send an explicit bounds message:

```
Execute steps 1-3 from the plan only.
Do not touch main.go yet.
Run go test ./internal/handlers/... after step 3.
```

### Checklist before Send

Every execution message passes this check before you send it:

- [ ] The scope is bounded to specific steps or files
- [ ] Claude knows what NOT to touch
- [ ] There is a verification step in the message
- [ ] This message matches what the approved plan authorizes

If any item fails, edit the message.

### Keeping Claude in scope during execution

Watch for scope creep signals:
- Claude mentions files not in the plan
- Claude adds "while I'm here, I also..." behavior
- The response is longer than the step warrants
- Claude adds error handling you didn't specify

When scope creep appears: stop immediately. Send: "Stop. You've gone beyond the plan. Revert to step [N] scope only."

---

## Phase 5: Verify

Verification maps each acceptance item to a concrete check. "Looks good" is not verification.

| Acceptance item | Verification method |
|---|---|
| POST /tasks returns 201 with JSON body | `curl -s -X POST http://localhost:8080/tasks -d '{"title":"test"}'` |
| Missing title returns 400 | `curl -s -X POST http://localhost:8080/tasks -d '{}'` |
| go test passes | `go test ./...` output shows PASS |
| No race conditions | `go test -race ./...` |
| Handler is in correct file | `ls internal/handlers/tasks.go` |

Write the verification commands before execution starts. If you cannot write them, the acceptance criteria are not concrete enough.

---

## What breaks without this flow

| Symptom | Root cause |
|---|---|
| Claude rewrites files you didn't ask about | No scope boundary in execution message |
| "Done" but tests don't pass | Acceptance criteria not defined before execution |
| Session needs 15 rounds to converge | No decomposition — problem sent raw |
| You're not sure what Claude changed | No plan on disk — only chat history |
| Same mistake in the next session | No capture phase — CLAUDE.md not updated |
| Claude adds features you didn't request | No explicit out-of-scope in frame |

---

## Checklist

- [ ] I can state the problem in one sentence with explicit out-of-scope.
- [ ] I wrote my own 3-7 step decomposition before touching Claude.
- [ ] I used /plan when the change touches 2+ files or has rollback concerns.
- [ ] I edited the plan before approving — Claude did not decide scope.
- [ ] My execution message contains step bounds and a verification instruction.
- [ ] I ran the verification commands before calling the session complete.
- [ ] I wrote down what to capture before closing the session.
