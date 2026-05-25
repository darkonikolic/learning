# When agents fail

Agent failures in execute-phase are not exceptional. They are operational. The skill is not avoiding failure — it is classifying it fast and recovering without losing your bearings.

---

## The reliability template

Every failure you encounter during execute-phase should map to these seven fields. Do not diagnose from memory. Fill in the template.

| Field | What to record |
|-------|----------------|
| **FAILURE MODE** | What class of failure? Scope creep, acceptance mismatch, execution loop |
| **DETECTION SIGNAL** | What told you it failed? Test output, SPEC comparison, STATE.md anomaly |
| **CONFIDENCE LEVEL** | High / Medium / Low / Stop — does the output warrant trust? |
| **VERIFY STEP** | The independent check you run — not "Claude says it's correct" |
| **RETRY DECISION** | Retry same prompt / replan / repair STATE.md — with reason |
| **FALLBACK** | What partial behavior survives while you repair |
| **ESCALATION TRIGGER** | When you stop autonomous work and make a human decision |

Fill this template before touching any code. Diagnosing mid-recovery without the template produces thrash: you fix one symptom, expose another, and loop.

---

## Three execute-phase failure modes

### Failure 1 — Claude adds out-of-scope code

**What happens:** execute-phase produces a commit that implements something not in the SPEC. Common example: SPEC says `GET /tasks` returns all tasks with no filtering. Claude adds `?completed=true` query parameter filtering because it seems useful.

**Detection signal:** diff review reveals a feature branch not described in SPEC. `/gsd:verify-work` shows green on core criteria but surfaces unexpected behavior. Excess behavior in the response or routing logic.

**Why it happens:** Claude completes the task it was given and then "improves" it with adjacent behavior it inferred from context. The improvement is often technically correct code. It is scope drift.

**Confidence impact:** output is not Low confidence — it compiles and acceptance criteria pass. But it fails the SPEC boundary. Classify as **scope violation**, not a quality failure.

---

### Failure 2 — Code compiles but fails acceptance

**What happens:** execute-phase produces a commit. `go build ./...` succeeds. `go test ./...` fails — or tests pass but manual verification of acceptance criteria fails.

**Detection signal:** test failure output, or running the verification commands from SPEC and seeing wrong HTTP status codes / response shapes / missing fields.

**Why it happens:** Claude implemented a plausible interpretation of the task, not the SPEC-specified behavior. The gap is usually in edge cases: wrong status code on 404, wrong response field name, missing header.

**Confidence impact:** this is a **Medium → Low** confidence output. Plausible but wrong. Do not advance to the next wave with this output as input — downstream tasks build on wrong foundations.

---

### Failure 3 — Claude stuck in a loop

**What happens:** execute-phase does not complete. Claude cycles through the same actions without producing a commit. Or produces a commit, you flag it as wrong, Claude "fixes" it, produces the same wrong output again.

**Detection signal:** two or more commits with the same acceptance failure. Retry count at 2 with no improvement. No new commit after 10+ minutes of apparent execution.

**Why it happens:** the prompt has an ambiguity that allows multiple valid interpretations. Each retry produces a different valid-but-wrong implementation. Or the prior wave's output is wrong and Claude is working around it in a local minimum.

**Confidence impact:** classify as **Stop**. Do not retry a third time. Replan from the last clean state.

---

## Confidence scoring rubric

Apply this rubric before deciding to advance a wave or retry a task.

| Level | Criteria | Action |
|-------|----------|--------|
| **High** | Output matches all SPEC acceptance criteria. Tests pass. No excess behavior. | Advance to next wave. |
| **Medium** | Output is plausible. Core behavior correct. One or two edge cases unverified or failing. | Verify manually before advancing. Fix gaps before moving on. |
| **Low** | Output contradicts a SPEC criterion, or a prior-wave output it depends on is wrong, or SPEC section is missing and output is inferred. | Do not advance. Diagnose root cause. Fix SPEC or prior output first. |
| **Stop** | Loop detected (2+ retries with no improvement). SPEC ambiguity that produces different wrong output each retry. Human decision required to resolve. | Stop autonomous execution. Make an explicit call. |

One rule: the agent that produced the output cannot assign its own confidence level. You assign confidence after independent verification. Self-attestation ("this implementation looks correct") is not a verification step.

---

## Hallucination recovery — three-step procedure

Hallucination in execute-phase does not mean invented facts. It means the implementation includes behavior that is not grounded in the SPEC. The code may be high quality. It is still wrong relative to the contract.

### Step 1 — Identify

Find the exact SPEC section that the implementation violates or exceeds. Be specific. "Claude added filtering" is not enough. Record:
- The SPEC section that defines the boundary (e.g., `## GET /tasks — acceptance criteria`)
- The specific acceptance criterion that is contradicted or missing (e.g., "Returns all tasks — no filtering, sorting, or pagination in v0.1")
- The exact code that crosses the boundary (e.g., `if r.URL.Query().Get("completed") != ""`)

