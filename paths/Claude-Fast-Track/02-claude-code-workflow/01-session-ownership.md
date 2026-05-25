# Session ownership

The model executes. You own the session. That distinction is the entire difference between a tool that drifts and a tool that ships.

A session without an owner becomes a conversation. Conversations produce suggestions. Sessions produce artifacts.

---

## The core shift

| Passive user | Session owner |
|---|---|
| Opens Claude and types a vague request | States the problem, scope boundary, and desired artifact before anything else |
| Asks Claude to "figure out the best approach" | Decomposes the problem in their own words first |
| Accepts whatever Claude returns | Reviews output against explicit acceptance criteria |
| Lets the session run until it feels done | Decides when the session is closed and captures what changed |
| Treats context as Claude's responsibility | Manages context deliberately: what's in, what's out |
| Asks "did you do it right?" | Maps each acceptance item to a verification step |
| Relies on chat memory | Writes decisions to CLAUDE.md and plan files |

The model is stateless between sessions and degrading within a long session. You are the persistent layer.

---

## Three modes of a session

### Thinking mode (decompose)

You work alone. No code, no Claude output yet.

- Write the problem in one sentence.
- List what is explicitly out of scope.
- Write 3–7 steps in your own words.
- Identify the artifact you want: code file, plan, spec, curl output, diff.

If you cannot do this in under five minutes, the problem is not scoped. Stop and scope it.

### Planning mode (/plan)

Claude proposes a plan. You read it, edit it, approve it. No code executes.

Use `/plan` when:
- The change touches more than one file
- The change has a rollback concern
- You aren't sure what files are involved
- You want to verify scope before tokens are spent on implementation

Do not use `/plan` for single-file edits with a clear, bounded outcome you can describe entirely yourself.

### Execution mode

Claude writes code, edits files, runs commands — bounded by the approved plan. You watch the execution, interrupt when scope creep appears, verify the output against acceptance criteria.

Execution without an approved plan is exploration, not engineering.

---

## When to use each mode — decision rules

| Situation | Mode |
|---|---|
| You haven't framed the problem yet | Thinking only — don't open Claude yet |
| Change touches 2+ files | Thinking then /plan then execution |
| Single-file bounded edit, outcome is clear | Thinking then execution (no /plan needed) |
| Mid-session you realize scope expanded | Stop execution, return to /plan |
| You need to understand the codebase before deciding | Thinking + read-only Claude queries, no writes |
| Debugging a specific known issue | Execution with explicit bounds ("only touch X") |

---

## The one-problem-per-session principle

A session degrades when it holds multiple unrelated problems. Context fills with irrelevant history. Claude starts referencing earlier decisions that don't apply. Suggestions become broader and less precise.

Context scatter kills quality in three ways:

1. Earlier irrelevant code snippets pollute responses to later questions.
2. Claude interpolates between problems and generates hybrid suggestions that solve neither.
3. You lose the ability to verify: which output addresses which problem?

One session = one artifact. If a second problem surfaces mid-session, capture it as a note and open a new session after this one closes.

The session ends when the acceptance criteria are met and the artifact is saved. Not when the conversation feels complete.

---

## How to open a session correctly

Three required components:

1. **Problem statement** — one sentence, specific and grounded. References the actual file, endpoint, or system component.
2. **Out-of-scope** — what you are explicitly not doing in this session.
3. **Desired artifact** — the concrete thing that will exist on disk when this session ends.

### Bad session opener

```
I want to build the task manager API. Can you help me figure out what to do?
```

Problems: no scope boundary, no artifact specified, no decomposition, invites Claude to define the work.

### Good session opener

```
Problem: Add POST /tasks endpoint to the task-api Go project.
The handler validates title (required, max 200 chars), stores the task in-memory,
returns 201 with JSON body containing id, title, completed, created_at.

Out of scope: database persistence, authentication, GET /tasks, PATCH /tasks/:id/complete.

Desired artifact: internal/handlers/tasks.go with the handler + TestPostTask passing.
```

What this does:
- Claude knows exactly what to build
- Claude cannot drift into related features
- You have an objective verification target
- The session is closeable when the test passes

---

## How to close a session

A session is closed — not just abandoned. Closing requires three steps:

1. **Verify the artifact** against the acceptance criteria you opened with.
2. **Capture what changed** that wasn't on disk at session start: decisions made, constraints discovered, patterns that should persist.
3. **Update CLAUDE.md** if a constraint, convention, or gotcha emerged that should apply to future sessions on this project.

If you close without capturing, the next session starts with less context than this one ended with. You will re-discover the same constraints.

A session that ends with "looks good!" and no capture is half a session.

---

## Mindset table

| Passive user | Session owner |
|---|---|
| "Claude will figure out the approach" | "I specify the approach; Claude implements it" |
| "Let me see what it produces" | "I know what artifact I want before I start" |
| "I'll clean it up later" | "Acceptance criteria are defined before execution" |
| "The conversation is the record" | "The plan file and CLAUDE.md are the record" |
| "That's not quite right, try again" | "Specific flaw: missing idempotency check at line 42" |
| "It's done when it feels done" | "It's done when the acceptance checklist is complete" |

---

## Checklist

- [ ] I can state the problem in one sentence before opening Claude.
- [ ] I have written explicit out-of-scope items before the session opener.
- [ ] I can name the artifact that will exist on disk when this session ends.
- [ ] I have decomposed the problem into 3-7 steps in my own words.
- [ ] I know which mode I am starting in: thinking, /plan, or execution.
- [ ] I have a verification step for each acceptance item.
- [ ] I will capture decisions to CLAUDE.md before closing the session.
- [ ] I will open a new session for any problem that surfaces during this one.
