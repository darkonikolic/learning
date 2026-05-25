# Lab: safe refactor of task-api

This lab has one objective: extract the in-memory store from `handler.go` into `store/store.go` without breaking the API at any intermediate step. You will fill the template first, send a scoped instruction to Claude, verify after each step, and triage if anything breaks.

Do not send any message to Claude until step 2 is complete.

---

## Starting state

`handler.go` in a minimal task-api looks like this:

```go
package main

import (
    "encoding/json"
    "net/http"
    "strconv"
    "strings"
    "sync"
)

type Task struct {
    ID        int    `json:"id"`
    Title     string `json:"title"`
    Completed bool   `json:"completed"`
}

type Handler struct {
    mu     sync.Mutex
    tasks  []Task
    nextID int
}

func (h *Handler) CreateTask(w http.ResponseWriter, r *http.Request) {
    var req struct{ Title string }
    json.NewDecoder(r.Body).Decode(&req)
    h.mu.Lock()
    h.nextID++
    t := Task{ID: h.nextID, Title: req.Title}
    h.tasks = append(h.tasks, t)
    h.mu.Unlock()
    w.WriteHeader(http.StatusCreated)
    json.NewEncoder(w).Encode(t)
}

func (h *Handler) ListTasks(w http.ResponseWriter, r *http.Request) {
    h.mu.Lock()
    out := make([]Task, len(h.tasks))
    copy(out, h.tasks)
    h.mu.Unlock()
    json.NewEncoder(w).Encode(out)
}

func (h *Handler) CompleteTask(w http.ResponseWriter, r *http.Request) {
    parts := strings.Split(r.URL.Path, "/")
    id, _ := strconv.Atoi(parts[2])
    h.mu.Lock()
    defer h.mu.Unlock()
    for i, t := range h.tasks {
        if t.ID == id {
            h.tasks[i].Completed = true
            json.NewEncoder(w).Encode(h.tasks[i])
            return
        }
    }
    http.NotFound(w, r)
}
```

`main.go`:

```go
package main

import "net/http"

func main() {
    h := &Handler{}
    http.HandleFunc("/tasks", func(w http.ResponseWriter, r *http.Request) {
        switch r.Method {
        case http.MethodPost:
            h.CreateTask(w, r)
        case http.MethodGet:
            h.ListTasks(w, r)
        }
    })
    http.HandleFunc("/tasks/", func(w http.ResponseWriter, r *http.Request) {
        if r.Method == http.MethodPatch {
            h.CompleteTask(w, r)
        }
    })
    http.ListenAndServe(":8080", nil)
}
```

---

## Step 1: identify the refactor target

Before touching anything, answer these questions in writing (a comment in a scratch file is fine):

- Which fields and methods on `Handler` belong to data management rather than HTTP handling?
- What is the coupling: which methods reach directly into `mu`, `tasks`, `nextID`?
- What would a `store.Store` type own, and what interface would `handler.go` need from it?

The answers determine your MIGRATION STEPS. If you cannot answer them, you do not understand the cut point yet.

---

## Step 2: fill the refactor template

Create `docs/refactor-store-extraction.md` inside the task-api project. Fill every field.

```
CURRENT STATE
  File: handler.go
  Type: Handler struct { mu sync.Mutex; tasks []Task; nextID int }
  Handler owns: ID generation, task storage, concurrency control
  Methods: CreateTask, ListTasks, CompleteTask — all access raw fields directly
  Package: main

TARGET STATE
  New package: store (internal to task-api)
  New file: store/store.go
  New type: store.Store { mu sync.Mutex; tasks []Task; nextID int }
  New methods: Add(title string) Task, List() []Task, Complete(id int) (Task, bool)
  Modified: handler.go — Handler struct holds *store.Store; methods call store methods
  Modified: main.go — instantiates store.NewStore(), passes to Handler
  HTTP behaviour: identical — status codes, JSON field names, path routing unchanged

DIFF
  CREATE  store/store.go          Task type; Store struct; NewStore(); Add; List; Complete
  MODIFY  handler.go              remove mu/tasks/nextID; add S *store.Store; rewrite method bodies
  MODIFY  main.go                 pass store.NewStore() to Handler initialiser
  DELETE  (none until step 3)     Task in main package removed after confirmed stable

RISK
  Task type duplication across main and store until step 3 — manage with import alias
  Mutex ownership must transfer completely; any remaining raw field access causes race
  main.go instantiation order: Store must be created before Handler

MIGRATION STEPS
  Step 1: create store/store.go with Task, Store, NewStore, Add, List, Complete
          Do not modify handler.go. Verify: go build ./...
  Step 2: modify handler.go and main.go to use store.Store
          Remove raw fields from Handler. Verify: go build ./... and go test ./...
  Step 3: remove Task from main package; update any remaining references
          Verify: go build ./... and go test ./...

ROLLBACK
  git revert <step-commit-hash> — each step is one commit
  No irreversible state: no external systems, no schema migrations
  Highest coupling risk at step 2; confirm go test ./... before step 3

VALIDATION
  go build ./...
  go test ./...
  curl -s -X POST localhost:8080/tasks -H 'Content-Type: application/json' \
    -d '{"title":"write tests"}' | jq .
  curl -s localhost:8080/tasks | jq .
  curl -s -X PATCH localhost:8080/tasks/1/complete | jq .
```

Do not send any message to Claude until this file exists on disk.

---

## Step 3: execute step 1 — create the store package

Send Claude this exact message:

