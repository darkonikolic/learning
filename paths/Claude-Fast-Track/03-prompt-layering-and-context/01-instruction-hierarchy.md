# Instruction hierarchy — the full stack

Every response Claude generates is shaped by instructions from multiple sources loaded simultaneously. Understanding which source wins, when each source loads, and how to write for each layer is the foundation of reliable Claude Code use.

The full stack from lowest to highest authority:

```
Per-message inline constraints          ← highest override power for current turn
Spec or plan block referenced in message
Session context (what you've stated this session)
.claude/rules/*.md                      ← scoped rules, loaded conditionally
project/CLAUDE.md                       ← project-level persistent instructions
~/.claude/CLAUDE.md                     ← global user instructions (all projects)
Managed policy (org/enterprise)         ← absolute ceiling, cannot be overridden
```

Reading bottom to top: managed policy sets the ceiling. Your global CLAUDE.md establishes project-independent defaults. Project CLAUDE.md adds project-specific context. Rules files carry detailed policy. Session context carries what you've said this conversation. Per-message instructions narrow the current turn.

---

## Layer 1: Managed policy

Who writes it: organization administrator, not you.
When it loads: always, before everything else.
What it overrides: everything below it.
What belongs here: enterprise-wide rules — no secrets in context, approved tool list, compliance requirements.

You typically cannot see managed policy content. You know it exists when Claude declines an action you expected to be allowed.

---

## Layer 2: Global CLAUDE.md (`~/.claude/CLAUDE.md`)

Who writes it: you, for your personal defaults across all projects.
When it loads: every session, every project, always.
What it overrides: project and session layers below it.
What belongs here: personal workflow preferences, tool preferences, global prohibitions that apply regardless of project.

Example entry that belongs here:
```markdown
## Global constraints
- Never use fmt.Println in Go production code — use structured logging.
- Always check for an existing SPEC before writing implementation.
```

What does NOT belong here: project-specific paths, project-specific stack constraints, anything that only applies to one project.

Size discipline: under 50 lines. This file loads in every session of every project. Every line costs context in unrelated projects.

---

## Layer 3: Project CLAUDE.md (`./CLAUDE.md`)

Who writes it: you, at project initialization. Updated as constraints are discovered.
When it loads: every session in this project, automatically.
What it overrides: session context and per-message layers below it.
What belongs here: project identity, stack, critical constraints, key paths, known gotchas.

Example for task-api:
```markdown
# task-api

## Stack
- Language: Go 1.22
- HTTP: stdlib net/http
- Storage: in-memory with sync.RWMutex
- External dependencies: none (stdlib only)

## Critical constraints
- Must not add external packages.
- Must validate input at handler boundary.
- Error responses: {"error": "message"}, always application/json.

## Key paths
- Handlers: internal/handler/
- Domain: internal/domain/
- Entry point: main.go

## Rules
- spec-before-code: .claude/rules/spec-before-code.md
- stdlib-only: .claude/rules/stdlib-only.md
```

Size discipline: under 150 lines ideal. Over 200 lines, split detailed rules to `.claude/rules/`.

---

## Layer 4: Rule files (`.claude/rules/*.md`)

Who writes it: you, as you discover patterns that need enforcement.
When it loads: either always (no `paths:` frontmatter) or on demand when Claude works with matching paths.
What it overrides: session context and per-message layers.
What belongs here: detailed, specific, binary must/must-not rules. More detail than CLAUDE.md can hold. Path-scoped rules that apply only to specific parts of the codebase.

The "load on demand" pattern is critical. A rule file with paths frontmatter only loads when Claude is working with matching files:

```markdown
---
paths:
  - "internal/handler/**"
---

# Handler rules

- Must validate all request body fields before calling domain layer.
- Must not call store methods directly — must go through domain service.
- Must return 400 with {"error": "..."} for validation failures, not 500.
```

This rule loads when Claude touches `internal/handler/task.go`. It does not load when Claude works on `internal/domain/` — reducing context pollution.

A rule without `paths:` loads every session, like an extension of CLAUDE.md. Use for project-wide constraints that are too detailed for CLAUDE.md.

Size discipline: one page per rule file. A 200-line rule file is two rule files.

---

