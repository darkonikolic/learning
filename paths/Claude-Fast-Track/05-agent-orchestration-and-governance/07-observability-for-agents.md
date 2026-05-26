# Observability for agents

Observability is the ability to understand a system's internal state from its external outputs. For distributed systems — including multi-agent AI systems — observability is what makes debugging possible. Without it, failures are mysteries.

The three pillars of observability applied to agent systems: logs, traces, and metrics.

---

## The three pillars

**Logs: what happened.**

A log is a timestamped record of a discrete event: "agent received task X", "agent produced output Y", "file Z was written", "test failed with error W".

Logs answer: "what did the system do?"

In Claude Code:
- Git commits are logs — each commit records what was written and when.
- STATE.md updates are logs — each update records a task completion event.
- Agent output text is a log — it describes what the agent did.

**Traces: the execution path.**

A trace is a record of one complete workflow from start to finish. It shows which component called which other component, in what order, with what inputs and outputs.

Traces answer: "how did the system execute?" and "where did it go wrong?"

In Claude Code:
- A trace of one execute-phase run: which wave ran first, which agents were spawned, what each produced, which succeeded and which failed.
- The chain of files produced: CONTEXT.md → PLAN.md → source files (one per task) → test files → STATE.md updates.

**Metrics: aggregate behavior.**

Metrics are aggregate measurements over time: success rate, average latency, token usage per agent type, failure frequency by task category.

Metrics answer: "is the system healthy?" and "is it getting better or worse?"

In Claude Code: harder to measure directly without tooling. Approximate metrics: pass rate on first execute-phase run, frequency of --gaps-only retries, frequency of manual corrections.

---

## Distributed tracing terminology

**Trace:** a record of one complete workflow execution. Example: one execute-phase run from start to finish.

**Span:** one unit of work within a trace. Example: one agent executing one task. The span records: task description, start time, end time, success/failure, files changed, output summary.

**Parent-child relationship:** orchestrator spans contain worker spans. The execute-phase run (parent span) contains all executor agent runs (child spans). If a child span fails, it is visible as a failure inside the parent.

**Correlation ID:** an identifier that links all spans in one trace. This is implicitly the phase identifier — all activity for a phase is linked by that identifier.

In Claude Code today, this vocabulary applies conceptually. Explicit distributed tracing with span IDs and collectors is not built into Claude Code — but the same mental model applies when debugging agent failures.

---

## What to observe in multi-agent Claude systems

**Per-agent (span-level):**
- Task description: what was this agent asked to do?
- Files changed: which files did it write?
- Commit created: yes/no — the most reliable success signal.
- Agent summary: what did the agent report?
- Token usage: approximately how much context was used?

**Per-wave:**
- Wave number and tasks included.
- Completion order: did any agent take significantly longer?
- Failures: which agents failed, what error?
- STATE.md delta: what changed in STATE.md after this wave?

**Per-phase:**
- Total tasks, success count, failure count.
- First-run pass rate (how often execute-phase completes without retries).
- Time elapsed.
- Final STATE.md vs initial PLAN.md: are all tasks accounted for?

---

## Audit trail as governance

Every agent action should be traceable: who did what, when, with what result. This is not just for debugging — it is a governance requirement for AI systems acting on your codebase.

**The audit trail:**
- **Git commits:** atomic per task. Each commit message identifies the task and agent that wrote it. `git log --oneline` is a timeline of agent actions.
- **STATE.md:** records task completion events with timestamps and results.
- **REQUIREMENTS.md:** records satisfaction markers — which requirements were addressed by which implementation.

When something breaks after an execute-phase run, this audit trail tells you:
1. Which agent made the change (git log — commit message identifies the task).
2. Exactly what changed (git diff on that commit).
3. Whether the requirement was marked satisfied (REQUIREMENTS.md).

Without an audit trail: "something broke and I don't know what agent did it or when."

With an audit trail: "wave 3, task C (implement complete handler) made this change at 14:23. Here is the exact diff. The requirement R-07 was marked satisfied. The test I'm now looking at was written in wave 4."

---

## Observability for debugging agent failures

Systematic approach when an execute-phase fails or produces wrong output:

**Step 1: Identify which agent failed (trace).**

Check STATE.md: which tasks are complete? Which are missing?

```bash
cat .planning/phases/01-endpoints/STATE.md
```

The missing task in STATE.md is the one that failed.

**Step 2: Find what it produced (log).**

Check git log for the period of the execute-phase run:
```bash
git log --oneline --since="1 hour ago"
```

If the task has no commit: it failed silently or was never attempted. If it has a commit: the work was attempted. Read the diff.

**Step 3: Find what state it left (log + state check).**

```bash
go build ./...
go test ./...
```

If build fails: the agent produced invalid Go code. The error message identifies the file and line.

If tests fail: the agent's implementation doesn't match the test's expectations. Or the test is wrong. Read both.

**Step 4: Determine if failure propagated (trace).**

If wave N failed and wave N+1 ran anyway: wave N+1's input was wrong. Wave N+1's output may be wrong even if it "succeeded."

Check: did wave N+1 agents have access to wave N output? If yes and wave N was wrong, wave N+1 results are suspect.

---

## Observability tools in Claude Code

| Tool | What it shows |
|------|--------------|
| `git log --oneline` | Timeline of agent commits (audit trail) |
| `git diff <commit>` | Exact changes made by a specific agent action |
| `cat STATE.md` | Current task completion status |
| `go build ./...` | Build-time errors introduced by agent changes |
| `go test ./...` | Test failures (agent implementation vs test expectations) |

These are your observability tools. Using them systematically after each wave is the difference between understanding what your agent system did and guessing.

---

## Checklist

- [ ] I know the three pillars of observability: logs, traces, metrics.
- [ ] I can explain trace, span, and parent-child relationship in agent context.
- [ ] I know the audit trail components: git commits, STATE.md, REQUIREMENTS.md.
- [ ] I follow the four-step debugging sequence: trace → log → state → propagation.
- [ ] I run go build and go test after each wave and treat failures as observability signals.
- [ ] I read git log after execute-phase to understand what each agent did.
- [ ] I check STATE.md to identify which tasks completed and which failed.
