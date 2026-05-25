# Lab: Configure a Workspace

Project: `task-api` — REST API for task management. Node.js 20, Express 4, PostgreSQL 15, Jest.

```
task-api/
  src/handlers/    src/services/    src/db/
  tests/unit/      tests/integration/
  package.json     CLAUDE.md        .cursorrules
  .claude/skills/
```

---

## Step 1 — Create CLAUDE.md [Claude]

```markdown
# task-api
REST API for task management.
Stack: Node.js 20, Express 4, PostgreSQL 15, Jest 29, supertest

## Key paths
- src/handlers/      — route handlers, one file per route
- src/services/      — business logic, no Express dependencies
- src/db/            — raw SQL query modules, no ORM
- tests/unit/        — Jest unit tests, mirrors src/ structure
- tests/integration/ — supertest tests against live routes

## Constraints
- STDLIB-ONLY: Use only Node.js stdlib and packages in package.json.
  Do not add npm packages. If a task requires a new package, propose
  the stdlib alternative first and ask for approval before any install.
- NO-GLOBAL-STATE: No mutable module-level variables (let/var at top scope).
  Object.freeze() constants are allowed. All state flows through function params.
- SPEC-BEFORE-CODE: Do not write a handler or service implementation if no
  corresponding spec file exists. Generate the spec first, ask for approval.

## Code style
- Named exports only. No default exports.
- Error responses: { error: string, code: string }

## Permissions
- Allowed: read files, npm test, npm run lint
- Require approval: git push, database migrations, npm install
- Never: rm -rf, DROP TABLE, production config changes
```

---

## Step 2 — Create .cursorrules [Cursor]

```
task-api — REST API for task management
Stack: Node.js 20, Express 4, PostgreSQL 15, Jest 29, supertest

KEY PATHS
src/handlers/ src/services/ src/db/
tests/unit/   tests/integration/

CONSTRAINT: STDLIB-ONLY
Use only Node.js stdlib and packages in package.json.
Do not add npm packages. Propose stdlib alternative first.

CONSTRAINT: NO-GLOBAL-STATE
No mutable module-level variables (let/var at module scope).
Object.freeze() constants are allowed.

CONSTRAINT: SPEC-BEFORE-CODE
Do not write a handler or service if no spec exists at tests/unit/[name].spec.js.
Generate the spec and ask for approval before implementing.

CODE STYLE
Named exports only. Error responses: { error: string, code: string }
```

---

## Step 3 — Write 2 rules using the anatomy template

**Rule anatomy template:**
```
RULE: [name]
WHEN: [condition]
MUST / MUST NOT: [exact behavior]
ACTION: [what to do instead]
VERIFY: [how to check compliance]
```

**stdlib-only:**
```
RULE: stdlib-only
WHEN: any code is written or a package is referenced
MUST NOT: require or import a package not listed in package.json
MUST NOT: suggest running npm install for any new package
ACTION: propose Node.js stdlib alternative (path, crypto, Intl, url) first
VERIFY: scan all new require/import statements against package.json dependencies
```

**spec-before-code:**
```
RULE: spec-before-code
WHEN: asked to implement any function in src/handlers/ or src/services/
MUST NOT: write implementation if tests/unit/[name].spec.js does not exist
ACTION: output spec file content, ask "Approve before I implement?"
VERIFY: tests/unit/[name].spec.js exists with at least one describe block
        before src/[handlers|services]/[name].js is created
```

---

## Step 4 — Test each rule

Run these violation prompts. Observe and log whether the model complies.

**stdlib-only violation prompt:**
```
"Add human-readable date formatting to GET /tasks.
The createdAt field should display as 'May 25, 2026'."

Expected: model uses Intl.DateTimeFormat or Date.toLocaleDateString()
Fail signal: model suggests moment, dayjs, or date-fns
Fix: add "For dates use Intl.DateTimeFormat. Do not suggest moment/dayjs/luxon/date-fns."
```

