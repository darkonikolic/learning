# Context propagation

Context propagation is how state and information pass between agents in a multi-agent system. Get it wrong and agents operate on stale information, duplicate work, or make conflicting decisions. Get it right and each agent has exactly what it needs, nothing more.

---

## Three propagation patterns

**Pattern 1: Message passing**

The orchestrator explicitly includes the task and all relevant context in the agent's prompt. Each agent receives a self-contained message.

```
Agent prompt: "Implement GetAll on the Store interface defined in internal/store/store.go.
Context: the Task struct is defined in internal/domain/task.go.
Your output: GetAll method on *MemoryStore, return []Task.
Stop condition: stop after GetAll — do not add other methods."
```

The agent does not need to read other agents' prompts or understand the broader workflow. It has everything it needs.

Pros: agent gets exactly what it needs. Context is isolated — no irrelevant information. Easy to debug — the context is explicit in the prompt.

Cons: the orchestrator must know exactly what each agent needs. As tasks grow complex, crafting accurate context becomes the bottleneck.

Use when: most single-agent Claude interactions. The orchestrator (you) assembles context from SPEC, PLAN.md, and relevant source files before writing the agent prompt.

**Pattern 2: Shared state**

Agents read from and write to a shared state store. One agent writes its result; the next agent reads it and adds its result.

In GSD: STATE.md, REQUIREMENTS.md, ROADMAP.md, and the source code files themselves are shared state.

```
Wave 1 agent writes: internal/store/store.go (the implementation)
Wave 2 agent reads: internal/store/store.go (uses it as context to write handler)
STATE.md updated by wave 1: wave 2 orchestrator reads STATE.md to know wave 1 succeeded
```

Pros: agents don't need the orchestrator to hand them all context explicitly. They read current state directly.

Cons: write conflicts if two agents write to the same file simultaneously. Agent must know where to find state, not just what its task is.

Use when: GSD wave execution — agents read files written by prior waves. Shared documents (PLAN.md, SPEC files) that multiple agents reference.

**Pattern 3: Event-driven**

Agents emit events; other agents subscribe to and react to events. No direct communication between agents.

This pattern is not natively implemented in Claude Code, but can be simulated with file-based events: agent A writes a file; agent B checks for that file's existence as its start condition.

Not covered in depth here — event-driven multi-agent systems are an advanced pattern beyond the scope of this module.

---

## Context isolation

Each subagent should receive only what it needs for its task. Not the full parent context.

**Why not the full context:**
- Token cost: parent context is expensive. Passing 10,000 tokens of conversation history to every subagent multiplies that cost.
- Noise: parent context contains decisions, alternatives considered, and discussion. Most of it is irrelevant to the subagent's specific task.
- Dependency: a subagent that understands the full parent context may make decisions that should be the orchestrator's responsibility.

**What to include in a subagent context:**
- The specific task
- The relevant file contents (not the full codebase)
- The constraints that apply to this task
- The expected output format
- The stop condition

**What to exclude:**
- Full conversation history
- Files unrelated to this task
- Parent session state ("we've been working on this for 3 hours")
- Context from other agents' tasks (unless this task depends on it)

---

## Passing context to a Claude agent: practical guide

**Minimal effective context for an executor agent:**

```
Task: Implement the GetAll method on *MemoryStore.

Interface contract (from internal/store/store.go):
  type Store interface {
    GetAll(ctx context.Context) ([]Task, error)
    AddTask(ctx context.Context, title, description string) (Task, error)
  }

Current implementation (read internal/store/store.go):
  type MemoryStore struct {
    mu    sync.RWMutex
    tasks []Task
  }
  // AddTask is already implemented.
  // GetAll is not yet implemented.

Constraints:
  - Use mu.RLock() / mu.RUnlock() for GetAll (read operation).
  - Return a copy of the tasks slice, not a direct reference.
  - Never return nil — return empty slice if no tasks.

Output: the GetAll method only. No other changes to the file.
Stop: after GetAll is written. Do not add other methods or modify existing code.
```

This context is approximately 200 tokens. It is complete. The agent can implement GetAll correctly without reading anything else.

**What this context includes:**
- The interface (what GetAll must satisfy)
- The current struct (what state is available)
- The constraints (how to implement correctly)
- The stop condition (what "done" means)

**What it excludes:**
- The full store.go file with other methods
- The handler that will call GetAll
- Test files
- Any other file in the project

---

## Context propagation in GSD execute-phase

GSD execute-phase uses message passing + shared state together.

**Message passing:** each executor agent receives a slice of PLAN.md (its task) + the relevant portions of CONTEXT.md. The orchestrator assembles this per-agent context before spawning each agent.

**Shared state:** CONTEXT.md, SPEC files, and source code files are shared. Wave 2 agents read files written by wave 1 agents. STATE.md is updated after each task completes, so the orchestrator knows the current state before spawning the next wave.

**Wave isolation:** wave 2 agents do not start until wave 1 STATE.md updates are written and read by the orchestrator. This prevents wave 2 agents from reading stale state (pre-wave-1) or conflicting state (mid-wave-1).

The boundary between message passing and shared state:
- Task-specific context (what this agent specifically needs to do): message passing.
- Project-wide context (SPEC, architecture decisions, prior agent outputs): shared state via files.

---

## Common context propagation failures

**Stale state:** agent reads a file that another agent is currently writing. Result: agent acts on partial data.

Fix: wave isolation. Wave 2 does not start until wave 1 is confirmed complete.

**Context overflow:** agent receives too much context and key information is crowded out.

Fix: context isolation. Pass only what the agent needs. If the agent needs 20 files, reconsider the task decomposition — the task may be too large.

**Missing prior decision:** agent makes a decision already made by an earlier agent, creating an inconsistency.

Fix: explicitly include relevant prior decisions in message-passing context. Don't rely on agents reading each other's work to pick up implicit decisions.

**Write conflict:** two parallel agents write to the same file.

Fix: ensure parallel agents (within a wave) write to different files. If two agents must write to the same file, they cannot be in the same wave — one must depend on the other.

---

## Checklist

- [ ] I can name the three context propagation patterns: message passing, shared state, event-driven.
- [ ] I know which GSD components are shared state: STATE.md, REQUIREMENTS.md, source files.
- [ ] I know what to include in a subagent prompt: task, interface, constraints, stop condition.
- [ ] I know what to exclude from a subagent prompt: full history, unrelated files, parent session state.
- [ ] I can explain why wave isolation prevents stale state reads.
- [ ] I can identify if two parallel tasks have a write conflict before assigning them to the same wave.
