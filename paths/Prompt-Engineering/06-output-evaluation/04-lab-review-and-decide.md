# Lab: Review and Decide

**Task:** Add `PATCH /tasks/:id/complete` to a Go task API.

Work through all six steps below. Do not read ahead to the answers — the value is in doing the classification before you see the discussion.

---

## Step 1: Write 3 binary criteria

Before looking at any output, write 3 binary criteria for correct implementation of `PATCH /tasks/:id/complete`.

The endpoint should mark a task as complete by setting `completed_at` to the current UTC time. The task is stored in a Postgres database. The handler lives in `internal/handler/tasks.go`.

Write your criteria here:

```
Criterion 1: ___________________________________________________

Criterion 2: ___________________________________________________

Criterion 3: ___________________________________________________
```

**Reference criteria** (compare against yours after you've written your own):

```
Criterion 1: The handler returns HTTP 404 when no task with the given ID
             exists in the store.

Criterion 2: The handler sets completed_at to time.Now().UTC() on the
             matching task and persists it via the store before returning.

Criterion 3: The handler returns HTTP 200 with the updated task as JSON
             when the operation succeeds.
```

---

## Step 2: Sample output

This is the output a model produced for the task.

```go
// internal/handler/tasks.go (excerpt — CompleteTask handler added at end of file)

func (h *Handler) CompleteTask(w http.ResponseWriter, r *http.Request) {
    idStr := chi.URLParam(r, "id")
    id, err := strconv.Atoi(idStr)
    if err != nil {
        http.Error(w, "invalid task id", http.StatusBadRequest)
        return
    }

    task, err := h.store.GetTask(id)
    if err != nil {
        // return the raw error so the client can see what went wrong
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }

    task.CompletedAt = time.Now().UTC()
    if err := h.store.UpdateTask(task); err != nil {
        http.Error(w, "failed to update task", http.StatusInternalServerError)
        return
    }

    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(http.StatusOK)
    json.NewEncoder(w).Encode(task)
}

// internal/store/tasks.go (modified — GetTask function updated)

func (s *Store) GetTask(id int) (*Task, error) {
    var t Task
    err := s.db.QueryRowContext(
        context.Background(),
        "SELECT id, title, completed_at FROM tasks WHERE id = $1",
        id,
    ).Scan(&t.ID, &t.Title, &t.CompletedAt)
    if err == sql.ErrNoRows {
        return nil, ErrNotFound
    }
    if err != nil {
        return nil, fmt.Errorf("store.GetTask: %w", err)
    }
    return &t, nil
}
```

Additionally, the model modified `go.mod` to add `github.com/go-chi/chi/v5 v5.0.10` — chi was already present in the project at v5.0.8.

---

## Step 3: Classify each issue

Identify the issues in the sample output and classify each with a severity.

**Issues present:**

1. The handler calls `http.Error(w, err.Error(), http.StatusInternalServerError)` when `h.store.GetTask` returns an error — including when it returns `ErrNotFound`. The client receives HTTP 500 with the internal error message when the task doesn't exist.

2. `internal/store/tasks.go` was modified. This file was not in the stated scope for this session.

3. `go.mod` was modified to bump the chi version from v5.0.8 to v5.0.10. This was not requested.

**Classification table — fill in before reading the key:**

| # | Issue | Your Severity | Correct Severity |
|---|---|---|---|
| 1 | HTTP 500 + raw error when task not found | | |
| 2 | `internal/store/tasks.go` modified out of scope | | |
| 3 | `go.mod` chi version bumped without request | | |

**Severity key:**

| # | Correct Severity | Reasoning |
|---|---|---|
| 1 | CRITICAL | Criterion 1 fails (HTTP 404 not returned for missing task). Additionally, raw internal error messages are exposed to the client — this is a security and correctness failure. |
| 2 | HIGH | An out-of-scope modification to a store file introduces regression risk across every caller of `GetTask`. The modification may or may not be correct, but it is unreviewed and out of scope. |
| 3 | MEDIUM | A dependency version bump in `go.mod` changes the behavior surface of an existing dependency without a stated reason. It won't break compilation, but it's unasked-for and may introduce behavioral changes from the version delta. |

---

## Step 4: Accept / reject / correct decisions

Apply the decision rules from `02-review-discipline.md`.

| # | Severity | Decision |
|---|---|---|
| 1 | CRITICAL | Reject. Do not accept the handler. |
| 2 | HIGH | Revert `internal/store/tasks.go` to the prior state before proceeding. |
| 3 | MEDIUM | Decide explicitly. Either revert `go.mod` to v5.0.8 or accept the bump with a recorded rationale. Do not let it pass silently. |

The overall verdict for this output: **Reject.** A CRITICAL issue is present. The handler is not accepted.

---

## Step 5: Write the correction prompt

Using the structure from `02-review-discipline.md`, write the correction prompt for Issue 1.

**Template:**
```
Output accepted except: [specific issue at specific location].
Fix only this. Do not change anything else.
```

**Your correction prompt:**

```
(write here before reading the reference)
```

**Reference correction prompt:**

```
Output accepted except: the CompleteTask handler at
internal/handler/tasks.go does not distinguish between a not-found error
and other store errors. When h.store.GetTask returns ErrNotFound, the
handler should return HTTP 404 with the body "task not found". When it
returns any other error, the handler should return HTTP 500 with the body
"internal error" — not the raw error message.

Fix only this error-handling block. Do not change the update logic, the
response encoding, or anything in the store layer. Do not change anything
else.
```

---

## Step 6: Regression check

List which files the sample output touched. Identify which file(s) should not have been touched.

**Files touched by the sample output:**

```
1. internal/handler/tasks.go     — in scope
2. internal/store/tasks.go       — NOT in scope
3. go.mod                        — NOT in scope
```

**Regression check actions:**

```bash
# Before this session, you should have committed a known-good state:
git log --oneline -3
# e.g.: abc1234 chore: known-good state before PATCH /tasks/:id/complete

# After the session, check what actually changed:
git diff --stat
# internal/handler/tasks.go  | 22 ++++++++++++++++++++++
# internal/store/tasks.go    |  8 ++++----
# go.mod                     |  2 +-

# Revert the out-of-scope files before accepting anything:
git checkout -- internal/store/tasks.go
git checkout -- go.mod

# Verify the revert:
git diff --stat
# internal/handler/tasks.go  | 22 ++++++++++++++++++++++

# Now run the full test suite against the handler-only change:
go test ./...
```

If `go test ./...` surfaces failures in files other than `internal/handler`, you have a regression. The handler change (even with the CRITICAL bug) has affected something else. Investigate before proceeding.

---

## Pre-prompt checklist (reusable)

```
Before sending this prompt, I can state:

[ ] Criterion 1: ___________________________________________________
    Can verify in 60 seconds using only this text? [ ] Yes  [ ] No

[ ] Criterion 2: ___________________________________________________
    Can verify in 60 seconds using only this text? [ ] Yes  [ ] No

[ ] Criterion 3: ___________________________________________________
    Can verify in 60 seconds using only this text? [ ] Yes  [ ] No

Files this session will touch:
[ ] ___________________________________________________
[ ] ___________________________________________________

If any criterion has "No" checked, rewrite it before proceeding.
If you cannot produce 3 criteria, the prompt is not ready.
```

---

## Lab checklist

- [ ] Wrote 3 binary criteria before reading the sample output
- [ ] Read the full sample output before classifying any issues
- [ ] Classified Issue 1 as CRITICAL (HTTP 404 not returned, raw error exposed)
- [ ] Classified Issue 2 as HIGH (out-of-scope store modification)
- [ ] Classified Issue 3 as MEDIUM (unrequested dependency version bump)
- [ ] Made explicit accept/reject decision: Reject (CRITICAL present)
- [ ] Wrote a correction prompt using the structure: "Output accepted except: [issue at location]. Fix only this. Do not change anything else."
- [ ] Identified `internal/store/tasks.go` and `go.mod` as out-of-scope modifications
- [ ] Listed the git commands to revert out-of-scope files before accepting
- [ ] Confirmed the regression check requires running `go test ./...` after reverting
