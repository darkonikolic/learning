# Hallucination Recovery

## Detection signals

- A function or method name appears in the output that does not exist in your codebase
- Behavior is described that no test covers and no code implements
- The model refers to a prior conversation or decision that never happened ("as we discussed", "based on what you said earlier")
- An import path is slightly wrong — package exists but the specific symbol does not
- The model describes what a function *should* do, not what it *does*
- A struct field is used that isn't in your type definition

---

## Why it happens

The model generates plausible continuations. When it lacks a ground truth (your actual codebase, the actual API), it fills gaps with statistically likely names and behaviors. The output is syntactically valid and semantically coherent. It is not true.

Hallucinations compound: if you accept an invented function name and continue, the next turn builds on that invention. By turn 4 you have a coherent but entirely fictional subsystem.

**Do not continue the session after detecting a hallucination.**

---

## Recovery: 3 steps

1. **Identify exactly what was invented.**
   Name it specifically. "The function `task.FindByTag` does not exist" — not "something seems wrong."

2. **Isolate it. Do not merge or accept the output.**
   In Claude Code: do not run `git add`. In Cursor: reject the diff. Treat the entire output as suspect if it contains one hallucination.

3. **Re-prompt with the specific correction and the real source.**
   Give the model the actual thing to use, not just a correction.

```
# Recovery prompt structure

The function `task.FindByTag` does not exist in this codebase.
The real function is `task.ListByFilter(ctx, filter TaskFilter)` — see internal/task/query.go line 44.

Rewrite the handler using `task.ListByFilter`. Do not invent any other function names.
Before using any function, confirm it exists in the file I just referenced.
```

---

## The grounding instruction

Add this to any prompt where the model will write code against your codebase:

```
Verify each function name exists before using it.
If you are unsure whether a function exists, stop and ask — do not invent a plausible name.
```

This works because it shifts the model from generation mode ("what would make sense here?") to verification mode ("does this actually exist?").

For larger codebases, be more specific:

```
All task operations are in internal/task/.
All HTTP handlers are in internal/api/.
Do not use any function from a package not listed here without asking first.
```

---

## Tool-specific notes

**Claude Code:**
Hallucinations in code are caught by `go build`. Run the build after every non-trivial generation. A build failure on a function that "should exist" is a hallucination signal — stop there, do not try to fix the invented function, fix the prompt.

```bash
go build ./... 2>&1 | grep "undefined:"
```

Undefined symbols are the hallucination ledger. Each one is an invented name.

**Cursor:**
The editor will not stop you from accepting a diff that calls a nonexistent function. Check every new function name before accepting:
- Hover to see if the IDE can resolve it
- Search the codebase for the exact symbol
- If the IDE shows an error after accept, reject immediately — do not try to "fix" an invented API

---

## Prevention

```
# Grounding block — add to any code-writing prompt

Context:
- Task model: internal/task/model.go
- Task queries: internal/task/query.go
- HTTP handlers: internal/api/task_handler.go

Rules:
- Use only functions that exist in the files above
- If you need a function that doesn't exist, say so — do not invent one
- After writing code, list every function you called and which file it comes from
```

The self-audit at the end ("list every function you called") catches hallucinations before you do. The model will either correctly cite the file or flag that it is uncertain.

---

## Checklist

- [ ] Build run after generation; zero undefined symbols
- [ ] Every new function name verified to exist in the codebase
- [ ] No output accepted that references a prior conversation you cannot confirm
- [ ] Grounding instruction in any prompt that touches existing code
- [ ] Session not continued after detecting one hallucination
- [ ] Isolation confirmed: hallucinated output not staged or merged
- [ ] Recovery prompt includes the real function/file as the explicit replacement
