# Phase workflow commands

Commands that operate within a single phase lifecycle. These extend or replace steps in the core loop for specific situations: ambiguous deliverables, minimal slices, research-heavy domains, and session continuity.

---

## Before planning: clarify WHAT vs clarify HOW

Two distinct problems require two distinct commands:

| Problem | Command | Output |
|---------|---------|--------|
| Goal is fuzzy — intent unclear | `/gsd:discuss-phase N` | CONTEXT.md |
| Goal is clear — deliverables ambiguous | `/gsd:spec-phase N` | SPEC.md with ambiguity score |
| PRD already written externally | `/gsd:plan-phase N --prd path` | PLAN.md directly |
| ADRs already approved | `/gsd:plan-phase N --ingest path` | PLAN.md with decision context |

The most common mistake: running discuss-phase when the real problem is that you cannot describe the outputs, not the intent. If you know WHY but not WHAT, run spec-phase first.

---

## `/gsd:spec-phase <N>`

**Purpose:** Clarify deliverables before discuss. Produces a SPEC.md with an ambiguity score. Use this when you cannot write a one-sentence "done" definition.

**When discuss is sufficient:** You can say "Phase 1 is done when POST /tasks returns 201 with the created task." One sentence, verifiable.

**When spec-phase is needed:** You find yourself saying "Phase 1 is done when... well, we have the basic task creation working, plus maybe validation, and we should probably think about error format..." That is ambiguity — run spec-phase first.

**Output:** `.planning/phases/XX-name/SPEC.md` — deliverables, acceptance criteria, explicit non-goals, ambiguity score (0–10, with 0 = perfectly clear).

**After running:** If ambiguity score > 5, do not proceed to discuss. Answer the open questions in SPEC.md until score drops below 3.

### discuss-phase vs spec-phase: when to use which

`/gsd:discuss-phase N` is conversational. It asks adaptive questions, then writes a CONTEXT.md capturing the answers. Use it when requirements are clear enough that a discussion can surface the relevant details. The output is context, not a contract.

`/gsd:spec-phase N` is structured. It runs an ambiguity scoring pass (0–100, where 0 = perfectly clear) before producing SPEC.md with acceptance criteria. Use it when the feature is complex, under-defined, or has cross-cutting concerns that interact in ways not immediately obvious.

The rule: if you can describe the feature in two sentences without caveats, use discuss-phase. If you find yourself writing paragraphs with "but also" and "depends on whether", use spec-phase first to resolve the ambiguity before discuss.

**task-api examples:**

GET /tasks — use discuss-phase. The deliverable is one sentence: "Return all tasks in creation order with current completion status." Nothing to resolve.

POST /tasks with pagination, filtering, authentication, and rate limiting — use spec-phase first. These four concerns interact: does pagination affect auth checks? Do filters apply before or after rate limiting? Spec-phase surfaces the interaction questions before discuss-phase tries to plan around them.

---

## `/gsd:ingest-docs`

For onboarding an existing project that already has planning artifacts: ADRs, PRDs, OpenAPI specs, or design documents. It classifies what it finds, detects conflicts between documents, and produces a `.planning/` directory that reflects the existing decisions rather than starting from scratch.

**When to use:**
- Joining an existing codebase that has design docs but no GSD structure
- Importing an externally written spec before starting GSD phases
- Migrating from another planning system (Notion, Confluence, plain docs) into GSD

**What it does NOT do:** it does not create a ROADMAP.md or milestone structure. After `/gsd:ingest-docs`, you still need to run `/gsd:new-milestone` to set up the phase structure for your first batch of work.

**What it does with conflicts:** if two documents make incompatible claims (PRD says "use PostgreSQL", ADR says "use SQLite for v0.1"), ingest-docs flags the conflict and asks you to resolve it before writing anything. Do not skip this step — unresolved conflicts produce inconsistent plans.

**task-api example:** if task-api had an existing OpenAPI spec at `docs/openapi.yaml` describing GET /tasks, POST /tasks, and DELETE /tasks/:id, you would run:

```
/gsd:ingest-docs docs/openapi.yaml
```

GSD classifies it as a contract spec, extracts the endpoint definitions and response schemas, and writes them into `.planning/` as project context. When you then run `/gsd:discuss-phase 1`, the planner already knows the endpoint contracts — you do not need to re-state them.

---

## `/gsd:mvp-phase <N>`

**Purpose:** Plan the smallest shippable vertical increment. Combines user story definition, SPIDR splitting, and plan generation into one command.

