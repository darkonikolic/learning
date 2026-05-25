# Context for different task types

Concrete examples for task-api. Each task type has a different context shape. Using the wrong shape forces Claude to guess what it should already know, or floods it with irrelevant content it has to ignore.

---

## Debug session context

What to include: exact error message, stack trace if available, the specific function that fails, the test that reproduces it.

What to exclude: unrelated handlers, infrastructure files, tests for other features, migration files, anything not in the failure's call path.

Why: a debug session has a narrow blast radius. You are looking for one wrong thing in one specific place. Context that puts Claude in the right 50 lines of code beats context that puts Claude in the right file.

**task-api debug example:**

Scenario: POST /tasks returns 200 instead of 201.

Wrong context approach:
```
Something is broken in the task API. Can you look at it?
```
Claude will read the whole codebase, form opinions about unrelated things, and probably miss the specific issue.

Correct context approach:
```
POST /tasks returns 200 instead of 201. The handler is not setting the status code explicitly.

Handler: internal/handler/task.go, CreateTask function (read this)
Test that fails: internal/handler/task_test.go, TestCreateTaskReturns201 (read this)

The test:
  assert.Equal(t, http.StatusCreated, w.Code)  // line 34

The handler currently calls:
  json.NewEncoder(w).Encode(task)
  
It never calls w.WriteHeader(). Find where WriteHeader should be called and what status code.
```

This message gives Claude:
- The exact failure (wrong status code)
- The exact location (CreateTask function)
- The exact test (TestCreateTaskReturns201)
- The diagnostic already done (WriteHeader is missing)
- The question (where should it go, what code)

Claude does not need to read the whole codebase. It needs to read one function and one test.

**Debug message template:**
```
[Error]: [exact error message or test failure output]
[Location]: [function name, file path]
[Reproducer]: [test name, file path]
[Observation]: [what you've already diagnosed]
[Question]: [what you need to determine]

Read [file1] and [file2] only.
```

---

## Architecture session context

What to include: current package structure (can be a brief listing, not file contents), key interfaces, the specific problem you're trying to solve.

What to exclude: implementation details of each function, test files, configuration files, anything that is stable and not being reconsidered.

Why: architecture decisions are about relationships between components. Claude needs to understand the current structure to reason about alternatives. It does not need every line of every function.

**task-api architecture example:**

Scenario: validation logic is currently in the handler. You want to discuss moving it.

Wrong context approach: paste internal/handler/task.go (200 lines).

Correct context approach:
```
Current structure of the handler (interface only, not full implementation):

func (h *Handler) CreateTask(w http.ResponseWriter, r *http.Request) {
    // reads body
    // validates title (currently here — want to move)
    // calls h.store.AddTask()
}

type Store interface {
    AddTask(ctx context.Context, title string, description string) (Task, error)
    GetAll(ctx context.Context) ([]Task, error)
    Complete(ctx context.Context, id string) (Task, error)
}

Current package layout:
- internal/handler/ (HTTP concerns + validation currently)
- internal/store/  (data storage)

Problem: validation in the handler is fine for simple cases, but we'll have three handlers
sharing the same validation rules. Want to avoid duplication.

Propose where to put validation logic. Options to consider:
1. internal/domain/ package with domain functions
2. internal/handler/ middleware
3. Keep in handler, extract to shared validation functions

Constraints: stdlib only. No external validation libraries.
```

This context gives Claude enough to reason about the architecture without drowning in implementation details.

**Architecture message template:**
```
Current structure: [package layout or key interfaces — not full implementations]
Problem: [what is wrong or what decision needs making]
Constraints: [stack constraints, must/must-not]
Options to consider: [what you want evaluated — optional]

Do not show implementation — only the structural decision.
```

---

## SPEC writing context

What to include: problem statement (what the endpoint or feature should do), constraints (what are the hard rules), one adjacent SPEC for format consistency.

What to exclude: existing implementation — you are specifying what SHOULD be, not documenting what IS. Including the implementation biases Claude toward ratifying existing code rather than specifying correct behavior.

Why: a SPEC written from a clean problem statement is a contract. A SPEC written from looking at the implementation is documentation. These are different things.

**task-api SPEC writing example:**

Scenario: writing SPEC for PATCH /tasks/:id/complete.

Wrong context approach: "Read internal/handler/task.go and write a spec for the complete endpoint."

