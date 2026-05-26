# Partial failure and recovery

Partial failure is the normal failure mode of parallel multi-agent systems. When five agents run simultaneously, the probability that at least one fails is higher than the probability that one agent running alone fails. Partial failure handling is not an edge case — it is the expected case.

---

## What partial failure is

**Complete failure:** all agents fail. Easy to detect, easy to handle — retry everything.

**Partial failure:** some agents succeed, some fail. Hard to handle because:
- Successful agents may have written changes to files or state.
- Naive retry re-runs successful agents, causing duplicate work (or worse, overwriting correct results).
- No retry leaves the system in an inconsistent state.

Example:
- Wave 2 has three tasks: A (write handler), B (write tests), C (write CLAUDE.md update).
- A succeeds: internal/handler/task.go is written.
- B fails: test file not written.
- C succeeds: CLAUDE.md updated.

If you retry all of wave 2: A runs again and may overwrite its own correct output with a different implementation. B runs and writes the tests. C runs again and may add duplicate entries to CLAUDE.md.

If you don't retry: the system is missing the tests. Incomplete.

The correct recovery requires: retry only B.

---

## Idempotency in agent tasks

**Idempotent:** running a task twice produces the same result as running it once.

Designing tasks to be idempotent is the prerequisite for safe retry. If retrying a successful agent is harmless, partial retry (retry only the failed agents) is safe.

**Idempotent task design:**
- Write file if not exists, overwrite if exists — not append.
- Create resource if not present, skip if already present.
- Each task has a clear, deterministic output that doesn't accumulate.

**Executor convention:** each task makes an atomic git commit. If a task fails mid-execution, no commit is made. The next retry starts from the last clean commit. Running the task again overwrites the partial (uncommitted) work with a complete implementation.

This makes tasks idempotent: running a completed task again (with `--gaps-only` off) re-writes the file and re-makes the commit. Running a failed task again starts from clean state.

---

## Retry policies

Not all failures warrant the same retry approach:

| Failure type | Retry policy | Reason |
|-------------|-------------|--------|
| Timeout (agent too slow) | Immediate retry once | Transient — likely resolves |
| Network error (MCP server down) | Backoff retry (wait, then retry) | Resource contention — wait helps |
| Agent produced wrong output | No retry — fix prompt first | Logic failure — retrying produces same wrong output |
| Partial file write (corruption) | Restore from last commit, then retry | Bad state — clean slate needed |
| Wave 1 partial failure | Retry only failed tasks (--gaps-only) | Idempotent tasks — safe to re-run |

**Maximum retries:** always set a limit. An infinite retry loop on a logic failure will run forever generating wrong output and burning tokens. Three retries is typical. If it fails three times, escalate to human review.

**When NOT to retry:**
- The task succeeded but produced wrong output. Retrying with the same prompt produces the same wrong output.
- The SPEC is ambiguous. Retrying with an ambiguous SPEC produces a different interpretation each time, not a correct one.
- The prior wave's output is wrong. Retrying the current wave with wrong input produces wrong output.

In all three cases: stop, diagnose, fix the root cause, then retry.

---

## Recovery strategies

| Failure type | Recovery action |
|-------------|----------------|
| Agent timeout | Retry the specific task with the same prompt |
| Agent wrong output (logic failure) | Diagnose: which constraint was violated? Fix prompt. Retry. |
| Partial file write / corruption | `git checkout <file>` to restore last clean state. Retry task. |
| Wave 1 partial failure | Use --gaps-only flag: re-run only tasks not in STATE.md as complete |
| STATE.md inconsistent | Manual STATE.md repair: mark only genuinely-complete tasks. |
| Multiple waves partially complete | Audit STATE.md manually. Re-run from the earliest incomplete wave. |

---

## The --gaps-only retry pattern

When partial failure occurs during execute-phase, use `--gaps-only` mode to re-run only tasks not marked complete in STATE.md.

How it works:
1. Read STATE.md.
2. Tasks marked as complete are skipped.
3. Tasks not marked complete are re-run.
4. STATE.md is updated as tasks complete.

