# Pattern: Fixing a Bug

```
Bug: <observed behavior — exact, not interpreted>.
Expected: <correct behavior per spec or failing test>.
Hypothesis: <one sentence — specific code location and mechanism>.
Fix only the hypothesis.
Do not refactor unrelated code.
After the fix, verify with: <exact command>.
```

---

## Why the template is shaped this way

**You must state the hypothesis.**
Without it, the model treats the bug as open-ended. It searches for "improvements," "potential issues," "related problems." The result is a diff that touches five things, one of which is the bug. You cannot tell which fix did the work. You cannot revert safely.

The hypothesis pins the fix to one mechanism. If the hypothesis is wrong, the fix is small and reversible. If it is right, the fix is small and verifiable.

**Observed vs. expected — exact, not interpreted.**
"Returns wrong status" is interpreted. "Returns 404, expected 200" is exact. The model cannot drift on an exact description.

**"Per spec or failing test."**
The correct behavior must be sourced from a ground truth — not from your intuition. If a test already describes the correct behavior, reference it. If the spec does, reference it. "I expected it to return 200" is not a source. `internal/handler/task_handler_test.go:TestGetTask_found` is.

**"Do not refactor unrelated code."**
Explicit. Without this, the model will "clean up" surrounding code while fixing the bug. The cleanup is well-intentioned and hard to review. Reject it.

**Verification command.**
Every fix needs a falsifiable check. If you cannot name the command before fixing, you do not understand the bug yet. The model cannot verify its own work without it — but it will confidently claim success anyway.

---

## Filled Example

Bug: `POST /tasks` returns 404 when creating a new task. Expected: 201 with the created task body.

Hypothesis: the route is registered under `/task` (singular) in `router.go`, but the handler is mounted at `/tasks` (plural).

Prompt:

```
Bug: POST /tasks returns 404. Request body is valid JSON.
Expected: 201 with created task body, per docs/specs/post-tasks.md.
Hypothesis: route registered as /task (singular) in internal/router/router.go, handler mounted at /tasks (plural).
Fix only the hypothesis.
Do not refactor unrelated code.
After the fix, verify with: go test ./internal/handler/... -run TestPostTask -v
```

Expected diff: one line in `router.go` — the route path string.

---

## What to Reject

| Signal | Why it's wrong |
|---|---|
| Diff touches files not mentioned in the hypothesis | Fix is wider than the hypothesis; cannot verify scope |
| Handler logic rewritten "while we're here" | Unauthorized refactor; revert |
| Test added that matches the (possibly wrong) implementation | Test derived from code, not spec |
| No verification command in the output | Unverifiable fix; ask for one before accepting |
| "I also noticed..." followed by additional changes | Additional changes are out of scope; separate ticket |
| Hypothesis changed in the output without explanation | Model decided your diagnosis was wrong; challenge it or confirm before accepting |

---

## Checklist

- [ ] Observed behavior is exact (specific status code, specific error message)
- [ ] Expected behavior is sourced from spec or failing test — not intuition
- [ ] Hypothesis names specific file and mechanism (not "somewhere in the handler")
- [ ] Prompt includes "fix only the hypothesis"
- [ ] Prompt includes "do not refactor unrelated code"
- [ ] Verification command is specified before sending the prompt
- [ ] After output: diff is limited to what the hypothesis predicted
- [ ] After output: verification command passes
- [ ] After output: no test files modified to match new behavior
