# Regression Prevention

## What a regression is in AI-assisted work

A regression is a change to module A that breaks behavior in module B that was previously correct. The behavior in module B was not the subject of your prompt. You didn't ask for it to change. It changed anyway, because module A had a dependency on module B that neither you nor the model tracked.

This is not a model failure. It is a scoping failure. You passed the model a set of files and asked it to make changes. It optimized for those files. Files you didn't pass were invisible. If those invisible files had dependencies on what changed, they break — and you won't know until you run the full suite or until a user hits it in production.

---

## Why AI introduces regressions

The model sees what you show it. Context is not the full codebase — it's the files you've included in the session, the diff in the composer, or the files Claude Code read during the task.

Consequences:

- A store interface change satisfies the handler you're working on, but breaks three other handlers that implement the same interface.
- A shared utility function is modified to suit the caller you're focused on, but the other six callers relied on the old behavior.
- A config struct field is renamed, the model updates the one usage it saw, and the five usages it didn't see compile with a zero value instead of the intended default.

These are invisible from inside the session. They become visible when the test suite runs against the full codebase.

---

## The regression check

After every implementation session, run the full test suite. Not just the tests for the feature you built. All of them.

```bash
# Go
go test ./...

# Node
npm test

# Python
pytest

# Rust
cargo test
```

If any previously passing test fails, you have a regression. The implementation is not complete, regardless of how well it satisfies the feature criteria. Do not proceed to code review or merge until all previously passing tests pass again.

If you don't have a test suite, the regression check is a manual walkthrough of every affected interface. This is slower and less reliable. Invest in the test suite.

---

## The file scope check

Before a session, list the files the model will touch. After the session, verify no other files were modified.

**Before:**
```
Files this session will modify:
- internal/handler/tasks.go
- internal/handler/tasks_test.go
```

**After:**
```bash
git diff --name-only
```

Compare the two lists. Any file in the diff that is not in your before-list is an out-of-scope modification. Out-of-scope modifications require review, not just acceptance. If the modification was necessary and correct, add it to your known scope. If it was not necessary, revert it.

Out-of-scope modifications are not automatically wrong. They are automatically unreviewed. Unreviewed changes that touch working code are the source of regressions.

---

## Git as regression guard

Use git to create explicit state checkpoints around sessions.

**Before a session:**
```bash
git add -p          # stage only what belongs to the prior state
git commit -m "chore: known-good state before PATCH /tasks/:id/complete"
```

You now have a named point you can return to. The working tree is clean. Any modification the session produces shows cleanly in the diff.

**After a session:**
```bash
git diff            # review every line changed
git diff --stat     # check which files were touched
```

Do not proceed until you have reviewed this diff. The diff is the scope check and the regression surface rolled into one view.

**If scope is violated:**
```bash
git checkout -- internal/store/tasks.go   # revert one file
git restore internal/store/tasks.go        # equivalent
git reset HEAD~1                           # revert the session commit if already committed
```

Reverting a file that was modified out of scope is not a loss. The modification was unasked for and unreviewed. It is not an asset until you've reviewed it.

---

## Cursor-specific

The Composer shows a file diff before you click Accept. This is the scope check built into the tool.

Review every file in that diff before accepting:
1. Expand each file in the diff view.
2. Check that the modifications are in scope.
3. Check that no new imports were added that pull in unexpected dependencies.
4. Accept only after this review.

If Cursor modified a file you didn't expect, do not accept and then investigate. Reject, identify why the unexpected file was touched, and restate the scope in your next prompt: "Modify only `internal/handler/tasks.go`. Do not change any other file."

---

## Claude Code-specific

After an `execute-phase` completes, run the git diff before moving to verify.

```bash
git diff HEAD~1     # if the phase committed
git diff            # if working tree changes are unstaged
git diff --stat     # file-level summary first
```

Do not proceed to the verify step without reviewing the diff. The execute step is not complete until the scope check passes. The verify step tests behavior; the scope check tests that only the intended behavior was changed.

If Claude Code modified files outside the stated scope, treat this as a CRITICAL issue in the verify phase. Log it in the phase notes. Revert the out-of-scope changes before proceeding.

---

## Regression prevention summary

| Step | When | Tool |
|---|---|---|
| Commit known-good state | Before every session | `git commit` |
| List intended file scope | Before every session | written list |
| Review diff for scope | After session, before accept | `git diff --stat` + `git diff` |
| Run full test suite | After accepting output | `go test ./...` or equivalent |
| Revert out-of-scope files | When scope check fails | `git checkout -- <file>` |

---

## Session checklist

- [ ] Committed known-good state before the session started
- [ ] Listed which files the session would touch before starting
- [ ] Reviewed `git diff --stat` after the session to check file scope
- [ ] Reviewed the full `git diff` before accepting
- [ ] Reverted any out-of-scope file modifications
- [ ] Ran the full test suite after accepting output
- [ ] No previously passing tests are now failing
