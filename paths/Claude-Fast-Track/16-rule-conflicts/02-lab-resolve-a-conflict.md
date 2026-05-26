# Lab — resolve a conflict in task-api

Two rules in task-api now contradict each other. You will identify the conflict type, apply the priority ladder, document the decision in `RULE_PRIORITY.md`, optionally write a time-bounded exception, and verify that Claude respects the winning rule under a conflicting prompt.

Estimated time: 25–35 minutes.

Prerequisites: task-api with `.claude/rules/stdlib-only.md` in place. You will create `readable-ids.md` in this lab.

---

## Step 1 — Create the second rule

Create `.claude/rules/readable-ids.md` with this content:

```markdown
# readable-ids

Task IDs must be human-readable short strings, not UUID hex blobs.

Rationale: IDs appear in API responses, logs, and error messages. A UUID like
`550e8400-e29b-41d4-a716-446655440000` is opaque. A short ID like `xK9p2m` is
readable, copyable, and memorable in a support context.

Requirement: use a short-ID generator that produces 6–8 character alphanumeric strings.
Suggested implementation: github.com/teris-io/shortid or equivalent.

Applies to: internal/id/ and any code that generates task identifiers.
```

Save the file. Do not commit yet.

---

## Step 2 — Identify the conflict

State the conflict explicitly before doing anything else. Use this format:

```
Conflict record:
  Rule A: .claude/rules/stdlib-only.md
  Rule A requires: no external packages — standard library only
  Rule B: .claude/rules/readable-ids.md
  Rule B requires: use a short-ID package (github.com/teris-io/shortid or equivalent)
  Contradiction: Rule B explicitly suggests an external package. Rule A explicitly forbids it.
```

**Conflict type:** this is Type 1 — risk vs ergonomics. `stdlib-only.md` enforces a supply-chain constraint (risk). `readable-ids.md` improves developer and operator ergonomics (ergonomics). They are not competing correctness claims — one is a risk constraint, the other is a preference about UX.

Write this classification down. You will reference it in `RULE_PRIORITY.md`.

---

## Step 3 — Apply the priority ladder

Map each rule to a tier:

| Rule | Tier | Rationale |
|------|------|-----------|
| `stdlib-only.md` | Correctness | Dependency integrity and supply-chain risk management |
| `readable-ids.md` | Maintainability | Operator ergonomics — improves readability, not correctness |

**Winner: `stdlib-only.md`.** Correctness > Maintainability. The winning rule does not need justification beyond tier position. Document the decision — do not re-argue it each time.

**What this means:** ID generation in task-api must use only the standard library. A valid approach:

```go
// internal/id/id.go — stdlib-only short ID generator
package id

import (
    "crypto/rand"
    "encoding/base64"
)

// New returns a URL-safe 8-character random ID using only stdlib.
func New() (string, error) {
    b := make([]byte, 6)
    if _, err := rand.Read(b); err != nil {
        return "", err
    }
    return base64.RawURLEncoding.EncodeToString(b), nil
}
```

This satisfies `readable-ids.md` (short, alphanumeric-ish) and `stdlib-only.md` (no external packages). When both rules can be satisfied simultaneously, do that before reaching for an exception.

---

## Step 4 — Document the decision in RULE_PRIORITY.md

Create or update `.claude/RULE_PRIORITY.md`:

```markdown
# RULE_PRIORITY.md

## Priority order

1. Security
2. Correctness
3. Reliability
4. Maintainability
5. Performance / cost

## Rule tier assignments

| Rule file | Tier | Notes |
|-----------|------|-------|
| no-plaintext-secrets.md | Security | Hard stop |
| stdlib-only.md | Correctness | Supply-chain integrity — no external packages |
| no-global-state.md | Reliability | Test isolation |
| readable-ids.md | Maintainability | Ergonomics preference for short IDs |

## Conflict resolutions

| Conflict | Winner | Loser | Conflict type | Date |
|----------|--------|-------|---------------|------|
| stdlib-only vs readable-ids | stdlib-only.md | readable-ids.md | Type 1 — risk vs ergonomics | 2026-05-25 |

Resolution note: `readable-ids.md` is satisfied via stdlib implementation (crypto/rand + base64).
No external package required. Both rules are honored simultaneously.

## Active exceptions

(none)

## Resolved exceptions

(none)
```

---

## Step 5 — Write a time-bounded exception (if warranted)

The ergonomics argument in `readable-ids.md` does have merit — if task-api moves to production use, truly human-readable IDs (collision-resistant, short, URL-safe) are a legitimate operational concern.

Write this as a time-bounded exception **scoped to Phase 4+** — the phase where task-api moves beyond a learning project:

