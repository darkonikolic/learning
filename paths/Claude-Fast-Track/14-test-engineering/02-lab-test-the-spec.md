# Lab: test the spec

Prerequisites: `docs/specs/get-tasks.md` exists (written in module 09 lab). Phase 2 GET /tasks is implemented and `go build ./...` passes. You have not written any tests for GET /tasks yet.

---

## Step 1: read the acceptance criteria

Open `docs/specs/get-tasks.md`. Find the Acceptance section. You need these six criteria:

```
- [ ] GET /tasks with no tasks returns HTTP 200 and body `[]`
- [ ] GET /tasks after creating two tasks returns HTTP 200 and a JSON array of length 2
- [ ] Tasks in response appear in creation order — first-created task is at index 0
- [ ] Each task object contains exactly: id (string), title (string), done (boolean), created_at (string)
- [ ] done field is JSON boolean type (verifiable with `jq '.[0].done | type'` = "boolean")
- [ ] Response Content-Type header is application/json
```

If your SPEC has different wording, use your wording. The point is: criteria on disk, not criteria from memory.

---

## Step 2: derive 6 test stubs from the criteria

One stub per criterion. Name derived directly from criterion text. Empty bodies only — no assertions yet.

Create `handler/handler_test.go` (or append if it exists):

```go
package handler_test

import (
    "net/http"
    "net/http/httptest"
    "testing"
)

// Criterion: GET /tasks with no tasks returns HTTP 200 and body []
func TestGetTasks_Returns200_EmptyArray_WhenNoTasks(t *testing.T) {
}

// Criterion: GET /tasks after creating two tasks returns HTTP 200 and array of length 2
func TestGetTasks_Returns200_ArrayOfLength2_AfterTwoPosts(t *testing.T) {
}

// Criterion: Tasks in response appear in creation order — first-created task is at index 0
func TestGetTasks_ReturnsTasksInCreationOrder(t *testing.T) {
}

// Criterion: Each task object contains exactly: id, title, done, created_at
func TestGetTasks_EachTask_HasExactlyRequiredFields(t *testing.T) {
}

// Criterion: done field is JSON boolean type
func TestGetTasks_DoneField_IsBooleanType(t *testing.T) {
}

// Criterion: Response Content-Type header is application/json
func TestGetTasks_ContentType_IsApplicationJSON(t *testing.T) {
}
```

Run immediately:

```bash
go test ./handler/...
```

Expected: all six pass (empty test bodies pass in Go). This confirms compilation. Any compile error here is a package structure problem to fix before the next step.

---

## Step 3: give Claude the stubs and SPEC — bodies only, no implementation

Send this message exactly:

```
Fill the test bodies in handler/handler_test.go.

Each test corresponds to one acceptance criterion in docs/specs/get-tasks.md.
The criterion is in the comment above each test function.

Rules:
- Use net/http/httptest — no live server, no net.Listen
- Use a real store (store.New()), not mocks
- Each test asserts exactly the criterion it names — nothing more
- Do not modify handler.go or store.go
- Do not add helper functions unless used by more than one test

Stop after filling the test bodies. Do not implement any handler code.
```

Do not add context about how the handler works. Do not explain the store structure. Claude reads `docs/specs/get-tasks.md` — the SPEC is the contract. If Claude asks about the handler's interface, tell it to derive from the SPEC only.

---

## Step 4: review the test bodies before running

Before `go test`, read each test body. For each one, answer:

**Does this test assertion come from the criterion, or from what the implementation happens to do?**

Specific checks:

For `TestGetTasks_Returns200_EmptyArray_WhenNoTasks`:
- Does the test check for `"[]"` as the body string? Not `"null"`, not `""`.
- Does it check status 200 explicitly?

For `TestGetTasks_ReturnsTasksInCreationOrder`:
- Does the test POST two tasks with distinct titles?
- Does it check `tasks[0].Title == "first"` — not `tasks[1]`?

For `TestGetTasks_EachTask_HasExactlyRequiredFields`:
- Does it check for all four fields: id, title, done, created_at?
- Does it check for absence of extra fields? (The criterion says "exactly".)

For `TestGetTasks_DoneField_IsBooleanType`:
- Does it decode into `interface{}` and check the Go type, not just the value?
- `false` and `"false"` are different. The test must distinguish them.

For `TestGetTasks_ContentType_IsApplicationJSON`:
- Does it check `w.Header().Get("Content-Type")`?
- Does it use `strings.Contains` (handles `application/json; charset=utf-8`) rather than exact match?

If any test body was derived from implementation behavior rather than criterion text, rewrite it from the criterion before proceeding. Use the criterion comment as the only source.

---

## Step 5: add a regression test for the nil-vs-[] store bug

This test is not in the acceptance criteria. It is a guarded test for a known failure class.

