# CLAUDE.md vs .cursorrules

Both files load automatically when a session starts. The developer does not type project context, stack details, or standing constraints into the first message. The model already has them.

---

## What each file does

**CLAUDE.md** [Claude]
- Loaded from project root and merged with `~/.claude/CLAUDE.md` (global)
- Markdown format; supports headers, lists, code blocks
- Read before the first tool call in every session
- Applies to all Claude Code interactions in that working tree

**.cursorrules** [Cursor]
- Loaded from project root only
- Plain text or markdown (Cursor strips formatting for injection)
- Applied to every Composer and Chat session automatically
- No global equivalent — Cursor uses User Rules in Settings for that

---

## What goes in both

```
# Project
task-api — REST API for task management
Stack: Node.js 20, Express, PostgreSQL, Jest

# Key paths
src/handlers/    — route handlers
src/services/    — business logic
src/db/          — query modules
tests/unit/      — Jest unit tests
tests/integration/ — supertest integration tests

# Constraints
- Standard library and declared dependencies only. No new packages without explicit approval.
- No global mutable state. All state flows through function parameters.
- Every handler must have a corresponding spec file before implementation begins.

# Code style
- Functions over classes for stateless logic
- Named exports only (no default exports)
- Error messages in the format: { error: string, code: string }
```

Paste that content into CLAUDE.md and a nearly identical block into .cursorrules. Both tools will enforce it from session start.

---

## What CLAUDE.md has that .cursorrules doesn't

**@import** — split rules across files to keep CLAUDE.md maintainable:

```markdown
# CLAUDE.md
@import .claude/rules/api-constraints.md
@import .claude/rules/testing-standards.md
@import .claude/rules/database-rules.md
```

Each imported file is a focused rule set. The root CLAUDE.md stays short.

**Tool permissions** — declare what Claude Code may and may not run:

```markdown
## Permissions
- Allowed: read any file, run tests, run lint
- Require approval: git push, database migrations, npm install
- Never run: rm -rf, DROP TABLE, any production credentials
```

**Hook configuration** — run scripts on session events:

```markdown
## Hooks
- Before commit: run npm test && npm run lint
- On file write to src/: update the relevant test file if it exists
```

.cursorrules has none of these. It is instruction text only.

---

## What .cursorrules has that CLAUDE.md doesn't

**Simpler syntax** — no structure required. Cursor reads it as a flat prompt prefix.

**Natural @file integration** — Cursor's @file references in chat work alongside .cursorrules without extra configuration. Rules and file context compose cleanly.

---

## Rule of thumb

If you would type it in the first message of every session, it belongs in workspace config.

```
"Remember, we're using stdlib only — no lodash, no moment"     → workspace config
"This project uses PostgreSQL not MySQL"                        → workspace config
"Explain how async/await works"                                 → prompt, not config
"Help me think through this architecture"                       → prompt, not config
```

---

## Side-by-side: the same rule in both formats

**Constraint:** No global mutable state

```markdown
<!-- CLAUDE.md [Claude] -->
## Constraints
- No global mutable state. All state must flow through function parameters or
  be encapsulated in a returned object. Module-level constants (frozen) are allowed.
  If asked to introduce global state, flag this as a constraint violation and suggest
  an alternative before proceeding.
```

```
# .cursorrules [Cursor]
CONSTRAINT: No global mutable state.
All state flows through function parameters or returned objects.
Module-level frozen constants are allowed.
If I ask you to introduce global state, tell me this violates the project constraint
and suggest a parameter-passing alternative before writing any code.
```

The behavior expected is identical. The format differs: CLAUDE.md uses structured Markdown; .cursorrules uses plain imperative text.

---

## Side-by-side: stdlib-only constraint

```markdown
<!-- CLAUDE.md [Claude] -->
## Dependencies
- Use only Node.js standard library and packages already listed in package.json.
- Do not suggest or introduce new npm packages.
- If a task seems to require a new package, name the stdlib alternative or ask for
  explicit approval before proceeding.
```

```
# .cursorrules [Cursor]
DEPENDENCIES: Use only Node.js stdlib and packages in package.json.
Do not add new npm packages.
If a task seems to need a new package, propose the stdlib approach first.
Ask for explicit approval before suggesting an install.
```

---

## Checklist

- [ ] CLAUDE.md exists at project root with project name, stack, key paths, and constraints
- [ ] `~/.claude/CLAUDE.md` has global rules that apply across all projects
- [ ] .cursorrules exists at project root with the same core constraints in plain text
- [ ] CLAUDE.md uses @import if rule count exceeds ~30 lines
- [ ] Tool permissions are declared in CLAUDE.md if any commands need to be restricted
- [ ] Every rule passes the "would I say this every session?" test
- [ ] No rule is in CLAUDE.md only because of formatting preference — if .cursorrules supports it, it's in both