**SPIDR** is a backlog refinement technique: Split by path, Interface, Data, Rules, or Scenario. MVP-phase applies it to constrain scope.

**When to use:**
- You have a large phase and want to ship something real within one session.
- Stakeholders need working software fast, not a complete feature.
- You want to validate an assumption before building the full implementation.

**What it produces:** PLAN.md scoped to the minimum vertical slice — one user story path, end to end, with no optional tasks.

**Task-api example:** Full task manager has POST /tasks, GET /tasks, PATCH /tasks/:id/complete. An MVP slice would be POST /tasks alone — handler, route registration, one test, curl working. Not all three endpoints.

---

## `/gsd:plan-phase` flags: deep dive

The flag you pick reshapes the structure of every task in PLAN.md. Pick once, commit.

### `--research`

Spawns a research agent before the planner runs. Produces RESEARCH.md. The planner then consumes RESEARCH.md as context.

**Use when:** You are building in a domain where the planner's default knowledge is insufficient — a Go library you have not used, a specific RFC, an unfamiliar API contract.

**Do not use when:** The domain is standard CRUD. Research overhead adds cost without benefit.

**Task-api example:** Not needed for basic HTTP routing. Would be appropriate if using a specific Go framework (chi, gin) you have not used before.

### `--tdd`

Tasks are structured test-first. For each task, the test file is created before the implementation file. The planner generates tasks in pairs: TEST task followed by IMPL task.

**Use when:** Correctness is the primary concern. The endpoint contract must be exact. You want test coverage by construction, not as an afterthought.

**Consequence:** Slower initial execution. Higher confidence in final state.

**Task-api example:** Appropriate for PATCH /tasks/:id/complete — the state transition (done: false → done: true) is a precise invariant you want locked by test.

### `--mvp`

Same as running `/gsd:mvp-phase` but inline with plan-phase. Constrains the plan to minimum viable tasks.

### `--prd path`

Skip discuss entirely. Ingest an existing Product Requirements Document. The planner reads it and produces PLAN.md.

**Requirement:** The PRD must have explicit acceptance criteria. A narrative description without checkable outcomes produces a vague plan.

### `--ingest path`

Import approved Architecture Decision Records into planning context. Planner respects existing decisions rather than proposing alternatives.

### `--gaps`

Replan only tasks that are missing a completion marker or explicitly failed. Does not touch tasks already marked complete.

**Use when:** Execute-phase stopped mid-run due to a blocker. You fixed the blocker and want to continue without re-executing completed work.

---

## What PLAN.md looks like

After `/gsd:plan-phase` runs, you get a PLAN.md file on disk. Here is an abbreviated example for task-api Phase 2 (GET /tasks), followed by annotations explaining the structure.

```markdown
# PLAN.md — Phase 2: GET /tasks
# Goal: implement GET /tasks endpoint returning all tasks in creation order
# Spec: docs/specs/get-tasks.md

## Wave 1

### Task 2-01
id: 2-01
description: Add `List() []Task` method to `MemStore` in tasks/store.go.
  Returns a copy of the in-memory task slice. Returns empty slice (not nil) when
  no tasks exist.
file: tasks/store.go
depends_on: []

## Wave 2

### Task 2-02
id: 2-02
description: Implement `GetTasks(w http.ResponseWriter, r *http.Request)` in
  tasks/handler.go. Calls store.List(), encodes to JSON, returns 200.
  Returns 405 for non-GET methods. Sets Content-Type: application/json.
file: tasks/handler.go
depends_on: [2-01]

### Task 2-03
id: 2-03
description: Write unit tests in tasks/handler_test.go.
  TestGetTasksEmpty: GET returns 200 + [].
  TestGetTasksWithTasks: GET after POST returns 200 + task array.
  TestGetTasksMethodNotAllowed: POST to /tasks returns 405.
  Use httptest — no running server needed.
file: tasks/handler_test.go
depends_on: [2-01]

## Wave 3

### Task 2-04
id: 2-04
description: Register GET /tasks route in main.go.
  Add http.HandleFunc("/tasks", handler.GetTasks) in the server setup block.
file: main.go
depends_on: [2-02]

### Task 2-05
id: 2-05
description: Write integration test in tasks/integration_test.go.
  Start a test server, POST a task, GET /tasks, verify response body and status.
file: tasks/integration_test.go
depends_on: [2-02, 2-04]
```

> Wave 1 contains only one task (2-01). This is not inefficiency — `store.List()` is the
> foundation every other task in this phase depends on. It cannot be parallelized with
> anything because nothing else can start until it exists.

