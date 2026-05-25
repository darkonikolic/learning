# Lab: Bootstrap task-api from scratch

This lab walks through the full project bootstrap using GSD, starting from an empty directory. You will run `/gsd:new-project`, answer the four context questions for task-api, review the generated artifacts, and create Milestone 1. By the end you have a `.planning/` directory ready for Phase 1 execution.

**Prerequisite:** GSD installed. `/gsd-help` works in a Claude Code session. See module 00 if not.

---

## Step 1: Create an empty directory and open Claude Code

```bash
mkdir task-api && cd task-api
git init
claude
```

You need a git-initialized directory before running `/gsd:new-project`. GSD uses git to track artifact changes.

---

## Step 2: Run `/gsd:new-project`

Inside the Claude Code session:

```
/gsd:new-project
```

GSD will ask four questions. Answer them for task-api:

**Question 1 — Domain and purpose:**
```
A Go REST API for task management. Endpoints: POST /tasks (create), GET /tasks (list),
DELETE /tasks/:id (delete). Single user, no authentication required.
```

**Question 2 — Tech stack:**
```
Go 1.21, stdlib net/http only. No external HTTP frameworks. In-memory store for v0.1,
SQLite in a later phase. No external dependencies in v0.1.
```

**Question 3 — Team size:**
```
Solo.
```

**Question 4 — Timeline:**
```
2 weeks.
```

Wait for GSD to finish generating artifacts before proceeding.

---

## Step 3: Review PROJECT.md

Open `.planning/PROJECT.md`. Verify these four things:

1. **Vision sentence** captures "Go REST API, task management, no auth, in-memory" — not a generic description.
2. **Stack section** lists Go 1.21, stdlib net/http, and in-memory store. If it says "to be decided" for the storage layer, update it now: `Storage: in-memory MemStore for v0.1`.
3. **Non-goals section** exists and includes at minimum: authentication, persistent storage for v0.1, multi-user support.
4. **Constraints section** includes: `stdlib only for HTTP routing`, `go build ./... must pass clean`.

If any of these are missing or incorrect, edit the file directly. PROJECT.md is a document you own — GSD generated a scaffold, not a final artifact.

---

## Step 4: Review ROADMAP.md

Open `.planning/ROADMAP.md`. Check:

1. **Milestone 1 is named clearly** — "Core CRUD API" or "v0.1". Not just "Milestone 1".
2. **Four phases are listed** — project setup, GET /tasks, POST /tasks, DELETE /tasks/:id. The order matters: setup must come first; DELETE depends on both GET and POST.
3. **Each phase has a success definition** — one sentence that can be verified. If a phase says only "implement the endpoint" without a success definition, add one.
4. **Dependencies are correct** — DELETE /tasks/:id depends on GET /tasks and POST /tasks. If ROADMAP.md omits this dependency, add it. A missing dependency means execute-phase could try to run DELETE before the store exists.

If ROADMAP.md lists more than 6–8 phases, check whether it has accidentally collapsed Milestone 2 (pagination, SQLite migration) into Milestone 1. Split them now, before you start.

---

## Step 5: Run `/gsd:new-milestone`

```
/gsd:new-milestone
```

When prompted, provide:

```
Name: v0.1
Theme: Core CRUD API — all three endpoints working with in-memory store, tests passing
```

GSD creates `.planning/milestones/v0.1/` and marks it active in ROADMAP.md.

---

## Step 6: Verify the .planning/ structure

Before starting Phase 1, confirm this structure exists:

```
.planning/
  PROJECT.md          — exists, vision and constraints filled
  ROADMAP.md          — milestone v0.1 active, 4 phases listed
  STATE.md            — exists (may be empty or show "initialized")
  config.json         — exists
  milestones/
    v0.1/             — exists and empty (phases not started yet)
```

Run:

```bash
ls .planning/
ls .planning/milestones/
```

If any directory is missing, check that `/gsd:new-project` completed without error. If config.json is missing, GSD did not finish — re-run `/gsd:new-project` (it will prompt before overwriting).

---

## Deliverable

A `.planning/` directory with:
- PROJECT.md reflecting the task-api stack and constraints you reviewed
- ROADMAP.md with Milestone v0.1 active and four correctly sequenced phases
- `milestones/v0.1/` directory ready to receive phase artifacts

You are ready for Phase 1. The next step is `/gsd:discuss-phase 1` or `/gsd:spec-phase 1` — see module 05 for the decision rule.

---

## Checklist

- [ ] `/gsd:new-project` completed without error.
- [ ] PROJECT.md has vision, stack, constraints, and non-goals filled in.
- [ ] ROADMAP.md shows Milestone v0.1 as active with four phases.
- [ ] DELETE /tasks/:id phase has depends_on pointing to both GET and POST phases.
- [ ] `/gsd:new-milestone` has run and `.planning/milestones/v0.1/` exists.
- [ ] `ls .planning/` shows PROJECT.md, ROADMAP.md, STATE.md, config.json.
