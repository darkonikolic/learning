# New project flow

`/gsd:new-project` is the entry point for any greenfield project. It gathers context interactively, then writes the foundational planning artifacts before you write a single line of code. You run it once per project.

This is not the right command if a codebase already exists. For existing projects with code, ADRs, or specs already on disk, see `/gsd:ingest-docs` in module 05.

---

## What the command does

When you run `/gsd:new-project`, it asks four questions, then generates three artifacts:

**The four questions:**

1. **Domain and purpose** — what does the project do and who uses it? One sentence is enough. The goal is to anchor PROJECT.md scope, not to write marketing copy.
2. **Tech stack** — language, runtime, key libraries, any constraints you know about. If you do not know yet, say so — the planner records it as "to be decided" and you lock it during milestone planning.
3. **Team size** — solo, small team (2–5), or larger. This affects how GSD structures agent governance and review steps. Solo projects skip some review gates that exist for team coordination.
4. **Timeline** — rough target (days, weeks, months). GSD uses this to calibrate milestone scope. A 2-week timeline produces smaller milestones than a 6-month timeline.

**What it produces:**

| Artifact | Location | Contains |
|----------|----------|---------|
| PROJECT.md | `.planning/PROJECT.md` | Vision, stack, constraints, team size, non-goals |
| ROADMAP.md | `.planning/ROADMAP.md` | Phase list with status, success criteria, dependencies |
| config.json | `.planning/config.json` | GSD configuration: model profile, workflow toggles |

---

## Reading a ROADMAP.md

After `/gsd:new-project` runs, open `.planning/ROADMAP.md` and check four things before accepting it:

**Phase list:** each phase should be a named deliverable, not an activity. "Implement POST /tasks" is a deliverable. "Backend work" is not.

**Success criteria:** every phase has a brief success definition. If a phase lacks one, add it before starting — unclear success criteria produce unclear execution.

**Dependencies:** phases that must complete before others can start are listed as `depends_on`. A phase without dependencies can start immediately. A phase with multiple dependencies cannot start until all predecessors are complete. Check that the dependency graph is acyclic — a cycle means your decomposition is wrong.

**Phase count:** if ROADMAP.md has more than 8–10 phases, consider whether it is scoped to a single milestone or accidentally contains multiple milestones. A milestone should deliver a coherent, shippable increment — not an entire product roadmap.

---

## When NOT to use it

- Existing project with code → use `/gsd:ingest-docs` to classify what is already there before starting phases.
- Joining a project someone else structured → use `/gsd:ingest-docs` to bring GSD state in line with the existing planning artifacts.
- Resuming a paused project that already has `.planning/` → do not re-run `/gsd:new-project`; it will overwrite existing state. Use `/gsd:resume-work` instead.

---

## task-api example

If you ran `/gsd:new-project` for task-api from scratch, you would answer:

1. **Domain:** Go REST API for task management. Endpoints: POST /tasks, GET /tasks, DELETE /tasks/:id. Single user, no auth required.
2. **Stack:** Go 1.21, stdlib net/http only, no external frameworks, in-memory store for early phases.
3. **Team size:** solo.
4. **Timeline:** 2 weeks.

The resulting artifacts would look like this:

**`.planning/PROJECT.md` (abbreviated):**

```markdown
# task-api

## Vision
A minimal Go REST API for task management. Demonstrates clean HTTP handler patterns,
in-memory storage, and test coverage without external dependencies.

## Stack
- Language: Go 1.21
- HTTP: stdlib net/http
- Storage: in-memory (MemStore), SQLite in later phases
- No external frameworks

## Constraints
- stdlib only for HTTP routing
- No auth required in v0.1
- Must compile and test clean: `go build ./...` and `go test ./...`

## Non-goals
- Multi-user support
- Authentication or authorization
- Persistent storage in v0.1
```

**`.planning/ROADMAP.md` (abbreviated):**

```markdown
# Roadmap

## Milestone 1: Core CRUD API

### Phase 1: Project setup
Status: planned
Success: `go build ./...` passes, handler skeleton exists, routes registered
Depends on: —

### Phase 2: GET /tasks
Status: planned
Success: GET /tasks returns 200 + [] with no tasks; returns task array after POST
Depends on: Phase 1

### Phase 3: POST /tasks
Status: planned
Success: POST /tasks returns 201 + task with id, title, done=false, created_at
Depends on: Phase 1

### Phase 4: DELETE /tasks/:id
Status: planned
Success: DELETE returns 204 on success, 404 on missing id; task no longer in GET response
Depends on: Phase 2, Phase 3
```

This is the starting state. You will edit it — add, reorder, tighten success criteria — before running phase 1. The artifact is a scaffold, not a binding contract.

---

## Checklist

- [ ] I know the four questions `/gsd:new-project` asks before generating artifacts.
- [ ] I can identify a phase with missing success criteria in a ROADMAP.md.
- [ ] I know the difference between a project ROADMAP and a milestone — not the same scope.
- [ ] I would use `/gsd:ingest-docs` instead of `/gsd:new-project` on an existing codebase.
- [ ] I know not to re-run `/gsd:new-project` on a project that already has `.planning/`.
