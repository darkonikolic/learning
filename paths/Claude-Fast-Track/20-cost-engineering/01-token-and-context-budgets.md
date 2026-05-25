# Token and context budgets

Two distinct budgets govern every Claude Code workflow. They are not the same budget. Conflating them produces the wrong optimisations.

---

## Two distinct budgets

| Budget | What it measures | Unit | Who controls it |
|--------|-----------------|------|----------------|
| **Token budget** | Cost per request — tokens consumed by input + output per API call | Tokens / dollars | You, via prompt discipline and context trimming |
| **Context budget** | What fits in the context window — total characters / tokens available before the window fills | Context window percentage | You, via what you include in each call |

**Why they differ:**

- You can make many cheap (low-token) calls that individually stay within budget but collectively exhaust the context window if output from earlier calls is fed forward.
- You can make one call that uses most of the context window but costs little if the inputs are short and the output is tightly scoped.
- Optimising only for token cost while ignoring context fill leads to: truncation of earlier instructions, lost SPEC sections mid-execute, and agent behavior that degrades without warning.

---

## Cost ownership per workflow stage

Each GSD workflow stage has a different token profile. Knowing where cost concentrates tells you where to apply budget discipline.

| Stage | Token cost | Dominant input | Dominant output | Budget lever |
|-------|-----------|---------------|----------------|-------------|
| `/gsd:discuss-phase` | Low | Questions + brief answers | Analysis text | Minimize answer verbosity |
| `/gsd:spec-phase` | Low–Medium | Requirements discussion | SPEC.md draft | Keep SPEC sections atomic |
| `/gsd:plan-phase` | Medium | SPEC.md + PROJECT.md + rules | PLAN.md + task list | Trim what Claude reads |
| `/gsd:execute-phase` | High | PLAN.md + SPEC.md + source files per task | Code commits | Scope tasks narrowly; pass only needed files |
| `/gsd:review` | Medium | Source files + SPEC.md | Review report | Limit files to changed scope |
| `/gsd:verify-work` | Low | Acceptance criteria + targeted output | Pass/fail assessment | Pass only the relevant SPEC section |

**Execute-phase dominates cost.** During execute, Claude reads PLAN.md at the start of every task (because each task re-establishes context), plus the source files relevant to that task. With 10 tasks in a wave, PLAN.md is read 10 times. A 400-line PLAN.md at ~300 tokens costs 3,000 tokens just in PLAN.md reads per wave — before any code is written.

---

## The cost–quality tradeoff

Reducing context is not free. The relationship is not linear: below a threshold, removing context degrades output quality sharply, which increases retry count, which increases net cost.

**The degradation spiral:**

```
Over-trimmed context
    → Claude misses a SPEC constraint
        → Wrong implementation
            → You retry (add back the context you removed)
                → Net token spend: original cost + correction cost + verification cost
```

A 20% context reduction that causes one retry costs more than no reduction would have.

**Where thrift is forbidden:**

| Context element | Removable? | Why |
|----------------|-----------|-----|
| SPEC acceptance criteria | Never | Removing them guarantees acceptance failures |
| Security rules | Never | Removing them produces insecure code that costs more to fix than it saved |
| Error handling requirements | Never | Silent removal causes runtime failures, not compile failures |
| Existing file contents (if task modifies that file) | Never | Claude will invent the current state rather than read it |
| Changelog / prior decision context | Sometimes | Safe to remove if the task does not depend on prior decisions |
| Full PROJECT.md | Sometimes | Pass only the relevant sections per task |

---

## Soft vs hard ceilings per phase

Define ceilings before running a phase, not after you receive the invoice.

| Ceiling type | Definition | Response when hit |
|-------------|-----------|------------------|
| **Soft ceiling** | Budget you expect to stay within; crossing it triggers a review | Stop, assess whether the remaining tasks justify continuing; trim context or narrow scope |
| **Hard ceiling** | Absolute limit; crossing it stops execution | Stop. Replan remaining tasks with narrower scope before resuming. |

**Example ceilings for task-api Phase 3 (PATCH endpoint):**

```
Token budget:
  Soft ceiling: 80,000 tokens for the full phase
  Hard ceiling: 120,000 tokens
  
Context budget:
  Soft ceiling: 60% context window fill per task
  Hard ceiling: 80% context window fill (above this, earlier instructions are at risk of truncation)
```

If you have no data yet, start with soft ceilings at 1.5× your initial estimate. Record actual spend. Use it to calibrate the next phase.

---

## Parallelization cost multiplier

Parallelizing agents does not reduce token cost — it multiplies it. Fan-out of N agents costs N× the tokens of a single-agent run, because each agent receives its own full context copy.

**When parallelization is worth it:**

