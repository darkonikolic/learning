# Context Hierarchy

## Three Levels in Both Tools

Every interaction with Claude Code or Cursor operates across three layers simultaneously. Most context problems come from putting information at the wrong level.

```
Level 1 — Workspace config     CLAUDE.md / .cursorrules
Level 2 — Session context      spec file, PLAN.md, or explicit session message
Level 3 — Task prompt          the individual message or composer turn
```

The levels stack. Workspace is background, always present. Session sits on top, active for this work. Prompt is foreground, governs this turn.

---

## What Belongs at Each Level

### Level 1 — Workspace Config

Always-true constraints that apply to every task in this project.

- Language and library rules ("stdlib only", "no ORM")
- Code style that isn't enforced by a linter
- Architectural decisions that can't change ("in-memory store, no DB")
- Patterns you want repeated everywhere ("errors wrapped with fmt.Errorf")
- What files/dirs are off-limits

[Claude] Lives in `CLAUDE.md` at the project root. Read automatically at session start.

[Cursor] Lives in `.cursorrules` at the project root. Applied to all composer sessions.

```markdown
# CLAUDE.md / .cursorrules example

## Constraints
- Go stdlib only. No third-party packages.
- All errors: fmt.Errorf("operation: %w", err)
- JSON responses always include a "status" field
- Do not modify internal/store — that layer is frozen
```

### Level 2 — Session Context

The spec or plan for the current work unit. Active while you're implementing a feature or working through a task.

- Endpoint spec (request shape, response shape, status codes)
- Acceptance criteria for this milestone
- Decisions made in earlier turns that must carry forward
- Current file state that matters for the rest of the session

[Claude] Introduce this at the start of a session as a message, or reference a spec file: "Read SPEC.md before we start." Keep it in a file so it persists.

[Cursor] Add the spec file with `@SPEC.md` at the start of the composer. It stays in context for that session.

```markdown
# SPEC.md (session-level context)

## Task API — Sprint 3 endpoints

PATCH /tasks/:id/complete
- Body: none
- Returns: 200 + updated Task, 404 if not found, 409 if already complete
- Task.CompletedAt set to time.Now()

POST /tasks
- Body: {"title": string, "due": RFC3339}
- Returns: 201 + created Task, 400 on missing title
```

### Level 3 — Task Prompt

The individual turn instruction. What you want done right now.

- One specific action
- Any clarification that is specific to this turn only
- A question or a correction

```
# Good task prompt — specific, one action
Implement PATCH /tasks/:id/complete using the spec in SPEC.md.
Handler goes in internal/api/tasks.go.
```

---

## Why Mixing Levels Breaks Things

### Putting task-level instructions in .cursorrules / CLAUDE.md

Task-level instructions in workspace config don't disappear when the task is done — they persist and contaminate future tasks.

```
# .cursorrules — wrong
- When implementing endpoints, always check if tasks are already complete before updating.
```

This was true for one endpoint. Now it applies to every future endpoint, whether or not it makes sense. Three weeks later, you're debugging why a new endpoint is checking task completion status.

**Rule**: if the instruction stops being true when the task is done, it doesn't belong in workspace config.

### Putting workspace constraints in the prompt

Constraints typed only in a prompt are lost when context clears or degrades.

```
# Prompt — wrong place for this
Use stdlib only. No third-party packages. Add the PATCH endpoint.
```

Next session, next clear, the stdlib constraint is gone. The model uses a library. You revert it. This happens three times.

**Rule**: if the constraint is true for every task in this project, it goes in CLAUDE.md or .cursorrules — not the prompt.

---

## How the Levels Interact

Workspace is the background layer. It is always present but low-salience. The model treats it as defaults.

Session context is mid-ground. It narrows what workspace config means for this task. If workspace says "JSON responses always include a status field" and session says "PATCH /tasks/:id/complete returns 200 + Task", the model combines them.

Prompt is foreground. It gets the most weight. If the prompt explicitly says something that conflicts with session context, the prompt wins.

```
Workspace:  "errors wrapped with fmt.Errorf"
Session:    "PATCH /tasks/:id/complete spec"
Prompt:     "Implement the PATCH endpoint"
```

Result: model implements the endpoint, follows the spec, wraps errors as defined in workspace config. Each level contributes without you restating it.

---

## Concrete Placement Examples

| Instruction | Level | Reason |
|-------------|-------|--------|
| "stdlib only, no frameworks" | Workspace | True forever in this project |
| "in-memory store, do not add DB" | Workspace | Architectural constraint |
| "errors: fmt.Errorf with %w" | Workspace | Style rule, always applies |
| "PATCH /tasks/:id/complete spec" | Session | True for this task, not all tasks |
| "do not modify internal/store" | Workspace | Frozen layer, always true |
| "implement the PATCH endpoint" | Prompt | One action, this turn |
| "return 409 if already complete" | Session | Part of spec, not a global rule |
| "use the handler I showed you earlier" | Prompt | Turn-specific reference |

---

## Checklist

- [ ] Workspace config contains only always-true constraints
- [ ] Task-specific instructions are NOT in .cursorrules / CLAUDE.md
- [ ] Session-level spec is in a file (not just typed in the first message)
- [ ] [Claude] CLAUDE.md exists and is accurate for this project
- [ ] [Cursor] .cursorrules exists and doesn't contain stale task instructions
- [ ] Prompts contain only this-turn instructions
- [ ] If a constraint was only true for one task, it has been removed from workspace config
- [ ] The three levels are not redundantly repeating the same constraint
