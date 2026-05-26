# Memory and persistence

## Types of memory in Claude Code

Claude Code has five distinct memory layers. Mixing them up is one of the most common sources of lost context and session confusion.

| Memory type | Written by | Survives session? | Purpose |
|-------------|------------|-------------------|---------|
| Context window | Both | No — ephemeral | Active working memory; current session |
| CLAUDE.md (project) | You | Yes — reloaded each session | Project instructions, conventions, constraints |
| ~/.claude/CLAUDE.md | You | Yes — reloaded each session | Personal preferences across all projects |
| Auto-memory | Claude | Yes — stored in ~/.claude/projects/ | Claude's learned facts about you and your projects |
| STATE.md | You | Yes — file on disk | Workflow state; last known good position |

**The most important rule:** decisions that matter must land in a file. Anything that exists only in the chat scrollback is gone after `/compact` or `/clear`.

---

## What goes where — decision table

| Content type | Where it goes |
|--------------|---------------|
| Project stack, language, key paths | CLAUDE.md (project root) |
| Global personal preferences | ~/.claude/CLAUDE.md |
| Current phase and last completed task | .planning/STATE.md |
| Requirements and acceptance criteria | .planning/REQUIREMENTS.md |
| Implementation plan for current phase | .planning/PLAN.md |
| Multi-step procedure or workflow | .claude/skills/<name>.md |
| Module-specific conventions | .claude/rules/<subpath>/ |
| Claude's observed preferences | Auto-memory (auto-managed) |
| One-session working notes | Chat thread (acceptable) |

---

## CLAUDE.md — structure and content rules

CLAUDE.md is loaded at session start. It is context, not hard enforcement — but it is persistent context that Claude reads before any prompt.

**Target size: under 200 lines.** Above that, the signal-to-noise ratio drops. Use `.claude/rules/` path-scoped files for module-specific content.

### What to put in CLAUDE.md

- Build and test commands (the exact commands, not "run tests")
- Project language and framework version
- Key directory structure (where handlers live, where tests go)
- Critical constraints ("never commit to main directly", "always run go vet before committing")
- Naming conventions that differ from language defaults
- Facts Claude cannot infer from the codebase (team decisions, historical context)

### What NOT to put in CLAUDE.md

- Full specification text — put in SPEC.md
- Implementation history — put in git log or ADRs
- Long procedures (more than 10 steps) — put in .claude/skills/
- Module-specific rules that don't apply to the whole project — put in .claude/rules/
- Information that changes frequently — it will become stale and mislead Claude

### Example CLAUDE.md for task-api

```markdown
# task-api

Go 1.22 HTTP API for task management. No frameworks — stdlib net/http only.
SQLite via database/sql with github.com/mattn/go-sqlite3.

## Build and test

go build ./...
go test ./... -race
go vet ./...

## Structure

main.go         — server setup, router, graceful shutdown
tasks/
  handler.go    — HTTP handlers
  store.go      — database operations
  store_test.go — integration tests against a test DB
schema.sql      — database schema (run once on init)

## Conventions

- Handlers receive (w http.ResponseWriter, r *http.Request) only.
- Store methods return (T, error) — never panic on DB errors.
- Tests use a separate in-memory SQLite DB, not the app DB.
- Error responses use {"error": "message"} JSON, not plain text.

## Constraints

- No external HTTP router packages (chi, gorilla, etc.)
- No ORM — raw SQL only
- Tests must pass before any commit
```

This CLAUDE.md is 30 lines. It tells Claude everything non-obvious about the project without duplicating what the code already shows.

---

## ~/.claude/CLAUDE.md — global user instructions

This file loads for every project. Keep it minimal — it adds to the context of every session regardless of relevance.

Good content for global CLAUDE.md:
- Your preferred code review verbosity
- Languages you work in (so Claude does not waste time asking)
- Hard personal rules ("never commit secrets", "always ask before deleting files")
- Personal skill and agent locations

Bad content for global CLAUDE.md:
- Project-specific conventions — put in project CLAUDE.md
- Long procedures — put in skills
- Anything that would confuse Claude on projects where it does not apply

---

## Auto-memory — Claude's learned facts

Claude stores observed facts about you in `~/.claude/projects/*/memory/`. These load at session start alongside CLAUDE.md.

View and manage via `/memory`. The key actions:
- Review entries periodically — stale auto-memory ("user prefers tabs") can conflict with current project conventions.
- Delete entries that are wrong or outdated.
- Disable auto-memory with `autoMemoryEnabled: false` in settings if you find it causes more confusion than help.

Auto-memory is useful for personal preferences (communication style, review depth) and less useful for project-specific facts (project CLAUDE.md serves that purpose better).

---

## /compact and what gets lost

`/compact [instructions]` summarizes the chat scrollback into a compressed form. It frees context window space.

| What survives compaction | What does not fully survive |
|--------------------------|----------------------------|
| CLAUDE.md content | Detailed reasoning from earlier in the chat |
| Rules files | Specific decisions made only verbally |
| Auto-memory | Step-by-step context from long explorations |
| Active plan if you pass it as an instruction | Chat-only working notes |

**Before running /compact on work-in-progress:**
1. Write the current plan to PLAN.md on disk.
2. Update STATE.md with current status and next action.
3. Capture any important decisions in a file.
4. Then compact.

`/compact "summarize only, preserve the implementation plan for task 3"` passes an instruction to the compaction to bias what it keeps.

---

## STATE.md — workflow memory

STATE.md is the artifact that tracks workflow state across sessions. Update it at phase boundaries, and update it manually when a session ends unexpectedly.

A well-maintained STATE.md:
```yaml
phase: v0.1-api-core
status: in-progress
last_completed: PLAN.md task 3 (CreateTask handler)
next_action: Implement GetTasks handler (PLAN.md task 4)
blockers: none
last_session: 2026-05-24
```

A STATE.md that misleads you:
```yaml
phase: v0.1-api-core
status: complete
```

When a session ends mid-task, update STATE.md before closing. The 90 seconds this takes prevents 20 minutes of context reconstruction next session.

---

## Anti-patterns

| Anti-pattern | Consequence | Fix |
|---|---|---|
| Putting everything in CLAUDE.md | Context bloat; important rules lost in noise | Under 200 lines; use path rules for module content |
| Relying on chat memory across sessions | Lost context; Claude re-derives wrong conclusions | Important decisions land in files |
| Stale auto-memory | Wrong "facts" influence new work | Review auto-memory monthly; delete stale entries |
| STATE.md not updated before session end | Next session starts with wrong context | Update STATE.md as last action of every session |
| Global CLAUDE.md with project-specific rules | Rules apply to wrong projects; confusing | Project-specific content in project CLAUDE.md only |

---

## Checklist

- [ ] CLAUDE.md has build and test commands that actually work (verify them).
- [ ] CLAUDE.md is under 200 lines.
- [ ] Long procedures are in .claude/skills/, not CLAUDE.md.
- [ ] Module-specific rules are in .claude/rules/ path-scoped files.
- [ ] I have reviewed auto-memory at least once with `/memory`.
- [ ] STATE.md is honest about what is incomplete (not optimistically "done").
- [ ] I understand what survives `/compact` and what does not.
- [ ] I run `/context` to check memory footprint when sessions feel bloated.
