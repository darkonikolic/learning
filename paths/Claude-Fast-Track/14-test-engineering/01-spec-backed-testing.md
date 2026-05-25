# Spec-backed testing

Tests prove spec satisfaction. Not "the code does what I wrote." Not "it compiles and runs." Whether the code satisfies the acceptance criteria in the SPEC — those are the two possible outcomes, and nothing else matters.

A test written from code verifies implementation. A test written from a SPEC criterion verifies intent. When the implementation is wrong, a test written from code passes. A test written from the SPEC criterion fails. That failure is valuable. It is the entire point.

---

## Test posture

Every test in task-api has a position on this axis:

| Position | Origin | What it verifies |
|----------|--------|-----------------|
| Spec-backed | Derived from acceptance criterion in SPEC | Whether the acceptance criterion is satisfied |
| Implementation-backed | Derived from reading the code | Whether the code continues to do what it did when the test was written |

Implementation-backed tests are not worthless. They catch regressions. But they cannot catch the most dangerous class of failure: code that does the wrong thing correctly. A store that returns tasks in reverse order will pass implementation-backed tests. It will fail spec-backed tests.

Rule: every acceptance criterion in a SPEC gets a spec-backed test. Implementation-backed tests may exist in addition. They do not substitute.

---

## Ownership framework

When a test breaks, ownership resolution is three cases. Same three cases as drift repair — the same logic applies.

**Case 1: code is wrong**

Behavior changed and the SPEC was not updated. The test is correct. Fix the code. Re-run. Done.

**Case 2: SPEC is wrong**

The acceptance criterion no longer reflects intent. It was written too early, before the implementation revealed something. The test faithfully caught a real divergence, but the divergence is actually desired. Update the SPEC criterion. Update the test to match. The failure was correct — it surfaced a SPEC debt.

**Case 3: test is wrong**

The test was not derived from the SPEC criterion. It was derived from the code. The criterion is still satisfied but the test was checking the wrong implementation detail. Fix the test derivation. Delete tests that are not traceable to a SPEC criterion or a documented risk.

Ownership question: "If this test breaks tomorrow, who is responsible for resolving it?" The answer must be: the person who can check the criterion against the behavior. Not the person who last touched the file.

---

## Test posture levels for task-api

Three levels, each with a distinct scope. Do not collapse them.

**Unit — store.go**

Scope: the in-memory store, isolated. No HTTP. No JSON encoding. Pure domain behavior.

```go
// store/store_test.go

func TestStore_Add_AssignsSequentialIDs(t *testing.T) {
    s := store.New()
    t1 := s.Add("first")
    t2 := s.Add("second")
    if t2.ID != t1.ID+1 {
        t.Fatalf("expected sequential IDs, got %d and %d", t1.ID, t2.ID)
    }
}

func TestStore_List_ReturnsEmptySlice_WhenNoTasks(t *testing.T) {
    s := store.New()
    tasks := s.List()
    if tasks == nil {
        t.Fatal("List() returned nil; want non-nil empty slice")
    }
    if len(tasks) != 0 {
        t.Fatalf("expected 0 tasks, got %d", len(tasks))
    }
}

func TestStore_List_PreservesInsertionOrder(t *testing.T) {
    s := store.New()
    s.Add("first")
    s.Add("second")
    tasks := s.List()
    if tasks[0].Title != "first" {
        t.Fatalf("expected first task at index 0, got %q", tasks[0].Title)
    }
}
```

Unit tests own domain invariants. Sequential IDs, insertion order, nil-vs-empty — these are store contracts. They break if and only if the store contract changes.

**Handler-level — httptest**

Scope: HTTP request/response contract. Real handler, real store, no live port.

```go
// handler/handler_test.go

func TestGetTasks_Returns200_EmptyArray_WhenNoTasks(t *testing.T) {
    s := store.New()
    h := handler.New(s)
    req := httptest.NewRequest(http.MethodGet, "/tasks", nil)
    w := httptest.NewRecorder()

    h.ServeHTTP(w, req)

    if w.Code != http.StatusOK {
        t.Fatalf("expected 200, got %d", w.Code)
    }
    body := strings.TrimSpace(w.Body.String())
    if body != "[]" {
        t.Fatalf("expected [], got %q", body)
    }
}

func TestGetTasks_ContentType_IsApplicationJSON(t *testing.T) {
    s := store.New()
    h := handler.New(s)
    req := httptest.NewRequest(http.MethodGet, "/tasks", nil)
    w := httptest.NewRecorder()

    h.ServeHTTP(w, req)

    ct := w.Header().Get("Content-Type")
    if !strings.Contains(ct, "application/json") {
        t.Fatalf("expected application/json content-type, got %q", ct)
    }
}
```

