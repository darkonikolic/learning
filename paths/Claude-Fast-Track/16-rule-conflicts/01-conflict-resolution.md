# Rule conflict resolution

Rules collide. The collision is not a failure in your rules system — it is a signal that two legitimate concerns are competing for the same decision. The skill is resolving collisions deliberately, not ad-hoc.

---

## The priority ladder

When two rules disagree, one wins because of where it sits on the ladder, not because someone argued louder.

```
Security                  — vulnerabilities, auth, secret handling, injection
    ↓
Correctness               — spec-compliance, data integrity, contract accuracy
    ↓
Reliability               — change safety, reversibility, predictability under failure
    ↓
Maintainability           — readability, clarity, long-term understandability
    ↓
Performance / cost        — speed, token efficiency, resource optimisation
```

**Why this order:**

- Security supersedes everything because violations cause harm outside the codebase.
- Correctness supersedes reliability because a reliably wrong system is worse than an occasionally failing correct one.
- Reliability supersedes maintainability because stable-but-messy is survivable; clean-but-fragile is not.
- Maintainability supersedes performance because premature optimisation creates debt faster than it recovers latency.

A rule in the Performance tier never overrides a rule in the Correctness tier. Document the exception explicitly if you deviate.

---

## Conflict types

### Type 1 — Risk vs ergonomics

One rule blocks a risk. The other makes the developer's life easier. These are never genuinely ambiguous — the risk rule wins. The ergonomics rule identifies a cost you are accepting, not a competing authority.

**Pattern:** "Do not use X" (risk rule) vs "X makes this easier" (ergonomics). Apply the ladder: what tier is the risk rule in? Almost always Correctness or Security. Ergonomics lives in Maintainability or Performance. Higher tier wins.

---

### Type 2 — Two correctness rules that contradict

Both rules are at the same tier. This is a genuine conflict. The ladder does not resolve it because they are equal. You need an explicit tiebreaker.

**Resolution path:**

1. Identify which rule is more specific to the current context. Specific beats general.
2. If equally specific, identify which rule was established more recently with more deliberate context (ADR, SPEC decision, explicit author reasoning). Deliberate beats default.
3. If still unresolved, escalate to a human decision and document it as an ADR or exception in `RULE_PRIORITY.md`.

---

### Type 3 — Rule vs SPEC constraint

A rule says X. The current SPEC section says the constraint for this phase is not-X. The SPEC wins for this phase. The rule is not wrong — it applies outside this scope.

**Key distinction:** a SPEC constraint is not an exception to a rule. It is a scoped decision that the rule does not apply here and now. Document the scope boundary. When the SPEC constraint lifts, the rule resumes without further action.

---

## Resolution procedure

Apply these four steps in order. Do not skip ahead.

| Step | Action |
|------|--------|
| **1 — Identify** | Name both rules. State exactly what each requires. Find the line where they contradict. |
| **2 — Apply ladder** | Assign each rule to a tier. The higher tier wins. If same tier, go to tiebreaker (specificity → recency → human). |
| **3 — Document exception** | If you are overriding the higher-tier rule for any reason, write an exception record: which rule is overridden, what permits it, the scope, and the expiry condition. |
| **4 — Set expiry** | Every exception is time-bounded or event-bounded. "Until Phase 4 is complete" or "until the crypto library is audited" or "review at 2026-09-01". Open-ended exceptions become permanent invisible overrides. |

---

## Time-bounded exceptions

When a higher-tier rule must be violated temporarily — because a dependency does not exist yet, a phase constraint is active, or a migration is in progress — encode the exception formally.

**Exception record format:**

```
## EXCEPTION: <rule-name> overridden by <overriding-concern>

Overridden rule: .claude/rules/<rule-file>.md
Permitted by: <SPEC section | ADR number | commit reference>
Scope: <which phases, files, or contexts this applies to>
Reason: <one sentence — why the override is necessary right now>
Expiry: <date | event | phase completion>
Cleanup: <what to do when expiry is reached — remove exception, re-enable rule, audit output>
Recorded by: <author> on <date>
```

Never write an exception without an expiry. An expiry without a cleanup action is not an expiry — it is a reminder that will be ignored.

---

## task-api concrete examples

### Scenario 1: global TDD rule vs project scaffolding rule

**Setup:** Your global CLAUDE.md (at `~/.claude/CLAUDE.md`) contains:

```markdown
# Global rule: test-driven development
Always write tests before implementation. For every new function or handler,
create the test file first. Do not write implementation code before a failing
test exists.
```

Your project-level `.claude/rules/scaffolding-order.md` contains:

