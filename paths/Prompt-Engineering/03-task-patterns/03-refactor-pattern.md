# Pattern: Safe Refactoring

```
Refactor: <what is moving and where>.

CURRENT STATE:
<describe current structure — file, function, or package>

TARGET STATE:
<describe end structure — file, function, or package>

STEPS:
1. <atomic step — must compile and pass tests after this step alone>
2. <atomic step — must compile and pass tests after this step alone>
...

VALIDATION after each step: go build ./... && go test ./...

Do not combine steps.
Do not rewrite the file to be "cleaner."
Do not change behavior.
```

---

## Why the template is shaped this way

**The incremental rule.**
Each step must leave the codebase in a working state independently. No "we'll fix the broken reference in step 3." If step 2 breaks the build, step 2 is wrong — stop, diagnose, rewrite step 2. This rule makes refactors reviewable and revertable at any point.

**CURRENT STATE / TARGET STATE.**
Refactoring is moving code, not rewriting it. Naming the current structure and the target structure eliminates ambiguity about what the model is authorized to change. Everything outside that scope is off-limits.

**Validation after each step.**
`go build ./... && go test ./...` is the gate. Not "I think it compiles." Not "the main logic looks right." The gate is binary. Run it after each step before proceeding.

**"Do not rewrite the file to be cleaner" — why this is explicitly forbidden.**
This is the most common refactor failure. The model sees messy code and cannot resist improving it. The "clean rewrite" has a different diff shape than a mechanical move. It is hard to review, hard to revert, and mixes two concerns. If you want to clean the code, that is a separate task — not part of this refactor.

---

## Filled Example

Extracting store logic from `handler.go` into `store/store.go`.

```
Refactor: move store logic from internal/handler/handler.go into internal/store/store.go.

CURRENT STATE:
- internal/handler/handler.go contains an in-memory tasks map and CRUD operations on it.
- No store package exists.

TARGET STATE:
- internal/store/store.go contains a Store struct with Add, Get, List, Delete methods.
- internal/handler/handler.go depends on store.Store via interface; no direct map access.

STEPS:
1. Create internal/store/store.go with Store struct and methods copied verbatim from handler.go.
   Validation: go build ./... && go test ./...
2. In handler.go, import store package; replace direct map access with store method calls.
   Validation: go build ./... && go test ./...
3. Remove the in-memory map and CRUD operations from handler.go.
   Validation: go build ./... && go test ./...

Do not combine steps.
Do not rewrite handler.go to be cleaner.
Do not change behavior.
```

---

## What to Reject

| Signal | Why it's wrong |
|---|---|
| Step that breaks `go build` before the next step is applied | Violates incremental rule; stop and fix the step |
| Step that changes function signatures "for clarity" | Behavior change disguised as refactor |
| "I rewrote handler.go to be cleaner while moving the logic" | Explicitly forbidden; revert and redo mechanically |
| Steps combined into one ("I moved and updated in the same step") | Cannot validate intermediate state; reject |
| New error handling added that wasn't in original | Behavior change; separate task |
| Test updated to match new structure before validation passes | Test was the only thing making it pass; invalid |

---

## Checklist

- [ ] CURRENT STATE names exact file(s) and structure
- [ ] TARGET STATE names exact file(s) and structure
- [ ] Each step is atomic and independently compilable
- [ ] Validation command is specified (`go build ./... && go test ./...`)
- [ ] Prompt includes "do not combine steps"
- [ ] Prompt includes "do not rewrite the file to be cleaner"
- [ ] Prompt includes "do not change behavior"
- [ ] After each step: run the validation command before proceeding
- [ ] After final step: full test suite passes with no modifications to test files
- [ ] Diff shape matches "move" not "rewrite" — same logic in new location
