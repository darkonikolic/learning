# Must / Must Not — Writing Constraints That Hold

## Why soft language fails

"Try to keep it simple" is not a constraint. The model reads it as a preference and weighs it against other signals — the existing codebase style, what seems reasonable, what a senior dev might add. It will lose that competition.

Soft language the model will ignore:
- "try to", "prefer", "ideally", "where possible", "keep it simple", "avoid if you can"

Hard language the model treats as a rule:
- "must", "must not", "do not", "never", "stop if", "only"

The difference is not style — it is whether the instruction creates a decision boundary. Soft language gives the model room to decide. Hard language removes that room.

## The constraint template

Every constrained prompt needs at minimum:

```
must: [what must be true about the output]
must not: [what the output must never include]
stop if: [condition where the model should halt and ask rather than guess]
```

You do not need all three for every prompt. Use `stop if` whenever the model would need to make a design decision with non-obvious tradeoffs. Use both `must` and `must not` for any task touching more than one file.

## Scope constraints vs method constraints

These are different and both matter.

**Scope constraint** — what to build, what to touch:
- "must only modify files under `internal/handler/`"
- "must not create new files"
- "must not change the public API"

**Method constraint** — how to build it:
- "must not add new dependencies"
- "must use the existing `logger` package, not `fmt.Println`"
- "must not use reflection"

A prompt with only scope constraints can still produce code that violates your architectural rules. A prompt with only method constraints can still cause unbounded scope creep. You need both for any non-trivial task.

## Weak vs strong: adding a feature

**Weak:**
```
Add rate limiting to the API. Keep it simple and don't over-engineer it.
```

**Strong:**
```
Add rate limiting to POST /api/tasks.

must: use the existing `middleware/` package pattern
must: store rate limit state in the Redis client already injected into the handler
must not: add new packages or dependencies
must not: modify any handler other than tasks_handler.go
must not: add configuration structs — hardcode the limit as a constant with a TODO comment
stop if: the existing Redis client does not have the methods needed for atomic increment+TTL
```

The weak version will produce rate limiting that adds a new library, touches multiple handlers, and adds a config struct "for flexibility". The strong version cannot — each of those paths is explicitly closed.

## Weak vs strong: fixing a bug

**Weak:**
```
Fix the nil pointer panic in the user service. Be careful not to break anything.
```

**Strong:**
```
Fix the nil pointer panic in internal/service/user.go at the GetByEmail method.

must: fix only the nil check on the returned db row
must not: change the method signature
must not: modify the calling code in handler/auth.go
must not: add logging or error wrapping beyond what already exists in this file
stop if: the fix requires changing how the db layer returns errors — ask before proceeding
```

"Be careful not to break anything" is the most common useless constraint in prompts. It has no effect. The model was already trying not to break things. The strong version defines exactly what "not breaking anything" means in this context.

## Weak vs strong: refactoring

**Weak:**
```
Refactor the payment processing code to be cleaner and more maintainable.
```

**Strong:**
```
Refactor internal/payment/processor.go.

must: extract the charge logic into a private method with a clear name
must: preserve all existing method signatures on PaymentProcessor
must not: change any behavior — refactor only, no logic changes
must not: add new types or interfaces
must not: split into multiple files
must not: change error types returned
stop if: you identify a logic bug — report it as a comment, do not fix it
```

"Cleaner and more maintainable" is a value judgment. The model will make it differently than you would. The strong version specifies exactly what refactoring is permitted and puts a hard stop on the most common failure mode of refactoring tasks: the model finds a real bug and fixes it, mixing refactor and behavior change in the same commit.

## The "stop if" instruction

Use `stop if` when:
- The model would need to make a non-trivial architectural decision to proceed
- The task has a dependency you are not sure exists
- There are two valid approaches with meaningfully different tradeoffs
- Proceeding incorrectly would be harder to undo than asking upfront

```
stop if: the existing auth middleware does not export the claims struct —
         ask whether to add an export or use a different approach
```

Without `stop if`, the model will make that decision silently. You will only discover it when reviewing the output. In Claude Code, an unanswered question means three files changed in a direction you did not choose.

## Checklist

- [ ] Every soft word replaced with must/must not or removed
- [ ] Scope constraint present: which files/modules may be touched
- [ ] Method constraint present: what approaches are permitted or forbidden
- [ ] `stop if` covers any decision point where the model would guess
- [ ] Constraints are specific enough that a different model would produce the same boundaries
