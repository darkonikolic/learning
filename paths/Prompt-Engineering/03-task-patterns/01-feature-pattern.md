# Pattern: Implementing a New Feature

```
Implement <feature name> per <path/to/spec.md>.
Boundary: only touch files listed in the spec's boundary section.
Stop after implementation.
Do not write tests.
Do not add behavior not described in the spec.
```

---

## Why the template is shaped this way

**Spec on disk, referenced by path — not paraphrased.**
Paraphrasing introduces drift. The moment you summarize the spec in the prompt, you become the source of truth, and any gap in your summary becomes a gap in the implementation. The model reads the file; it does not rely on your memory of it.

**"Stop after implementation."**
Without this, the model will write tests. The problem: those tests are derived from the implementation, not the spec. A bug in the implementation produces a passing test. Tests must come from the spec — written separately, after the feature is in.

**"Do not add behavior not described in the spec."**
Models improve. They infer. They add "helpful" validations, extra fields, convenience methods. Every one of these is unreviewed scope. Reject them.

**Boundary section in the spec.**
The spec must name which files may be created or modified. This is the blast radius. If a file appears in the diff that is not in the boundary list, the output is out of scope regardless of correctness.

---

## Filled Example

Spec file: `docs/specs/get-tasks.md`

```
Boundary:
  create: internal/handler/task_handler.go
  modify: internal/router/router.go
  do not touch: store/, main.go, go.mod

GET /tasks
- Returns 200 with JSON array of all tasks
- Empty list returns 200 with []
- No filtering, no pagination
- Task shape: { id: string, title: string, done: bool }
```

Prompt sent to Claude Code or Cursor:

```
Implement GET /tasks per docs/specs/get-tasks.md.
Boundary: only touch files listed in the spec's boundary section.
Stop after implementation.
Do not write tests.
Do not add behavior not described in the spec.
```

Expected output: changes to `task_handler.go` and `router.go` only.

---

## What to Reject

| Signal | Why it's wrong |
|---|---|
| New file outside the boundary section | Out-of-scope change; reject regardless of quality |
| Test file created | Tests derived from code, not spec; delete and re-run from spec |
| Extra fields added to response struct | Unreviewed behavior; not in spec |
| Validation logic added that spec doesn't mention | Scope creep; remove |
| Comment: "I also updated X for consistency" | Not authorized; revert |
| go.mod or go.sum modified without being in boundary | Unauthorized dependency; reject |

---

## Checklist

- [ ] Spec file exists on disk before sending the prompt
- [ ] Spec has a boundary section listing exact file paths
- [ ] Prompt references the spec by path, not by description
- [ ] Prompt includes "stop after implementation"
- [ ] Prompt includes "do not write tests"
- [ ] Prompt includes "do not add behavior not in spec"
- [ ] After output: diff contains only files in the boundary section
- [ ] After output: no test files created
- [ ] After output: no behavior present that spec doesn't describe