```markdown
# scaffolding-order
For scaffolding tasks — creating new files with stub functions that will be
filled in during execute — write the stub first, tests after.
Rationale: plan generates stubs so execute can fill them.
Writing tests before stubs exist causes plan to generate malformed plans.
```

**The conflict:** You are running plan for Phase 2 GET /tasks. Claude starts by writing a test file before writing the handler stub. But plan needs the stub to exist so it can plan around it.

**Classify it:** This is Type 3 — rule vs SPEC constraint. The project rule (`scaffolding-order.md`) is a scoped decision: for scaffolding tasks specifically, stubs come before tests. The global TDD rule is not wrong — it applies during execute when you are filling in stubs. It does not apply to plan scaffolding setup.

**Apply the ladder:** Both rules could be considered Correctness tier (test coverage) and Reliability tier (plan stability). But the scoping is the key: the project rule explicitly scopes itself to "scaffolding tasks". The global rule has no scope restriction.

**Resolution:** Specific beats general. `scaffolding-order.md` is more specific to the current context. It wins for this task. Document it:

```markdown
## Conflict: global TDD vs scaffolding-order.md

Conflict type: Type 3 — rule vs scoped project decision
Winner: scaffolding-order.md (project scope)
Loser: global TDD rule (deferred to execute)
Scope: plan scaffolding tasks only
Rationale: global TDD applies during execute when stubs are being filled;
  scaffolding-order.md applies during plan stub creation. No actual contradiction
  when scopes are respected.
```

---

### Scenario 2: user turn instruction vs project rule

**Setup:** Mid-session, you send this message to Claude:

```
Stop after writing the GET /tasks handler. Don't write tests for it — I'll add them manually.
```

Your project-level `.claude/rules/test-coverage.md` contains:

```markdown
# test-coverage
All handlers must have corresponding unit tests before the phase is considered
executable. A handler without tests is incomplete work. Do not mark any handler
task complete without at least one passing test.
```

**The conflict:** Your turn instruction says stop without tests. The project rule says handlers must have tests before they are complete.

**This is not a Type 2 conflict.** The turn instruction and the project rule are at different levels of authority, not different correctness claims. Turn-level instructions are the highest priority in the execution hierarchy — but "highest priority" does not mean they silently override safety constraints. This is where judgment and escalation apply.

**Resolution path:**

1. Claude should follow your turn instruction — you are the human in the loop.
2. Claude should flag the conflict explicitly, not silently comply: "Following your instruction to stop here. Note: `test-coverage.md` requires tests before this task is marked complete. Stopping without tests means `docs/state.md` will record this task as incomplete, and incomplete-only retry will re-run it."
3. The right response from you: decide whether to update the rule for this phase (write a scoped exception) or to add the tests after verifying the handler works.

**When to escalate:** If the project rule is in the Security tier (e.g., "all authentication handlers must have tests") and the turn instruction is asking to skip tests for an auth handler, Claude should decline the instruction and explain why. Security rules are not turn-overridable — they are organizational constraints, not preferences.

**Document the exception if you proceed without tests:**

```markdown
## EXCEPTION: test-coverage.md — handler task 2-02 delivered without tests

Overridden rule: .claude/rules/test-coverage.md
Permitted by: author decision — turn instruction during Phase 2 execute
Scope: task 2-02 (GetTasks handler) only
Reason: manual test addition planned after handler verification
Expiry: Phase 2 complete — tests must be added before verification stage runs
Cleanup: add TestGetTasksEmpty, TestGetTasksWithTasks before running the verification stage
Recorded by: [your name] on [date]
```

Without this record, the missing tests look like an oversight, not a deliberate decision.

---

## RULE_PRIORITY.md template

The following template captures the four-level hierarchy for task-api. Place this file at `.claude/RULE_PRIORITY.md`:

```markdown
# RULE_PRIORITY.md
# Four-level hierarchy — each level overrides the one below it within its scope

## Level hierarchy (highest to lowest)

1. Turn-level instructions — what you type in the current message
   - Highest priority for execution
   - Cannot override Security-tier project rules
   - Expires at end of turn

2. Session-level context — `docs/plans/<phase>-context.md`, session flags, frame output
   - Scoped to the current phase
   - Can narrow or tighten project rules for this phase
   - Expires when the session ends or phase changes

3. Project-level rules — .claude/rules/*.md
   - Default authority for all work in this project
   - Can override global rules within project scope
   - Persists until explicitly changed

4. Global rules — ~/.claude/CLAUDE.md
   - Applies to all projects unless overridden
   - Lowest priority when a more specific rule exists

## Priority ladder (severity order within a tier)

1. Security — vulnerabilities, auth, secret handling, injection
2. Correctness — spec-compliance, data integrity, contract accuracy
3. Reliability — change safety, reversibility, predictability under failure
4. Maintainability — readability, clarity, long-term understandability
5. Performance / cost — speed, token efficiency, resource optimization

## Rule tier assignments — task-api

| Rule file | Level | Tier | Notes |
|-----------|-------|------|-------|
| no-plaintext-secrets.md | Project | Security | Hard stop — no exceptions |
| stdlib-only.md | Project | Correctness | Supply-chain integrity |
| test-coverage.md | Project | Correctness | Handler completeness gate |
| scaffolding-order.md | Project | Reliability | Plan stage scaffolding scope only |
| no-global-state.md | Project | Reliability | Test isolation requirement |
| error-wrapping.md | Project | Maintainability | Diagnostic quality |
| readable-ids.md | Project | Maintainability | Operator ergonomics |
| Global TDD rule | Global | Correctness | Applies in execute; deferred for scaffolding |

## Active exceptions

(none)

## Resolved exceptions

| Exception | Overridden rule | Resolved date | Resolution |
|-----------|----------------|---------------|------------|
```

---

### Scenario 3: stdlib-only vs a refactor instruction

**Conflict:** `stdlib-only.md` vs a refactor instruction that wants to import a package.

```
Rule A — stdlib-only.md (Correctness tier)
Requirement: task-api uses only the Go standard library. No external packages.
Rationale: reduces supply-chain risk, makes the project self-contained for learning purposes.

Rule B — refactor ergonomics (Maintainability tier)
Requirement: ID generation should use a battle-tested package rather than home-rolled logic.
Suggestion: github.com/google/uuid or similar.
```

**Apply the ladder:**

- `stdlib-only.md` sits in the Correctness tier (dependency integrity, supply-chain constraint).
- The refactor ergonomics rule sits in the Maintainability tier.
- Correctness > Maintainability. `stdlib-only.md` wins.

**What this means in practice:** Claude must not import any external package to satisfy the refactor. The ID generation must use `crypto/rand` + `encoding/hex` from the standard library. If the home-rolled approach has a correctness flaw, fix the flaw without adding a dependency.

**When the ergonomics argument does have merit:** If the project advances past its learning phase and supply-chain risk is accepted, write a scoped exception:

```
## EXCEPTION: stdlib-only.md overridden for id-generation

Overridden rule: .claude/rules/stdlib-only.md
Permitted by: `docs/project.md` decision — Phase 4+ allows audited third-party packages
Scope: internal/id/ package only
Reason: home-rolled ID generation has collision risk at scale
Expiry: Phase 4 complete + security review of chosen package
Cleanup: update stdlib-only.md to list approved packages explicitly
Recorded by: <you> on 2026-05-25
```

---

## RULE_PRIORITY.md

One file. Lives at `.claude/RULE_PRIORITY.md`. Its job: make the priority order explicit and list all active exceptions. Claude reads it. You read it. There is no ambiguity about what wins.

**Format:**

```markdown
# RULE_PRIORITY.md

## Priority order

1. Security
2. Correctness
3. Reliability
4. Maintainability
5. Performance / cost

## Rule tier assignments

| Rule file | Tier | Notes |
|-----------|------|-------|
| no-plaintext-secrets.md | Security | Hard stop — no exceptions |
| stdlib-only.md | Correctness | Supply-chain integrity |
| no-global-state.md | Reliability | Test isolation requirement |
| error-wrapping.md | Maintainability | Diagnostic quality |

## Active exceptions

(none)

## Resolved exceptions

| Exception | Overridden rule | Resolved date | Resolution |
|-----------|----------------|---------------|------------|
```

When you add an exception, move it into the Active section. When the expiry condition is met, move it to Resolved with the resolution action taken.

---

## Checklist

- [ ] I can name the five tiers of the priority ladder in order and explain why that order holds.
- [ ] I can identify which of the three conflict types a given collision belongs to.
- [ ] I apply the four-step resolution procedure (identify → ladder → document → expiry) before resolving any conflict.
- [ ] Every exception I write has a scope, a reason, an expiry condition, and a cleanup action.
- [ ] I know that SPEC constraints are scoped decisions, not exceptions to rules.
- [ ] `RULE_PRIORITY.md` exists in task-api with tier assignments and an active-exceptions table.
- [ ] Time-bounded exceptions without an expiry do not exist in my project.
- [ ] I can resolve the TDD-vs-scaffolding conflict using the Type 3 (scoped decision) classification.
- [ ] I know when a turn-level instruction can override a project rule — and when it cannot (Security tier).
- [ ] I can write a turn-override exception record with scope, reason, expiry, and cleanup steps.