| Condition | Worth it? | Reason |
|-----------|----------|--------|
| Tasks are fully independent (no shared state) | Yes | Each agent solves a separate problem; no merge cost |
| Subtasks have been verified as non-overlapping | Yes | No divergence risk; merge is trivial |
| Wall-clock time matters more than total token spend | Yes | Parallel cuts latency at a cost premium |
| Task scope is narrow and well-specified | Yes | Narrow scope limits context per agent |

**When parallelization is not worth it:**

| Condition | Not worth it | Reason |
|-----------|-------------|--------|
| Tasks share mutable state (same file, same data store) | No | Merge conflicts cost more than you saved |
| Tasks have sequential dependencies | No | Agent 2 cannot start until Agent 1 finishes; no actual parallelism |
| Tasks are underspecified | No | Each agent takes a different interpretation; merge diverges |
| Context window is near capacity | No | Each agent gets a truncated copy; quality degrades |

**The multiplier in practice:** two agents in parallel cost 2× tokens. If the merge step requires a third agent to reconcile diverging outputs, the actual cost is 3× a sequential run, with added latency for the merge pass. Fan-out decisions need a token budget that accounts for the merge.

---

## task-api phase cost estimates

These are rough estimates for orientation — your actual spend will vary by PLAN.md size, source file size, and model version.

| Phase | Tasks | Estimated tokens | Where most tokens go |
|-------|-------|-----------------|---------------------|
| Phase 1 — project setup | 3 | 15,000–25,000 | SPEC.md creation during plan-phase |
| Phase 2 — POST /tasks | 4 | 30,000–45,000 | PLAN.md reads during execute (×4 tasks) |
| Phase 3 — GET /tasks + PATCH | 6 | 50,000–75,000 | Source file reads + PLAN.md reads (×6) |
| Phase 4 — DELETE + error handling | 5 | 45,000–65,000 | Error handling rules + source file reads |

**Most tokens are spent in execute-phase reading PLAN.md.** During a 6-task execute, PLAN.md is read once per task initialization. If PLAN.md is 500 lines (~400 tokens), that is 2,400 tokens in PLAN.md reads alone — before any file reads or code generation.

**Optimisation target:** PLAN.md verbosity. A PLAN.md that describes each task in 10–15 lines costs roughly half the context of one that describes each task in 25–30 lines, with no quality loss if the task descriptions are precise.

---

## Context budget anatomy

The context window is shared by: system prompt + CLAUDE.md + rules files + PLAN.md + source files + task instruction + prior conversation turns.

Each component competes for the same space. During execute-phase with a complex task:

```
System prompt:              ~2,000 tokens  (fixed — not removable)
CLAUDE.md:                  ~1,500 tokens  (semi-fixed — trim rarely)
Rules files (loaded):       ~3,000 tokens  (control by selective loading)
PLAN.md:                    ~2,000 tokens  (control by PLAN.md discipline)
Source files (task-relevant): ~4,000 tokens  (control by file selection)
Task instruction:           ~500 tokens   (fixed per task)
Prior turns (accumulated):  ~3,000 tokens  (grows as conversation continues)
─────────────────────────────────────────
Total:                     ~16,000 tokens per task in a long session
```

In a 200,000-token context window, 16,000 tokens per task leaves substantial room. But in a 32,000-token window, a session with 10 prior turns and 5 loaded source files is near capacity before the task begins.

**Context fill monitoring:** Claude Code shows context usage in the session header. Watch for it climbing past 70% during execute-phase. Above 70%, early instructions (SPEC, rules, CLAUDE.md) risk being displaced by accumulated output.

---

## Cost–quality minimum floor

Budget discipline does not mean minimising cost at all costs. There is a floor below which cost reduction is not a trade-off — it is a defect.

| Category | Floor | Consequence of violating |
|----------|-------|------------------------|
| Security rules in context | Always present | Insecure code with no audit trail |
| SPEC acceptance criteria | Always present per relevant endpoint | Acceptance failures that require a full re-execute |
| File contents for files being modified | Always present | Claude invents current state; produces merge conflicts |
| Verification step before advancing a wave | Always run | Wrong output becomes the foundation for the next wave |

**The test for a valid optimisation:** removing this context element cannot cause a correctness, security, or reliability failure for any task in this wave. If you cannot confirm that, do not remove it.

Budget decisions that violate the floor are not optimisations. They are deferred rework with interest.

---

## Checklist

- [ ] I can distinguish token budget (cost per request) from context budget (what fits in the window).
- [ ] I know which workflow stage dominates token cost (execute-phase) and why (PLAN.md reads × task count).
- [ ] I understand the degradation spiral: over-trimming context → wrong output → retries → net higher cost.
- [ ] I know which context elements are never removable (SPEC acceptance criteria, security rules, modified file contents).
- [ ] I can define soft and hard ceilings for a phase and state what to do when each is crossed.
- [ ] I know the parallelization cost multiplier: N agents = N× tokens, plus merge cost.
- [ ] I know the two conditions that make parallelization not worth it: shared state and sequential dependencies.
- [ ] I can estimate where most tokens are spent in a task-api execute-phase.