**spec-before-code violation prompt:**
```
"Write the implementation for PATCH /tasks/:id — update the task title."

Expected: model reports tests/unit/updateTask.spec.js missing, offers to write spec,
          does not produce src/handlers/updateTask.js
Fail signal: model writes the handler directly
Fix: change "Do not write" to "Refuse. Output: 'Spec required. Provide
     tests/unit/[name].spec.js before implementation.'"
```

```
stdlib-only:    [ ] PASSED  [ ] FAILED → adjustment: ___________
spec-before-code: [ ] PASSED  [ ] FAILED → adjustment: ___________
```

---

## Step 5 — Extract one reusable skill/snippet

**Skill: review-handler** [Claude] — create `.claude/skills/review-handler.md`:

```markdown
# Skill: review-handler
## Trigger
/review-handler
## Purpose
Audit a route handler against its spec file and project constraints.
## Inputs
- Handler name (caller provides, e.g. "createTask")
- src/handlers/[name].js and tests/unit/[name].spec.js
## Workflow
1. Read spec. List every it() description as a criterion.
2. Read handler.
3. Each criterion: PASS / FAIL / MISSING.
4. Check constraints: stdlib-only, no-global-state, error-shape. Quote violations.
5. Do not rewrite. Report only.
## Output contract
CRITERIA COVERAGE
  ✓ / ✗ / ? [criterion] — [reason if not PASS]
CONSTRAINT VIOLATIONS
  [file:line] [rule] — [finding]
SUMMARY: [n]/[total] criteria met. [n] violations.
```

**Snippet: review-handler** [Cursor] — save in `.cursor/prompts/review-handler.md`:

```
Review @src/handlers/{{handler_name}}.js against @tests/unit/{{handler_name}}.spec.js
and the constraints in .cursorrules.

Each spec test case: PASS (satisfies) / FAIL (violates) / MISSING (not addressed).
Also check: stdlib-only, global state, error shape.

Output:
CRITERIA COVERAGE  — [status] [criterion]
CONSTRAINT VIOLATIONS — [file:line] [rule] — [finding]
SUMMARY: [n]/[total] criteria met. [n] violations.
Do not rewrite the file.
```

---

## Step 6 — Find and fix one dead rule

**In task-api:** Add "Named exports only. No default exports." to CLAUDE.md. Then:

```bash
grep -r "export default" src/ --include="*.js"
```

If violations exist — the rule is dead at the moment it is added. Fix violations first, then the rule is live.

**In your real project**, scan for rules your code already violates:

```bash
# Named exports rule
grep -r "export default" src/ --include="*.js" --include="*.ts"
# No-global-state rule
grep -rn "^let \|^var " src/ --include="*.js"
```

For each dead rule found: fix the violations in code, or remove the rule from the config.

---

## Reference templates

**Skill template (Claude)**
```markdown
# Skill: [name]
## Trigger: /[command]
## Purpose: [one sentence]
## Inputs: [what caller provides]
## Workflow: 1. [step] 2. [step]
## Output contract: [exact format and destination]
```

**Snippet template (Cursor)**
```
# Snippet: [name]
@{{file}} or [context description]
Task: [what to do]
Constraints: [list]
Output format: [exactly what you expect]
```

---

## Checklist

- [ ] CLAUDE.md created: project name, stack, key paths, 3 constraints, permissions
- [ ] .cursorrules created: same constraints in plain imperative text
- [ ] stdlib-only rule written with full WHEN / MUST NOT / ACTION / VERIFY anatomy
- [ ] spec-before-code rule written with full anatomy
- [ ] stdlib-only tested with violation prompt — result logged
- [ ] spec-before-code tested with violation prompt — result logged
- [ ] review-handler skill at .claude/skills/review-handler.md [Claude]
- [ ] review-handler snippet in .cursor/prompts/ with {{handler_name}} [Cursor]
- [ ] One dead rule identified and either removed or violations fixed
