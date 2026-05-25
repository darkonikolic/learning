# GSD troubleshooting

Systematic failure patterns and their fixes. When something breaks in the GSD loop, the answer is almost always in STATE.md, PLAN.md, or git log. Read those three before asking Claude anything.

---

## First response to any GSD problem

Before looking up a specific failure: run these three commands.

```
/gsd:progress         ← where am I according to STATE.md
/gsd:health           ← is .planning/ structurally valid
git log --oneline -10 ← what actually happened in git
```

If these three outputs agree and make sense, the problem is in your understanding, not the state. If they disagree with each other, the problem is state drift — STATE.md is lying about git reality.

---

## Failure: execute fails immediately

**Symptom:** `/gsd:execute-phase N` exits with an error before any wave starts.

**Common causes:**

| Cause | Diagnosis | Fix |
|-------|-----------|-----|
| PLAN.md not found | Check `.planning/phases/XX-name/` — no PLAN.md exists | Run `/gsd:plan-phase N` |
| PLAN.md empty or corrupt | PLAN.md exists but has no tasks | Re-run `/gsd:plan-phase N` |
| STATE.md shows phase already complete | GSD thinks phase is done | Check if it is actually done; if not, repair STATE.md |
| CONTEXT.md missing | Phase folder has no CONTEXT.md | Run `/gsd:discuss-phase N` first |
| Go compile error in existing code | Agent cannot build on top of broken code | Fix compile error before execute |

---

## Failure: agent produces off-plan output

**Symptom:** Execute-phase completes, but the code does not match PLAN.md. Agent implemented something adjacent to the task, not the task itself.

**Causes:**
- Task description was vague — agent filled the ambiguity with its best guess
- Task did not specify a file path — agent chose a different file
- Task said "improve" or "refactor" — agent interpreted scope too broadly

**Fix procedure:**
1. Identify which task produced the wrong output (compare git log commit messages to PLAN.md task IDs)
2. Undo the bad commit: `/gsd:undo` for the specific task, or `git revert` if undo is unavailable
3. Edit the PLAN.md task to be specific: add file path, explicit function signature, exact behavior
4. Re-run: `/gsd:execute-phase N --gaps-only`

**Prevention:** Before every execute, apply the task specificity test from `02-plan-phase-and-approval-gates.md`. Every task must name a file. Every action must be implementable without asking questions.

---

## Failure: STATE.md inconsistent with git history

**Symptom:** STATE.md shows task 01-02 as completed with commit `def456`, but `git log` has no such commit. Or: git log has commits that STATE.md does not list.

**Cause:** Agent reported completion without committing. Or: manual commits happened outside GSD. Or: STATE.md was written from a stale cache.

**Repair procedure:**

```bash
# 1. Get actual commit history
git log --oneline -20

# 2. Open PLAN.md — list every task ID

# 3. Match: for each task ID, is there a commit mentioning it?

# 4. Update STATE.md completed tasks to match git history
#    Only mark a task complete if a commit exists for it

# 5. Update STATUS to reflect reality

# 6. Run health check
# /gsd:health
```

After repair, run `/gsd:progress` to confirm GSD reads the repaired state correctly.

---

## Failure: Wave 2 starts before Wave 1 is done

**Symptom:** Wave 2 agents start and fail because Wave 1 artifacts (files, interfaces) do not exist yet.

**Causes:**
- Manual interference with execute-phase timing
- GSD version bug where wave gate did not wait for all Wave 1 completions
- Some Wave 1 tasks completed but STATE.md was not updated, so GSD thought Wave 1 was done

**Fix:**
1. Stop any running Wave 2 agents
2. Check STATE.md — which Wave 1 tasks are actually complete in git log?
3. Re-run any incomplete Wave 1 tasks: `/gsd:execute-phase N --wave 1`
4. After Wave 1 is fully complete in both git and STATE.md: run Wave 2 explicitly: `--wave 2`

---

## Failure: agent loops on same mistake

**Symptom:** Running `--gaps-only` or `--wave W` produces the same wrong output multiple times. The agent repeats the same error on retries.

**Causes:**
- Problem is in the PLAN.md task description — the description itself leads to the wrong behavior
- Problem is in CLAUDE.md or `.claude/rules/` — a behavioral rule is causing the agent to deviate
- The task depends on something that does not exist yet — dependency not captured in wave ordering

