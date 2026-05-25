# Binary Criteria

## "Looks good" is not a criterion

"Looks good" is a feeling. Feelings don't survive a second session, a code review, or a Monday morning. When you accept output because it looks right, you're outsourcing the definition of correct to your current mood. The next time you look at the code, the feeling is gone and the criterion never existed.

A criterion is a checkable condition. Either the output satisfies it or it doesn't. No interpretation. No judgment call. No "I think this is what I meant."

---

## Binary criteria defined

A binary criterion has one valid outcome: pass or fail.

**Binary:** "The function returns `nil, ErrNotFound` when the record does not exist in the store."
**Not binary:** "The function handles the not-found case cleanly."

Binary criteria require zero inference. Someone who has never seen your codebase, given only the criterion, can look at the output and produce the same pass/fail verdict you would.

---

## Write criteria before asking, not after

Criteria written after output are retrofitted. They bend to fit what was produced, not what was needed. This defeats the entire purpose.

The sequence is:
1. Write the criteria.
2. Send the prompt.
3. Check the output against the criteria.

Not:
1. Send the prompt.
2. Read the output.
3. Decide what you wanted.

If you can't write the criteria before sending the prompt, you don't yet know what you want. Stop. Define the output before requesting it.

---

## The 60-second test

A criterion passes the 60-second test if you can verify it in under 60 seconds using only the criterion text and the output.

**Passes the test:**
"The `Patch` handler returns HTTP 400 when `completed_at` is missing from the request body."
→ You can check this by reading the handler and tracing the validation path. 60 seconds.

**Fails the test:**
"The handler is well-structured and follows best practices."
→ This requires you to define "well-structured" before you can check anything. Rewrite it.

If your criterion requires you to know what you were thinking when you wrote it, it fails the test. Rewrite it until the criterion is self-contained.

---

## Non-binary vs binary by output type

### Code implementation

| Non-binary | Binary |
|---|---|
| "Validates input correctly" | "Returns HTTP 422 when `title` field is absent from the request body" |
| "Handles errors properly" | "Wraps all database errors with `fmt.Errorf(\"store: %w\", err)` before returning" |
| "Is readable" | "Has no function longer than 30 lines" |

### Test suite

| Non-binary | Binary |
|---|---|
| "Tests the happy path" | "Has a test case that sends a valid request and asserts HTTP 200 with the updated resource in the body" |
| "Good coverage" | "`go test ./... -cover` reports ≥ 80% statement coverage for `internal/handler`" |
| "Tests edge cases" | "Has a test case for each of: missing field, invalid type, resource not found" |

### Config file

| Non-binary | Binary |
|---|---|
| "Looks correct" | "`yamllint config.yml` exits 0 with no warnings" |
| "Properly structured" | "Contains exactly the keys: `server.port`, `db.dsn`, `log.level`; no others" |

### Refactored function

| Non-binary | Binary |
|---|---|
| "Cleaner than before" | "The function has no more than one level of nesting inside the loop body" |
| "Same behavior" | "All existing tests for this function pass without modification after the refactor" |

---

## Pre-prompt checklist

> Use this block before sending any implementation request.

```
Before sending this prompt, I can state:

[ ] Criterion 1: ___________________________________________________
    Can verify in 60 seconds using only this text? [ ] Yes  [ ] No

[ ] Criterion 2: ___________________________________________________
    Can verify in 60 seconds using only this text? [ ] Yes  [ ] No

[ ] Criterion 3: ___________________________________________________
    Can verify in 60 seconds using only this text? [ ] Yes  [ ] No

If any criterion has "No" checked, rewrite it before proceeding.
If you cannot produce 3 criteria, the prompt is not ready.
```

Three is the floor, not the ceiling. Large requests need more. But if you can't produce three, you don't know what you're asking for.

---

## Connection to SPEC acceptance criteria

If you use GSD or Fast-Track, the acceptance criteria in your SPEC.md are exactly this. The spec-first workflow forces you to write binary criteria before any code is generated — that's the mechanism that makes it work.

If you're not using a spec workflow, the pre-prompt checklist above is the minimal equivalent. Same concept, applied at the prompt level instead of the phase level.

The principle is the same either way: the definition of done must exist before the work starts, and it must be checkable without interpretation.

---

## Session checklist

- [ ] Wrote 3 binary criteria before sending the implementation prompt
- [ ] Each criterion states a checkable condition, not a quality feeling
- [ ] Each criterion passes the 60-second test
- [ ] Criteria were written before reading any output, not retrofitted after
- [ ] Non-binary criteria were identified and rewritten
