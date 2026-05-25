# Lab: orchestrate parallel agents for GET /tasks

Map, execute, and verify a parallel agent strategy for task-api Phase 2. The deliverable is a working GET /tasks implementation plus a DAG diagram that documents why the work was structured the way it was.

**Prerequisites:**
- task-api has POST /tasks implemented (Phase 1 complete)
- `tasks/handler.go` exists with `CreateTask` function
- `tasks/store.go` exists with `Store` interface and `AddTask`
- `go build ./...` and `go test ./...` pass

---

## Step 1: Verify prerequisites

```bash
cd task-api
go build ./...
go test ./...
```

Both commands must pass before proceeding. Starting a multi-agent task on a broken codebase compounds problems — each agent's output will build on the broken foundation.

Check what exists:
```bash
ls tasks/
cat tasks/store.go  # read the Store interface signatures
```

Note the exact method signatures — both agent prompts will reference them.

---

## Step 2: Map the DAG for GET /tasks

Before writing a single prompt, draw the dependency graph. GET /tasks requires:

1. A `List() []Task` method on the store (reading from the in-memory store)
2. A `GetTasks` handler function in `tasks/handler.go` that calls `store.List()`
3. Route registration in `main.go` binding `GET /tasks` to the handler
4. Unit tests for `GetTasks` in `tasks/handler_test.go`

Which of these depend on which?

```
[store.List() method]           <- no dependencies
        |
        v
[GetTasks handler]              <- depends on store.List() existing
        |
        v
[route registration in main.go] <- depends on GetTasks handler existing
        |
        v
[integration test]              <- depends on route + handler wired together
```

Unit tests for the handler can be written against the interface contract — they do not require `store.List()` to be implemented, just defined. This makes tests parallelizable with the handler in Wave 2.

**Wave structure for Phase 2:**

| Wave | Tasks | Can run in parallel? |
|------|-------|---------------------|
| Wave 1 | `store.List()` method in `tasks/store.go` | Only task in wave — establishes foundation |
| Wave 2 | `GetTasks` handler in `tasks/handler.go` + handler unit tests in `tasks/handler_test.go` | Yes — handler and tests are in different files and don't depend on each other |
| Wave 3 | Route registration in `main.go` + integration test | Route and integration test can be parallel, but both depend on Wave 2 completing |

Wave 2 is where the parallelism lives: the handler and its tests can be written simultaneously because the tests verify the interface contract (defined in Wave 1), not the handler's internal implementation.

---

## Step 3: Answer the dependency question

**What breaks if Wave 2 runs before Wave 1?**

The `GetTasks` handler calls `store.List()`. If Wave 1 has not run, `List()` does not exist on the `Store` interface. The handler code will fail to compile:

```
./tasks/handler.go:42:22: store.List undefined (type *MemStore has no field or method List)
```

The unit tests in Wave 2 will also fail to compile for the same reason — they call the handler, which calls a method that doesn't exist.

This is why Wave 1 is a prerequisite gate. It is not enough for the handler to "look right" — the entire dependency chain must compile before the next wave starts.

---

## Step 4: Create the DAG diagram

Create the file `docs/plans/phase-2-dag.md` in your task-api project:

```bash
mkdir -p task-api/docs/plans
```

Write the following content (fill in your own analysis where indicated):

```markdown
# Phase 2 DAG — GET /tasks

## Tasks

| ID   | Description                                                                 | File                    | Depends on |
|------|-----------------------------------------------------------------------------|-------------------------|------------|
| 2-01 | Add `List() []Task` method to `MemStore`                                    | tasks/store.go          | none       |
| 2-02 | Implement `GetTasks(w http.ResponseWriter, r *http.Request)` handler        | tasks/handler.go        | 2-01       |
| 2-03 | Write unit tests: TestGetTasksEmpty, TestGetTasksWithTasks, TestGetTasksMethodNotAllowed | tasks/handler_test.go | 2-01 |
| 2-04 | Register `GET /tasks` route in `main.go`                                    | main.go                 | 2-02       |
| 2-05 | Write integration test: server responds end-to-end                          | tasks/handler_test.go   | 2-02, 2-04 |

## Wave execution plan

Wave 1: [2-01]
Wave 2: [2-02, 2-03]  <- parallel
Wave 3: [2-04, 2-05]  <- parallel

## Dependency analysis

What breaks if Wave 2 runs before Wave 1:
[fill in your analysis — which compile error appears and why]

What breaks if Wave 3 runs before Wave 2:
[fill in your analysis — which error appears and why]

## Parallelism justification

2-02 and 2-03 can run in parallel because:
[fill in — why are handler.go and handler_test.go independent?]

## Interface contract (shared ground truth for Wave 2 agents)

Store.List() returns: []Task (empty slice when no tasks, never nil)
GetTasks handler:
- Method: GET only — 405 for other methods
- Success: 200 + JSON array
- Empty: 200 + [] (not null, not 404)
- Content-Type: application/json
```

Save this file. It is the deliverable for the first half of this lab.

---

## Step 5: Write Agent A's prompt (handler)

Agent A implements the `GetTasks` handler. Brief it with task, location, contract, and stop condition.

```
You are implementing the GET /tasks handler for task-api.

Task: Implement GetTasks handler in tasks/handler.go.

Read these files before starting:
- tasks/store.go (the Store interface you will call — specifically the List method)
- tasks/handler.go (the existing file — add GetTasks, do not modify CreateTask)

Interface contract:
- store.List() returns []Task (empty slice when no tasks — never nil)
- If error from store: return 500 with {"error": "internal error"}
- If success: return 200 with JSON array of tasks
- Empty task list: return 200 with [] (not null, not 404)

Handler requirements:
- Method: GET only — return 405 for other methods
- Response Content-Type: application/json
- HTTP status: 200 on success

Stop condition: implement GetTasks function only. Do not modify CreateTask. Do not add
tests. Do not modify main.go or route registration.
```

