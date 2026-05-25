# Claude + GSD concept mapping

This file is the synthesis of modules 01-08. Every pattern and concept covered in this module appears in Claude Code and GSD under a specific name. Knowing the mapping lets you use GSD deliberately — not as a black box — and read about multi-agent patterns in other contexts (LangGraph, CrewAI, AutoGen) and understand how they apply here.

---

## Full concept-to-implementation mapping

| Concept | Definition | In Claude Code + GSD |
|---------|------------|---------------------|
| Orchestrator | Central controller that assigns tasks, monitors, and recovers | GSD execute-phase — reads PLAN.md, spawns executor agents, monitors STATE.md |
| Worker / Executor agent | Executes one task, reports result, no broader awareness | Executor agents spawned by execute-phase — one per task in a wave |
| Supervisor | Monitors worker output and intervenes when quality fails | execute-phase post-task verification (STATE.md check, commit check) |
| Fan-out | Distribute N tasks to N workers simultaneously | One wave: all tasks in wave spawn simultaneously |
| Fan-in | Wait for all workers to complete before proceeding | Wave completion gate: all wave-N tasks must complete before wave N+1 starts |
| DAG | Task graph with dependencies as directed edges | PLAN.md wave structure: wave N depends on wave N-1 completing |
| Shared state | Common store all agents read from and write to | STATE.md (completion status), REQUIREMENTS.md (satisfaction markers), source files |
| HITL gates | Human approval required at defined checkpoints | CONTEXT.md approval, PLAN.md approval, verify-work before ship |
| Blast radius | Scope of potential damage from an agent action | Phase scope bounded by CONTEXT.md non-goals; worktree isolation for risky phases |
| Least privilege | Give agents only the permissions they need | `.claude/settings.json` allow/deny lists |
| Trust boundary | Line between autonomous actions and human-required actions | Deny list items (push, rm -rf) = outside boundary; allow list = inside |
| Context propagation | How state passes between agents | Agent prompts include PLAN.md slice + CONTEXT.md + relevant SPEC section |
| Message passing | Orchestrator includes all needed context in each agent prompt | Executor agent prompts: task + context + constraints assembled by GSD |
| Idempotency | Running a task twice produces same result as running once | Atomic commits per task — retry with --gaps-only is safe |
| Partial failure | Some agents succeed, some fail; inconsistent state | Addressed by --gaps-only flag: re-runs only incomplete STATE.md tasks |
| Audit trail | Every agent action traceable: who, what, when, result | Git commits (one per task) + STATE.md + REQUIREMENTS.md satisfaction markers |
| Distributed trace | Full execution path from workflow start to finish | execute-phase run: sequence of waves + agents + STATE.md updates |
| Span | One unit of work within a trace | One executor agent task: PLAN.md task → commit → STATE.md update |
| Observability | Ability to understand system state from external outputs | /gsd:stats, /gsd:health, STATE.md, git log, go test |
| Trust but verify | Agent summary ≠ proof of correctness | /gsd:verify-work after execute-phase + go build/test verification |
| Hallucination recovery | Fresh context + file-system grounding, not argument | /gsd:debug systematic investigation from file-system state |
| Orchestration pattern | Centralized control with single-point-of-state | GSD execute-phase (always orchestrator, never choreography for dependent tasks) |
| Choreography pattern | Decentralized, event-driven, no coordinator | Parallel independent Claude agents in one message (no GSD coordination) |
| Retry with backoff | Re-run failed tasks with increasing wait time | Manual: re-run specific failed tasks; automated: --gaps-only for wave retries |
| Context isolation | Subagents receive only what they need | Each executor agent prompt is a minimal slice, not the full conversation |

---

## How to use this mapping

**When using GSD execute-phase:** you are using an orchestrator. The orchestrator is GSD. Your job is to approve HITL gates (CONTEXT.md, PLAN.md, verify-work) and to verify output using trust-but-verify techniques after each wave.

**When sending parallel Claude agents in one message:** you are using a choreography-adjacent pattern. This is appropriate only for tasks with no dependencies between them. For dependent tasks, use sequencing (wave structure) or GSD.

**When reading about LangGraph, CrewAI, or AutoGen:** the same vocabulary applies. Different tools, same patterns. An "agent graph" in LangGraph is a DAG. A "crew" in CrewAI is an orchestrator-worker system. The concepts are universal; the APIs differ.

**When debugging a failed execute-phase:** work through the observability framework.
1. Which span (agent task) failed? (STATE.md — which task is missing?)
2. What did it produce? (git log — is there a commit?)
3. What state did it leave? (go build, go test)
4. Did failure propagate? (did subsequent waves build on failed output?)

---

## The GSD workflow as a concrete orchestrator-worker system

End-to-end flow with terminology:

```
You (human-in-the-loop)
    │
    ▼
/gsd:discuss-phase         ← context gathering (orchestrator builds task graph input)
    │
    ▼  [HITL Gate 1: CONTEXT.md approval]
    │
/gsd:plan-phase            ← DAG construction (orchestrator builds PLAN.md)
    │
    ▼  [HITL Gate 2: PLAN.md approval]
    │
/gsd:execute-phase         ← fan-out wave 1 (orchestrator spawns N workers in parallel)
    │
    │  Wave 1: fan-in (orchestrator waits, reads STATE.md)
    │
    │  Wave 2: fan-out (dependencies resolved, next wave starts)
    │  Wave 2: fan-in
    │  ... (repeat for each wave)
    │
    ▼
/gsd:verify-work           ← trust-but-verify (orchestrator validates output against SPEC)
    │
    ▼  [HITL Gate 3: verification approval]
    │
/gsd:ship                  ← audit trail finalized, PR created
```

Every step in this flow has a name from the vocabulary in this module. None of it is magic. It is a specific implementation of well-understood multi-agent coordination patterns.

---

## What GSD does NOT do (and why)

| Pattern | GSD decision | Reason |
|---------|-------------|--------|
| Choreography for dependent tasks | Not used | Dependencies require orchestration; GSD always uses waves |
| Automatic push to remote | Not done | Push is outside the trust boundary; requires explicit human action |
| Infinite retry on failure | Not done | Logic failures need human diagnosis, not more retries |
| Skip HITL gates for speed | Not done | Gates are the governance mechanism; skipping them trades safety for convenience |
| Full parallel execution of all tasks | Not done | Most tasks have dependencies; full parallel would produce wrong output |

Understanding what GSD doesn't do and why prevents the temptation to bypass these constraints "just this once."

---

## Cross-tool vocabulary: GSD concepts in other frameworks

When you read about other multi-agent frameworks, the same concepts appear under different names. The implementation differs; the patterns are the same.

| GSD concept | LangGraph equivalent | CrewAI equivalent | AutoGen equivalent |
|-------------|---------------------|------------------|--------------------|
| execute-phase orchestrator | StateGraph with supervisor node | Crew manager | GroupChat manager |
| Executor agent | ToolNode / agent node | CrewAI agent | ConversableAgent |
| PLAN.md wave structure | Conditional edges (DAG) | Task dependencies | GroupChat order |
| STATE.md | State dict | Shared memory | Chat history |
| HITL gate | human-in-the-loop node | Human input step | Human proxy agent |
| --gaps-only retry | Resume from checkpoint | Re-run failed tasks | Selective re-run |
| Fan-out | Parallel nodes | Parallel tasks | Broadcast message |
| Fan-in | Aggregation node | Task completion wait | Reply collection |

The takeaway: learning GSD well means learning multi-agent orchestration well. The concepts transfer. The vocabulary is the same. Only the API calls differ.

---

## How to read GSD output with this vocabulary

When `/gsd:execute-phase` runs and you see output like:

```
Wave 1: spawning 2 executor agents
  - task 01-01-A: define Store interface
  - task 01-01-E: update CLAUDE.md
Wave 1: complete (2/2 tasks)

Wave 2: spawning 1 executor agent
  - task 01-01-B: implement GetAll
Wave 2: complete (1/1 tasks)
```

You can now read this as: fan-out wave 1 (2 tasks, no dependencies, parallel), fan-in wave 1 (all complete), fan-out wave 2 (1 task, depends on wave 1), fan-in wave 2.

The orchestrator (GSD execute-phase) is managing the DAG traversal level by level. The executor agents are the workers. STATE.md is the shared state. Your approvals at CONTEXT.md and PLAN.md were the HITL gates.

When something fails:
```
Wave 3: spawning 1 executor agent
  - task 01-01-C: implement GetTasks handler
Wave 3: FAILED — task 01-01-C did not commit
```

Translation: worker for task C failed (no git commit = no span completion). Orchestrator detected the failure via shared state (git and STATE.md). Human-in-the-loop required — the orchestrator cannot auto-retry a logic failure. You diagnose, fix the context, and re-run task C.

---

## Checklist

- [ ] I can explain every row in the mapping table without looking.
- [ ] I know which GSD component corresponds to the orchestrator, worker, fan-out, fan-in, DAG, HITL gate, audit trail, and trust-but-verify.
- [ ] I can map a execute-phase failure to the right observability tool (STATE.md, git log, go test).
- [ ] I know why GSD uses orchestration (not choreography) for phase execution.
- [ ] I understand that the GSD workflow is an implementation of universal multi-agent patterns — not GSD-specific magic.
- [ ] I can explain the full GSD workflow using orchestrator-worker vocabulary.
