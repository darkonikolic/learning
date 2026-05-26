# Prompt layering in practice

A well-structured message has three explicit layers on top of the implicit base already loaded from CLAUDE.md and rules. Understanding each layer's job — and what breaks when layers conflict — determines whether Claude executes correctly or drifts.

---

## The three message layers

**Layer 1 (implicit — already loaded):** CLAUDE.md constraints and rule files. You don't write these in the message. They are already active.

**Layer 2 (explicit in message):** SPEC block or plan reference. Points Claude at the approved ground truth for this task.

**Layer 3 (explicit in message):** Per-turn constraints. Narrows the scope of this specific turn.

A message that uses all three layers:
```
Implement step 3 from docs/plans/01-post-tasks-plan.md.

SPEC contract: docs/specs/post-tasks.md — acceptance section is the contract.
Do not expand scope beyond listed acceptance items.

Constraints for this turn:
- No external packages
- Return errors as JSON: {"error": "message"}
- Stop after handler implementation, no tests yet
```

What each section does:
- The task reference (`step 3 from docs/plans/<phase>-plan.md`) bounds execution to a known work unit.
- The SPEC block (`docs/specs/post-tasks.md`) points Claude at approved truth. Claude uses the acceptance section — not its own invention — to define what "done" means.
- The per-turn constraints narrow this specific execution: no scope creep, specific error format, stop condition stated explicitly.

**Edit scope (Layer 3)** — repeat or tighten when the task touches multiple files or refactors:

```text
Only modify explicitly requested scope.

Do not rename symbols unless requested.

Do not reformat unrelated code.

Do not optimize unrelated code.

Preserve architecture boundaries.

Minimize diff size.

If required changes exceed requested scope:
STOP and explain why.

List touched files before changes.

Explain blast radius before large refactors.

Preserve public contracts unless explicitly approved.
```

Same block belongs in `CLAUDE.md` for every session (`04-claude-code-configuration/01-claude-md-authoring.md`). Full workflow: `12-diff-refactor/04-idempotent-refactoring-discipline.md`.

---

## The SPEC block pattern in detail

The SPEC block is layer 2. Its job is to replace "Claude's best guess at what you want" with "the approved document that defines what you want."

Without a SPEC block, Claude fills the gap with plausible assumptions. Sometimes right. Often drifts.

With a SPEC block, Claude has a reference point. When the implementation is done, you can compare it to the SPEC and check mechanically.

Full SPEC block example:
```
SPEC contract: docs/specs/post-tasks.md

Acceptance criteria from that SPEC are the binding contract. 
If a line in the SPEC says "must return 201 on success", that is not a suggestion.
If a line says "must validate title is non-empty", that validation must be in the implementation.
Do not implement acceptance items not in the SPEC — out-of-scope additions fail review.
```

What the SPEC block does NOT do:
- It does not override CLAUDE.md constraints. If CLAUDE.md says "stdlib only" and the SPEC implies an external library, CLAUDE.md wins.
- It does not give Claude permission to invent additional behavior. The SPEC is a ceiling, not a floor.

---

## Structuring a layered message for task-api

**Scenario:** Implementing body parsing for POST /tasks.

Complete layered message:
```
Implement body parsing for the POST /tasks handler.

SPEC contract: docs/specs/post-tasks.md — the "Request body" section defines the fields.
Acceptance: title (string, required), description (string, optional).

Constraints for this turn:
- Parse only: read body, decode JSON, validate field presence.
- Stop before: validation error responses, store interaction, tests.
- Error format: {"error": "message"} on bad JSON, application/json content-type.
- Handler location: internal/handler/task.go, CreateTask function.
```

Why this works:
- CLAUDE.md is already active: stdlib only, no external packages, key paths.
- SPEC contract: specifies which section of which file defines the fields.
- Turn constraints: explicit stop condition prevents Claude from continuing to store interaction (which would happen without it).

**Second turn — expanding scope:**
```
Extend the CreateTask handler: add validation and store call.

Same SPEC contract: docs/specs/post-tasks.md — now include validation section and response section.

Constraints for this turn:
- Validate: title non-empty, max 200 chars.
- Call store.AddTask() if validation passes.
- Return 201 with created task JSON on success.
- Return 400 with {"error": "..."} on validation failure.
- Write unit tests in internal/handler/task_test.go.
```

The only change between turn 1 and turn 2: the per-turn constraints expanded. The SPEC contract is the same file. CLAUDE.md is still active.