---

## Step 6: Write Agent B's prompt (tests)

Agent B writes unit tests for the handler. It tests the interface contract, which means it can start as soon as the contract (Wave 1) is in place — it does not need to wait for Agent A.

```
You are writing unit tests for the GET /tasks handler in task-api.

Task: Write tests for GetTasks in tasks/handler_test.go.

Read these files before starting:
- tasks/store.go (the Store interface — specifically List method signature)
- tasks/handler_test.go (if it exists — add to it, don't replace existing tests)

Interface contract to test:
- GET /tasks returns 200 with JSON array
- GET /tasks with no tasks returns 200 with [] (empty array, not null)
- POST to /tasks returns 405 Method Not Allowed
- Response Content-Type is application/json

Test requirements:
- Use net/http/httptest for handler testing
- Use a mock store or in-memory store — do not rely on a running server
- Test function names: TestGetTasksEmpty, TestGetTasksWithTasks, TestGetTasksMethodNotAllowed
- Each test is independent — no shared state between tests

Stop condition: write the three tests listed above. Do not implement any handlers.
Do not modify handler.go. Do not modify main.go.
```

---

## Step 7: Execute both agents in parallel

After Wave 1 (`store.List()`) is verified with `go build ./...`, send both agent prompts simultaneously:

```
Run two independent agents in parallel for task-api Phase 2:

AGENT A — implement handler:
[paste Agent A's full prompt here]

AGENT B — write tests:
[paste Agent B's full prompt here]

Both agents work on different files. Start them simultaneously.
```

Claude Code will spawn both as subagents. They run concurrently. If your Claude Code version doesn't support subagent dispatch in a single message, open a second session for Agent B while Agent A runs in the first.

---

## Step 8: Trust but verify — build check

After both agents report completion:

```bash
go build ./...
```

Expected: zero errors.

If build fails, read the error precisely:
- Which file, which line, what error?
- If the error is in `handler.go`: Agent A produced invalid code
- If the error is in `handler_test.go`: Agent B used a method or type that doesn't compile

Common failure and fix:

```
./tasks/handler.go:42:22: store.List undefined
```

This means Agent A called `store.List()` but Wave 1 did not add `List()` to the interface. Fix Wave 1 first, then re-run Agent A.

---

## Step 9: Trust but verify — test check

```bash
go test ./...
```

Expected: all tests pass.

If `TestGetTasksEmpty` fails with status 404:

The route is likely not registered. Agent A wrote the handler, but `main.go` route registration (Wave 3) has not run yet. This is expected at this stage — Wave 3 is intentionally separate.

For the unit tests using httptest, they call the handler function directly and don't need routing. If they still return 404, Agent A's handler has a routing issue internally (returning 404 instead of 200 for valid GET). Diagnose using the exact expected vs actual status.

---

## Step 10: Complete Wave 3

Register the route and verify end-to-end:

In `main.go`, add:
```go
http.HandleFunc("/tasks", handler.GetTasks)
```

Then run a live test:

```bash
go run . &
curl -s http://localhost:8080/tasks
# Expected: []
curl -s -X POST localhost:8080/tasks -H "Content-Type: application/json" -d '{"title":"first"}'
curl -s http://localhost:8080/tasks
# Expected: [{"id":...,"title":"first","done":false}]
```

This step demonstrates the DAG gap that would have occurred if Wave 3 had been assigned to one of the Wave 2 agents — the handler can be written without the route, but the feature is not usable until the route exists. The DAG must include all steps, including wiring.

---

## Step 11: Update the DAG diagram

Return to `docs/plans/phase-2-dag.md`. Fill in the two analysis sections:

1. "What breaks if Wave 2 runs before Wave 1" — fill in the specific compile error you would have seen
2. "What breaks if Wave 3 runs before Wave 2" — fill in what would happen (agent calls a function that doesn't exist yet)
3. "Parallelism justification" — explain in one sentence why handler.go and handler_test.go are safe to write simultaneously

Save the file. This is the final deliverable.

---

## Verification checklist

- [ ] Prerequisites: `go build ./...` and `go test ./...` both pass before starting
- [ ] `docs/plans/phase-2-dag.md` created with all tasks, waves, and dependency table
- [ ] DAG identifies Wave 1 (store.List) as prerequisite gate — cannot be parallelized
- [ ] Wave 2 correctly identifies handler + unit tests as safe to parallelize
- [ ] Both agent prompts include: task, file location, interface contract, stop condition
- [ ] Both agents invoked simultaneously (or near-simultaneously in parallel sessions)
- [ ] `go build ./...` passes after both Wave 2 agents complete
- [ ] `go test ./...` passes after Wave 2 agents complete
- [ ] No write conflict: agents wrote to different files (handler.go vs handler_test.go)
- [ ] Wave 3 completed: route registered in main.go
- [ ] End-to-end curl test passes: GET /tasks returns [] then a task after POST
- [ ] DAG analysis sections filled in with specific failure analysis

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `go build` fails: undefined List | Wave 1 (store.List) not implemented | Implement List() in store.go before running Wave 2 |
| Tests fail: expected 200, got 404 | Route not registered — Wave 3 not done | Register route in main.go |
| Tests fail: wrong status code | Agent A returned wrong status | Report exact expected vs actual to Agent A with handler.go line reference |
| Both agents edited handler.go | Stop condition was unclear | Re-run with explicit file ownership per agent |
| Agent B tests pass, Agent A's handler is wrong | B tested the contract, A violated it | Fix Agent A to match the contract that B tested |
| Agent output missing entirely | Agent failed silently | Check git log — no commit means it failed; re-run with corrected prompt |
