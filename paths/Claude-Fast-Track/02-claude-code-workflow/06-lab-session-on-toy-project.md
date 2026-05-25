# Lab: Session ownership on task-api

This lab runs a complete plan-to-execution-to-capture cycle on the task-api Go project. Every step has a concrete deliverable. Do not proceed to the next step until the current step's deliverable exists.

---

## Prerequisites

- Go 1.21+ installed: `go version`
- Claude Code installed: `claude --version`
- Git installed: `git --version`

---

## Step 1: Create the project

```bash
mkdir task-api
cd task-api
git init
go mod init task-api
mkdir -p internal/store internal/handlers docs/plans
```

Verify:
```bash
ls
# go.mod  internal/  docs/
go env GOMOD
# .../task-api/go.mod
```

Deliverable: directory exists with `go.mod` and subdirectory structure.

---

## Step 2: Write the session opener (before opening Claude)

Before opening Claude Code, write your session opener in `docs/plans/post-tasks.md`. Do not skip this step. Writing before opening Claude is the practice.

Required components:
1. One-sentence problem statement
2. Explicit out-of-scope list
3. Desired artifact (file + test)
4. Your decomposition (3-7 steps in your own words)

Template to fill in:

```markdown
# Plan: POST /tasks endpoint

## Problem
Add POST /tasks endpoint to task-api: [fill in specific behavior]

## Out of scope
- [list at least 3 things you are not doing today]

## Desired artifact
- internal/store/store.go with Task struct and in-memory store
- internal/handlers/tasks.go with CreateTask handler
- TestCreateTask passing with: happy path, missing title 400, title too long 400

## My decomposition
1. [your step 1]
2. [your step 2]
3. [your step 3]
4. [your step 4]
5. [your step 5]
```

Deliverable: `docs/plans/post-tasks.md` exists with all sections filled in, in your own words.

---

## Step 3: Open Claude Code and use /plan

Open Claude Code in the task-api directory:

```bash
claude
```

Send the /plan command with the no-implementation constraint:

```
/plan Add POST /tasks endpoint as specified in docs/plans/post-tasks.md — no implementation yet. Propose file structure and step list only.
```

Read Claude's plan output carefully.

Do not approve yet.

Ask yourself:
- Does the plan match your decomposition from Step 2?
- Are there steps you didn't ask for?
- Is the file structure what you expected?
- Are the acceptance items objectively verifiable?

Deliverable: Claude has produced a plan proposal. You have read it and noted at least one thing to edit.

---

## Step 4: Edit the plan — add your constraint

Before approving the plan, add one constraint you care about. For this lab, use:

**Constraint to add:** "No database. In-memory store only. Use a slice with sync.Mutex. No external dependencies beyond the standard library."

Edit the plan in-chat by responding:

```
Edit the plan to add this constraint: in-memory store only using a slice with sync.Mutex, no external dependencies. Confirm the updated steps reflect this.
```

Read the updated plan. Verify the constraint appears.

Only then say: "Plan approved. Do not execute yet."

Deliverable: Plan with the in-memory constraint is explicitly stated. You have given explicit approval.

---

## Step 5: Execute ONE step from the plan only

Identify the first step in the approved plan. Execute it with explicit bounds:

```
Execute step 1 only from the approved plan.
Do not proceed to step 2.
Do not touch any file not mentioned in step 1.
Show me the output before continuing.
```

Wait for Claude's response. Read it fully.

Verify step 1 output:
- Is the file it created what step 1 specified?
- Does the content match what you expected?
- Did Claude stay in step 1's scope?

Deliverable: One file exists that matches step 1 of the plan. You have verified it manually.

---

## Step 6: Write a correction citing a specific problem

Review the output from Step 5. Find a specific, concrete flaw. Every output has at least one improvable aspect.

Examples of things to look for:
- Is the Task struct missing a field you want (e.g., `created_at`)?
- Is the mutex not embedded correctly in the struct?
- Is a method name not idiomatic Go?
- Is there missing context propagation?

Write your correction using this structure:
```
Flaw: [specific problem]
Location: [file and function/struct]
Expected: [what correct looks like]
```

Send the correction. Review the updated output.

Deliverable: You have sent a correction with a named flaw, location, and expected behavior. Claude has responded with a specific fix.

---

## Step 7: Run /compact

You have now completed one sub-problem (step 1 + one correction cycle). Before moving to the next sub-problem, compact:

```
/compact
```

After compacting, re-anchor:

```
Continuing from docs/plans/post-tasks.md. Step 1 is complete: internal/store/store.go exists with Task struct and in-memory store using sync.Mutex. Ready for step 2.
```

Verify Claude acknowledges the re-anchor correctly. If it seems confused, re-read the plan file:

```
Read docs/plans/post-tasks.md to reestablish context.
```

Deliverable: /compact has run. Claude is re-anchored to the plan. Context is clean for the next step.

---

## Step 8: Capture for CLAUDE.md

Close the session (type `/exit` or close the terminal). Before doing anything else, write down what you would put in CLAUDE.md based on this session.

Open a text file or a notepad. Answer these questions:

1. What constraint did you enforce that Claude wouldn't have assumed? (e.g., in-memory only, no external deps)
2. What convention emerged that should apply to future sessions? (e.g., Task struct field naming, error response format)
3. What file layout decision was made that future sessions should respect? (e.g., store in internal/store/, handlers in internal/handlers/)
4. Was there a mistake Claude made that you corrected? That correction should become a rule.

Write at least 3 CLAUDE.md bullet points from this session. Format:

```markdown
## task-api

- Language: Go 1.21. Standard library only — no external HTTP router, no external test library.
- In-memory store: slice with sync.Mutex in internal/store/store.go. No database.
- Error responses: JSON with {"error":"message"} body. Content-type: application/json on all responses including 4xx.
- [add your own from what you discovered]
```

Deliverable: 3+ CLAUDE.md bullet points written and ready to paste.

---

## Reference: what a good session opener looks like for this project

For comparison, here is a complete well-formed session opener for step 2 of the full task-api:

```
Problem: Add GET /tasks endpoint to task-api. Returns JSON array of all tasks, sorted by created_at ascending. Returns 200 with empty array if no tasks exist.

Out of scope: filtering, pagination, authentication, POST or PATCH endpoints (already done).

Desired artifact: updated internal/handlers/tasks.go with GetTasks handler, route registered in main.go, TestGetTasks passing with: empty list, one task, multiple tasks in order.

Plan file: docs/plans/get-tasks.md
```

Note what is explicit: the sort order, the empty case behavior, exactly which test cases are required.

---

## Checklist

- [ ] `task-api/` directory exists with `go.mod` and subdirectory structure.
- [ ] `docs/plans/post-tasks.md` contains my decomposition in my own words before I opened Claude.
- [ ] I used `/plan` before any code was generated.
- [ ] I edited the plan to add the in-memory constraint before approving.
- [ ] I executed exactly one step, with explicit bounds in the execution message.
- [ ] My correction cited a specific flaw with location and expected behavior.
- [ ] I ran `/compact` before starting the next sub-problem.
- [ ] I wrote 3+ CLAUDE.md bullet points from this session.