This works safely because tasks are designed to be idempotent. A task that was already completed and is re-run will overwrite its own correct output — which is safe because it produces the same correct output again.

Precondition for --gaps-only to be safe: tasks in STATE.md marked "complete" must actually be complete. If a task was marked complete prematurely (agent said "done" but work was wrong), --gaps-only will skip it. Manual STATE.md repair is needed: remove the "complete" marker for the incorrectly-completed task.

---

## Preventing partial failure through task design

The best partial failure handling is preventing it in the first place.

**Make tasks small and bounded.** A task that writes one function to one file has a smaller failure surface than a task that writes a whole package. Smaller tasks fail less and recover faster.

**Make tasks independent within a wave.** If two tasks in the same wave both write to the same file, partial failure of one leaves the file in a state that the other agent either also modified or didn't expect.

**Verify before advancing waves.** Run `go build ./...` and `go test ./...` after each wave completes. Advancing to wave 2 with broken wave 1 output means wave 2 builds on broken foundations.

**Commit atomically.** Each task should produce one commit. If the commit doesn't exist after the agent says "done," the task failed (silently or partially). The absence of a commit is a reliable failure signal.

---

## Practical partial failure walkthrough: task-api wave 2

Scenario: wave 2 has three tasks. Task A (write handler) succeeds. Task B (write tests) fails with a timeout. Task C (update CLAUDE.md) succeeds.

**State after partial failure:**
- STATE.md shows: A complete, B not present, C complete.
- Git log shows: two commits (one for A, one for C). No commit for B.
- go test ./...: fails because tests don't exist.

**Correct recovery path:**

Step 1: Identify what failed.
```bash
cat .planning/phases/01-endpoints/STATE.md
```
Task B is not in STATE.md as complete.

Step 2: Confirm the failure type.
```bash
git log --oneline --since="30 minutes ago"
```
Two commits present (A and C). No commit for B. This confirms B failed silently — it didn't commit.

Step 3: Choose retry policy.
The failure was a timeout (transient). Not a logic failure. Retry is appropriate.

Step 4: Retry only task B.
```
Write integration tests for GET /tasks in internal/handler/task_test.go.
[Task B's full prompt, same as the original]
```

Step 5: Verify.
```bash
go test ./...
```
Tests pass. STATE.md now shows B complete.

Note what did NOT happen: you did not re-run tasks A and C. They were complete and correct. Retrying them would have been wasteful and potentially harmful (if re-running C added duplicate entries to CLAUDE.md).

---

## Diagnosing failure type before retrying

Before retrying any failed task, diagnose why it failed:

**Check 1: Did the agent produce any output?**
```bash
git log --oneline --since="1 hour ago"
```
If no commit for the task: the agent either failed to execute or produced no output. May be a transient failure.

**Check 2: Is there partial output (uncommitted)?**
```bash
git status
```
If there are unstaged or modified files: the agent started but didn't finish. The partial output may be wrong.
Fix: `git checkout -- <file>` to discard partial output, then retry.

**Check 3: Did a prior wave succeed?**
If wave 1 is wrong and wave 2 ran anyway: wave 2's input was corrupt. Retrying wave 2 with the same (wrong) input produces the same (wrong) output. Fix wave 1 first.

**Check 4: Is the SPEC ambiguous?**
If the agent produced output but the output was wrong in a way that suggests it interpreted the task differently each time: the SPEC has an ambiguity. Retry without fixing the ambiguity will produce another valid-but-wrong interpretation.
Fix: clarify the SPEC or constraint before retrying.

---

## Checklist

- [ ] I can explain partial failure: some agents succeed, some fail, state is inconsistent.
- [ ] I know what idempotency means for agent tasks and why it enables safe retry.
- [ ] I know the four failure types and their correct retry policies.
- [ ] I know when NOT to retry: logic failure, ambiguous SPEC, wrong prior-wave output.
- [ ] I know how --gaps-only works and its precondition (STATE.md accuracy).
- [ ] I can design a task to be idempotent: one file, one commit, deterministic output.
- [ ] I run go build and go test after each wave to catch partial failures before advancing.
