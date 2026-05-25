# From discuss to CONTEXT.md

The discuss phase exists for one reason: surface unknowns before they become wrong code. A plan built on unclear assumptions produces a correct implementation of the wrong thing. CONTEXT.md is the human gate that stops that.

---

## Why discuss-phase before plan-phase

Planning is cheap. Execution is expensive. CONTEXT.md is a 30-line text file. A misunderstood requirement in CONTEXT.md costs minutes to fix. The same misunderstanding in code costs a full re-execute cycle, state repair, and possible rework of dependent tasks.

The discuss-phase runs a structured interview: GSD asks questions about the goal, constraints, boundaries, and risks of the phase. When it has enough answers, it writes CONTEXT.md. Your job is to edit that file before plan-phase reads it.

**Rule:** CONTEXT.md is not plan input until you have edited it. What GSD writes is a draft. What you approve is the gate.

---

## Running `/gsd:discuss-phase <N>`

```
/gsd:discuss-phase 1
```

GSD asks adaptive questions. The depth depends on how much information is already in PROJECT.md and REQUIREMENTS.md. If you bootstrapped the project with a detailed vision, the interview is short. If PROJECT.md is sparse, expect more questions.

**`--batch` flag:**

```
/gsd:discuss-phase 1 --batch
```

Presents all questions at once rather than one at a time. Faster when you know what to specify. For new users or unfamiliar domains, the default conversational mode surfaces gaps you would have skipped in batch.

When to use `--batch`:
- You have used GSD on several projects and know what CONTEXT.md needs.
- The phase is simple and well-understood.
- You want to answer all questions offline, paste them back, and move on.

When to use default (conversational):
- New project with many unknowns.
- Phase is architecturally complex.
- Previous discuss runs produced vague CONTEXT.md — the back-and-forth helps.

---

## What CONTEXT.md must contain

After discuss-phase writes it and before you approve it, CONTEXT.md must satisfy this template:

```markdown
# Phase N: [Concise Name]

## Goal
One sentence. Observable outcome when phase is done.
Must be verifiable with a single check (curl, test, grep).

## Non-goals
- [Explicit things OUT of scope for this phase]
- [Use this to prevent the most likely scope creep]
- [At least two entries; three is better]

## Constraints
- [Hard technical rules: language, library, pattern]
- [Performance bounds if measurable]
- [Integration requirements]

## Boundaries
- [What this phase owns end-to-end]
- [What it delegates to a later phase]
- [What it depends on from a prior phase]

## Acceptance criteria
- [Testable outcome 1]
- [Testable outcome 2]
- [All items should be curl-verifiable or test-assertable]

## Open questions
[Must be empty or explicitly deferred with risk noted before plan-phase proceeds]
```

---

## Task-api Phase 1 example

Bad CONTEXT.md (GSD draft, unedited):

```markdown
# Phase 1: Task Creation

## Goal
Implement the task creation functionality to allow users to create tasks
through the REST API endpoint in a reliable and efficient manner.

## Non-goals
N/A

## Constraints
Standard library preferred.

## Open questions
- How should errors be formatted?
- What fields should the task contain?
```

Good CONTEXT.md (after human editing):

```markdown
# Phase 1: POST /tasks endpoint

## Goal
POST /tasks accepts a JSON body with a required title field and returns 201
with the created task object including auto-assigned integer ID.

## Non-goals
- No authentication or authorization
- No database or persistence (data lost on restart by design)
- No GET /tasks or PATCH /tasks/:id endpoints (later phases)
- No filtering, sorting, or pagination

## Constraints
- Standard library only: net/http, encoding/json, no external packages
- IDs are sequential integers starting at 1 (not UUIDs)
- In-memory storage: global slice, no concurrency protection needed (single-threaded for now)

## Boundaries
- This phase owns: task struct, in-memory store, POST handler, route registration, main.go wiring
- Delegates to Phase 2: GET handler
- Depends on: nothing (greenfield)

## Acceptance criteria
- POST /tasks with {"title":"buy milk"} returns 201 and {"id":1,"title":"buy milk","done":false}
- POST /tasks with {} returns 400 and {"error":"title is required"}
- POST /tasks with {"title":""} returns 400 and {"error":"title is required"}
- POST /tasks with {"title": string of 201 chars} returns 400
- Second task has id:2

## Open questions
(none — all resolved above)
```

