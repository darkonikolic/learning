# Rules and skills authoring

Rules enforce constraints. Skills encode repeated workflows. Both extend Claude's behavior beyond CLAUDE.md, but they serve different purposes and have different lifecycles.

---

## Rules

**Location:** `.claude/rules/<name>.md`

Rules are policy files — they tell Claude what it must and must not do. They are binary: Claude either follows a rule or violates it. Good rules can be checked in code review.

### Rule frontmatter format

```markdown
---
name: rule-name
description: One-line description — used to decide when this rule is relevant
paths:
  - "internal/handler/**"
---

Rule content here.
```

| Frontmatter field | Behavior |
|------------------|---------|
| `name` | Identifier for the rule — matches the key in CLAUDE.md rules section |
| `description` | How Claude decides if this rule is relevant — write it like a trigger condition |
| `paths` (optional) | File globs — rule loads only when Claude works with matching files |
| No `paths` | Rule loads every session (always-on, like an extension of CLAUDE.md) |

A rule with no `paths` is an always-on rule. Use for project-wide constraints.
A rule with `paths` is a lazy-loaded rule. Use for layer-specific or path-specific constraints.

### What makes a good rule

**Specific and binary.** Claude can determine with yes/no whether it's following the rule.

Weak:
```markdown
Be careful with error handling.
```

Strong:
```markdown
Must not assign errors to _. Every error returned by a function must be either:
1. Handled (log + return) 
2. Wrapped and returned to caller with fmt.Errorf("context: %w", err)
```

**Explains the why.** When Claude understands the reason, it applies judgment in edge cases the rule didn't anticipate.

Weak (no why):
```markdown
Must use RLock for reads and Lock for writes.
```

Strong (with why):
```markdown
Must use sync.RWMutex for the store: RLock for reads (GetAll, GetByID), Lock for writes (AddTask, Complete).

Why: multiple concurrent readers are safe; concurrent write + read creates a data race. RWMutex maximizes read throughput while protecting writes.
```

**Short.** One page max. If the rule requires more than one page, split it into two rules with separate concerns.

**Not contradicting CLAUDE.md or other rules.** Run a mental conflict check before writing a rule.

### Rule examples for task-api

`.claude/rules/spec-before-code.md`:
```markdown
---
name: spec-before-code
description: Require SPEC file before implementation for any new feature or endpoint
---

# spec-before-code

Before writing implementation code for any feature:

1. Check whether docs/specs/<feature>.md exists.
2. If no SPEC exists: write the SPEC first and stop. Do not proceed to implementation.
3. If a SPEC exists: confirm the acceptance criteria match what you're about to implement.
4. Do not implement without an approved SPEC on disk.

Why: code written without a SPEC cannot be verified against intent. The SPEC is the contract; tests confirm contract fulfillment.

Applies to: new endpoints, new business logic, new validation rules.
Does not apply to: refactoring existing behavior, bug fixes, test additions for existing specs.
```

`.claude/rules/stdlib-only.md`:
```markdown
---
name: stdlib-only
description: No external Go packages — stdlib only for this project
---

# stdlib-only

task-api uses Go standard library only. Do not suggest or add external packages.

If a stdlib solution exists, always prefer it over an external package — even if the external package is more convenient.

Packages to refuse: gorilla/mux, gin, chi, gorm, google/uuid, pkg/errors, and all other non-stdlib packages.

Allowed exception: explicit user approval + go.mod comment explaining why exception was granted. This requires a two-step: user types "I approve adding X" and the go.mod comment is written before adding the import.

Why: stdlib-only means zero dependency management overhead, zero supply chain risk, zero version conflicts. task-api is a learning project — the constraint is educational.
```

`.claude/rules/handler-contracts.md`:
```markdown
---
name: handler-contracts
description: Validation and response format rules for HTTP handlers
paths:
  - "internal/handler/**"
---

# handler-contracts

Rules for all files in internal/handler/:

- Must validate all request body fields before calling any domain or store function.
- Must return 400 with {"error": "..."} for all validation failures — never 500.
- Must set Content-Type: application/json on all responses, including errors.
- Must not call store methods directly — must use the domain layer if one exists.
- Must not read request body more than once — read into struct, pass struct.
- Must use r.Context() for context propagation — not context.Background().

Why: handlers are the boundary layer. Clean boundaries prevent business logic from leaking into HTTP concerns and HTTP concerns from leaking into business logic.
```

---

## Skills

**Location:** `.claude/skills/<name>/SKILL.md` (project) or `~/.claude/skills/<name>/SKILL.md` (personal)

Skills are reusable multi-step workflows. You invoke them with `/skill-name` or, if the description matches, Claude loads them automatically.

### When to create a skill vs typing a prompt

| Use case | Use |
|----------|-----|
| Workflow repeated 3+ times per week | Skill |
| Complex multi-step procedure with consistent output format | Skill |
| One-off or infrequent task | Inline prompt |
| Task that varies significantly each time | Inline prompt |
| Quick fix or single-step operation | Inline prompt |