```go
// Regression: store.List() returning nil causes json.Marshal to produce null, not []
// Criterion origin: docs/specs/get-tasks.md constraint — "store.List() must return non-nil empty slice"
func TestGetTasks_NilSliceBug_BodyIsArray_NotNull(t *testing.T) {
    s := store.New()
    // Do not add any tasks — store is empty
    h := handler.New(s)

    req := httptest.NewRequest(http.MethodGet, "/tasks", nil)
    w := httptest.NewRecorder()
    h.ServeHTTP(w, req)

    body := strings.TrimSpace(w.Body.String())
    if body == "null" {
        t.Fatal("body is null: store.List() returned nil slice; use make([]Task, 0) or []Task{}")
    }
    if body != "[]" {
        t.Fatalf("expected [], got %q", body)
    }
}
```

Add a parallel unit test at the store level:

```go
// store/store_test.go

func TestStore_List_ReturnsNonNilSlice_WhenEmpty(t *testing.T) {
    s := store.New()
    tasks := s.List()
    if tasks == nil {
        t.Fatal("List() returned nil; json.Marshal(nil) produces null, not []")
    }
}
```

The error message explains the consequence. When this test fails at 2am on-call, the message tells the reader what to fix without requiring them to remember the json.Marshal behavior.

---

## Step 6: run go test and record results

```bash
go test ./... -v 2>&1 | tee test-results.txt
```

Expected output pattern:

```
--- PASS: TestGetTasks_Returns200_EmptyArray_WhenNoTasks (0.00s)
--- PASS: TestGetTasks_Returns200_ArrayOfLength2_AfterTwoPosts (0.00s)
--- PASS: TestGetTasks_ReturnsTasksInCreationOrder (0.00s)
--- PASS: TestGetTasks_EachTask_HasExactlyRequiredFields (0.00s)
--- PASS: TestGetTasks_DoneField_IsBooleanType (0.00s)
--- PASS: TestGetTasks_ContentType_IsApplicationJSON (0.00s)
--- PASS: TestGetTasks_NilSliceBug_BodyIsArray_NotNull (0.00s)
--- PASS: TestStore_List_ReturnsNonNilSlice_WhenEmpty (0.00s)
```

Record the actual results. "Tests passed" is not a record. The test names are the record.

If any test fails, go to Step 7. Do not fix the test until you complete Step 7.

---

## Step 7: apply the three-case triage to failing tests

For each failing test, apply the triage table before touching any code:

| Question | If yes | Action |
|----------|--------|--------|
| Is the implementation behavior what we actually want? | Code is right, SPEC/test is wrong | Update SPEC criterion; re-derive test from updated criterion |
| Does the criterion describe the intended behavior? | SPEC is right, code drifted | Fix the code; do not touch the test |
| Is the criterion ambiguous — both interpretations defensible? | Both are wrong | Return to Problem/Goal in SPEC; rewrite criterion; then fix code or test |

**Common failures and their correct triage:**

| Test | Failure | Triage | Resolution |
|------|---------|--------|------------|
| `TestGetTasks_Returns200_EmptyArray_WhenNoTasks` | body is `null` | Case 1 SPEC right | Fix `store.List()` to return `[]Task{}` |
| `TestGetTasks_ReturnsTasksInCreationOrder` | tasks[0] is second task | Case 1 SPEC right | Fix store append order |
| `TestGetTasks_DoneField_IsBooleanType` | done is string `"false"` | Case 1 SPEC right | Fix Task struct json tag or field type |
| `TestGetTasks_EachTask_HasExactlyRequiredFields` | extra field `updated_at` present | Case 2 ambiguous | Decide: add to SPEC (evolution) or remove from code |
| `TestGetTasks_ContentType_IsApplicationJSON` | header is `text/plain` | Case 1 SPEC right | Fix handler to set Content-Type header |

Do not apply case 2 (SPEC wrong) unless you can explain in one sentence why the criterion was wrong and what it should say instead. If you cannot write that sentence, the criterion was probably right and the code needs fixing.

After resolving each failure: re-run `go test ./...`. Every criterion must have a passing test before this lab is complete.

---

## Checklist

- [ ] `docs/specs/get-tasks.md` was open during stub derivation — names came from criteria text, not from memory
- [ ] All 6 stubs compiled before any test bodies were filled
- [ ] Test bodies reviewed before running — each assertion traces to its criterion comment
- [ ] The nil-vs-[] regression test exists in both handler and store packages
- [ ] `go test ./...` passes with all 8 tests (6 spec-backed + 2 regression/unit)
- [ ] Any failures triaged with the three-case table before code was touched
- [ ] Test error messages include enough context to diagnose the failure without re-reading the code
- [ ] No test was modified to make it pass — only implementation was changed
