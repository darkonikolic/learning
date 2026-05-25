# Review Discipline

## The review workflow

Read the entire output before accepting any of it. Partial acceptance is not acceptance — if you merge line 1 through 40 without reading lines 41 through 80, you accepted all of it. You just did it uninformed.

The review is not a skim. It is a structured check against your binary criteria. You run each criterion against the output and record pass or fail. You do not accept until every CRITICAL and HIGH item is resolved.

**Sequence:**
1. Read the full output. Do not touch Accept, Apply, or merge until you finish.
2. Run each binary criterion. Record: pass or fail.
3. Inspect for unasked-for changes (see below).
4. Classify any issues you found.
5. Make the accept/reject/correct decision.

---

## What to check in code output

### 1. Does it touch only the files it should?

If your prompt was "add a PATCH handler to `internal/handler/tasks.go`", the output should touch `internal/handler/tasks.go` and possibly its test file. It should not touch `internal/store/tasks.go`, `main.go`, or `go.mod` unless you explicitly asked it to.

Check the diff scope before reviewing content. Unexpected file modifications are a disqualifying signal before you read a single line.

### 2. Does it add behavior not asked for?

"Add a PATCH handler" should produce a PATCH handler. It should not add logging middleware, restructure the router, rename existing handlers, or refactor the store interface. These are changes you didn't request. They may be reasonable. They are still not what you asked for, and they carry risk you haven't evaluated.

Extra behavior requires its own binary criteria. You don't have them, so you can't evaluate it. Reject it.

### 3. Does it satisfy each binary criterion?

Work through the criteria you wrote before sending the prompt. For each:
- State which criterion you're checking.
- Point to the specific line or block in the output that addresses it.
- Mark pass or fail.

If you didn't write criteria before sending the prompt, you have to write them now — then check the output against them. This is slower and harder than writing them first.

### 4. Does it break anything that was working?

This is not always visible in a code review. Run the test suite. If tests fail that were passing before, you have a regression. The output is rejected regardless of how well it satisfies your criteria for the new feature.

---

## Severity classification

| Severity | Meaning | Examples |
|---|---|---|
| **CRITICAL** | Breaks correctness or security | Wrong return value, missing auth check, data written to wrong location, SQL injection surface, panic path not handled |
| **HIGH** | Wrong behavior, data loss risk | Feature doesn't satisfy its primary criterion, silently drops errors, wrong HTTP status code |
| **MEDIUM** | Tech debt, maintainability | Duplicate logic, exported symbol that should be unexported, hardcoded value that should be a constant |
| **LOW** | Style, naming | Variable name inconsistent with codebase convention, comment spelling, unnecessary blank line |

When in doubt between two levels, use the higher one.

---

## Accept / reject / correct decisions

- **CRITICAL found** → Reject. Start a new prompt with the correction (see below). Do not patch the accepted output.
- **HIGH found** → Reject. Same as CRITICAL. A wrong behavior is a wrong implementation regardless of how clean the code looks.
- **MEDIUM found** → Decide explicitly. Either accept it and immediately file it as known debt with a location reference, or reject and add it to the correction prompt. Do not let MEDIUM issues accumulate silently.
- **LOW found** → Note and defer. Accept the output. Add the LOW item to a deferred list. Address it in a dedicated cleanup session.
- **All criteria pass, no issues** → Accept.

---

## The correction prompt structure

When rejecting, use this structure:

```
Output accepted except: [specific issue at specific location].
Fix only this. Do not change anything else.
```

**Example:**

```
Output accepted except: the PATCH handler at internal/handler/tasks.go:47
does not return HTTP 404 when the task ID does not exist in the store — it
returns HTTP 500 with the store error exposed in the response body.

Fix only this. Do not change the request parsing, the response struct,
or anything in the store layer. Do not change anything else.
```

The phrase "fix only this" is load-bearing. Without it, a second pass may fix your CRITICAL issue and introduce two new MEDIUM ones. Constrain the scope explicitly.

Do not describe what you want instead. Describe what is wrong and where. The model derives the fix from the description of the problem. If you find yourself writing "instead, do X", you are writing a new prompt, not a correction.

---

## What not to do

**Do not accept then fix in the same session.**

If you accepted it, you own it. Once you click Accept or Apply, the code is in your codebase. Asking the model to fix it in the next message means you're asking it to modify code that is now your responsibility. That's a new session with a new scope, not a continuation of review.

The accept step is a gate, not a checkpoint. Pass/fail, not "mostly pass".

**Do not accept with comments like "I'll clean this up later."**

"Later" is not a work item. If you mean it, open a concrete task: file name, line number, what needs to change. Otherwise you've accepted a known defect with no remediation path.

**Do not use phrases like "mostly looks correct."**

Mostly is not binary. If you're using "mostly," you have an issue you haven't classified. Classify it. Then decide.

---

## Session checklist

- [ ] Read the full output before accepting any part of it
- [ ] Checked file scope: output touches only files it should
- [ ] Checked for unasked-for behavior additions
- [ ] Ran each binary criterion against the output
- [ ] Classified each issue with severity (CRITICAL / HIGH / MEDIUM / LOW)
- [ ] Made explicit accept/reject/correct decision for each severity level
- [ ] If rejecting: correction prompt uses the structure above
- [ ] Did not accept then attempt to fix in the same session
