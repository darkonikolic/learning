# Orchestration vs choreography

Two fundamental patterns for coordinating multiple agents. The choice between them determines system architecture, failure modes, and observability characteristics. Understanding both makes GSD's execution model legible.

---

## Orchestration (centralized control)

One orchestrator agent controls execution. It assigns tasks, monitors progress, handles failures, and decides what happens next.

Workers are subordinate. They execute the specific task they are assigned. They report results back to the orchestrator. They do not need to understand the full workflow — only their piece of it.

The orchestrator has the full picture of state at all times.

```
┌─────────────────────────────────────┐
│           ORCHESTRATOR              │
│  - holds global state               │
│  - assigns tasks                    │
│  - monitors results                 │
│  - handles failures                 │
└──────┬────────────┬─────────────────┘
       │            │
       ▼            ▼
  [Worker A]   [Worker B]
  executes     executes
  task 1       task 2
```

When to use orchestration:
- Tasks have dependencies on each other — task B cannot start until task A is complete
- You need a single point of recovery — when something fails, one entity knows what to retry
- State must be consistent — the orchestrator ensures no two workers contradict each other
- Failure recovery requires context — the orchestrator can reassign failed tasks with full knowledge of what succeeded

Drawbacks:
- The orchestrator is a bottleneck — all work flows through it
- Single point of failure — if the orchestrator fails, everything stops
- Scaling is harder — the orchestrator must track N workers simultaneously

---

## Choreography (decentralized control)

No central controller. Each agent knows its trigger and its output. Agents react to events or shared state changes and produce outputs that trigger the next agent.

State is shared — typically through events, a message queue, or a shared data store. Agents read from and write to this shared medium.

```
[Agent A] ──produces output──► [shared state / event bus] ──triggers──► [Agent B]
                                          │
                                          └──triggers──► [Agent C]
```

No orchestrator sees the full picture. Each agent only knows: "when I see X, I do Y and emit Z."

When to use choreography:
- Tasks are fully independent — no dependency between them
- Maximum throughput is the goal — no coordination overhead
- Agents are truly isolated — each can succeed or fail without affecting others
- The workflow is simple — complex dependencies are hard to track without a central controller

Drawbacks:
- Harder to debug — no single entity knows what the overall state is
- Difficult to track overall progress — must reconstruct from event history
- Order-dependent bugs are subtle — a state change from Agent A may cause Agent C to fail in ways that are hard to trace

---

## Comparison

| Dimension | Orchestration | Choreography |
|-----------|--------------|--------------|
| Control | Centralized — one orchestrator | Decentralized — no coordinator |
| State | Orchestrator holds global state | Shared store or event bus |
| Failure recovery | Orchestrator knows what to retry | Must reconstruct from events |
| Dependencies | Handles complex dependencies | Best for independent tasks |
| Debuggability | High — trace through orchestrator | Low — trace through events |
| Throughput | Bottlenecked by orchestrator | Maximum parallel throughput |
| Complexity | Orchestrator logic is complex | Individual agents are simple |

---

## Decision table

| Situation | Use |
|-----------|-----|
| Tasks have strict ordering dependencies | Orchestration |
| Tasks are fully independent, no shared state | Choreography / parallel agents |
| Need failure recovery with context | Orchestration |
| Maximum throughput, simple tasks | Choreography |
| Complex workflow with branching logic | Orchestration |
| Loosely coupled, event-driven pipeline | Choreography |
| GSD phase execution | Orchestration (GSD is orchestrator) |
| Multiple independent Claude agents in one message | Choreography-adjacent (no coordinator) |

---

## In Claude Code and GSD

**GSD execute-phase = orchestrator pattern.**

When you run `/gsd:execute-phase`, GSD acts as the orchestrator:
1. It reads PLAN.md — the full task DAG.
2. It identifies which tasks are in the current wave (no unmet dependencies).
3. It spawns executor agents for each task in the wave (fan-out).
4. It waits for all agents in the wave to complete (fan-in).
5. It reads STATE.md — the shared state store — to assess results.
6. It moves to the next wave, or handles failures, based on results.
7. It repeats until all tasks are complete or until a failure requires human intervention.

GSD is not a passive runner. It monitors, it sequences, it recovers.

**Parallel agent calls in one message = choreography-adjacent.**

When you invoke multiple Claude agents in a single message with independent tasks, there is no orchestrator. Each agent operates independently. They do not coordinate. This works well for truly independent tasks. It fails for dependent tasks — neither agent knows what the other did.

```
Message: "Agent 1: write GET handler. Agent 2: write GET handler tests."
```

Both agents run simultaneously. Agent 2 writes tests against an interface contract — not against Agent 1's actual implementation. If Agent 1 made different decisions than the interface contract specifies, Agent 2's tests may not match. No orchestrator resolves this.

For dependent tasks, use orchestration: run Agent 1 first, verify output, then run Agent 2 with Agent 1's output in context.

---

## Why the pattern choice matters

Choosing the wrong pattern wastes effort or introduces bugs.

Using choreography for dependent tasks: Agent B starts based on old state before Agent A finishes writing. Result: race condition or incorrect output.

Using orchestration for independent tasks: unnecessary coordination overhead, slower execution, bottleneck where none was needed.

The GSD PLAN.md wave structure encodes this choice explicitly. Wave 1 tasks are independent — choreography is safe, parallel execution is correct. Wave 2 tasks depend on wave 1 — orchestration is required, sequential wave execution is necessary.

---

## Mixing patterns

Real systems often use both patterns. The outer workflow uses orchestration (GSD controls phase execution). Within a wave, the tasks run in a choreography-adjacent pattern (parallel agents, no coordination between them). This is appropriate because: the wave-level dependencies are handled by the orchestrator (ensuring wave 2 only starts after wave 1 completes), and the within-wave tasks are genuinely independent (handled by the choreography pattern — no coordinator needed).

The mistake to avoid: applying choreography where orchestration is needed. If two tasks within a wave have an implicit dependency (task B uses output from task A), they are in the wrong wave. Choreography between them will produce incorrect output. Move task B to a subsequent wave where orchestration ensures A completes before B starts.

---

## Checklist

- [ ] I can explain orchestration and choreography to someone who hasn't read this module.
- [ ] I know when GSD execute-phase uses orchestration (always — it's the orchestrator).
- [ ] I know when parallel agents in one message are safe (independent tasks only).
- [ ] I can identify whether a set of tasks has dependencies before choosing a pattern.
- [ ] I know the failure mode of using choreography for dependent tasks (race condition / stale state).
