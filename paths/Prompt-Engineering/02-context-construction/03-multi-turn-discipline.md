# Multi-Turn Discipline

## How Context Degrades

By turn 5, the model is working from a compressed representation of what you said in turn 1. This is not a failure — it is how attention and context windows work. Planning around it is the skill.

What degrades is not the model's capability. What degrades is the fidelity of older messages. Early constraints become lower-salience. Early file state gets replaced by what the model has written. Specifications from turn 1 compete with decisions from turns 3 and 4.

The practical consequence: the model that correctly followed your stdlib constraint in turn 2 may import a package in turn 7 not because it forgot the rule but because the rule is now less salient than everything else in context.

---

## Three Degradation Patterns

### 1. Constraint Forgetting

A rule that was followed early in the session is violated later.

```
Turn 2: correctly uses stdlib net/http
Turn 6: adds github.com/gorilla/mux

Turn 1: errors wrapped with fmt.Errorf
Turn 5: returns raw errors without wrapping
```

**Cause**: the constraint was stated once in turn 1. By turn 5-6, the model is attending more to recent exchanges than to the original setup.

**Signal**: review generated code for the specific constraints in your workspace config. Don't assume compliance persists.

### 2. Scope Drift

The model gradually expands what it's doing beyond the stated task.

```
Turn 1: "add PATCH /tasks/:id/complete"
Turn 3: adds a CompletedAt field to the store interface
Turn 4: refactors the store to support the new field
Turn 5: updates all existing handlers to use the new store interface
```

None of these individual steps is unreasonable — but the model has gone from "add one endpoint" to "refactor the store layer."

**Signal**: output touches files or layers you didn't specify. The model starts making decisions that weren't part of the task.

### 3. Reference Drift

The model uses an older version of a file — either the one it read at session start or one it generated earlier — rather than the current state.

```
You edited tasks.go after turn 2.
Turn 4 output: the model regenerated a function that was already updated in your edit.
```

**Signal**: generated code doesn't reflect recent manual edits or re-introduces code you removed.

[Claude] Re-read files explicitly after you make manual edits: "Read internal/api/tasks.go again — I made changes outside this session."

[Cursor] Re-add `@tasks.go` in the next composer message after manual edits.

---

## The Reset Signal — When to Clear vs Continue

**Continue the session when:**
- The task is progressing and constraints are being followed
- You're building incrementally on previous output
- No degradation patterns have appeared
- Turn count is low (1-4)

**Clear and restart when:**
- The model has violated a constraint (continuing compounds it — the violation is now in context as apparent precedent)
- The task has shifted significantly from the original spec
- You're past turn 6-8 on a complex task
- The model's last response required significant correction

[Claude] `/clear` clears the session. Re-establish context from your files — CLAUDE.md, SPEC.md, relevant source files.

[Cursor] Start a new composer. Re-add `@spec.md` and `@relevant-files`.

**The rule**: if the session has gone wrong, do not try to fix it with more turns. Clear and restart with clean context.

---

## The Checkpoint Technique

A checkpoint is a single message you write at a stable milestone before context degrades. It must allow a fresh session to resume without reading the conversation history.

**When to write one**: after each meaningful unit of work (one endpoint implemented and verified, one module completed). Write it before starting the next unit.

**What it must contain:**

```
## Checkpoint — [date/time or milestone label]

### Verified state
- PATCH /tasks/:id/complete implemented in internal/api/tasks.go
- Returns 200 + Task, 404 if not found, 409 if already complete
- Manual test: curl -X PATCH localhost:8080/tasks/1/complete → 200 ✓
- All existing tests pass

### Active constraints (from CLAUDE.md)
- stdlib only
- errors: fmt.Errorf("operation: %w", err)
- in-memory store, no DB layer

### Files modified this session
- internal/api/tasks.go (added handler)
- internal/api/router.go (registered route)

### Next action
Implement POST /tasks — spec in SPEC.md under "POST /tasks"
```

This message can be pasted verbatim to start a new session. It is the minimum viable context for continuation.

---

## Turn-by-Turn Discipline

Each turn should be as self-contained as possible. The goal is that losing the previous turn does not break the current one.

**Good turn structure:**
- Reference files by path, not by "the file we discussed"
- State constraints that matter for this turn, even if stated before
- Include the specific acceptance criterion for this turn's output

```
# Good — self-contained turn
Implement PATCH /tasks/:id/complete in internal/api/tasks.go.
Constraint: stdlib only, errors wrapped with fmt.Errorf.
Done: 200 + updated Task, 404 if not found, 409 if already complete.
```

```
# Fragile — depends on previous turns being remembered
Now add the complete endpoint like we discussed.
```

The second form works at turn 2. At turn 6, the model's reconstruction of "what we discussed" may differ from what you intended.

---

## When NOT to Continue a Session

**The model has already violated a constraint.**

If the model used a third-party library when stdlib was required, do not continue in the same session. The violation is now part of the conversation context. Continuing treats the violation as accepted prior art. The model may continue the pattern.

Clear. Revert the change. Start fresh with clean context.

**The model's last output required major rewriting.**

If you had to rewrite 30+ lines of the model's output, the session has drifted. The model's internal representation of what "good output" looks like for this task has diverged from yours. More turns will produce more output that needs rewriting.

Clear. Restate what was done, what was wrong, and what the actual requirement is.

---

## Checklist

- [ ] Degradation patterns identified: constraint forgetting, scope drift, reference drift
- [ ] Files re-read after manual edits before continuing
- [ ] Session cleared when a constraint violation occurred
- [ ] Checkpoint written at each stable milestone
- [ ] Checkpoint contains: verified state, active constraints, modified files, next action
- [ ] Individual turns are self-contained — no "like we discussed" references
- [ ] Sessions past turn 6-8 on complex tasks are checkpointed and optionally restarted
- [ ] [Claude] /clear used when session has gone wrong, not just when context is long
- [ ] [Cursor] New composer started rather than continuing after a failed direction