```markdown
## EXCEPTION: stdlib-only.md relaxed for id-generation (Phase 4+ only)

Overridden rule: .claude/rules/stdlib-only.md
Permitted by: PROJECT.md Phase 4 scope — production-readiness milestone permits audited packages
Scope: internal/id/ package only. No other packages may be added without a new exception record.
Reason: at production scale, collision probability and URL-safety requirements exceed what
  a naive stdlib implementation provides without significant custom code.
Expiry: Phase 4 begins (milestone boundary) — re-evaluate at that point
Cleanup:
  1. Audit the chosen package (license, last commit, CVE history)
  2. Add it to an approved-packages list in stdlib-only.md
  3. Remove this exception record and update the Resolved table
Recorded by: <your name> on 2026-05-25
```

Add this to the **Active exceptions** section of `RULE_PRIORITY.md`.

**Note:** this exception is not active now. It is a pre-approved path that activates only when Phase 4 begins. Write it now so the decision is documented, not deferred and forgotten.

---

## Step 6 — Verify Claude respects the decision

Use this test prompt to confirm Claude honors `stdlib-only.md` over `readable-ids.md`:

```
Implement the internal/id package for task-api. IDs should be human-readable
short strings — approximately 8 characters, URL-safe, alphanumeric.
```

**What to check in Claude's output:**

| Check | Pass condition | Fail condition |
|-------|---------------|----------------|
| No `go get` commands issued | Claude does not fetch external packages | Claude runs `go get github.com/teris-io/shortid` or any other package |
| No import of non-stdlib package | `import` block contains only standard library | Import block contains `github.com/...` |
| `go.mod` unchanged | `go.mod` has no new `require` entries | `go.mod` gains a new dependency |
| `readable-ids.md` intent satisfied | Output produces short, URL-safe strings | Output produces UUIDs or random hex blobs |

If Claude attempts to import an external package, the rule file is not being read. Verify `.claude/rules/stdlib-only.md` exists at the correct path and that Claude Code is picking up `.claude/rules/` files. Check `CLAUDE.md` for a `@.claude/rules/` import directive.

**Recovery prompt if Claude violates stdlib-only:**

```
Stop. Your implementation imports an external package. Read .claude/rules/stdlib-only.md.
That rule is Correctness tier and takes precedence over readable-ids.md (Maintainability tier)
per .claude/RULE_PRIORITY.md. Reimplement using only the Go standard library (crypto/rand,
encoding/base64, or encoding/hex). The short-ID requirement can be satisfied without
external dependencies.
```

---

## Exercise 2 — TDD rule vs scaffolding rule

This exercise uses the two-rule conflict from `01-conflict-resolution.md` (Scenario 1).

### Setup

Create `.claude/rules/scaffolding-order.md` with this content:

```markdown
# scaffolding-order

For scaffolding tasks — creating new files with stub functions that will be
filled in during execute-phase — write the stub first, tests after.

Rationale: plan-phase generates stubs so execute-phase can fill them.
Writing tests before stubs exist causes plan-phase to generate malformed plans.

Applies to: plan-phase scaffolding only. Does not apply during execute-phase.
```

Your global CLAUDE.md (`~/.claude/CLAUDE.md`) should already contain a TDD instruction. If it does not, you can simulate it by creating `.claude/rules/global-tdd.md` with:

```markdown
# global-tdd

Always write tests before implementation. For every new function or handler,
create the test file first. Do not write implementation code before a failing
test exists.
```

### Identify the conflict

Write the conflict record:

```
Conflict record:
  Rule A: [file path for global TDD rule]
  Rule A requires: [fill in]
  Rule B: .claude/rules/scaffolding-order.md
  Rule B requires: [fill in]
  Contradiction: [fill in — when exactly do they contradict each other?]
```

### Classify and resolve

1. What conflict type is this? (Type 1, 2, or 3)
2. Which rule wins? Why?
3. Does the loser become permanently irrelevant, or does it apply elsewhere?

### Document in RULE_PRIORITY.md

Add an entry to `.claude/RULE_PRIORITY.md`:

```markdown
## Conflict resolutions

| Conflict | Winner | Loser | Conflict type | Date |
|----------|--------|-------|---------------|------|
| global-tdd vs scaffolding-order | [fill in] | [fill in] | [fill in] | [today] |

Resolution note: [fill in — one sentence on how both rules can coexist]
```

---

## Exercise 3 — Turn instruction vs project rule

This exercise uses the conflict from `01-conflict-resolution.md` (Scenario 2).

### Setup

Create `.claude/rules/test-coverage.md` with this content:

```markdown
# test-coverage

All handlers must have corresponding unit tests before the phase is considered
executable. A handler without tests is incomplete work. Do not mark any handler
task complete without at least one passing test.

Tier: Correctness
```

### Simulate the conflict

In a Claude Code session, send this message:

```
Implement the GET /tasks handler in tasks/handler.go.
Stop after writing the handler — don't write tests, I'll add them manually.
```

### Observe and evaluate

Does Claude:
- Follow the instruction silently (skips tests, no warning)?
- Follow the instruction but flag the conflict explicitly?
- Refuse the instruction because of test-coverage.md?

The expected behavior: Claude follows your instruction (you are the human) but flags the conflict: "Note: `test-coverage.md` requires tests before this task is complete. Proceeding without tests means STATE.md will record this task as incomplete."

If Claude follows the instruction silently, you have found a gap: the rule file is not being read or not being honored. Check that `.claude/rules/test-coverage.md` is at the correct path and that CLAUDE.md loads the rules directory.

### Write the exception record

Even if you have a good reason to skip tests now, document it:

```markdown
## EXCEPTION: test-coverage.md — task [ID] handler without tests

Overridden rule: .claude/rules/test-coverage.md
Permitted by: author turn instruction during Phase [N] execute
Scope: [specific handler function] only
Reason: [your actual reason]
Expiry: [when the tests must be added]
Cleanup: [what to do — add which specific tests]
Recorded by: [your name] on [date]
```

Add this to the **Active exceptions** section of `.claude/RULE_PRIORITY.md`.

### Deliverable

A `RULE_PRIORITY.md` at `.claude/RULE_PRIORITY.md` containing:
1. Priority order (5 tiers)
2. Rule tier assignments for at least: stdlib-only.md, test-coverage.md, scaffolding-order.md
3. Conflict resolutions table with entries from all three exercises
4. Active exceptions section with the turn-override exception from this exercise

Optionally: create the file at `docs/rules/RULE_PRIORITY.md` if your project keeps docs separate from `.claude/`.

---

## RULE_PRIORITY.md format reference

```markdown
# RULE_PRIORITY.md

## Priority order
(ordered list — 1 is highest)

## Rule tier assignments
| Rule file | Tier | Notes |

## Conflict resolutions
| Conflict | Winner | Loser | Conflict type | Date |

## Active exceptions
## EXCEPTION: <rule-name> overridden by <concern>
Overridden rule: ...
Permitted by: ...
Scope: ...
Reason: ...
Expiry: ...
Cleanup: ...
Recorded by: ... on ...

## Resolved exceptions
| Exception | Overridden rule | Resolved date | Resolution |
```

---

## Exception record format reference

```
## EXCEPTION: <overridden-rule> overridden by <permitting-concern>

Overridden rule: .claude/rules/<file>.md
Permitted by: <SPEC section | ADR | commit ref | milestone decision>
Scope: <files, packages, phases — be specific>
Reason: <one sentence — why the override is necessary>
Expiry: <date | event | phase>
Cleanup: <numbered steps to take when expiry is reached>
Recorded by: <author> on <YYYY-MM-DD>
```

---

## Checklist

**Exercise 1 — stdlib-only vs readable-ids:**
- [ ] I created `.claude/rules/readable-ids.md` with the full rule content.
- [ ] I identified the conflict type as Type 1 — risk vs ergonomics.
- [ ] I assigned tier positions: `stdlib-only.md` = Correctness, `readable-ids.md` = Maintainability.
- [ ] I documented the resolution in `RULE_PRIORITY.md` with winner, loser, type, and date.
- [ ] I recognized that both rules can be honored simultaneously via a stdlib implementation.
- [ ] I wrote a time-bounded Phase 4+ exception with scope, reason, expiry, and cleanup steps.
- [ ] I ran the test prompt and verified Claude did not import an external package.
- [ ] `go.mod` in task-api has no new dependencies after the id package is implemented.
- [ ] I know the recovery prompt to use if Claude violates `stdlib-only.md`.

**Exercise 2 — TDD vs scaffolding rule:**
- [ ] I created `.claude/rules/scaffolding-order.md` with the full rule content.
- [ ] I wrote the conflict record with both rules and the exact contradiction.
- [ ] I classified the conflict type correctly (Type 3 — scoped decision).
- [ ] I explained where the loser rule (global TDD) still applies (execute-phase, not scaffolding).
- [ ] I added the conflict resolution entry to `RULE_PRIORITY.md`.

**Exercise 3 — Turn instruction vs project rule:**
- [ ] I created `.claude/rules/test-coverage.md` with the full rule content.
- [ ] I sent the test prompt and observed whether Claude flagged the conflict.
- [ ] I wrote a complete exception record: scope, reason, expiry, cleanup.
- [ ] I added the exception to the Active exceptions section of `RULE_PRIORITY.md`.
- [ ] `RULE_PRIORITY.md` exists at `.claude/RULE_PRIORITY.md` (or `docs/rules/`) with all four sections complete.
