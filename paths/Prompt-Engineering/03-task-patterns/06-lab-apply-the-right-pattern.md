# Lab: Apply the Right Pattern

No prompts are given to you. You select the pattern, write the prompt, apply it, and audit the output.

---

## Setup

This lab assumes the task-api project from earlier in the path. If you do not have it, use any small HTTP service in your language. The patterns apply regardless of language; the verification commands change.

---

## Four Tasks

Read each task. Do not write a prompt yet.

**Task A — New endpoint**
The spec at `docs/specs/delete-task.md` describes `DELETE /tasks/{id}`. The spec includes a boundary section. Your job is to implement it.

**Task B — Broken response**
`GET /tasks/{id}` returns a 404 for a task ID that exists in the store. A test `TestGetTask_found` in `internal/handler/task_handler_test.go` describes the correct behavior (200 with task body). The test is failing.

**Task C — Extract logic**
Input validation (checking that `title` is non-empty, that `id` is a valid UUID) lives inside `CreateTask()` in `handler.go`. It needs to move to `internal/validator/validator.go` without changing behavior.

**Task D — Storage decision**
The current in-memory store uses a plain map with a `sync.RWMutex`. You are about to add a streaming endpoint (`GET /tasks/stream`) that pushes SSE events when tasks change. You need to decide whether to keep the mutex-based store, switch to a channel-based store, or introduce a third approach.

---

## Step 1: Pattern Selection

For each task, identify the correct pattern from this directory. Write your answer and a one-sentence justification.

| Task | Pattern file | Justification |
|---|---|---|
| A | | |
| B | | |
| C | | |
| D | | |

**Expected answers** (check after completing on your own):

| Task | Pattern | Why |
|---|---|---|
| A | 01-feature-pattern.md | Spec exists on disk; boundary section present; implementation only |
| B | 02-bug-fix-pattern.md | Specific observed vs. expected behavior; existing failing test as ground truth |
| C | 03-refactor-pattern.md | Moving code without changing behavior; must be atomic and incremental |
| D | 04-architecture-pattern.md | Decision between structural alternatives; no implementation yet |

---

## Step 2: Write Two Prompts

Choose **two** of the four tasks. Write the full prompt for each using the pattern template.

Requirements:
- Copy the template from the pattern file.
- Fill every field — no placeholders.
- For Task A: spec file must exist before you write the prompt. Create a minimal spec file if needed.
- For Task B: state the hypothesis as one sentence with file and mechanism.
- For Task C: write all steps; each must be independently compilable.
- For Task D: include all six fields per option; end with "do not recommend."

Write your prompts here before sending them:

**Prompt for Task ___:**

```
(your prompt here)
```

**Prompt for Task ___:**

```
(your prompt here)
```

---

## Step 3: Send and Observe

Send each prompt to Claude Code or Cursor. Do not intervene mid-output.

After each response, run the "What to Reject" checklist from the relevant pattern file.

---

## Step 4: Audit the Output

Record your observations for each task you prompted.

**Task ___:**

| Check | Pass / Fail | Notes |
|---|---|---|
| Output stayed within stated scope | | |
| No unauthorized files modified | | |
| No behavior added beyond the prompt | | |
| Verification command (if applicable) passes | | |
| Specific rejection trigger (if any) | | |

**Task ___:**

| Check | Pass / Fail | Notes |
|---|---|---|
| Output stayed within stated scope | | |
| No unauthorized files modified | | |
| No behavior added beyond the prompt | | |
| Verification command (if applicable) passes | | |
| Specific rejection trigger (if any) | | |

---

## Step 5: Record What Was Rejected

For each output, list what you rejected and why.

If nothing was rejected, write "nothing rejected" — then ask: was the output genuinely clean, or did you not look hard enough? Apply the checklist again.

**Task ___:**
- Rejected: 
- Why:

**Task ___:**
- Rejected:
- Why:

---

## Lab Completion Checklist

- [ ] Pattern selected for all four tasks with justification
- [ ] Two full prompts written before sending (no placeholders)
- [ ] Output audited against the "What to Reject" checklist for both tasks
- [ ] Rejected items recorded with specific reasons
- [ ] Verification command ran and passed (for Tasks A, B, C)
- [ ] No fixes applied during a review-only output (if Task B review was involved)
- [ ] One sentence written: what would break if you had used the wrong pattern for one of your tasks