The difference is not length — it is verifiability. Every line in the good version has a corresponding curl command that proves it.

---

## CONTEXT.md editing: what to look for and fix

### Signs of bad CONTEXT.md

- Goal contains "appropriate", "efficiently", "robust", "handle edge cases" — these are not observable
- Non-goals section is empty or missing
- Open questions exist without resolution or explicit deferral
- Acceptance criteria are missing or say "should work as expected"
- Constraints say "preferred" instead of specifying the actual constraint
- Goal requires multiple sentences to express

### Signs of good CONTEXT.md

- Goal verifiable in one curl command or test assertion
- Non-goals explicitly name the three most likely scope creep items
- Zero unresolved open questions
- Every acceptance criterion has an obvious corresponding test
- Constraints leave no implementation choices ambiguous

### Editing procedure

1. Read the goal sentence. Can you write the curl command that proves it? If not, rewrite.
2. Read non-goals. What is the one feature someone would assume is in scope? Add it as a non-goal.
3. Check open questions. If any exist: answer them in the body, then delete the question. Never plan with open questions.
4. Read acceptance criteria. For each: can a Go test assert this directly? If not, make it more specific.

---

## Spec-phase vs discuss-phase

Two commands exist for pre-planning clarification. They solve different problems:

| Command | When | Output | Ambiguity addressed |
|---------|------|--------|---------------------|
| `/gsd:discuss-phase N` | Intent is fuzzy — you know WHY but not HOW | CONTEXT.md | Goals and constraints unclear |
| `/gsd:spec-phase N` | Deliverables are ambiguous — you know WHAT but not the exact contract | SPEC.md with ambiguity score | Acceptance criteria and output shape unclear |

The most common mistake: using discuss-phase when the real problem is that you cannot describe the outputs. If you can say "Phase 1 is done when POST /tasks works" but cannot describe what the response body looks like, you need spec-phase, not discuss-phase.

**When to run both:** Major phase with unclear scope and unclear contract — run spec-phase first to nail the deliverables, then discuss-phase to capture constraints and boundaries.

**When one is enough:** For the task-api toy project, discuss-phase is sufficient. The deliverables are obvious (201 with task JSON). Use spec-phase when building something genuinely novel.

---

## The human gate rule

CONTEXT.md is the first and most important human gate. Its purpose is not to produce a document — it is to force a decision. Every line you remove is a scope you are eliminating. Every acceptance criterion you add is a commitment the executor agent must meet.

Gate rule: do not run `/gsd:plan-phase N` until:
1. You have read every line of CONTEXT.md
2. You have edited at least the goal sentence and non-goals
3. Open questions section is empty
4. Every acceptance criterion is verifiable

If you skip this gate, you are delegating the phase definition to the model. The model will write a plan for the phase it imagined, not the phase you needed.

---

## Checklist

- [ ] I can explain why discuss-phase exists and what problem it prevents.
- [ ] I know what --batch does and when to prefer it over conversational mode.
- [ ] I know the six sections that CONTEXT.md must contain.
- [ ] I can identify a vague goal sentence and rewrite it as a verifiable one.
- [ ] I know the difference between discuss-phase and spec-phase and when each applies.
- [ ] I have edited a CONTEXT.md goal sentence at least once before planning.
- [ ] I understand that open questions must be resolved before plan-phase runs.
- [ ] I can name three signs of a bad CONTEXT.md without looking at this file.
