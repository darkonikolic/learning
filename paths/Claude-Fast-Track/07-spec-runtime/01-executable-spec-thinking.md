# Executable spec thinking

Module 09 showed you how to write a SPEC. This module shows you how to verify at runtime that your implementation actually satisfies it.

A SPEC that cannot be verified is a wish list. A SPEC that can be verified is a runtime contract. The difference is not intent — it is whether every acceptance criterion has a corresponding check that can be run without human interpretation.

"Executable" has a precise meaning here: for every acceptance criterion in the SPEC, a person picking up the project tomorrow can derive a verification step — a command, a test, a script — without asking what was meant. That verification step either passes or it does not.

---

## The shift: planning document vs runtime contract

A planning document describes intent. A runtime contract describes behavior that is either present or absent at a specific moment on a specific input.

| Planning document | Runtime contract |
|------------------|-----------------|
| "The API should return task data" | "GET /tasks returns 200 with JSON array; body is [] when no tasks exist" |
| "Validation should be robust" | "POST /tasks with missing title returns 400 with `{\"error\":\"title is required\"}`" |
| "Errors should be handled gracefully" | "POST /tasks with empty string title returns 400; not 201, not 500" |
| "The endpoint should be fast" | "GET /tasks p95 latency < 20ms under 50 concurrent requests (hypothesis)" |
| "Authentication should be considered" | "No auth. All endpoints are public. This is a deliberate scope exclusion." |

Every cell in the right column has a corresponding check. Every cell in the left column invites interpretation drift. The last row — the scope exclusion — is also executable: if any authentication code appears in the implementation, the constraint is violated and the check fails.

---

## The SPEC-to-test mapping

Each acceptance criterion maps to exactly one verification type. There are four types, ordered by preference.

| Verification type | When to use | Example |
|------------------|-------------|---------|
| Automated test (unit/integration) | Always when possible | `TestGetTasks_ReturnsEmptyArray` passes |
| Scripted curl/CLI check | When a running server is needed | `curl localhost:8080/tasks` = `[]` |
| Log line assertion | When behavior is not externally visible | Log contains "store initialized" on startup |
| Manual check with specific steps | Last resort — document steps precisely | "Open browser, navigate to /tasks, observe empty array in response body" |

Manual checks are not executable in the repeatable sense. They depend on a human following the steps correctly every time. Use them only when no automated or scripted alternative exists. Document them precisely enough that two different people would perform the same check.

**For task-api GET /tasks:**

| Acceptance criterion | Executable verification |
|---------------------|------------------------|
| Returns 200 with JSON array | `curl -s -o /dev/null -w "%{http_code}" localhost:8080/tasks` outputs `200` |
| Empty list = 200 + [] | Fresh server: `curl -s localhost:8080/tasks` outputs `[]` |
| Tasks in creation order | POST task A, POST task B, GET, check `jq '.[0].title'` = `"A"` |
| Each task has id, title, done, created_at | `curl -s localhost:8080/tasks | jq '.[0] | keys'` contains all four |
| done field is boolean | `curl -s localhost:8080/tasks | jq '.[0].done | type'` outputs `"boolean"` |
| Content-Type is application/json | `curl -sI localhost:8080/tasks | grep -i content-type` contains `application/json` |

Each row in that table is a testable claim. None requires asking what "correct" means.

---

## Spec-driven TDD

Spec-driven TDD reverses the usual sequence. In standard TDD, you write the test then write the code. In spec-driven TDD, you write the acceptance criterion first, then derive the test from it, then write the code.

This matters because a test written without an acceptance criterion tests what the code does. A test written from an acceptance criterion tests what the code is supposed to do. The difference surfaces when the code does the wrong thing correctly.

**Sequence:**

1. Write acceptance criteria in SPEC (each binary, observable)
2. Derive test names from acceptance criteria — one test per criterion, no implementation yet:

```go
func TestGetTasks_Returns200_WithEmptyArray_WhenNoTasks(t *testing.T) {}
func TestGetTasks_ReturnsAllTasks_InCreationOrder(t *testing.T) {}
func TestGetTasks_EachTask_HasRequiredFields(t *testing.T) {}
func TestGetTasks_DoneField_IsBooleanType(t *testing.T) {}
func TestGetTasks_ResponseContentType_IsApplicationJSON(t *testing.T) {}
```

3. Implement until tests pass
4. Map each passing test back to its SPEC acceptance criterion — trace is explicit

The test names are derived directly from the acceptance criterion text. Anyone reading the test file can find the corresponding SPEC criterion without a cross-reference document.

**Giving the test stubs to Claude:**

You can give Claude the empty test stubs and the SPEC, and ask for implementation only:

```
Fill the test stubs in handler_test.go.
Each test name corresponds to an acceptance criterion in docs/specs/get-tasks.md.
Do not implement handler.go yet.
```