## Layer 5: Session context

Who writes it: you, during the current conversation. Not persisted.
When it loads: from the moment you state it, for the rest of the session.
What it overrides: per-message layers only.
What belongs here: session-specific decisions, things you established earlier this session, state that doesn't warrant a CLAUDE.md update.

Example: "For this session, we're working in the handler layer only. All store changes are out of scope." That constraint now applies to every message until you change it.

Session context disappears when the session ends. If it matters long-term, write it into CLAUDE.md.

---

## Layer 6: Spec or plan block in message

Who writes it: you, in the message body.
When it loads: this message only.
What it overrides: nothing higher in the stack, but makes explicit what to use as ground truth.
What belongs here: reference to the approved spec or plan that bounds this task.

Example:
```
Implement step 2 from docs/plans/01-post-tasks-plan.md.

SPEC contract: docs/specs/post-tasks.md — acceptance section is the contract.
```

This tells Claude where to find the approved truth. It doesn't override CLAUDE.md — it points at a file that defines what "correct" means for this turn.

---

## Layer 7: Per-message constraints

Who writes it: you, in the message body.
When it loads: this message only. Highest override power for the current turn.
What it overrides: session context for this turn only.
What belongs here: turn-specific scope limits, temporary deviations from rules.

Example:
```
Constraints for this turn:
- Implement body parsing only, stop before validation.
- No tests yet — tests are the next step.
```

This overrides the session rule "always write tests" for this turn only. The rule still applies next turn unless you restate this constraint.

---

## The override hierarchy in practice

Lower layers cannot contradict hard constraints from higher layers. This is non-negotiable.

Example of illegal contradiction:
- Global CLAUDE.md: "Never use fmt.Println in Go production code."
- Per-message: "Use fmt.Println for logging in this handler."

The per-message instruction loses. The global constraint wins. Claude should refuse or use the correct logging approach.

Example of legal override:
- Project CLAUDE.md: "Always write tests with every implementation."
- Per-message constraints: "Stop after handler implementation — tests are the next step."

This is a temporary narrowing, not a contradiction. It is legal. Claude should implement the handler and stop, knowing tests come next.

The distinction: a permanent must-not (never do X) cannot be overridden by lower layers. A scope boundary (do X in step 1, Y in step 2) is not a contradiction — it is sequencing.

---

## The "load on demand" pattern

Large rule files referenced in CLAUDE.md but not directly included. The reference tells Claude the rule exists. Claude loads it when relevant.

In CLAUDE.md:
```markdown
## Rules (load when relevant)
- spec-before-code: require SPEC before implementing any feature
- stdlib-only: no external packages in this project
- handler-contracts: validation and response format rules for handlers
```

These three lines in CLAUDE.md cost almost nothing in context. The actual rule files are only loaded when Claude judges them relevant, or when you explicitly reference them.

Why this matters: a project with 10 detailed rule files does not pay the context cost of all 10 rules in every session. A session working only on tests doesn't need the handler contract rules loaded.

The tradeoff: Claude may sometimes miss a rule if it doesn't recognize relevance. For critical rules (security, never-do-X), keep them in CLAUDE.md directly. For detailed how-to rules, the on-demand pattern is appropriate.

---

## Layer sizing summary

| Layer | Ideal size | What to split when over limit |
|-------|-----------|-------------------------------|
| Global CLAUDE.md | Under 50 lines | Move project-specific to project CLAUDE.md |
| Project CLAUDE.md | Under 150 lines | Move detailed rules to .claude/rules/ |
| Rule file | Under 60 lines | Split into two topic-specific rule files |
| Per-message constraints | Under 10 lines | If more, you need a session-level setup first |

---

## Checklist

- [ ] I can name all seven layers of the instruction stack without looking.
- [ ] My global CLAUDE.md contains only cross-project defaults, under 50 lines.
- [ ] My project CLAUDE.md uses hard must/must-not language for constraints.
- [ ] Rule files with paths frontmatter load only when relevant.
- [ ] I know the difference between a legal scope limit and an illegal contradiction.
- [ ] I use per-message constraints for turn-specific scope, not to override global rules.
- [ ] "Load on demand" referenced rules exist as actual .md files in .claude/rules/.