Handler tests own HTTP contract: status codes, response shapes, headers. They do not test store internals. The store is real — not mocked — because the handler-store seam is part of the contract.

**Integration — full stack**

Scope: server starts, real port, real HTTP. Used sparingly. One happy path, one critical unhappy path.

```go
// integration/tasks_test.go

func TestGetTasks_FullStack_ReturnsTasksInCreationOrder(t *testing.T) {
    srv := startTestServer(t)
    defer srv.Close()

    postTask(t, srv.URL, "first")
    postTask(t, srv.URL, "second")

    resp, err := http.Get(srv.URL + "/tasks")
    if err != nil {
        t.Fatal(err)
    }
    defer resp.Body.Close()

    var tasks []map[string]interface{}
    json.NewDecoder(resp.Body).Decode(&tasks)

    if tasks[0]["title"] != "first" {
        t.Fatalf("expected first task at index 0, got %v", tasks[0]["title"])
    }
}
```

Integration tests own behavior that only manifests when pieces are wired together: routing, middleware, startup order. Not substitutes for handler tests.

---

## Failure characterization

A test failure is a signal. The signal is only useful if you characterize it.

**Characterization sequence:**

1. Surfaced defect — what the failure message says
2. Reproducible specimen — smallest input that reliably triggers the failure
3. Root class — which of the three cases applies (code / SPEC / test)
4. Guarded test — a test that will catch this class of failure if it recurs

Do not skip to step 4. A test written without step 3 guards against the symptom, not the cause. The next failure of the same root class gets past it.

**For task-api GET /tasks, common failures:**

| Failure | Specimen | Root class |
|---------|----------|-----------|
| `null` instead of `[]` in response | Fresh server, GET /tasks | Code: `store.List()` returns nil |
| Tasks in reverse order | POST A, POST B, GET, check `.[0]` | Code: store uses wrong append strategy |
| `done` field missing from response | GET after POST | Code: struct field not exported or json tag missing |
| `done` is string "false" not boolean | GET, `jq '.[0].done \| type'` | Code: field type or json encoding mismatch |

Each row ends in "Code" — in task-api, these are all code failures. They have spec-backed tests that catch them. If the test was missing, the failure reached production silently.

---

## Regression ownership

Regression ownership is the specific case where a test passes on wrong behavior.

The sequence:

1. Store returns nil from `List()`
2. No test exists for nil-vs-[] (or the test was written from code, so it checks for nil)
3. `json.Marshal(nil)` → `null` in response
4. GET /tasks returns `null` — criterion fails

The test passed. The behavior was wrong. This is regression ownership failure: nobody owned the derivation chain.

Prevention: derive test from SPEC criterion text, not from inspecting the code.

```go
// Derived from criterion: "GET /tasks with no tasks returns HTTP 200 and body []"
// NOT derived from: "store.List() returns nil when empty"
func TestGetTasks_EmptyStore_BodyIsEmptyArray_NotNull(t *testing.T) {
    // ...
    if body != "[]" {
        t.Fatalf("expected [], got %q — nil slice serializes to null; use make([]Task, 0)")
    }
}
```

The test name and error message encode the criterion. A future reader can find `docs/specs/get-tasks.md` without a cross-reference document.

When a test was demonstrably written from code (it passes on clearly wrong behavior), delete it and re-derive it from the SPEC. Do not fix it in place — fixing it in place preserves the wrong derivation pattern.

---

## Checklist

- [ ] Every acceptance criterion in `docs/specs/get-tasks.md` has a corresponding test function
- [ ] Each test name is traceable to its acceptance criterion without a cross-reference
- [ ] `store.List()` returns non-nil empty slice — a unit test guards this
- [ ] Handler tests use `httptest` — no live port, no `net.Listen`
- [ ] At least one integration test covers the full POST → GET creation-order sequence
- [ ] For any failing test, I can state which of the three cases applies before touching any code
- [ ] No test derives its assertions from reading the implementation — all assertions come from SPEC criteria
- [ ] Test error messages include the criterion they guard (makes triage faster)