**Diagnosis:**
1. Run the task description through the specificity test: can you execute it yourself by reading the description?
2. Check `.claude/rules/` for any rule that might contradict the task
3. Check wave ordering — does this task depend on output from another task that is not yet complete?

**Fix:**
1. Edit the PLAN.md task description to be unambiguous
2. If a rule is interfering: add a more specific rule that takes precedence: "For task 01-03 only: return 400 with JSON error, not 422"
3. If dependency is missing: move the task to a later wave

---

## Failure: REQUIREMENTS.md not updated after execute

**Symptom:** Phase 1 completes. REQ-001 still shows "status: planned" in REQUIREMENTS.md instead of "status: satisfied — Phase 01".

**Cause:** GSD should update this automatically; if it did not, it is a GSD bug or the execute was not fully clean.

**Fix:** Manually update REQUIREMENTS.md after verifying the REQ is actually met.

```markdown
## REQ-001: Create task
...
Status: satisfied — Phase 01
Phase: 01
```

Only mark REQ as satisfied if verify-work confirmed all its acceptance criteria pass.

---

## Failure: "where am I?" disorientation

When you lose track of where you are in the workflow:

```
Step 1: /gsd:progress          ← GSD's view of current state
Step 2: Read STATE.md directly ← what was actually written
Step 3: /gsd:health            ← structural integrity of .planning/
Step 4: git log --oneline -10  ← what actually happened
```

If `/gsd:progress` and STATE.md agree and make sense: trust them, follow the suggested next step.

If they disagree: trust git log as ground truth. Update STATE.md to match reality. Re-run `/gsd:health`.

Common disorientation causes:
- Session ended without `/gsd:pause-work`
- Multiple Claude Code sessions running on the same repo (state race)
- Manual commits made outside GSD loop

---

## `/gsd:debug` vs manual debugging

| Situation | Use |
|-----------|-----|
| Obvious fix visible immediately (missing import, typo) | Fix directly — do not invoke /gsd:debug |
| Root cause unclear after one read-through | `/gsd:debug` |
| Bug survives one-turn fix attempt | `/gsd:debug` |
| Production incident with unknown cause | `/gsd:debug` |
| Test failure with obvious cause | Fix directly |
| Intermittent behavior (race condition) | `/gsd:debug` — multi-cycle investigation needed |
| Wrong HTTP status code, cause is visible | Fix directly |
| Wrong HTTP status code, cause is not visible | `/gsd:debug` |

`/gsd:debug` maintains state across context resets. Use it when the investigation will span multiple Claude interactions or sessions. For single-session obvious fixes, the overhead is not worth it.

---

## `/gsd:health` output guide

Health check outputs GREEN / YELLOW / RED per item:

| Color | Meaning | Action |
|-------|---------|--------|
| GREEN | File exists, valid, consistent | None needed |
| YELLOW | Warning — functional but messy | Understand it; fix if it causes confusion |
| RED | Blocking — GSD cannot operate correctly | Fix before running any GSD commands |

Common RED findings and fixes:
- "PLAN.md not found for active phase" → Run `/gsd:plan-phase N`
- "STATE.md phase does not exist in ROADMAP.md" → Repair STATE.md or add phase to ROADMAP
- "config.json parse error" → Fix JSON syntax in config.json

Common YELLOW findings and what they mean:
- "CONTEXT.md has no non-goals section" → You accepted the GSD draft without editing; add non-goals
- "STATE.md has no blockers entry" → Normal if there are no blockers; YELLOW to prompt awareness
- "No verification artifact for completed phase" → You skipped verify-work; run it now or create artifact manually

---

## Checklist

- [ ] I know the three commands to run first for any GSD problem.
- [ ] I can diagnose "execute fails immediately" from the failure cause table.
- [ ] I know how to repair STATE.md when it is inconsistent with git history.
- [ ] I know the difference between an agent loop due to a vague task vs a dependency issue.
- [ ] I can explain when to use /gsd:debug vs fix directly.
- [ ] I know what GREEN / YELLOW / RED mean in /gsd:health output.
- [ ] I know the four-step disorientation recovery sequence.
- [ ] I understand why git log is the ground truth when STATE.md and reality disagree.
