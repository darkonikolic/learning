# Iteration and correction

For repair loops, prompt debt, and when to replan instead of retry, see `02-claude-code-workflow/07-prompt-repair-discipline.md`.

Each correction you send is a signal. Vague corrections train Claude to produce vague improvements. Specific corrections produce specific fixes. The correction is as important as the original prompt.

---

## The iteration principle

Every follow-up message must cite a specific problem. Not a vague feeling of wrongness. Not a quality gradient. A named, locatable flaw.

If you cannot name the specific problem, you haven't analyzed the output. Analyze before you send the correction.

| Bad correction | Why it fails |
|---|---|
| "Do better" | No information about what to improve |
| "Make it more robust" | "Robust" is not a specification |
| "This doesn't feel right" | Feelings are not actionable |
| "Clean it up" | Clean is undefined |
| "Try again" | Identical to the original prompt |
| "I think there might be an issue with error handling" | Speculation is not a correction |

---

## How to structure a correction

Three components:

1. **What is wrong** — the specific flaw
2. **Where exactly** — file, function, line range, or behavior
3. **What correct looks like** — the expected behavior or structure

Template:
```
Flaw: [specific problem]
Location: [file:line or function name or HTTP response]
Expected: [what correct behavior/output looks like]
```

### Good correction examples

For the task-api POST /tasks handler:

```
Flaw: no idempotency check — submitting the same title twice creates two tasks.
Location: internal/handlers/tasks.go, CreateTask handler
Expected: check if a task with the same title already exists in the store before inserting; return 409 if duplicate found.
```

```
Flaw: the mutex is taken for the entire handler including JSON encoding.
Location: internal/store/store.go, AddTask method
Expected: hold the mutex only during the slice append, not during JSON marshaling or HTTP writing.
```

```
Flaw: TestPostTask does not verify the response body fields.
Location: internal/handlers/tasks_test.go, TestPostTask
Expected: assert id is a positive integer, title matches input, completed is false, created_at is recent.
```

Each correction is actionable without ambiguity about what to change or why.

---

## The flaw-first round 2 practice

Before sending any follow-up, write the flaw explicitly for yourself, even if you don't include all of it in the message.

Write: "The flaw in what Claude produced is: [specific description]."

If you cannot complete that sentence, you are not ready to send a correction. Read the output again. Find the specific problem. Then send.

This practice prevents two common failures:
1. Sending a correction before you understand the output
2. Sending a vague correction that produces a vague improvement

---

## When to iterate vs when to restart

Iteration is productive when each round narrows the gap between current output and acceptance criteria.

Iteration is failing when:
- You've sent 3+ corrections about the same issue and it hasn't converged
- Each correction reveals a new fundamental flaw in the approach
- The output has drifted so far from the plan that the plan is no longer applicable
- You're correcting symptoms rather than the underlying design

| Condition | Action |
|---|---|
| 1-2 corrections on specific, locatable issues | Continue iterating |
| 3+ corrections on the same issue | Restart with better framing |
| Output reveals a flawed approach | Stop, return to /plan with new constraints |
| You can't identify what's specifically wrong | Stop, analyze the output on paper first |
| Claude is looping: same suggestion, different wording | Restart — the plan context is exhausted |

---

## Recognizing when Claude is looping

Claude is looping when:
- Response N+1 has the same structure as response N but with minor wording changes
- The code changes are syntactic (variable names, formatting) rather than semantic
- Claude starts adding explanatory comments to justify why the code is correct as-is
- The diff between consecutive outputs is smaller than expected given the correction sent

When you see looping: stop. The context is saturated with the wrong framing. A 4th correction won't fix it. Restart with a cleaner, more constrained problem statement.

---

## Multi-turn refinement: building an artifact across turns

A good multi-turn session adds one specific thing per turn. Not "improve everything." One thing.

Example sequence for building the POST /tasks handler:

**Turn 1:** Get the basic handler structure — route, parse body, return 201.
**Turn 2:** Add input validation — title required, max 200 chars, return 400 with specific error message.
**Turn 3:** Add the store interaction — call AddTask, handle error if store is full.
**Turn 4:** Write the happy-path test.
**Turn 5:** Write the error-path tests (missing title, oversized title).

Each turn has one clear addition. The artifact grows in defined increments. At any point, you know exactly what is complete and what remains.

The anti-pattern: Turn 1 prompt is "write the handler with validation, storage, error handling, and tests." This produces an artifact that superficially has all the parts but misses edge cases in each one — because you never verified any part in isolation.

---

## Escalating specificity

In multi-turn sessions, the specificity of your prompts should increase as the artifact matures.

| Turn | Specificity level | Example |
|---|---|---|
| 1 | Broad structure | "Write the handler skeleton for POST /tasks with the correct function signature and route registration" |
| 2 | Specific behavior | "Add title validation: return 400 with body `{"error":"title required"}` if title is empty or missing" |
| 3 | Edge case | "The 400 for oversized title should include the character count: `{"error":"title exceeds 200 chars","length":247}`" |
| 4 | Integration | "Verify TestPostTask calls the handler through the actual router, not directly, so middleware runs" |
| 5 | Polish | "The error response content-type must be application/json even on 400s" |

Each turn you know more about what the correct output looks like, so you can specify more precisely.

---

## Correction patterns for common failure modes

| Claude failure mode | Correction structure |
|---|---|
| Missing error case | "Flaw: [case] is not handled. Location: [function]. Expected: return [status] with [body] when [condition]." |
| Wrong abstraction level | "Flaw: direct SQL in handler. Location: [handler file]. Expected: handler calls store interface method, not SQL directly." |
| Test doesn't test the thing | "Flaw: test only asserts status code. Location: [test function]. Expected: assert [specific response field] equals [value]." |
| Oversized function | "Flaw: CreateTask is 80 lines doing 5 things. Location: [function]. Expected: extract validation to validateCreateTaskRequest(), storage to store.AddTask()." |
| Silent error | "Flaw: error from AddTask is ignored. Location: [line]. Expected: if err != nil, return 500 with log.Printf of the error." |

---

## Checklist

- [ ] Every correction I send cites a specific, named flaw.
- [ ] Every correction specifies where the flaw is located.
- [ ] Every correction states what correct behavior looks like.
- [ ] I have analyzed the output before sending a correction.
- [ ] After 3 corrections on the same issue, I restart with better framing.
- [ ] I recognize looping: same suggestion with different wording.
- [ ] My multi-turn sessions add one thing per turn, not everything at once.
- [ ] I increase specificity across turns as the artifact matures.
