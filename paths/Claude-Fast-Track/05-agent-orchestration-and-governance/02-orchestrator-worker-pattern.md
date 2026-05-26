# Orchestrator-worker pattern

The orchestrator-worker pattern is the core architecture of execute and any multi-agent system with dependent tasks. Understanding the vocabulary — fan-out, fan-in, DAG, wave — is prerequisite to reading `docs/plans/<phase>-plan.md`, understanding execute behavior, and debugging multi-agent failures.

---

## Roles

**Orchestrator:** the agent that plans, assigns, monitors, and recovers. It understands the full workflow. It does not do implementation work — it delegates.

**Worker (executor agent):** the agent that executes one specific task. It receives a task description and context from the orchestrator. It produces a result. It does not understand the broader workflow. These are the executor agents spawned per task during execute.

**Supervisor:** a variant of the orchestrator that also monitors worker health and intervenes when a worker stalls or produces invalid output. You function as supervisor between waves: it checks agent output and can spawn correction agents.

The orchestrator knows everything. The worker knows its task. The supervisor watches both and intervenes when the system deviates.

---

## Fan-out and fan-in

**Fan-out:** the orchestrator distributes N independent tasks to N workers simultaneously. All workers start at the same time. This maximizes parallel throughput for independent tasks.

```
Orchestrator
    │
    ├──► Worker A (task 1) ──runs concurrently──┐
    ├──► Worker B (task 2) ──runs concurrently──┤
    └──► Worker C (task 3) ──runs concurrently──┘
```

**Fan-in:** the orchestrator waits for all workers to complete before proceeding to the next step. No downstream task starts until all upstream tasks report completion.

```
Worker A result ──┐
Worker B result ──┼──► orchestrator collects all results ──► next step
Worker C result ──┘
```

**Wave:** one fan-out / fan-in cycle. Fan-out all tasks in the wave, wait for fan-in (all complete), advance.

You run one wave at a time at a time:
- Wave 1: fan-out all wave-1 tasks, fan-in, verify all complete.
- Wave 2: fan-out all wave-2 tasks (now that wave-1 dependencies are satisfied), fan-in.
- Continue until all waves are complete or a failure halts execution.

---

## DAG: directed acyclic graph

A DAG is the mathematical structure underlying any dependency-aware task plan. Tasks are nodes. Dependencies are directed edges ("task B depends on task A" = edge A → B).

**Directed:** edges have direction. A depends on B is different from B depends on A.

**Acyclic:** no cycles. Task A cannot depend on task B if task B depends on task A. Cycles mean a task can never start (it needs itself to complete first).

**Why DAG matters for parallelism:** a DAG exposes which tasks can run simultaneously (no dependencies between them) and which must run sequentially (one depends on the other). Maximum parallelism is achieved by running all tasks at the same DAG level simultaneously.

The levels of a DAG correspond to waves in a phase plan:
- DAG level 0 (no dependencies): Wave 1
- DAG level 1 (depends on level 0): Wave 2
- DAG level 2 (depends on level 1): Wave 3

---

## Designing a DAG for task-api Phase 2: GET /tasks

Phase goal: implement GET /tasks endpoint.

Subtasks:
- A: define Task struct and Store interface in internal/store/store.go (if not already done)
- B: implement in-memory store with GetAll method
- C: implement GET /tasks handler in internal/handler/task.go
- D: write integration tests for GET /tasks
- E: update CLAUDE.md with new path entries

Dependency analysis:
- A has no dependencies — define the types first
- B depends on A — can't implement without the interface
- C depends on A and B — handler needs the interface (A) and calls the store (B)
- D depends on C — tests call the handler
- E has no dependencies — documentation update, parallel with everything

DAG:
```
A ──► B ──► C ──► D
E (independent, no arrows)
```

Wave structure:
- Wave 1: A + E (no dependencies, both run in parallel)
- Wave 2: B (depends on A, which wave 1 completes)
- Wave 3: C (depends on B completing)
- Wave 4: D (depends on C completing)

In phase plan format:
```markdown
## Wave 1 (parallel)
- A: define Task struct and Store interface
- E: update CLAUDE.md

## Wave 2 (depends on wave 1)
- B: implement in-memory store with GetAll

## Wave 3 (depends on wave 2)
- C: implement GET /tasks handler

## Wave 4 (depends on wave 3)
- D: write integration tests
```

---

## Why DAG analysis prevents bugs

Naive parallelization (running everything simultaneously):
- Worker C starts writing the handler before Worker B has written the store
- Worker C must guess what the store interface looks like
- Worker D starts writing tests before Worker C has written the handler
- Tests may not match the actual handler implementation

DAG-based wave execution:
- Workers A and E run in wave 1 — both safe because they have no dependencies
- Worker B runs in wave 2 only after A is complete — it reads the interface A defined
- Worker C runs in wave 3 only after B is complete — it calls the store B implemented
- Worker D runs in wave 4 only after C is complete — it tests exactly what C built

The DAG eliminates the guessing. Each worker receives work that can be done correctly because its dependencies are fully resolved.

---

## The supervisor pattern applied to Claude

A supervisor monitors worker output and intervenes when quality is below threshold.

In Claude Code, this means:
1. Orchestrator spawns worker for task X.
2. Worker completes and reports.
3. Supervisor (you, or an automated check) verifies the output.
4. If output is wrong: supervisor spawns a correction agent with specific error context.
5. If output is correct: supervisor moves to next task.

You implement a version of this: after each executor completes, it checks `docs/state.md` and git commits. If the task produced no commit (nothing changed), the task may have failed silently. The orchestrator can detect this and flag it.

The manual version: after each agent completes, run `go build ./...` and `go test ./...`. If they fail, the worker's output is wrong. Report the specific failure back to the agent as a correction.

---

## Checklist

- [ ] I can draw the fan-out/fan-in diagram for a 3-task wave without looking.
- [ ] I know what a DAG is and why acyclic matters (no task can depend on itself, directly or indirectly).
- [ ] I can convert a list of tasks with dependencies into a wave structure.
- [ ] I know that wave execution = one fan-out/fan-in cycle per wave.
- [ ] I can design the DAG for task-api Phase 2 from scratch.
- [ ] I understand why running D before C is wrong even if it "works" sometimes.
