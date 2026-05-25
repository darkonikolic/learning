# Execute-phase: waves and state

Execute-phase is the most automated step in the GSD loop. Understanding what happens inside it — and what STATE.md tracks — lets you recover when it fails or diverges.

---

## What execute-phase does internally

When you run `/gsd:execute-phase N`, the following happens:

1. GSD reads `.planning/phases/XX-name/XX-YY-PLAN.md` and extracts the wave structure
2. **Wave 1 starts:** GSD spawns one executor agent per task in Wave 1, in parallel
3. Each agent:
   - Reads its specific task from PLAN.md
   - Implements the task (writes code, creates files, modifies existing files)
   - Commits the change atomically with a message referencing the task ID
   - Reports completion status back to GSD
4. GSD waits for all Wave 1 agents to complete (fan-in)
5. GSD updates STATE.md with Wave 1 completions
6. **Wave 2 starts:** same process for Wave 2 tasks (fan-out)
7. After all waves complete: GSD updates ROADMAP.md phase status and REQUIREMENTS.md satisfied markers

The wave structure ensures that task 01-03 (which depends on 01-01 and 01-02) does not start until both Wave 1 tasks have committed successfully.

---

## STATE.md during execute

STATE.md is a live progress ledger. It updates after each wave. Here is what it looks like at different points for task-api Phase 1:

**After bootstrap (before execute):**
```markdown
# STATE

## Current phase
Phase 01: POST /tasks endpoint

## Status
Planned — ready to execute

## Completed tasks
(none)

## Active tasks
(none — waiting for execute)

## Blockers
None

## Next action
Run /gsd:execute-phase 1
```

**During Wave 2:**
```markdown
# STATE

## Current phase
Phase 01: POST /tasks endpoint

## Status
In progress — Wave 2 executing

## Last checkpoint
Wave 1 complete — commit range abc123..def456

## Completed tasks
- 01-01: Define task domain model — commit abc123
- 01-02: Create in-memory task store — commit def456

## Active tasks
- 01-03: Implement POST /tasks handler

## Blockers
None

## Decisions made this session
(none)

## Next action
After Wave 2: Wave 3 (01-04: wiring and tests)
```

**After all waves complete:**
```markdown
# STATE

## Current phase
Phase 01: POST /tasks endpoint

## Status
Execution complete — pending verification

## Completed tasks
- 01-01: Define task domain model — commit abc123
- 01-02: Create in-memory task store — commit def456
- 01-03: Implement POST /tasks handler — commit ghi789
- 01-04: Wire routes and write integration tests — commit jkl012

## Blockers
None

## Next action
Run /gsd:verify-work
```

---

## Execute flags

| Flag | Effect | When to use |
|------|--------|-------------|
| `--wave W` | Run a specific wave only | Wave N failed; want to re-run it after fix |
| `--gaps-only` | Run only tasks not marked complete in STATE.md | Execute stopped mid-run; fix applied |
| `--tdd` | Test-first task order (test before impl per task) | Plan was created with --tdd |

**`--wave` vs `--gaps-only`:**
- `--wave 2` re-runs everything in Wave 2, even if some Wave 2 tasks already completed
- `--gaps-only` skips any task marked complete in STATE.md regardless of wave

Use `--wave` when you want a clean re-run of a specific wave. Use `--gaps-only` when some tasks in a wave completed and you only want the failed ones re-run. Be sure tasks are idempotent (creating the same file twice should not break the build) before using either.

---

## Manual Claude Code work during execute

A valid hybrid pattern:

1. GSD PLAN.md is source of truth for task bounds
2. In the same Claude Code session, implement specific plan steps manually
3. Cite the plan in your Claude Code message: "Implement task 01-03 from PLAN.md: internal/handler/tasks.go, CreateTask handler with validation"
4. Commit manually with the same atomic scope that GSD would use
5. Update STATE.md completed tasks manually to match your commit
6. Return to GSD commands for verification and ship

This pattern is valid when: an executor agent failed on a specific task and you want to fix it manually rather than re-running the agent.

**Invalid pattern:** Implementing features not in PLAN.md while execute is in-flight. STATE.md tracks PLAN.md tasks. If you build things outside the plan, STATE.md diverges from reality — and `/gsd:resume-work` will reconstruct a false picture of progress.

---

## What to check after execute

Run these immediately after `/gsd:execute-phase N` completes:

```bash
# Verify the code compiles
go build ./...

# Verify tests pass
go test ./...

# Check what was committed
git log --oneline -10

# Read the state
# (view .planning/STATE.md)
```

Then cross-reference:
- Does git log show one commit per PLAN.md task? If yes, execution was atomic.
- Does STATE.md show all tasks as completed? If some are missing, they failed silently.
- Does `go build` pass? If not, an agent introduced a compile error — find it in git log.

---

## When execute fails mid-wave

Failure modes and responses:

| Failure | Symptom | Fix |
|---------|---------|-----|
| Compile error introduced | `go build` fails after execute | Find the bad commit in git log; fix the code; update STATE.md |
| Agent reported completion without committing | STATE.md says complete; git log has no commit | Re-run the task: `--wave W` or `--gaps-only` |
| Agent implemented wrong behavior | Code compiles but wrong output | Fix the code; verify-work will catch it |
| Dependency missing | Agent could not import required code | Check wave order; the dependency task may not have run first |
| Task vague, agent guessed wrong | Output not what PLAN.md described | Edit PLAN.md task to be more specific; re-run with `--gaps-only` |

Recovery procedure:

1. Check STATE.md — identify which tasks completed and which failed
2. Check git log — verify each "completed" task has a corresponding commit
3. Fix the root cause (bad code, vague task description, missing dependency)
4. Run `/gsd:execute-phase N --gaps-only` to re-run only failed tasks

---

## STATE.md integrity rules

STATE.md is read by GSD commands as source of truth. These rules prevent STATE.md from lying:

**Never mark a task complete if it partially works.** If the handler exists but validation is missing, the task is not complete. Write: "01-03: partial (handler created, validation missing, 01-03 not complete)".

**Record decisions in STATE.md as you make them.** If you decided to use sequential integers instead of UUIDs, write it in the "Decisions made this session" section. The next session's `/gsd:resume-work` uses this to reconstruct why the code looks the way it does.

**Do not leave blockers empty when blockers exist.** False confidence leads to off-track next steps. If there is a blocker, name it explicitly: "01-03: blocked — Go version 1.22 io/http.Servemux pattern routing not compiling, needs investigation."

**Repair procedure when STATE.md is stale:**

```
1. Run: git log --oneline -20
2. Cross-reference each commit with PLAN.md task IDs
3. Update STATE.md completed tasks to match actual commits
4. Update STATUS to reflect reality (in-progress, not completed)
5. Run /gsd:health to verify consistency
```

---

## Checklist

- [ ] I can describe the fan-out / fan-in wave execution pattern.
- [ ] I know what STATE.md looks like at three different points during execute.
- [ ] I know when to use --wave vs --gaps-only.
- [ ] I understand the valid hybrid pattern for manual work during execute.
- [ ] I know the five things to check immediately after execute-phase completes.
- [ ] I understand why marking partial tasks as complete in STATE.md causes problems.
- [ ] I can perform the STATE.md repair procedure from memory.
- [ ] I know what atomic commit means in the context of GSD execution.
