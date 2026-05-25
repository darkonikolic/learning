# Lab: Diagnose a Failing Prompt

Four broken prompt+output pairs from a Go task API project. For each:
1. Identify the failure mode
2. Write the diagnosis
3. For cases 2 and 4: write the recovery prompt
4. Apply the prevention technique for all four

---

## Setup: the codebase context

```
task-api/
  internal/
    task/
      model.go       — type Task struct { ID int; Title string; Done bool }
      query.go       — func List(ctx context.Context) ([]Task, error)
      store.go       — SQLite-backed persistence
    api/
      task_handler.go — HTTP handlers, uses task.List
  main.go
  go.mod             — module task-api, no external dependencies
```

---

## Case 1

**Prompt:**
```
Add filtering to the task list endpoint.
```

**Output:**
The model added `GET /tasks?done=true` to filter by completion status. It implemented `done=true` and `done=false` query params with correct SQL.

**Your intent:** you wanted to filter by keyword in the title.

---

### Diagnosis format

```
Failure mode: [ambiguity | hallucination | constraint failure | context drift]
What was invented or misread: [specific statement]
Why the model's behavior was reasonable: [explain the model's valid interpretation]
What broke: [what you got vs what you needed]
```

**Fill this in before reading further.**

<details>
<summary>Reference diagnosis</summary>

```
Failure mode: ambiguity
What was misread: "filtering" permits filtering by status, title, tag, date, or any field
Why the model's behavior was reasonable: filtering by done/undone is the most common task-list
  filter pattern; the model produced a fully correct implementation of a valid interpretation
What broke: the endpoint filters by completion status; you needed title substring search
```

</details>

---

## Case 2

**Prompt:**
```
Refactor task.List to support a filter argument so the handler can pass search criteria.
```

**Output (turn 1):** Model added `func List(ctx context.Context, f Filter) ([]Task, error)` where `Filter` is a new struct. Handler updated correctly. Build passes.

**Turn 2 prompt:**
```
Now add the title search — filter by substring match on Title.
```

**Turn 2 output:**
```go
import "github.com/jmoiron/sqlx"

func (s *Store) Search(ctx context.Context, q string) ([]Task, error) {
    return sqlx.SelectContext(ctx, s.db, &results,
        "SELECT * FROM tasks WHERE title LIKE ?", "%"+q+"%")
}
```

`sqlx` is not in go.mod. The `Store` type has no `db` field. `sqlx.SelectContext` does not exist with this signature.

---

### Your tasks for Case 2

**2a. Diagnosis:**
```
Failure mode:
What was invented:
Why the model's behavior was reasonable:
What broke:
```

**2b. Recovery prompt** — write a prompt that will produce correct output. Include:
- Identification of what was invented
- The real types/functions to use (from the codebase description above)
- The grounding instruction

<details>
<summary>Reference diagnosis</summary>

```
Failure mode: hallucination
What was invented: sqlx package (not in go.mod), Store.db field (doesn't exist in store.go),
  sqlx.SelectContext signature (invented API)
Why reasonable: sqlx is a common Go database package; the model generated a statistically
  plausible database layer
What broke: code does not compile; imports a nonexistent package; calls a nonexistent method
```

</details>

<details>
<summary>Reference recovery prompt</summary>

```
Do not use sqlx — it is not in go.mod and must not be added.

The real store is in internal/task/store.go. It uses database/sql directly.
The Store struct has a field `db *sql.DB`. Use db.QueryContext for queries.

Add a search method to Store that accepts a query string and returns []Task
filtered by case-insensitive substring match on Title. Use:
  db.QueryContext(ctx, "SELECT id, title, done FROM tasks WHERE title LIKE ?", "%"+q+"%")

Verify: list every import you use. All must be stdlib. List every method you call on
Store.db — all must be methods on *sql.DB.
```

</details>

---

## Case 3

**Session turn 1 prompt:**
```
CONSTRAINT: must not modify task_handler.go.

Add a ListByTitle function to internal/task/query.go that filters tasks by
title substring. Return []Task. No new packages.
```

