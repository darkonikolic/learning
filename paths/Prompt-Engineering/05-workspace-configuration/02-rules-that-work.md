# Rules That Work

---

## What makes a rule work

A rule works when it has three properties:

**Binary** — the model either followed it or didn't. No partial credit.
**Specific** — names the exact behavior, not a direction of preference.
**Testable** — you can write a prompt that would violate it, run it, and check.

A rule that lacks any one of these is not a rule. It is a suggestion, and models treat suggestions as optional.

---

## What makes a rule fail

These words kill rules:

| Broken phrasing | Why it fails |
|---|---|
| "prefer X" | Model will use Y when convenient and call it a preference trade-off |
| "try to avoid" | Model decides when the situation justifies avoiding |
| "where possible" | Model decides what counts as possible |
| "consider X" | Model considers X and then does Y |
| "generally" | Every exception feels like a general case |

Replace them:

| Broken | Fixed |
|---|---|
| "Prefer named exports" | "Use named exports only. No default exports." |
| "Try to avoid global state" | "No global mutable state. Flag and refuse if asked." |
| "Where possible, write specs first" | "Do not write implementation before a spec file exists." |
| "Consider adding tests" | "Every function in src/handlers/ requires a test in tests/unit/." |

---

## Rule anatomy

Every effective rule has three parts. Use this template:

```
RULE: [name]
WHEN: [condition — when does this rule apply?]
MUST/MUST NOT: [the exact behavior required or forbidden]
VERIFY: [how to check compliance — what to look for]
```

Examples:

```
RULE: stdlib-only
WHEN: any code is written or a package is suggested
MUST NOT: introduce npm packages not already in package.json
VERIFY: no new entries appear in package.json; no require/import of unlisted packages

RULE: spec-before-code
WHEN: a new handler or service function is requested
MUST: a spec file exist at the corresponding path before implementation begins
VERIFY: spec file exists at tests/unit/[module].spec.js before src/[module].js is written

RULE: error-shape
WHEN: any error is returned from a handler
MUST: response body matches { error: string, code: string }
VERIFY: no handler returns a plain string, number, or non-standard object on error
```

---

## Rule conflict

When two rules are incompatible, one must win. Use this priority ladder:

```
1. Security       — data exposure, injection, auth bypass
2. Correctness    — behavior matches spec
3. Reliability    — system stays stable under load/failure
4. Maintainability — future developers can change it
5. Performance    — it runs fast
```

Example conflict:

> Rule A: No new packages (maintainability)
> Rule B: Use `bcrypt` for password hashing (security)

Security wins. bcrypt is allowed. Note the exception explicitly in the rule:

```
RULE: stdlib-only
WHEN: any package is added
MUST NOT: add packages not in package.json
EXCEPTIONS: security-critical packages (bcrypt, jsonwebtoken) require explicit approval
            but are permitted when approved — do not block them
VERIFY: check for unapproved packages in require/import statements
```

Document the exception. Don't silently override.

---

## Effective rules for common scenarios

**stdlib-only**
```
RULE: stdlib-only
WHEN: writing any code or responding to a task
MUST NOT: require or import a package not listed in package.json
VERIFY: scan all new require/import statements against package.json dependencies
```

**no global state**
```
RULE: no-global-state
WHEN: writing any module-level code
MUST NOT: declare mutable variables at module scope (let, var at top level)
EXCEPTIONS: Object.freeze() constants are allowed
VERIFY: no module-level let or var declarations in new or modified files
```

**spec-before-code**
```
RULE: spec-before-code
WHEN: asked to implement a handler or service function
MUST: refuse implementation if no spec file exists at the matching test path
ACTION: if no spec exists, generate the spec first and ask for approval before implementing
VERIFY: tests/unit/[name].spec.js exists before src/handlers/[name].js is written
```

**test-names-from-criteria**
```
RULE: test-names-from-criteria
WHEN: writing test cases
MUST: derive test description text from acceptance criteria, not from implementation details
BAD:  it('calls db.findById with the id param')
GOOD: it('returns 404 when task does not exist')
VERIFY: no test names describe internal calls; all describe observable behavior
```

---

## Dead rules

A dead rule is one that has been violated and not enforced. It still exists in the config but models no longer treat it as binding — because past violations trained the expectation that it is optional.

Dead rules are actively harmful. They signal to the model (and to teammates) that the rules are aspirational, not constraints. This degrades trust in all rules.

**How to identify a dead rule:**
- Look for rules that are present in CLAUDE.md or .cursorrules
- Check recent commits or generated code for violations
- If violations exist and were not corrected, the rule is dead

**What to do with a dead rule:**

Option 1 — Remove it. If you're not enforcing it, it shouldn't be there.

```markdown
<!-- Remove this if you've been ignoring it: -->
- Use named exports only.
```

Option 2 — Fix it. Enforce the rule retroactively on existing violations, then re-add it.

```bash
# Find violations, fix them, then put the rule back
grep -r "export default" src/ --include="*.js"
```

Option 3 — Downgrade it. Move it to a comment or a "preferences" section so it doesn't pollute the rule set.

---

## How to test a rule

Write a prompt that would violate it. Run it. Check the output.

```
Rule: stdlib-only

Violation prompt:
"Add date formatting to the task list endpoint. Format the createdAt field as
a human-readable string like 'May 25, 2026'."

Expected behavior:
Model proposes using Date.toLocaleDateString() or Intl.DateTimeFormat (stdlib)
NOT: model suggests installing moment or date-fns

If model suggests moment → rule is not working → tighten the rule text
```

```
Rule: spec-before-code

Violation prompt:
"Write the implementation for the DELETE /tasks/:id handler."

Expected behavior:
Model checks for tests/unit/deleteTask.spec.js, finds it missing,
refuses to write src/handlers/deleteTask.js, and offers to write the spec first

If model writes the handler anyway → rule is not working → make the refusal explicit
```

If the model follows the rule on the violation prompt, the rule works. If not, rewrite using harder language: "Do not", "Refuse", "Must not proceed until".

---

## Checklist

- [ ] Every rule is binary — violation is clear and unambiguous
- [ ] No rule contains "prefer", "try", "where possible", "consider", or "generally"
- [ ] Every rule follows the WHEN / MUST / VERIFY anatomy
- [ ] Rule conflicts are resolved with the priority ladder and exceptions documented
- [ ] Each rule has been tested with a violation prompt
- [ ] Dead rules have been removed or enforced retroactively
- [ ] Rule count stays manageable — 5-10 enforced rules beats 30 ignored ones
