# Spec drift and repair

Spec drift is the gap between what the SPEC says and what the implementation does. It is not a failure of discipline — it is an inevitable consequence of working incrementally with an AI agent. Understanding when it happens, how to detect it, and how to repair it is the difference between a SPEC that stays useful and a SPEC that becomes a historical artifact no one trusts.

---

## How drift happens

Drift has a causal structure. These causes are ordered by likelihood in practice.

**1. SPEC exists only in chat — /compact removes it**

The most common cause. You draft the SPEC in a conversation turn, discuss it, then ask Claude to implement. Three hours and one /compact later, Claude is implementing from its working memory of the conversation — which is partial. The SPEC on disk is the only reliable anchor.

**2. Implementation reveals an unconsidered constraint**

You write the SPEC, start implementation, and discover that the constraint "must use stdlib only" conflicts with UUID generation (stdlib's `math/rand` produces non-crypto-random IDs). Someone updates the code to use a workaround. The SPEC still says something different. Neither is wrong — but they have diverged.

**3. Scope silently added during execute**

Wave 3 of an execute session adds error handling that wasn't in the SPEC. The handler now returns a 409 Conflict for duplicate task titles — behavior the SPEC never described. The agent "improved" the implementation. The improvement may be desirable, but it is not in the contract.

**4. Bug fix changes described behavior**

A bug is discovered: GET /tasks returns tasks in reverse creation order. The fix is correct. But the SPEC acceptance criterion said "tasks returned in the order they were added" — which was the buggy behavior that had been "verified" manually before the fix. Now the SPEC is describing the old bug.

**5. Multiple agents with inconsistent context**

Parallel agent runs in different context windows implement from different summaries of the same SPEC. Agent A uses `created_at`, Agent B uses `createdAt`. Both pass their local tests. The SPEC has one noun, the code has two.

---

## Spec evolution vs spec drift — critical distinction

These look similar but have opposite correct responses.

| | Spec evolution | Spec drift |
|--|---------------|-----------|
| Intent | Deliberate update after learning | Accidental divergence |
| Process | SPEC updated first, approved, code follows | Code changed, SPEC not updated |
| Traceability | Commit message references SPEC change | No record of divergence |
| Direction | SPEC leads code | Code leads SPEC |
| Resolution | Already resolved (SPEC and code agree) | Must detect and repair |

**Evolution example:** during Phase 3 implementation you learn that returning 204 No Content for PATCH /tasks/:id/complete makes client integration harder. You update the SPEC to say "returns 200 with updated task body", get sign-off, then implement. SPEC changes first. Code follows. This is evolution — correct process.

**Drift example:** during Phase 3 implementation Claude returns 200 with the updated task body without SPEC approval. You verify the acceptance criteria. They pass (the criteria said "success response" which is ambiguous). Three weeks later a teammate reads the SPEC, sees "returns 200 No Content", and files a bug. This is drift — code led, SPEC was never updated.

The process distinction is what matters. Evolution has a traceable decision. Drift is a silent divergence.

---

## Drift detection — when it is most likely

Be skeptical after:

**Long execute sessions.** Wave 3+ of a multi-wave execute is when agents add behavior beyond scope. They are "completing" the feature and filling in perceived gaps. Each gap they fill is potential drift.

**Bug fixes touching SPEC-covered behavior.** Any fix to an endpoint, response format, or field name should trigger a SPEC re-read.

**Refactors.** A rename from `created_at` to `createdAt` in the store package may propagate to the response without the SPEC being updated.

**Branch merges.** Another developer's changes may have modified behavior you specified. The merge commit does not know about your SPEC.

**After /compact.** Claude's working context was reset. Its next implementation turn is from a compressed summary, not the full SPEC. Subtle details drop out.

---

## Signs of drift

Drift shows up in specific patterns:

- A verification step fails on an item that "definitely works" — meaning the item passes a manual check but the SPEC criterion describes something slightly different
- Implementation has behavior the SPEC does not mention (excess behavior)
- SPEC acceptance criteria cannot be verified because the implementation does something the criterion doesn't describe
- A new team member reads the SPEC and expects different behavior than what is deployed
- /gsd:validate-phase reports coverage gaps between tests and SPEC

The third sign is the most dangerous. If you cannot run the SPEC acceptance criteria against the implementation, the SPEC has lost its verification function entirely.

---

## Drift repair procedure

This is a decision process, not a simple fix. The wrong repair (updating SPEC to match wrong code) perpetuates incorrect behavior. The right repair depends on which party — SPEC or code — represents correct intent.

**Step 1: Stop implementation.**
Do not continue implementing while a drift is unresolved. New implementation on top of drift makes the repair harder.

**Step 2: Read SPEC and code side by side.**
Open `docs/specs/<slug>.md` and the implementation files. Go section by section through the SPEC. Note each divergence.

**Step 3: For each divergence, decide which is correct.**

Three cases:

**Code is correct, SPEC is outdated:**
The SPEC described a design that was superseded during implementation for valid reasons. The code behavior is the right behavior.
Action: Update SPEC to match code. Write a one-sentence note in the SPEC explaining why the change was made (this is spec evolution — make it traceable).

**SPEC is correct, code has drifted:**
The code diverged from intent. The SPEC describes the required behavior.
Action: Fix the code to match the SPEC. Re-verify acceptance criteria.

**Both are wrong:**
The original problem statement has changed, or the acceptance criterion was ambiguous enough to permit both versions.
Action: Return to the Problem and Goal sections. Rewrite the relevant acceptance criterion from the ground truth. Get approval. Then fix code or update SPEC as appropriate.

**Step 4: Update the wrong party.**
Make exactly one update: either the SPEC or the code. Never update both simultaneously without a clear decision on which is truth.

**Step 5: Re-approve.**
The changed SPEC should be reviewed — even a self-review where you read it fresh — before the next implementation turn.

**Step 6: Resume from updated SPEC.**
Reference the SPEC file path in the next implementation message as normal.

---

## Drift severity and priority

Not all drift requires immediate action. Triage before repair.

| Severity | Example | Action |
|----------|---------|--------|
| Critical | Security behavior different from SPEC | Fix before any other work, do not ship |
| High | Acceptance criterion fails on deployed feature | Fix before ship |
| Medium | Excess behavior not in SPEC (unintentional feature) | Document as evolution or remove before ship |
| Low | Internal implementation strategy differs from SPEC strategy section | Log in SPEC, no immediate action required |

Critical drift is rare in task-api (no auth, no security model). High severity drift is the common case — an acceptance criterion that should pass does not. Medium drift (unintentional features) is the most frequent outcome of long execute sessions.

---

## Prevention

The best drift repair is drift that never happens.

**Rule 1: SPEC on disk before first implementation turn.**
Not drafted in chat. Not pasted in a prompt. Written to `docs/specs/<slug>.md` before you ask Claude to write a single line of code.

**Rule 2: Reference the SPEC file path in every implementation message.**
```
Implement per docs/specs/get-tasks.md.
Acceptance section is the contract.
Do not add behavior not described in the SPEC.
```
The explicit "do not add behavior" instruction reduces wave-3 scope additions.

**Rule 3: Verify at least one acceptance criterion after each implementation turn.**
Not at the end of the session. After each turn. Early verification catches drift while it is still small.

**Rule 4: When something unexpected appears in the implementation, stop and classify it.**
Is this undocumented behavior a feature (add to SPEC), a bug (remove from code), or an evolution (update SPEC with rationale)?

**Rule 5: /gsd:validate-phase is a drift detector, not just a coverage reporter.**
Run it after execute. Its coverage gaps point directly to acceptance criteria that have no corresponding test — which means they may also have no corresponding implementation.

---

## Drift in the task-api context — worked scenario

Scenario: after implementing GET /tasks, you run the acceptance verification and find:

- PASS: GET /tasks returns 200
- PASS: Response is a JSON array
- FAIL: Tasks are returned in creation order (they are in reverse order)
- PASS: Each task has id, title, done, created_at
- CANNOT VERIFY: done is boolean (SPEC says "boolean" but criterion doesn't say to check the type)

**FAIL on creation order:** is the SPEC right or is the code right? The SPEC says "creation order". The code returns reverse. The SPEC is describing intended behavior. The code has a bug. Fix the code. Re-verify.

**CANNOT VERIFY on done type:** the acceptance criterion is not binary enough. Rewrite it: "done field value is of JSON boolean type (true or false), not a string". Now it can be verified with `curl ... | jq '.[0].done | type'`.

This is the repair procedure applied to a real scenario. The SPEC had one bad criterion (not binary) and the code had one bug (wrong order). Both are resolved before ship.

---

## Spec evolution in practice — committing the record

When spec evolution happens, the commit that updates the SPEC should explain why. This is the traceability requirement. Without it, the evolution looks identical to drift when someone audits the history.

Bad commit message: "update get-tasks SPEC"

Good commit message: "spec(get-tasks): evolve empty list criterion — returns [] not null; add nil-slice store constraint to prevent json.Marshal(nil)=null regression"

The commit message contains: what changed, why it changed, and what constraint was added to prevent regression. A future developer reading this commit knows the behavior changed intentionally, can find the SPEC for the reasoning, and knows there is a constraint protecting it.

**Commit timing:**

Commit the SPEC update before the code fix that implements it. Not simultaneously, not after. The sequence:

1. Update SPEC (commit: "spec evolution: ...")
2. Fix code to match updated SPEC (commit: "fix: store.List returns non-nil empty slice per updated SPEC")

This sequence makes the decision traceable: SPEC changed first, then code followed. Even if only hours apart, the commit order is the proof of process.

---

## What drift is not

Drift is not:
- A test failing (that is a test failure — may or may not indicate drift)
- An improvement to internal code structure (implementation strategy differs from SPEC — Low severity, no drift)
- A bug fix that does not change user-observable behavior (internal repair — not drift)
- A SPEC update during plan-phase (SPEC is being written, not drifting)

Drift requires both: a SPEC that describes behavior, and implementation that contradicts that description. If the SPEC never described the behavior, there is nothing to drift from.

This means early phases where SPEC coverage is incomplete will have more apparent "excess behavior" than drift. The fix for excess behavior is to add it to the SPEC (if intentional) or remove it (if not). This is different from drift repair, which requires a decision between two competing truth sources.

---

## Checklist

- [ ] I can distinguish spec evolution from spec drift by process, not just by outcome
- [ ] I know the five causes of drift and can predict which is most likely after a long execute session
- [ ] I can execute the drift repair procedure: stop, read side by side, decide which is correct, update one party
- [ ] I apply the three-case decision (code right / SPEC right / both wrong) before making any change
- [ ] SPEC is on disk before implementation — this eliminates the most common drift cause
- [ ] After each execute turn I verify at least one acceptance criterion, not just at the end
- [ ] I run /gsd:validate-phase after execute and treat coverage gaps as potential drift signals