Correct context approach:
```
Write SPEC for PATCH /tasks/:id/complete. 

Do not read any existing implementation before writing. This is a specification, not documentation.

Requirements:
- Mark a task as complete
- Task must exist (404 if not found)
- Already-complete is idempotent: return 200, do not return 409
- Response: completed task as JSON
- Status codes: 200 on success, 404 not found, 400 invalid id format

Format: match docs/specs/post-tasks.md section structure exactly.
Output: docs/specs/patch-tasks-complete.md
```

Reading `docs/specs/post-tasks.md` is appropriate because you want format consistency, not because it defines behavior. The behavior comes from the requirements you stated.

**SPEC writing message template:**
```
Write SPEC for [feature/endpoint].

Do not read existing implementation.

Requirements:
- [behavioral requirement]
- [edge case]
- [error case]

Constraints:
- [hard constraint]
- [hard constraint]

Format: match [adjacent-spec.md] section structure.
Output: [output path]
```

---

## Refactor context

What to include: the current code being changed, what pattern you want to move toward, one example of the target pattern if it exists elsewhere.

What to exclude: code that is not being touched. If you're refactoring validation logic, you don't need the router, the store implementation, or the test helpers.

Why: refactoring is about transforming existing code. Claude needs to see what it's transforming and what it should look like after. It does not need the full context of everything around it.

**task-api refactor example:**

Scenario: extracting validation from handlers into a domain layer.

Current state: validation is inline in CreateTask handler.
Target state: validation function in internal/domain/task.go, called by handler.

```
Refactor: move validation from the handler into a new domain layer.

Current code (read this):
- internal/handler/task.go — contains inline validation in CreateTask

Target pattern (create this):
- internal/domain/task.go — pure validation functions, no HTTP concerns
- Signature: func ValidateCreateTask(title string, description string) error

Refactor rules:
- Handler calls domain.ValidateCreateTask() and returns 400 if non-nil error
- Domain function returns a descriptive error string (not an HTTP status)
- Do not change: store interface, Store implementation, test helpers

Show the refactored handler and the new domain file. Nothing else.
```

The constraint "do not change: store interface, store implementation, test helpers" is explicit. Without it, Claude may helpfully refactor adjacent things you didn't ask it to touch.

**Refactor message template:**
```
Refactor: [what you're changing]

Current code (read this): [files with code being changed]
Target pattern: [what it should look like after, or an example to match]

Refactor rules:
- [specific transformation]
- [what must not change]
- [what must not change]

Output: [refactored files only — not adjacent files]
```

---

## Cross-task context discipline

One rule that applies across all task types: tell Claude what NOT to read.

If you point Claude at a directory and say "read internal/handler/", Claude will read every file in that directory. If you only need it to read task.go, say "read internal/handler/task.go only."

Explicit exclusion:
```
Read internal/handler/task.go only. Do not read health.go or middleware.go.
```

This is especially important in a codebase with many files. Claude's tendency to be helpful means it reads adjacent context. Sometimes that helps. Often it introduces noise.

The cost of over-reading: Claude may be influenced by patterns in files you didn't intend to include. It may suggest refactoring things you weren't asking about. Its attention is divided.

---

## Quick reference

| Symptom | Cause | Fix |
|---------|-------|-----|
| Claude changes unrelated code | Too broad file inclusion | Specify exact files, add "do not change X" |
| Claude misses the bug | Wrong file in context | Include the exact function, not the file |
| SPEC ratifies existing code | Implementation in context when writing SPEC | Exclude implementation from SPEC-writing sessions |
| Refactor goes too far | No stop boundaries | Explicit "do not change X, Y, Z" |
| Architecture answer is shallow | Too much detail, too little structure | Use interface signatures, not implementations |

---

## Checklist

- [ ] For debug tasks: error message + specific function + failing test — nothing more.
- [ ] For architecture tasks: interfaces and structure — not full implementations.
- [ ] For SPEC writing: problem statement + constraints — no existing implementation.
- [ ] For refactoring: current code + target pattern + explicit do-not-change list.
- [ ] I specify exact files, not directories, when Claude only needs specific files.
- [ ] I add explicit "do not change X" when I want to prevent scope creep.
- [ ] I exclude implementation when writing a SPEC, to avoid ratifying existing code.