Creating a skill for something you do once wastes time. Not creating a skill for something you do daily wastes sessions.

### SKILL.md format

```markdown
---
name: skill-name
description: What this skill does — used for auto-invocation. Write trigger phrases users say.
disable-model-invocation: false
allowed-tools: Read, Bash, Edit
---

## Context setup

!`git status`
!`git log --oneline -5`

## Instructions

[Step-by-step instructions Claude follows when skill is invoked]
```

| Frontmatter field | Meaning |
|------------------|---------|
| `name` | The slash command name: `/skill-name` |
| `description` | Auto-invocation trigger. Include natural language users say. |
| `disable-model-invocation: true` | Manual-only — user must type `/skill-name` |
| `allowed-tools` | Restrict which tools Claude can use while skill is active |
| `context: fork` | Run skill in isolated subagent (prevents context pollution) |

Lines starting with `!` followed by a backtick-quoted command run the shell before Claude processes the skill. Use for live state injection: current git status, test output, file listing.

### Example skill: spec-template

`.claude/skills/spec-template/SKILL.md`:
```markdown
---
name: spec-template
description: Create a new SPEC file for an endpoint or feature. Use when asked to write a spec or spec-before-code rule is triggered.
disable-model-invocation: false
allowed-tools: Read, Write, Bash
---

## Instructions

When invoked with an endpoint or feature name, create docs/specs/<name>.md with this structure:

1. Run: `ls docs/specs/` to see existing specs for format reference.
2. Read one existing spec file for format consistency.
3. Create docs/specs/<name>.md with these sections:
   - # SPEC: [endpoint or feature name]
   - ## Summary (one sentence)
   - ## Request (method, path, content-type)
   - ## Request body (fields with types and required/optional)
   - ## Response: success (status, body, content-type)
   - ## Response: [error case] (for each distinct error)
   - ## Acceptance criteria (checklist items, each testable)

4. Acceptance criteria rules:
   - Each item starts with "- [ ]"
   - Each item is independently testable
   - No vague items ("works correctly" is not testable)
   - Include status code checks, body shape checks, edge cases

5. Output the file path after creating.
6. Do NOT write any implementation code.
```

### Example skill: verify-endpoint

`.claude/skills/verify-endpoint/SKILL.md`:
```markdown
---
name: verify-endpoint
description: Manually verify an HTTP endpoint works against its SPEC. Use when asked to verify, check, or test an endpoint manually.
disable-model-invocation: false
allowed-tools: Bash, Read
---

## Instructions

When invoked with an endpoint (e.g., "POST /tasks"):

1. Find the SPEC: docs/specs/<endpoint-slug>.md
2. Read the acceptance criteria.
3. Start the server: `go run .` in background (if not already running)
4. For each acceptance criterion, run a curl command and check the response.
5. Report: PASS or FAIL for each criterion with actual vs expected.
6. Stop the server if you started it.

Curl command patterns:
- POST: `curl -s -w "\n%{http_code}" -X POST -H "Content-Type: application/json" -d '{"key":"value"}' http://localhost:8080/path`
- GET: `curl -s -w "\n%{http_code}" http://localhost:8080/path`
- PATCH: `curl -s -w "\n%{http_code}" -X PATCH http://localhost:8080/path`
```

---

## Decision table: what goes where

| Content | Location |
|---------|----------|
| Always-on project constraint (short form) | CLAUDE.md constraints section |
| Always-on constraint with detail and examples | `.claude/rules/<name>.md` (no paths) |
| Path-scoped constraint (only certain files) | `.claude/rules/<name>.md` with paths frontmatter |
| Repeated multi-step workflow | `.claude/skills/<name>/SKILL.md` |
| One-off workflow | Inline message prompt |
| Per-session constraint | Session context (message layer) |
| Per-turn constraint | Per-message constraints block |

The escalation ladder: start with a message constraint. If you repeat it in 3 sessions, move it to CLAUDE.md. If CLAUDE.md entry grows too detailed, move detail to a rule file. If it becomes a repeated workflow, make it a skill.

---

## Checklist

- [ ] Rule files have frontmatter with `name` and `description`.
- [ ] Rules with paths frontmatter load only when those paths are relevant.
- [ ] Each rule has a "Why" section explaining the reasoning.
- [ ] Rules are binary — Claude can verify compliance yes/no.
- [ ] No rule contradicts CLAUDE.md or another rule.
- [ ] Each rule file is under 60 lines — if longer, split by concern.
- [ ] Skills have descriptions written as trigger phrases.
- [ ] Skills used 3+ times per week; one-off workflows stay as inline prompts.
- [ ] CLAUDE.md rules section points to each rule file.
- [ ] `disable-model-invocation: true` set on skills that should only be invoked manually.
