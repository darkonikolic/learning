# PROJECT.md and ROADMAP.md

These two files are the project's north star and its execution contract. Claude reads them at the start of every GSD command. If they are vague, every downstream phase inherits the vagueness. If they are precise, Claude has enough context to make good decisions without asking you at every turn.

---

## PROJECT.md structure

PROJECT.md answers: what are we building, why, for whom, with what constraints, and what is explicitly not in scope.

### Full annotated example — task-api

```markdown
# task-api

## Vision
An in-memory HTTP task manager exposing three endpoints over a single Go binary.
The goal is demonstrating Go HTTP patterns without external dependencies.

## Goals
1. POST /tasks creates a task and returns a unique ID within 10ms p99 under 50 concurrent clients.
2. GET /tasks returns all tasks in creation order, JSON-encoded, with correct status fields.
3. PATCH /tasks/:id/complete marks a task complete and returns 409 if already completed.

## Non-goals
- No authentication or authorization.
- No persistence — restart loses data by design.
- No pagination, filtering, or search.
- No metrics endpoint or observability tooling in v1.

## Stack
- Language: Go 1.22
- HTTP: net/http stdlib only (no external routers)
- Storage: in-process sync.Map or similar
- Build: single `go build` command, no Docker in v1
- Testing: go test stdlib

## Key constraints
- Zero external dependencies (go.mod must have no require entries in v1).
- No goroutine leaks — every spawned goroutine must be tracked or proven bounded.
- Binary must start in under 100ms.

## Team
- Owner: solo learner
- Reviewer: Claude Code
- Stakeholders: none external

## Links
- Repo: local only
- Reference: https://pkg.go.dev/net/http
```

---

## Good PROJECT.md vs bad PROJECT.md

| Dimension | Good | Bad |
|-----------|------|-----|
| Vision | Specific, one deliverable | "A modern API" |
| Goals | Measurable, numbered | "Fast and reliable" |
| Non-goals | Explicit list — what we are not building | Missing entirely |
| Stack | Named versions, named constraints | "We'll use Go" |
| Key constraints | Binary rules Claude cannot hand-wave | "Keep it simple" |
| Non-goals | Scope fence that prevents gold-plating | Missing entirely |

The non-goals section is the most commonly skipped and most valuable. Without it, Claude will add persistence, auth, or an ORM "because it seems useful." Explicit non-goals cut scope creep at the root.

---

## Goals must be measurable

Weak goals fail at verification. A goal is measurable if you can write a pass/fail test for it.

| Weak | Measurable |
|------|-----------|
| "API should be fast" | "POST /tasks returns 201 within 10ms p99 under 50 concurrent clients" |
| "Handle errors" | "POST /tasks with missing title field returns 400 with JSON error body" |
| "Be production-ready" | Out of scope — note it explicitly as a non-goal |

---

## ROADMAP.md structure

ROADMAP.md is the ordered phase plan. Each phase has one clear deliverable. Phases are contracts, not wishes.

### Full example — task-api

```markdown
# Roadmap

## Phase 01 — task-endpoints
Status: planned
Scope: Implement POST /tasks, GET /tasks, PATCH /tasks/:id/complete with in-memory storage.
Delivers: All three endpoints passing curl-based acceptance checks.
Requirements: REQ-001, REQ-002, REQ-003

## Phase 02 — validation
Status: planned
Scope: Input validation on POST /tasks (required fields, max length). Error response contract.
Delivers: 400 responses with structured JSON error body for all invalid inputs.
Requirements: REQ-004

## Phase 03 — concurrent-safety
Status: planned
Scope: Verify and enforce thread safety under concurrent requests. Benchmark.
Delivers: Race-detector-clean test suite, benchmark baseline at 50 concurrent clients.
Requirements: REQ-005
```

---

## Status values

| Status | Meaning | Who sets it |
|--------|---------|-------------|
| `planned` | Phase defined, not started | `/gsd:phase add` |
| `in-progress` | discuss-phase or plan-phase run | `/gsd:discuss-phase` start |
| `completed` | UAT passed, phase archived | `/gsd:complete-milestone` or phase completion |
| `blocked` | Cannot proceed, reason in STATE.md | Manual or GSD blocker detection |

Never set status by hand-editing ROADMAP.md. Use `/gsd:progress` or phase transition commands. GSD uses ROADMAP.md status to decide what `/gsd:resume-work` should load.

---

## The phases-as-contracts principle

Each phase must have:
1. One clear deliverable (what exists after this phase that did not before)
2. Named requirements it satisfies (REQ-IDs from REQUIREMENTS.md)
3. An observable done condition (not "implementation complete" — "acceptance checks pass")

A phase that delivers "improvements" or "refactoring" is not a contract. Name the specific observable change.

---

## How phases connect

Phase N completion enables phase N+1. This is a dependency graph, not just a list:

```
01-task-endpoints  →  02-validation  →  03-concurrent-safety
(endpoints exist)     (inputs validated)  (safe under load)
```

If phase N is not complete, do not start phase N+1. `/gsd:progress` enforces this by checking STATE.md and ROADMAP.md phase status before allowing execution.

---

## Adding and editing phases

Use `/gsd:phase` for all structural changes:

| Command | Effect |
|---------|--------|
| `/gsd:phase add` | Append a new phase to ROADMAP.md |
| `/gsd:phase insert` | Insert a phase between two existing ones (renumbers) |
| `/gsd:phase remove` | Remove a phase and its directory scaffold |
| `/gsd:phase edit` | Edit scope summary of an existing phase |

Manual edits to ROADMAP.md are permitted for prose corrections (typo in scope description), but never for phase number, status, or requirement mapping — those fields are parsed by GSD commands.

---

## Checklist

- [ ] My PROJECT.md has a non-goals section with at least two explicit items
- [ ] Each goal in PROJECT.md is verifiable with a pass/fail test
- [ ] My ROADMAP.md has at least one phase with a named deliverable
- [ ] Each phase maps to at least one REQ-ID
- [ ] I use `/gsd:phase` commands, not hand-edits, to manage phase structure
- [ ] I know the four status values and which commands set them
- [ ] The phases-as-contracts principle: each phase has one observable done condition