---

## Good layering vs bad layering

**Good layering: additive, not contradictory.**

Each layer adds specificity without contradicting higher layers.

| Layer | Content | Relationship |
|-------|---------|--------------|
| Global CLAUDE.md | "Never use external packages" | Always active |
| Project CLAUDE.md | "stdlib only: net/http, encoding/json, testing" | Adds specificity |
| SPEC block | POST /tasks body fields and validation rules | Grounds truth |
| Per-turn constraint | "Stop after body parsing" | Narrows scope |

Each layer narrows without contradicting. This is good layering.

**Bad layering: contradictions cause confusion.**

Example contradiction:
- CLAUDE.md: "Always write tests with every implementation."
- Per-turn: "No tests yet."

This is technically a conflict. How Claude resolves it varies. Sometimes it writes tests anyway (higher-layer rule wins). Sometimes it doesn't (per-turn instruction wins). Inconsistent behavior is the result.

Fix option 1 — be explicit about the override:
```
Constraints for this turn:
- No tests yet — tests are step 4, per the plan. This turn stops at implementation only.
```

The phrase "per the plan" signals that this is sequencing, not contradiction. The rule "always write tests" is still active — you're just doing it in the next step.

Fix option 2 — write the rule correctly. If "always write tests" means "tests must exist before this is marked complete" (not "tests must be in the same turn"), rewrite the rule. The rule was too aggressive.

**Bad layering: vague SPEC reference.**
```
Implement POST /tasks according to the spec.
```

Which spec? Where? What version? This is not a SPEC block — it is an instruction that requires Claude to guess.

**Good layering: specific SPEC reference.**
```
SPEC contract: docs/specs/post-tasks.md, version as of last commit.
Binding section: "Acceptance criteria" only. Ignore the "Notes" section.
```

Specific file. Specific section. Scope bounded.

---

## When layering fails

**Claude ignores lower layers because higher layers dominate context.**

If your CLAUDE.md is 300 lines and your per-turn constraints are 5 lines at the end of a long message, the per-turn constraints may be ignored. Claude reads context from the top — long CLAUDE.md compresses per-message instructions.

Signs this is happening:
- Claude implements things you explicitly said to skip.
- Claude uses patterns from CLAUDE.md that contradict your message.
- Per-turn stop conditions are ignored.

Fix: keep CLAUDE.md lean (under 150 lines). Put per-turn constraints at the start of the message, not the end. Use explicit language: "This turn only: ..." makes the scope clear.

**Layer 2 points at a file that doesn't exist.**

If you write `SPEC contract: docs/specs/post-tasks.md` and the file doesn't exist, Claude will either hallucinate a SPEC or fall back to its own assumptions. Neither is reliable.

Rule: always create the SPEC file before referencing it. If you can't create it before the turn, don't reference it — write the constraints inline instead.

**Session context becomes stale.**

In a long session, something you said 20 messages ago is still "in context" but may have been superseded by 10 subsequent decisions. Claude may act on the stale context.

Fix: re-state active context at the start of each major new task within a session.

```
Context reset for this task: we completed body parsing (step 3) and validation (step 4). 
Both tests pass. Now implementing store integration (step 5).
```

This makes the current state explicit. Claude operates from this statement, not from reconstructing it from conversation history.

---

## The minimal viable message

Not every message needs all three layers. The rule is: use the layers that reduce ambiguity.

| Task complexity | Layers needed |
|----------------|--------------|
| Trivial fix: "fix the typo in this error message" | None — no layering needed |
| Small addition: "add a field to the Task struct" | Layer 3 only (turn constraints) |
| Feature implementation | Layer 2 (SPEC) + Layer 3 (stop conditions) |
| Full phase execution | All three, explicitly stated |

The cost of under-layering: Claude implements more than you intended, or implements the wrong thing.
The cost of over-layering: verbose messages, slower interaction. Worth paying for complex tasks.

---

## Checklist

- [ ] I write layer 2 (SPEC block) pointing at a real file that exists on disk.
- [ ] I write layer 3 (per-turn constraints) with explicit stop conditions.
- [ ] My per-turn constraints do not contradict CLAUDE.md — they narrow, they don't conflict.
- [ ] For long sessions, I re-state context at the start of each major new task.
- [ ] I know the difference between a legal scope limit and an illegal contradiction.
- [ ] My CLAUDE.md is lean enough that per-message instructions are not crowded out.
- [ ] I test my layering: does Claude stop where I said to stop?
