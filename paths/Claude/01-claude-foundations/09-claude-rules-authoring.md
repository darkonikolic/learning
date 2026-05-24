# Claude rules authoring — `.claude/rules/`

**Goal:** write **path-scoped and modular rules** that load when needed — without stuffing everything into one giant `CLAUDE.md`.

**Docs:** [How Claude remembers — rules](https://code.claude.com/docs/en/memory#organize-rules-with-clauderules) · [Settings precedence](https://code.claude.com/docs/en/settings)

**Config map:** `03-workspace-configuration.md`. **Governance:** `13-claude-governance-permissions-and-hooks.md`.

Numerical prefixes = concept order only.

---

## Rules vs CLAUDE.md vs skills

| Mechanism | Loads when | Best for |
|-----------|------------|----------|
| **CLAUDE.md** | Every session (eager) or subdirectory lazy | Build commands, global conventions |
| **`.claude/rules/*.md`** | Every session or when paths match | Scoped must/must-not |
| **Skills** | Invoked or auto when relevant | Multi-step procedures |

**Rule of thumb:** if it must apply whenever Claude touches `*.go` in `internal/payments/`, use a **path rule**. If it is a checklist workflow, use a **skill** (`10`).

---

## File location and format

Project rules: **`.claude/rules/<name>.md`**

Optional YAML frontmatter:

```markdown
---
paths:
  - "src/api/**/*.php"
  - "tests/api/**"
---

# API layer rules

- Must validate input at controller boundary before domain layer.
- Must not call database from controllers — use application services.
- Must return problem+json shape for 4xx/5xx.
```

| Frontmatter | Behavior |
|-------------|----------|
| No `paths` | Loads every session (like always-on policy) |
| `paths:` globs | Lazy load when Claude works with matching files |

**Debug loading:** `InstructionsLoaded` hook fires when rules load — see `13`.

---

## Authoring checklist

1. **Scope** — which directories / file types?  
2. **≤ five must/must-not** — binary, verifiable  
3. **Evidence format** — what output shape proves compliance  
4. **No contradiction** — scan other rules and CLAUDE.md for conflicts  
5. **Length** — one screen; split files by topic  

### Weak vs strong

| Weak | Strong |
|------|--------|
| “Write clean API code” | “Must validate DTOs with Symfony Validator before handler body” |
| “Be careful with SQL” | “Must use repository methods in `OrderRepository` — no raw SQL in controllers” |

---

## Example — Symfony payments slice

`.claude/rules/payments-api.md`:

```markdown
---
paths:
  - "src/Payments/**"
  - "tests/Payments/**"
---

# Payments module

- Must treat webhook handlers as idempotent — document idempotency key field.
- Must not commit `.env` or PSP secret paths.
- Must add integration test for duplicate webhook delivery scenario.
- Output plan must list rollback: feature flag or queue pause step.
```

---

## Example — Go worker slice

`.claude/rules/go-workers.md`:

```markdown
---
paths:
  - "cmd/worker/**"
  - "internal/queue/**"
---

# Queue workers

- Must propagate `context.Context` through consume → handle → ack/nack.
- Must not swallow errors — wrap with `%w` and log correlation id.
- Must document retry vs DLQ policy in plan before changing ack behavior.
```

---

## Imports and organization

- Split by **bounded context** or **layer** — not one 400-line rule file.  
- CLAUDE.md can **`@import`** other markdown for organization — imported content still consumes context at launch; prefer **path rules** for large scoped policy.  
- Monorepo: use **`claudeMdExcludes`** in settings to skip irrelevant team CLAUDE.md files.

---

## Lab

| Step | Action |
|------|--------|
| 1 | Identify one directory where Claude repeatedly errs |
| 2 | Write path-scoped rule with 3 must/must-not lines |
| 3 | Open file in that path; ask Claude for a small change |
| 4 | Compare behavior with rule renamed away (temp disable) |
| 5 | Add one line to CLAUDE.md **pointing** to the rule file purpose — not duplicating body |

---

## Checklist

- [ ] Rule has explicit **paths** or intentional global scope.  
- [ ] Must/must-not items are **testable** in review.  
- [ ] No duplicate policy in CLAUDE.md and rule.  
- [ ] Team can read rule in under two minutes.  
