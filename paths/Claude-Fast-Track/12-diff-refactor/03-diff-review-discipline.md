# Diff review discipline

Claude Code’s natural loop is **plan → execute → diff → verify → merge**. `01-refactor-ownership.md` covers refactor templates. This file covers **every** diff: blast radius scan, unexpected edits, and merge confidence.

---

## Diff ownership

| Role | Owns |
|------|------|
| **Claude** | Produces diff |
| **You** | Approve diff — what enters git history |
| **Git** | Records truth |

**You** run `/diff` or `git diff` before every commit Claude suggests. No exceptions for “small” tasks.

---

## Review workflow

```
git diff                    # or /diff
  → scan file list (unexpected paths?)
  → scan hunks per file (scope creep?)
  → map to plan task or SPEC item
  → go test / acceptance checks
  → commit or revert
```

For multi-commit waves: `git log --oneline` then `git diff <last-good>..HEAD`.

---

## Blast radius scanning

**File list first** — before reading hunks:

| Flag | Action |
|------|--------|
| File not in plan | Revert hunk or reject commit |
| `vendor/`, `go.sum` unexpected | Investigate — dependency creep? |
| Config / CI / `.github/` | Was CI task in plan? |
| Unrelated package | Scope creep |

**Hunk second** — inside allowed files:

- Logic change vs formatting-only
- New exports (widen API surface)
- Deleted tests

---

## Unexpected edits detection

| Surprise | Likely class |
|----------|--------------|
| New endpoint | Scope creep |
| Renamed symbol across packages | Refactor without template |
| Comment block essay | Low harm; still noise |
| `.env` or secret file | Security — revert immediately |

Use `13-agent-reliability/03-claude-failure-taxonomy.md` — **scope creep**, **unrelated modification**, **formatting drift**, **rename drift**, **cross-boundary edits**, **large diff instability**, **implicit architecture change**, **constraint failure**. Prevention: `04-idempotent-refactoring-discipline.md`.

---

## Review heuristics

| Heuristic | Question |
|-----------|----------|
| **Plan alignment** | Does each hunk trace to one plan task? |
| **SPEC alignment** | Any behavior not in acceptance criteria? |
| **Constraint** | stdlib-only, error shape, idempotency |
| **Test pairing** | Behavior change has test change? |
| **Minimal diff** | Could this be smaller and still correct? |

**Red flag:** diff is huge but task was “add List method” — stop and split.

---

## Boundary validation

For layered code (handler / store / domain):

- Handler diff should not embed SQL or store internals
- Store diff should not import `net/http`
- Domain types should not know HTTP status codes

Violations mean **boundary failure** — fix before next wave.

---

## Merge confidence checklist

Before PR or push:

- [ ] I reviewed full `git diff` (not Claude summary)
- [ ] Every changed file is explained by plan or SPEC
- [ ] `go build ./...` and `go test ./...` pass (or equivalent)
- [ ] Acceptance commands run for this phase
- [ ] No secrets, no `.env`, no credential files
- [ ] `/code-review` or manual review for risky changes
- [ ] `docs/state.md` updated if phase advanced

**Merge confidence** is binary: all checked or not merged.

---

## Integration with Claude commands

| Command | Use |
|---------|-----|
| `/diff` | Interactive pass before commit |
| `/review` | Second pass on risky PRs |
| `/code-review` | Correctness before merge |
| `/rewind` | Wrong turn — roll back |

Human override when diff is wrong: revert, repair prompt (`02-claude-code-workflow/07-prompt-repair-discipline.md`), re-execute one task.

---

## Checklist

- [ ] I review file list before hunks.
- [ ] I reject or revert edits outside plan/SPEC.
- [ ] I validate package boundaries in the diff.
- [ ] I do not merge on Claude’s description of the diff.
- [ ] I run merge confidence checklist before push.
