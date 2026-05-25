# Constraint Failure

## Detection signals

- A package you prohibited appears in an import block
- A file you said not to touch has a diff
- A dependency was added when you said stdlib-only
- The model added an abstraction layer you explicitly excluded
- Output is correct for the happy path but the constraint applied to edge cases is ignored
- The constraint is present in the previous prompt; it is absent from the behavior

---

## Why it happens

Three causes, in order of frequency:

1. **Soft language.** "Prefer", "try to", "where possible", "ideally", "avoid if you can" — these are not constraints. They are suggestions the model weighs against other factors and may override.

2. **Buried rule.** A constraint in the middle of a 12-line prompt competes with everything around it. The model's attention is not uniform. Rules at position 6 of 10 lose.

3. **Implicit assumption conflict.** The model has a strong prior about how to solve this class of problem. "Add search to the task API" carries an implicit assumption that you'll use a query library. Your constraint ("stdlib only") conflicts with that prior. The prior wins unless the constraint is stated louder.

---

## Three reinforcement techniques

### 1. Move the constraint to the first line

```
# Weak (buried)

Add a search endpoint to the task API.
It should return tasks matching a query string.
Keep it simple and readable.
Do not import any external packages — use stdlib only.
Add tests.

# Strong (first line)

CONSTRAINT: stdlib only — no external packages.

Add a GET /tasks?q= endpoint that returns tasks whose title contains q
as a case-insensitive substring. Use strings.Contains. Add tests.
```

### 2. Make it binary (must / must not)

Replace all soft qualifiers with hard ones:

| Soft | Hard |
|------|------|
| `prefer stdlib` | `must use stdlib only` |
| `try not to touch other files` | `must not modify any file outside internal/task/` |
| `avoid global state` | `must not use any package-level variables` |
| `keep it simple` | `must not introduce any new interfaces` |

Soft language gives the model a decision to make. Binary language removes the decision.

### 3. Add a verification step

After stating the constraint, add an explicit self-audit:

```
After implementing, list every external package you imported.
The list must be empty.
If it is not empty, stop and revise before showing me the code.
```

This is the most reliable technique. It forces the model to check its own output against the constraint before you see it. Models catch their own violations when asked to audit explicitly.

---

## When the rule is violated

Do not continue. Do not try to patch the violation inline.

1. **Revert the change.** In Claude Code: `git checkout -- .`. In Cursor: reject the diff.
2. **Tighten the constraint.** Binary + first-line + verification step.
3. **Restart with the hardened prompt.**

Building on a constraint violation produces output that assumes the violation is acceptable. The next turn digs the hole deeper.

---

## Examples

### Example 1: stdlib-only violated

```
# Before (failed)

Add an in-memory cache for GET /tasks results.
Cache should expire after 60 seconds.
Use stdlib only.

# After (hardened)

CONSTRAINT: must use stdlib only — must not import any package outside
the Go standard library. If you need a cache, implement it with sync.Map
and time.Now(). Do not use github.com/patrickmn/go-cache or any other
external package.

Add an in-memory cache for GET /tasks.
After implementing, list every import. The list must contain only stdlib packages.
```

### Example 2: file boundary violated

```
# Before (failed)

Refactor the task search logic to be more testable.

# After (hardened)

CONSTRAINT: must not modify any file outside internal/task/query.go.
Do not touch handlers, models, or main.go.

Extract the filter logic in internal/task/query.go into a pure function
that takes a []Task and a string query and returns []Task.
After implementing, list every file you modified. The list must contain
only internal/task/query.go.
```

---

## Prevention

Append this block to any prompt that has a hard constraint:

```
Constraints (non-negotiable):
- [constraint 1 as must/must not statement]
- [constraint 2 as must/must not statement]

Verification: after implementing, confirm each constraint above was followed.
List any constraint you could not follow and why.
```

The verification step creates an accountability checkpoint. If the model cannot follow a constraint, it will say so before you discover it in review — which is the outcome you want.

---

## Checklist

- [ ] Every constraint stated as must/must not — no soft qualifiers
- [ ] Constraint appears on the first line or in a clearly marked block
- [ ] Verification step added: model asked to audit its own output
- [ ] On violation: change reverted before continuing
- [ ] Tightened prompt used on restart, not the original
- [ ] Binary constraint confirmed in generated import list or file diff