> Wave 2 has two tasks (2-02 and 2-03) with the same `depends_on: [2-01]`. Neither
> depends on the other, so they run in parallel. Agent A writes handler.go; Agent B writes
> handler_test.go simultaneously. Agent B tests the interface contract defined by 2-01,
> not Agent A's specific implementation — this is what makes them genuinely independent.

> `depends_on` in practice: GSD's execute-phase reads this field as a gate. A task with
> `depends_on: [2-01]` will not start until 2-01 is marked complete and verified. If 2-01
> fails, waves 2 and 3 are blocked until the failure is resolved.

> **How `--tdd` changes this output:** With `--tdd`, the test task (2-03) appears in Wave 1
> alongside the store task, and implementation (2-02) moves to Wave 2. Test stubs are
> written first as a specification; the handler is then implemented to make them pass.
> This gives you failing tests before any implementation exists — intentional, by design.

---

## `/gsd:execute-phase` flags: deep dive

### `--wave W`

Run a specific wave number. Waves are parallel task groups inside a phase.

**Use when:**
- Wave 1 completed successfully but wave 2 failed — rerun wave 2 only.
- You want to observe wave 1 results before committing to wave 2.
- A specific wave contains risky tasks you want to review manually first.

**Example:** `--wave 2` runs only the second parallel group.

### `--gaps-only`

Skip completed tasks. Execute only tasks with no completion marker.

**Difference from `--wave W`:** `--gaps-only` ignores wave structure entirely; it runs whatever is unfinished.

### `--tdd`

As in plan-phase: test before implementation per task. If your plan was generated without `--tdd`, using this flag at execute time attempts to retrofit test-first behavior.

**Recommendation:** Decide at plan-phase time. Using `--tdd` at execute without `--tdd` plan structure is less reliable.

---

## Session continuity commands

### `/gsd:pause-work`

**Purpose:** Create a handoff checkpoint mid-phase. Writes current context, active task, blockers, and intent into STATE.md in a resumable format.

**When to run:** Before switching to a different task, closing your laptop, or ending a session with incomplete work. Do not let the session end without this if you are mid-phase.

**What it creates:** A structured checkpoint in STATE.md. Not a separate file — an update to the existing state that resume-work can parse.

### `/gsd:resume-work`

**Purpose:** Restore full phase context after a session break or after `/compact`. Reads STATE.md, CONTEXT.md, PLAN.md, and recent commits to reconstruct working memory.

**When to run:** Start of any session where you are continuing an in-progress phase.

**After running:** Verify the context summary matches reality. STATE.md can become stale if work happened outside GSD (manual commits, direct file edits). If the summary is wrong, repair STATE.md manually before continuing.

---

## Express paths (skip discuss)

Both paths require that you already have externally approved documentation.

```
/gsd:plan-phase N --prd docs/requirements.md
/gsd:plan-phase N --ingest docs/architecture-decisions.md
```

Use these when joining an existing project that already has written requirements. Do not use as a shortcut to avoid writing requirements — a thin PRD produces a thin plan.

---

## Decision table: which planning command

| Situation | Command |
|-----------|---------|
| Phase intent unclear | `/gsd:discuss-phase N` |
| Intent clear, deliverables fuzzy | `/gsd:spec-phase N` then discuss |
| Everything clear, standard domain | `/gsd:plan-phase N` |
| Unfamiliar library or API | `/gsd:plan-phase N --research` |
| Test coverage is critical | `/gsd:plan-phase N --tdd` |
| Need smallest shippable thing | `/gsd:mvp-phase N` or `--mvp` |
| Have external PRD | `/gsd:plan-phase N --prd path` |
| Execute failed, fix blocker, continue | `/gsd:execute-phase N --gaps-only` |
| Want to see wave 2 in isolation | `/gsd:execute-phase N --wave 2` |

---

## Checklist

- [ ] I know when to use spec-phase before discuss-phase.
- [ ] I can apply the two-sentence rule to decide between discuss-phase and spec-phase.
- [ ] I know that `/gsd:ingest-docs` does not create a ROADMAP.md — I still need `/gsd:new-milestone` after.
- [ ] I can explain what SPIDR splitting does in mvp-phase.
- [ ] I know which plan-phase flag structures tasks test-first.
- [ ] I know the difference between `--wave W` and `--gaps-only`.
- [ ] I understand that `--prd` requires explicit acceptance criteria to produce a useful plan.
- [ ] I would run `/gsd:pause-work` before ending a session mid-phase.
- [ ] I know that `/gsd:resume-work` can be wrong and I must verify its summary.
