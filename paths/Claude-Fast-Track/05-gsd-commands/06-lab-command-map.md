# Lab: command map on task-api

Apply every command from this module to the task-api project. The goal is not a working API — it is a working `.planning/` directory and demonstrated command literacy. You will build the actual API in module 08's lab.

---

## Prerequisites

- GSD installed. Verify: `/gsd:help` returns output.
- Empty directory for task-api: `mkdir task-api && cd task-api && git init`
- You are in a Claude Code session with the task-api directory open.

---

## Task-api project context

You are building a Go HTTP task manager. Three endpoints:
- `POST /tasks` — create a task with a title, returns 201 with `{id, title, done: false}`
- `GET /tasks` — list all tasks, returns 200 with array
- `PATCH /tasks/:id/complete` — mark task done, returns 200 with updated task

Storage: in-memory map. No database. No auth. Standard library only (`net/http`).

Phase 1 scope: POST /tasks only.

---

## Steps

### Step 1: Bootstrap with new-project

Run `/gsd:new-project` in the task-api directory.

When prompted, provide:
- **Project name:** task-api
- **Description:** In-memory Go HTTP task manager. POST /tasks, GET /tasks, PATCH /tasks/:id/complete. No persistence, no auth, stdlib only.
- **Tech stack:** Go 1.22, net/http
- **Team:** Solo
- **Phases:** 3 (one per endpoint)

After it completes, open `.planning/PROJECT.md`. Find the vision section. If it contains words like "scalable", "production-grade", "enterprise", or "robust", delete them. Replace with: "Three-endpoint in-memory task API. Stdlib only. Done when all three endpoints pass curl tests."

**What to verify:** `.planning/` directory exists. Contains PROJECT.md, REQUIREMENTS.md, ROADMAP.md, STATE.md, config.json.

---

### Step 2: Run progress and read the output

Run `/gsd:progress`.

Read the output carefully. It will describe the current state and suggest a next command. Paste the suggested next command into your notes. Do not run it yet.

**What to verify:** Progress suggests `/gsd:discuss-phase 1` or `/gsd:spec-phase 1`. If it suggests something else, check that ROADMAP.md has a Phase 1 entry.

---

### Step 3: Run discuss-phase for Phase 1

Run `/gsd:discuss-phase 1`.

When it asks about the phase, answer:
- **Goal:** POST /tasks endpoint
- **Inputs:** JSON body with `title` string field
- **Outputs:** 201 with `{id, title, done: false}`, 400 if title missing or empty
- **Non-goals:** No persistence, no authentication, no task deletion
- **Constraints:** Standard library only. No external packages.

After the command completes, open `.planning/phases/01-post-tasks/CONTEXT.md` (or equivalent path).

---

### Step 4: Edit CONTEXT.md — human gate

Read every line of CONTEXT.md. Find one sentence that is vague, aspirational, or unverifiable. Delete it or replace it.

Then add one concrete constraint that is not already there. Example: "IDs are sequential integers starting at 1, not UUIDs."

**What makes a good constraint:** It is verifiable. You can write a curl command or test assertion that proves it is met.

**Bad line to leave in:** "The endpoint should handle edge cases gracefully."
**Replace with:** "Empty string title returns 400 with `{error: 'title is required'}`."

Save CONTEXT.md. This is your approval of the context. Do not proceed to plan without this edit.

---

### Step 5: Run plan-phase and review

Run `/gsd:plan-phase 1`.

When it completes, open the PLAN.md file under the phase folder.

Read every task. For each task, ask: "Does this name a specific file?" Apply the test:

| Task text | Assessment |
|-----------|-----------|
| "Add handler for POST /tasks" | VAGUE — which file? |
| "Create `internal/handler/tasks.go` with `CreateTask(w, r)` function" | SPECIFIC — pass |
| "Add validation logic" | VAGUE — where? what logic? |
| "In `CreateTask`, return 400 JSON `{error: 'title is required'}` if title absent or empty" | SPECIFIC — pass |

If any task fails the specificity test, edit it directly in PLAN.md.

**What to verify:** Every task in PLAN.md names at least one file. Wave groupings exist. Verification criteria reference the CONTEXT.md goal.

---

### Step 6: Verify task specificity

Count the tasks in PLAN.md. Write the count in your notes. Then confirm: every task names a specific file path relative to the project root.

If a task says "create the route registration", edit it to say: "In `main.go`, add `http.HandleFunc(\"/tasks\", handler.CreateTask)` in the `main()` function."

This is not pedantry — vague tasks produce vague execution. The executor agent cannot make good decisions without file-level specificity.

---

### Step 7: Run progress with --next

Run `/gsd:progress --next`.

Observe which command it proposes to run. It should propose `/gsd:execute-phase 1`. If it proposes something else, read the reason — it may have detected a missing artifact.

Do not let it auto-execute. The point of this step is to observe the router's reasoning, not to run execute (that is module 08's lab).

---

### Step 8: Run health check

Run `/gsd:health`.

Read the output. Note:
- Any RED findings (blocking) — resolve before proceeding.
- Any YELLOW findings (warnings) — understand them even if you leave them.
- GREEN findings — confirm these are the ones you expected.

Common YELLOW: "CONTEXT.md has no explicit non-goals section." If you edited CONTEXT.md correctly in step 4, this should be GREEN.

---

### Step 9: Explore a second command path (optional but recommended)

Without running execute, test the router with a different intent:

Run `/gsd:progress --do "I want to understand what files will be created in Phase 1"`.

Observe how the router interprets the intent and what it suggests. This is command literacy — knowing you can express intent in plain language and get a routed command.

---

## What you should have after this lab

| Artifact | Expected state |
|----------|---------------|
| `.planning/PROJECT.md` | Vision edited, no vague aspirations |
| `.planning/REQUIREMENTS.md` | REQ-IDs for POST /tasks acceptance criteria |
| `.planning/ROADMAP.md` | Phase 1 listed, status: in-progress or pending |
| `.planning/STATE.md` | Current phase = 1 |
| `CONTEXT.md` under phase folder | Edited by you, concrete constraints |
| `PLAN.md` under phase folder | Tasks with specific file names |

---

## Checklist

- [ ] `/gsd:new-project` ran and `.planning/` contains all five expected files.
- [ ] PROJECT.md vision edited to remove vague language.
- [ ] `/gsd:progress` output noted before running any other command.
- [ ] `/gsd:discuss-phase 1` ran and CONTEXT.md exists.
- [ ] CONTEXT.md edited: one vague line removed, one concrete constraint added.
- [ ] `/gsd:plan-phase 1` ran and PLAN.md exists.
- [ ] Every task in PLAN.md names a specific file.
- [ ] `/gsd:progress --next` output noted.
- [ ] `/gsd:health` ran with no RED findings.