**Turn 1 output:** Correct. `query.go` updated. `task_handler.go` untouched. Build passes.

**Turn 6 prompt** (after 4 turns of debugging an unrelated test):
```
Wire the ListByTitle function into the search endpoint.
```

**Turn 6 output:** Model modifies `task_handler.go` to add the search route, and also modifies `main.go` to register it.

---

### Diagnosis format

```
Failure mode:
What changed between turn 1 (followed constraint) and turn 6 (violated it):
Evidence that this is not constraint failure:
What broke:
```

**Fill this in before reading further.**

<details>
<summary>Reference diagnosis</summary>

```
Failure mode: context drift
What changed: after 4 intervening turns, the early constraint on task_handler.go has been
  compressed; "wire it in" carries an implicit assumption that the handler needs to change
Evidence this is not constraint failure: the constraint was binary and first-line; the model
  followed it correctly in turn 1 when it was at full weight
What broke: task_handler.go was modified in violation of the constraint; main.go was also
  touched (never constrained, but unexpected)
```

</details>

---

## Case 4

**Prompt:**
```
The task list endpoint is slow. Make it faster.
```

**Output:** Model added an in-memory LRU cache using `github.com/hashicorp/golang-lru/v2`. Rewrote the handler to check the cache before querying the store. Cache TTL logic added.

go.mod was not in the prompt context. There is no existing caching infrastructure. The model assumed an external package was acceptable and that LRU was the right strategy.

---

### Your tasks for Case 4

**4a. Diagnosis:**
```
Failure mode: (there are two here — name both)
Constraint violated (implicit):
What was assumed without being stated:
What broke:
```

**4b. Recovery prompt** — write a prompt that will produce a correct, stdlib-only in-memory cache for the task list.

<details>
<summary>Reference diagnosis</summary>

```
Failure mode: ambiguity + constraint failure (implicit constraint)
Ambiguity: "make it faster" has many valid implementations — caching, query optimization,
  index hints, pagination, response compression
Constraint violated: stdlib-only is implicit in a project with no external deps; the model
  did not know this without being told
What was assumed: LRU is the right cache strategy; external packages are acceptable
What broke: external package imported; cache strategy chosen without input; handler
  rewritten without scoped instruction
```

</details>

<details>
<summary>Reference recovery prompt</summary>

```
CONSTRAINT: stdlib only — must not import any package outside the Go standard library.
CONSTRAINT: changes must be limited to internal/task/query.go and internal/api/task_handler.go.

Performance goal: cache the result of task.List in memory for 30 seconds.
Use sync.Map to store the cache entry. Use time.Now() to track expiry.
Invalidation: clear the cache on any successful task creation or deletion.

Do not use github.com/hashicorp/golang-lru or any other external cache library.

After implementing, list every import across all modified files.
All imports must be stdlib. If any are not, revise before showing me the code.
```

</details>

---

## Prevention application

For each case, write the prevention technique you would apply to the *next* task of the same type.

| Case | Prevention technique | What you'd add |
|------|---------------------|----------------|
| 1 | Two-interpretation test | Before prompting: "what are the two most different ways to implement filtering?" |
| 2 | Grounding instruction | Add to prompt: "verify each function exists before using it; if unsure, ask" |
| 3 | Constraint anchor | Append to every turn: `Anchor: must not modify task_handler.go` |
| 4 | Binary constraint + verification step | First line: `CONSTRAINT: stdlib only`; end: "list every import — must be stdlib" |

---

## Checklist

- [ ] All four failure modes identified correctly
- [ ] Case 2 diagnosis names specific invented symbols
- [ ] Case 2 recovery prompt includes real types/functions as replacements
- [ ] Case 3 diagnosis distinguishes context drift from constraint failure
- [ ] Case 4 diagnosis names both failure modes
- [ ] Case 4 recovery prompt includes binary constraint + verification step
- [ ] Prevention technique written for all four cases
- [ ] Each prevention technique matches the specific failure mode (not generic)