Write this down before removing anything.

### Step 2 — Isolate

Contain the violation to a single git object. Two paths:

**Path A — clean commit:** the out-of-scope code is in its own commit (separate from other work).
```bash
git log --oneline -5
# Identify the bad commit hash
git revert <hash> --no-edit
# Produces a revert commit. Other waves are untouched.
```

**Path B — mixed commit:** the out-of-scope code is entangled with correct code in the same commit.
```bash
# Do not revert — that removes the correct code too
# Instead: manual removal
# Edit the file to remove only the out-of-scope behavior
git add <file>
git commit -m "fix: remove out-of-scope filtering from GET /tasks (not in SPEC v0.1)"
```

Never use `git reset --hard` here. You would lose the correct code that was part of the same wave.

### Step 3 — Replace

After isolation, you have a clean baseline. Now implement the correct behavior.

If the task was not yet complete (the out-of-scope code was the entire output):
```
Re-run the task with a constraint added to the prompt:
"Implement GET /tasks as specified. Do not add filtering, sorting, or pagination —
these are explicitly out of scope for v0.1 per SPEC section 3.1."
```

If the task was otherwise correct (only one method or block was wrong):
```
Write the specific missing behavior directly, or prompt Claude with:
"The only change needed is [specific criterion]. The rest of the handler is correct.
Do not modify any other behavior."
```

Verify immediately after replacement:
```bash
go test ./...
# Run the specific acceptance criteria manually
curl -s "localhost:8080/tasks?completed=true" | jq 'type'
# Expected: "array" — query param is silently ignored, not filtered
```

---

## Verification ownership separation

The agent that produces output cannot verify its own output. This is not a preference — it is structural. The same context that produced the implementation will evaluate it against that context, not against the SPEC.

In GSD, verification ownership works like this:

| Role | Who does it |
|------|-------------|
| Implementation | Claude (execute-phase agent) |
| Verification | You — running acceptance criterion commands |
| Confidence assignment | You — after running verification |
| Retry decision | You — based on confidence level and failure type |

Asking Claude "does this implementation satisfy the SPEC?" after Claude wrote the implementation is verification theatre. Claude will confirm it does. That confirmation has no signal value.

The verification procedure is: you read the SPEC acceptance criterion, you run the command, you read the output, you compare. Claude is not in that loop.

---

## Retry bounds

| Situation | Decision |
|-----------|----------|
| Task timed out, no output | Retry once with same prompt |
| Output wrong due to ambiguous SPEC | Do not retry — fix SPEC first, then retry |
| Output wrong due to wrong prior-wave output | Do not retry current wave — fix prior wave, then rerun |
| Loop detected (2 retries, same failure) | Stop. Replan the task. Narrow scope or rephrase constraint. |
| Wave partially complete (some tasks done, some not) | Use `--gaps-only` to rerun only incomplete tasks |
| STATE.md shows task complete but output is wrong | Manual STATE.md repair first — remove the false "complete" marker, then `--gaps-only` |

**Hard cap: three retries per task.** If a task fails three times, the problem is not transient. Either the prompt has an unresolved ambiguity, the SPEC has a gap, or prior-wave output is the wrong foundation. Stop retrying and diagnose.

### When to repair STATE.md vs when to replan

**Repair STATE.md and rerun:** task output was wrong but the task itself is correctly defined. The SPEC is clear. The failure was execution quality, not specification quality. Fix: remove the false "complete" marker, rerun with `--gaps-only`.

**Replan:** the task failed because it was specified wrongly in PLAN.md, or the SPEC has a gap that makes the task ambiguous. Fix: update the PLAN.md task definition or fill the SPEC gap, then re-run `/gsd:plan-phase` to regenerate.

```bash
# STATE.md repair — remove false complete marker
# Example STATE.md entry to edit:
# tasks:
#   - id: write-get-handler
#     status: complete    ← remove this line or change to: status: pending
#
# Then rerun:
/gsd:execute-phase --gaps-only
```

---

## Checklist

- [ ] I know the three execute-phase failure modes: scope creep, acceptance mismatch, execution loop.
- [ ] I can fill in all seven fields of the reliability template before touching code.
- [ ] I apply the four-level confidence rubric (High / Medium / Low / Stop) after verification.
- [ ] I assign confidence myself — not based on Claude's self-assessment.
- [ ] I know the hallucination recovery procedure: identify → isolate → replace.
- [ ] I use `git revert` for clean commits and manual removal for mixed commits.
- [ ] I know the retry hard cap (three attempts) and the two reasons to replan instead of retry.
- [ ] I know when to repair STATE.md vs when to replan the task.
- [ ] I never verify Claude's output by asking Claude.
