# Lab — Constrain a Real Prompt

## The original prompt

```
Add input validation to the task creation endpoint
```

This prompt will produce something. It will probably work. It will also do things you didn't ask for and leave out decisions you needed to make explicitly.

## Step 1 — Identify what's missing

Go through the original prompt and mark every missing constraint:

| Missing | Why it matters |
|---|---|
| No file path | Model picks where to add validation — may add it in the wrong layer |
| No definition of "valid" | Model decides what rules apply — required fields? length? format? |
| No constraint on what "valid" means for each field | Model invents rules |
| No method constraint | Model may use a validation library, add a new struct, or inline checks |
| No scope boundary | Model may touch the handler, the service, the model, the tests |
| No non-goals | Model will add: detailed error messages, a validation struct, error codes |
| No stop condition | Model will guess if it finds ambiguity in the existing code |

The original prompt has zero constraints. It is a description of intent, not an instruction. The model will produce its best interpretation of "validation done well" — which includes every decision listed above, made silently.

## Step 2 — Rewrite using must / must not / stop-if

```
Add input validation to the POST /tasks endpoint.

Target file: internal/handler/tasks_handler.go — CreateTask function only

must: validate that the request body contains `title` (non-empty string) and `due_date` (valid RFC3339 date)
must: return 400 with the existing error response format used in this file if validation fails
must: add validation inline in the CreateTask function — do not create a separate validator type
must not: add a validation library or new dependency
must not: modify the Task model or any file other than tasks_handler.go
must not: add field-level error messages — one error message per request is enough
must not: add tests — validation only

Non-goals:
- do not validate optional fields (assignee_id, tags, description)
- do not add max-length checks unless the existing db schema enforces a constraint
- do not add a reusable validation helper — this is handler-specific logic

stop if: the existing error response format is not consistent in this file — show me what you find and ask which pattern to follow
stop if: due_date validation requires a library not already imported — ask before adding an import
```

## Step 3 — Annotations explaining each choice

```
Add input validation to the POST /tasks endpoint.
# ^ specific endpoint, not "the endpoint"

Target file: internal/handler/tasks_handler.go — CreateTask function only
# ^ scope constraint: one file, one function

must: validate that the request body contains `title` (non-empty string) and `due_date` (valid RFC3339 date)
# ^ definition of "valid" — model cannot invent rules

must: return 400 with the existing error response format used in this file if validation fails
# ^ method constraint: use what exists, don't invent

must: add validation inline in the CreateTask function — do not create a separate validator type
# ^ method constraint: prevents speculative abstraction (Signal 3)

must not: add a validation library or new dependency
# ^ method constraint: hard dependency boundary

must not: modify the Task model or any file other than tasks_handler.go
# ^ scope constraint: one-file boundary (prevents Signal 1)

must not: add field-level error messages — one error message per request is enough
# ^ prevents reasonable-but-unasked feature (prevents Signal 2)

must not: add tests — validation only
# ^ explicit non-goal so tests don't appear in the diff

Non-goals:
- do not validate optional fields (assignee_id, tags, description)
# ^ prevents "while I'm here" validation expansion
- do not add max-length checks unless the existing db schema enforces a constraint
# ^ forces a real decision, not model judgment
- do not add a reusable validation helper — this is handler-specific logic
# ^ prevents abstraction for hypothetical future use

stop if: the existing error response format is not consistent in this file — show me what you find and ask which pattern to follow
# ^ the model finding inconsistency is a decision point, not a judgment call for it to make

stop if: due_date validation requires a library not already imported — ask before adding an import
# ^ closes the gap between "no new dependency" and "but what if stdlib isn't enough"
```

## Step 4 — The experiment

Send both versions. Use the same codebase, same context, same model.

After receiving output from each version, compare:

| Dimension | Vague prompt output | Constrained prompt output |
|---|---|---|
| Files touched | Count them | Count them |
| New types or structs | Present? | Present? |
| New imports | How many? | How many? |
| Validation rules | What did the model decide? | What you specified |
| Error format | Invented or existing? | Existing (per constraint) |
| Tests added | Yes/no | No (per constraint) |
| New helpers | Yes/no | No (per constraint) |

The vague prompt will score higher on almost every "added something" dimension. That is the failure mode, not the success mode.

## Step 5 — Apply the scope audit checklist to the constrained output

Before accepting the output from the constrained prompt:

- [ ] Does the diff include only `internal/handler/tasks_handler.go`?
- [ ] Does the output add only inline validation for `title` and `due_date`?
- [ ] Are there any new types, interfaces, or validation structs in the diff?
- [ ] Did any existing function signature change (e.g., CreateTask's parameters or return type)?

If all four pass: the prompt was tight enough. Accept the output.

If any fail: identify which scope signal triggered, add the missing constraint, restart.

## Reusable format

Save this as a template for any task with validation or input handling:

```
Add [specific feature] to [specific endpoint or function].

Target file: [path] — [function name] only

must: [rule about what valid means — specific, not "validate inputs"]
must: [rule about error format — use existing pattern, specify which]
must: [method constraint — inline vs helper vs library]
must not: [dependency constraint]
must not: [file scope constraint — what cannot be touched]
must not: [feature exclusion — what the reasonable dev would add]

Non-goals:
- do not [thing 1 that seems related but is out of scope]
- do not [thing 2 that seems related but is out of scope]
- do not [thing 3 that seems related but is out of scope]

stop if: [ambiguity that requires a decision, not a guess]
stop if: [missing dependency or inconsistency the model might discover]
```

## Checklist

- [ ] Can identify at least 5 missing constraints in the original prompt
- [ ] Rewrote the prompt with at least 3 must, 3 must not, and 2 stop-if clauses
- [ ] Added 3 non-goals that prevent common scope creep for this task type
- [ ] Sent both versions and compared the diffs
- [ ] Applied the 4-question scope audit to the constrained output
- [ ] Saved a reusable template for validation tasks in this codebase
