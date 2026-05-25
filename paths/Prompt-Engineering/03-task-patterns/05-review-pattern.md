# Pattern: Code Review

[Claude] Reference file by path or use `@filename` in Claude Code.
[Cursor] Use `@filename` to attach the file in Cursor chat.

```
Review <file path or diff>.
Classify each finding:
  CRITICAL — breaks correctness (wrong output, data loss, race condition)
  HIGH     — security or data integrity issue
  MEDIUM   — maintainability problem (unclear ownership, hidden coupling, missing error handling)
  LOW      — style, naming, minor inconsistency

For each finding:
  - Location: <file>:<line> or function name
  - What is wrong: <specific description>
  - What correct looks like: <concrete alternative — pseudocode or description>

Do not fix.
Report only.
```

---

## Why the template is shaped this way

**"Do not fix. Report only."**
Fixing during review mixes two concerns. The review output is a document — it must be readable, diffable, and discussable without also being a patch. When a model fixes while reviewing, the findings and the fixes blur together. You cannot accept a finding and reject its fix. You cannot share the review with a teammate. The separation is structural, not stylistic.

**Severity classification.**
Without classification, every finding lands at the same weight. "This variable name is confusing" gets equal attention as "this write is not protected by the mutex." Classification forces triage into the output — you apply HIGH+CRITICAL immediately, you decide on MEDIUM, you defer LOW.

**Location as `file:line` or function name.**
"In the handler function" is not a location. `internal/handler/task_handler.go:47` is. If a finding cannot be located exactly, it cannot be acted on. Vague location signals a vague finding — ask for specificity.

**"What correct looks like."**
Without this field, you have a complaint, not a review. "This is not thread-safe" is a complaint. "This should use `mu.Lock()` / `mu.Unlock()` around the map write at line 52" is a finding. The alternative does not have to be complete code — pseudocode or a description of the correct pattern is enough.

---

## Filled Example

[Claude]
```
Review internal/handler/task_handler.go.
Classify each finding: CRITICAL, HIGH, MEDIUM, or LOW.
For each finding:
  - Location: file:line or function name
  - What is wrong: specific description
  - What correct looks like: concrete alternative
Do not fix.
Report only.
```

[Cursor]
```
Review @task_handler.go.
Classify each finding: CRITICAL, HIGH, MEDIUM, or LOW.
For each finding:
  - Location: file:line or function name
  - What is wrong: specific description
  - What correct looks like: concrete alternative
Do not fix.
Report only.
```

Expected output shape:

```
CRITICAL — internal/handler/task_handler.go:52
What is wrong: tasks map written without lock; concurrent requests cause a data race.
What correct looks like: acquire mu.Lock() before write, defer mu.Unlock().

HIGH — CreateTask():88
What is wrong: task ID generated from math/rand without seed; collisions likely under load.
What correct looks like: use crypto/rand or google/uuid for ID generation.

MEDIUM — ListTasks():31
What is wrong: returns nil on empty store; callers must nil-check or panic.
What correct looks like: return empty slice ([]Task{}) for consistent JSON serialization.

LOW — task_handler.go:12
What is wrong: package-level var for store makes dependency implicit.
What correct looks like: inject store via constructor or handler struct.
```

---

## How to Use the Output

After receiving the review:

1. **CRITICAL** — fix before any further development. Non-negotiable.
2. **HIGH** — fix before merging. Security and data integrity issues compound.
3. **MEDIUM** — decide: fix now or create a tracked issue. Do not silently defer.
4. **LOW** — decide: batch into a style pass or defer. Do not let LOW findings block shipping.

When fixing, use the bug-fix pattern (02) for each CRITICAL/HIGH finding — one fix per finding, hypothesis stated, verification command named.

---

## What to Reject

| Signal | Why it's wrong |
|---|---|
| Finding without severity label | Cannot triage; ask for classification |
| "This could be improved" without specifics | Not a finding; ask for location and what correct looks like |
| Finding that includes a code fix inline | Mixes review and implementation; request report-only version |
| All findings are LOW or MEDIUM when a race condition is present | Under-severity; push back on classification |
| "The code looks good overall" with no findings | Not a review; send with explicit instruction to look for specific concerns |
| Findings numbered but unsorted — CRITICAL buried after 12 LOWs | Ask for output sorted by severity descending |

---

## Checklist

- [ ] File or diff is referenced by path, not pasted as text in the prompt
- [ ] Prompt specifies all four severity levels with their definitions
- [ ] Prompt specifies the three fields for each finding: location, what is wrong, what correct looks like
- [ ] Prompt includes "do not fix"
- [ ] Prompt includes "report only"
- [ ] After output: every finding has a severity label
- [ ] After output: every finding has an exact location
- [ ] After output: every finding has a concrete alternative (not a complaint)
- [ ] After output: CRITICAL and HIGH findings addressed before proceeding
- [ ] MEDIUM findings either fixed or tracked; LOW findings explicitly deferred