```
Execute step 1 from docs/refactor-store-extraction.md only.

Create store/store.go with the Task type, Store struct, NewStore constructor,
and Add/List/Complete methods as described in the TARGET STATE section.

Do not modify handler.go or main.go.
Stop when store/store.go is written.

After writing the file, run: go build ./...
Report the output. Do not proceed to step 2.
```

After Claude responds, verify yourself:

```bash
go build ./...
```

Expected: exits 0. The new package exists but nothing uses it yet — that is correct.

```bash
ls store/store.go
```

Expected: file exists.

```bash
go vet ./...
```

Expected: no output (no issues).

Commit if clean:

```bash
git add store/store.go
git commit -m "refactor: add store package with Task, Store, Add/List/Complete"
```

Do not proceed to step 2 if `go build` fails.

---

## Step 4: execute step 2 — migrate handler.go and main.go

Send Claude this exact message:

```
Execute step 2 from docs/refactor-store-extraction.md only.

Modify handler.go to remove the mu, tasks, nextID fields from Handler.
Add a field S *store.Store to Handler.
Rewrite CreateTask, ListTasks, CompleteTask to call h.S.Add, h.S.List, h.S.Complete.

Modify main.go to instantiate store.NewStore() and pass it to Handler.

Stop when both files are modified.

After modifying, run: go build ./... and go test ./...
Report both outputs. Do not proceed to step 3.
```

After Claude responds, verify yourself:

```bash
go build ./...
go test ./...
```

Both must exit 0. If either fails, stop and triage before continuing.

Run the smoke test manually:

```bash
go run . &
SERVER_PID=$!

curl -s -X POST localhost:8080/tasks \
  -H 'Content-Type: application/json' \
  -d '{"title":"write tests"}' | jq .
# Expected: {"id":1,"title":"write tests","completed":false}

curl -s localhost:8080/tasks | jq .
# Expected: [{"id":1,"title":"write tests","completed":false}]

curl -s -X PATCH localhost:8080/tasks/1/complete | jq .
# Expected: {"id":1,"title":"write tests","completed":true}

kill $SERVER_PID
```

Commit if clean:

```bash
git add handler.go main.go
git commit -m "refactor: migrate Handler to use store.Store"
```

---

## Step 5: execute step 3 — remove the duplicate Task type

Send Claude this exact message:

```
Execute step 3 from docs/refactor-store-extraction.md only.

Remove the Task type declaration from handler.go (or main.go if it moved there).
Update all references in handler.go and main.go to use store.Task.

Stop when the duplicate type is removed and all references are updated.

After modifying, run: go build ./... and go test ./...
Report both outputs.
```

After Claude responds, verify yourself:

```bash
go build ./...
go test ./...
```

Both must exit 0.

```bash
grep -n "type Task struct" *.go
```

Expected: no output. The type now lives only in `store/store.go`.

Commit:

```bash
git add handler.go main.go
git commit -m "refactor: remove Task from main package, use store.Task"
```

---

## 3-case triage if any step breaks tests

When `go test ./...` fails after a step, apply this triage before doing anything else:

**Case 1 — compilation error**
```
go build ./... 2>&1
```
Read the first error only. Fix that error, then re-run `go build`. Do not guess at multiple fixes simultaneously. One error, one fix, one re-run.

**Case 2 — test failure, code compiles**
```
go test ./... -v 2>&1 | grep -A 10 "FAIL"
```
Identify which test fails and what the assertion is. Ask: did this test pass before this step? If yes, the step introduced a regression. Revert the step commit and re-read the template. If the test was already failing before the step, that is a pre-existing issue — do not conflate it with the refactor.

**Case 3 — race condition**
```
go test -race ./...
```
If the race detector fires, the mutex was not migrated correctly. Check that all field accesses in handler.go go through store methods and no raw `mu`, `tasks`, or `nextID` references remain. Use `grep -n "\.mu\|\.tasks\|\.nextID" handler.go`.

Do not move to the next step until the current step is clean. This rule is not optional.

---

## Step 6: record what changed vs what was preserved

After all three steps are complete, write a short record (a commit message body or a comment in the template file):

```
CHANGED
  - Ownership: mu, tasks, nextID now owned by store.Store, not Handler
  - Instantiation: main.go now creates store.NewStore() explicitly
  - Type location: Task lives in store package, not main package
  - Method bodies: CreateTask/ListTasks/CompleteTask now delegate to store

PRESERVED
  - HTTP paths: POST /tasks, GET /tasks, PATCH /tasks/:id/complete
  - JSON field names: id, title, completed
  - Status codes: 201 on create, 200 on list/complete, 404 on missing ID
  - In-memory behaviour: no persistence, IDs are sequential integers from 1
  - Concurrency model: single mutex, same semantics, now inside store
```

This record serves two purposes: it confirms you understand what the refactor actually did, and it is the starting point for the next refactor step if one follows.

---

## Checklist

- [ ] I created `docs/refactor-store-extraction.md` and filled every field before writing any Claude message.
- [ ] My step 1 Claude message named exactly step 1 and included an explicit stop instruction.
- [ ] `go build ./...` passed after step 1 before I moved to step 2.
- [ ] `go build ./...` and `go test ./...` both passed after step 2 before I moved to step 3.
- [ ] I ran the manual smoke test (POST, GET, PATCH) after step 2.
- [ ] `go build ./...` and `go test ./...` both passed after step 3.
- [ ] Each step has its own git commit.
- [ ] `grep -n "type Task struct" *.go` returns no output after step 3.
- [ ] `grep -n "\.mu\|\.tasks\|\.nextID" handler.go` returns no output after step 2.
- [ ] I wrote the CHANGED / PRESERVED record after all steps completed.
- [ ] I can explain why deleting before migrating would have been wrong.
