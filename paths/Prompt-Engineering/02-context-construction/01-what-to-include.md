# What to Include in Context

## File References Beat Inline Text

Paste nothing. Reference paths.

When you paste code into the prompt you create a second copy the model treats as potentially stale. Reference the source of truth instead.

```
# Bad — you've now got two versions in context
Here is my handler:
func CreateTask(w http.ResponseWriter, r *http.Request) {
    // 40 lines
}
Now add validation.

# Good — one source of truth
Add input validation to the CreateTask handler in internal/api/tasks.go
```

[Claude] The agent reads files via the Read tool at session start or inline in a message. Say "read internal/api/tasks.go" or reference it — Claude will read it. Pasting it creates drift the moment the file is edited.

[Cursor] Use `@tasks.go` or `@internal/api/tasks.go` in the composer. Cursor fetches the current file state. Pasting forces Cursor to work from a potentially outdated snapshot.

---

## Minimum Required Context for Any Task

Three things. If any one is missing the model fills it in by guessing.

**1. The relevant file(s)**
The actual file(s) the task touches. Not the whole module — the file(s).

**2. The constraint or spec**
What rules apply to this task. Language, library restrictions, error handling style, conventions from the codebase. If it exists in a config or CLAUDE.md, say so; don't re-paste it.

**3. What "done" looks like**
An acceptance criterion or output shape. Not a general description — a specific outcome.

```
# Complete minimum context example
File: internal/api/tasks.go
Constraint: stdlib only, no frameworks, errors wrapped with fmt.Errorf("%w")
Done: PATCH /tasks/:id/complete returns 200 with updated task JSON, 404 if id missing, 400 if already complete
```

That's it. Everything else is noise unless the task touches it.

---

## What to Exclude

**Test files** — unless you're writing or fixing tests. Including `tasks_test.go` when adding an endpoint causes the model to consider the test structure when generating code, often producing code that mirrors existing test patterns rather than the actual requirement.

**Unrelated modules** — if the task is in `internal/api`, don't include `internal/store` unless the task explicitly calls into it.

**Config files not touched by the task** — `go.mod`, `.env`, `Makefile`. These get read and occasionally echo back into generated code (e.g. the model copies a library version number into a comment).

**Other endpoints or handlers in the same file** — if the file has 10 handlers and you're touching one, say which one. The model will still have the file; you don't need to call attention to the other 9.

---

## The Context Pollution Failure

Passing too many files causes the model to use them even when not needed.

```
# This prompt will produce output that mixes store logic into the handler:
Add PATCH /tasks/:id/complete
@tasks.go @store.go @config.go @middleware.go @auth.go @models.go
```

The model sees `store.go` and treats it as relevant. It will likely add store calls, import patterns, or error handling from `store.go` even if the spec says the handler should be simple.

**Pattern**: every file you include gets weighted as "probably relevant." The model doesn't have a way to confirm a file is decorative context.

The fix: include only what the task directly mutates or calls. If `store.go` is needed because the handler calls the store, include it. If not, exclude it.

---

## Minimum Viable Context

The smallest set that lets the model complete the task without guessing.

Test it this way: read back your context prompt and ask — "what would the model have to invent to complete this?" If the answer is "nothing", you have minimum viable context. If the answer is "the error response format" or "whether to use stdlib or a library", add that.

```
# Minimum viable — nothing left to guess
Task: add GET /tasks endpoint
File: internal/api/tasks.go (read it)
Constraint: stdlib only, respond with JSON array, empty array not null on no results
Done: returns 200 with []Task JSON, errors return {"error": "..."} with appropriate status
```

```
# Under-specified — model guesses the response format
Task: add GET /tasks endpoint
```

```
# Over-specified — includes irrelevant material
Task: add GET /tasks endpoint
Files: tasks.go, tasks_test.go, store.go, models.go, config.go, main.go, go.mod
```

---

## Tool-Specific Notes

[Claude] At session start, list files you want Claude to read before any task. Claude will read them once and hold them in context. Avoid re-reading mid-session unless the file changes.

```
Read these files before we start:
- internal/api/tasks.go
- internal/store/memory.go
```

[Cursor] Open the relevant files in the editor before starting a composer session. Use `@filename` to pin them. Cursor's context window is smaller — be stricter about exclusions.

---

## Checklist

- [ ] All file references point to paths, not pasted content
- [ ] Three elements present: relevant file(s), constraint, done condition
- [ ] Test files excluded (unless writing tests)
- [ ] Unrelated modules excluded
- [ ] Config files excluded unless the task modifies them
- [ ] Each included file has a reason to be there
- [ ] Nothing left for the model to guess
- [ ] [Cursor] Files opened in editor before composer session
- [ ] [Claude] Files listed for reading at session start