Then separately:

```
Implement GET /tasks per docs/specs/get-tasks.md.
Tests in handler_test.go define acceptance.
Stop when all tests pass.
```

Two-turn sequence. First tests, then implementation. Claude cannot "pass tests" by writing tests that always return nil — Go tests that don't assert anything fail the purpose, not the compile. But you review the test content before the second turn.

---

## Why "tests pass" does not equal "SPEC is satisfied"

This is the most important caveat in spec-driven development.

Tests written without a SPEC verify what the code does. If the code returns tasks in reverse order, and the test was written to match that behavior, the test passes on wrong behavior. The test is not wrong — it accurately describes the code. The code is wrong — it diverges from the SPEC.

The SPEC is the ground truth. Tests are derived from it. When they diverge:

- Tests written before SPEC: tests describe implementation, not intent
- Tests written after SPEC but from code, not criteria: same problem
- Tests written from SPEC criteria: tests are a derivative of the contract

**The derivation chain:**

```
Problem statement
  → Acceptance criterion (in SPEC)
    → Test function (derived from criterion)
      → Implementation (derived from test)
```

Each step is derived from the one above. If the chain breaks — if a test is written from implementation rather than from SPEC — the test no longer traces back to the problem statement. You cannot tell whether passing tests mean the problem is solved.

---

## Spec-to-test coverage check

After running execute-phase, verify that every acceptance criterion has a corresponding test. The verify step maps implementation coverage to SPEC acceptance criteria and reports gaps. Gaps are either:

1. Criteria with no test — implementation may be untested
2. Criteria with tests not derived from the criterion — tests may not verify intent

Both are drift risks.

**Running the coverage check for GET /tasks:**

```bash
go test ./... -v | grep -E "^(=== RUN|--- PASS|--- FAIL)"
```

Map each test name back to its SPEC acceptance criterion. If any criterion has no corresponding test, you have one of two problems:
- The test exists but its name doesn't map to the criterion (rename the test)
- The test doesn't exist (write it)

---

## Executable spec for the full task-api surface

Applying the SPEC-to-verification mapping to all three phases:

**Phase 1: POST /tasks (already complete)**
| Acceptance | Verification |
|------------|-------------|
| 201 on valid input | `curl -X POST ... -d '{"title":"t"}'` → `201` |
| Body has id, title, done, created_at | `jq 'has("id","title","done","created_at")'` → `true` |
| 400 on missing title | `curl -X POST ... -d '{}'` → `400` |
| id is sequential integer | `jq '.id | type'` → `"number"` |
| done defaults to false | `jq '.done'` → `false` |

**Phase 2: GET /tasks**
Already covered above. Six verifications, all scripted.

**Phase 3: PATCH /tasks/:id/complete (not yet implemented)**
| Acceptance | Verification |
|------------|-------------|
| 200 on valid id | `curl -X PATCH .../complete` → `200` |
| Response body contains updated task | `jq '.done'` → `true` |
| Idempotent: second PATCH returns same 200 | Run twice, compare responses |
| 404 on unknown id | `curl -X PATCH .../nonexistent/complete` → `404` |
| done field transitions from false to true | POST task, GET (done=false), PATCH, GET (done=true) |

Writing these before implementing Phase 3 forces you to think about the boundary cases — idempotency, the 404 case, the state transition — before they are embedded in code.

---

## The verification artifact

After every verification session, record results. The record is the verification artifact. Without it, "I verified everything" means nothing two weeks later.

Format: update the SPEC file directly. Change `- [ ]` to `- [x]` for each passing criterion. Add a note for each failure.

Alternatively, create a verification record at `docs/specs/get-tasks-verification.md`:

```markdown
# Verification record: get-tasks
Date: 2024-01-15
Verifier: [name]

| Criterion | Verification command | Result |
|-----------|---------------------|--------|
| 200 + [] empty | `curl -s localhost:8080/tasks` | PASS |
| Length 2 after two POSTs | `curl ... | jq length` | PASS |
| Creation order | `jq '.[0].title'` = "first task" | PASS |
| Required fields | `jq '.[0] | keys'` | PASS |
| done is boolean | `jq '.[0].done | type'` | PASS |
| Content-Type | curl -sI | grep content-type | PASS |
```

The artifact makes verification traceable. It also makes re-verification possible — if something breaks, you have the exact commands to run.

---

## Checklist

- [ ] Every acceptance criterion in every SPEC has a corresponding verification type (test, script, or documented manual check)
- [ ] I can write the verification command for each acceptance criterion without asking what the criterion means
- [ ] Test names are derived from acceptance criterion text — the trace is explicit
- [ ] I understand why "tests pass" does not guarantee SPEC satisfaction
- [ ] Coverage check is in my post-execute workflow — I run it and read the results
- [ ] Verification artifacts exist for completed phases — results are recorded, not just asserted
