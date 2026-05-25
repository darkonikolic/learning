# Context ownership

Claude does not know your codebase. It knows what you put in front of it this session. That is the complete model. Every assumption about ambient knowledge is a mistake.

Context ownership means: you decide what enters the context window, when, and why. Claude consumes what you give it. Nothing else.

---

## What the context window is

The context window is the total text Claude can process in a single session: your messages, Claude's responses, file contents you've loaded, tool results, CLAUDE.md, rules, and skills. It is finite. It degrades as it fills. It resets when you start a new session.

Current Claude models: 100k–200k token context windows. Sounds large. In practice, pasting three Go files, a plan, and 20 turns of chat gets you there faster than expected.

Two reasons context size matters:
1. **Cost**: every token in context is charged.
2. **Quality**: as context fills with irrelevant content, response quality drops. The model attends to more noise and less signal.

---

## What belongs in context

| Belongs | Why |
|---|---|
| The problem statement | Claude cannot work without it |
| The relevant code section (not the whole file) | Signal for the specific change |
| Explicit constraints for this session | Must/must-not that aren't in CLAUDE.md |
| The desired artifact description | Claude needs an output target |
| Error messages or test output | Specific evidence for debugging |
| The plan file path or content | Bounds execution |

A piece of content earns its place in context if removing it would cause Claude to make a different decision. If it wouldn't change the response, it doesn't belong.

---

## What doesn't belong in context

| Doesn't belong | Why |
|---|---|
| Full file dumps | Paste only the relevant function or struct |
| Unrelated earlier decisions | Start a new session for a new problem |
| Future scope / "we'll also need to..." | Out-of-scope by definition |
| Git history or changelogs | Not relevant to the current edit |
| Other files in the same package that aren't touched | Noise |
| Documentation that isn't directly referenced | Noise |

The anti-pattern: "let me paste the whole codebase so Claude has full context." This produces worse results than a targeted 50-line excerpt, costs more, and generates responses that address imaginary concerns from files you didn't ask about.

---

## How to build context deliberately

### Use /read for specific files, not whole directories

Bad:
```
Read everything in internal/
```

Good:
```
Read internal/store/store.go — I need to understand the Task struct and Store interface before writing the handler.
```

Read exactly what is needed for the next decision. Nothing else.

### The one-file-at-a-time principle

For large codebases, read one file per question. Read a second file only if the first file's content revealed a dependency that requires it.

Sequence for the task-api:
1. Read main.go — understand routing setup
2. Read internal/store/store.go — understand storage interface
3. Now write the handler — you have enough context

Not: read all six files upfront "just in case."

### Reference CLAUDE.md, don't repeat it

CLAUDE.md loads automatically. Don't paste its content into your messages. If a constraint from CLAUDE.md is relevant, say "as per CLAUDE.md constraints" — don't copy the text.

---

## Context hierarchy

| Layer | What it contains | Loaded when |
|---|---|---|
| CLAUDE.md (global `~/.claude/`) | Cross-project conventions | Every session |
| CLAUDE.md (project root) | Project-specific stack, constraints, gotchas | Every session |
| `.claude/rules/*.md` | Scoped must/must-not | On path match or always |
| Explicit additions | Files you /read, code you paste | When you add them |
| Session chat | Your messages + Claude responses | Accumulates during session |

CLAUDE.md is always there. You don't need to repeat it. Everything else is your responsibility to add deliberately.

---

## Signs of context pollution

You have context pollution when:

- Claude suggests something you didn't ask about from a different part of the codebase
- Claude references a "decision" from earlier in the chat that no longer applies
- Claude's response addresses the wrong file or the wrong layer
- Responses are getting longer but less specific
- Claude hallucinates a function name that doesn't exist — it's interpolating from noise

These are not model failures. They are context management failures. Claude is responding to what's actually in context, which has drifted from what's relevant.

---

## How to repair polluted context

| Tool | When to use it | What it does | What you lose |
|---|---|---|---|
| `/compact` | Mid-session, large context, switching sub-problems | Compresses history to summary | Detail from compressed turns |
| `/clear` | Context is corrupted or task is complete | Wipes the session | Everything — restart fresh |
| Restart with tighter framing | Same problem keeps drifting | New session with lean opener | Previous chat |

Use `/compact` before switching to a new sub-problem within the same session. Do not use it mid-task where losing intermediate reasoning breaks continuity.

Use `/clear` when you realize the session has been polluted from the start — bad opener, scope scatter, irrelevant files loaded. The cost of restarting is lower than the cost of continuing with bad context.

---

## Practical rules for context management

**Before adding anything to context, answer:** "Does this change what Claude should output?" If no, don't add it.

**Before pasting a file:** paste only the function or struct that matters. Add a comment: "Only the relevant section follows; rest of file omitted."

**After 20 turns:** run `/compact`. Context quality has likely degraded.

**Before a new sub-problem:** either `/compact` or open a new session. Never carry prior sub-problem context forward.

**When Claude references something you didn't ask about:** it's in context. Find it and remove it with `/compact` or restart.

---

## Task-api example: good vs bad context loading

Bad — for writing the POST /tasks handler:
```
Here's my whole project. main.go [400 lines], store.go [200 lines],
all three test files, the go.mod, and the README.
Write the POST /tasks handler.
```

Good:
```
Read internal/store/store.go — I need the Task struct and AddTask method signature.
Then write internal/handlers/tasks.go: POST /tasks handler using that interface.
Constraints: validate title non-empty and max 200 chars. Return 201 with task JSON.
Out of scope: authentication, GET /tasks, PATCH.
```

The second version gives Claude exactly what it needs. The first gives Claude everything and hopes it finds the signal.

---

## Checklist

- [ ] I can name everything that is currently in my context window.
- [ ] Every item in context has a reason: removing it would change Claude's output.
- [ ] I am reading specific functions/structs, not whole files.
- [ ] I ran /compact before switching to a new sub-problem.
- [ ] CLAUDE.md is not being duplicated in my messages.
- [ ] When Claude hallucinates or drifts, I identify the context pollution cause.
- [ ] I open a new session for a new problem rather than continuing with polluted context.
- [ ] My session opener explicitly lists what is out of scope.
