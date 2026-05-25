# Prompt Engineering — practical path

## What this is

Six modules covering the skills that determine whether AI-assisted development produces usable output or wasted work. Every file solves a concrete problem. No theory.

Works with Claude Code and Cursor — tool-specific notes are labeled [Claude] and [Cursor] where syntax differs.

---

## What you will be able to do

- Write constraints that AI actually follows (not suggestions it ignores)
- Construct context that produces correct output on the first turn
- Apply the right prompt pattern for each task type: feature, bug, refactor, architecture, review
- Detect and recover from the four failure modes before they compound
- Configure workspace files that carry constraints across sessions
- Evaluate output against binary criteria before accepting it

---

## Module map

| Module | Directory | Problem it solves |
|--------|-----------|-------------------|
| 01 | `01-constraint-and-scope/` | AI does too much, too little, or the wrong thing |
| 02 | `02-context-construction/` | Output is wrong because context was wrong |
| 03 | `03-task-patterns/` | Same task produces inconsistent results |
| 04 | `04-failure-patterns/` | Output is wrong and you don't know why or what to do |
| 05 | `05-workspace-configuration/` | Rules and constraints reset every session |
| 06 | `06-output-evaluation/` | You can't tell if output is good until it breaks |

**Reading order:** 01 → 02 → 05 → 03 → 04 → 06.
- Start with 01 and 02: these are the foundation — constraints and context determine everything else.
- Read 05 early: workspace configuration makes 01 and 02 durable across sessions.
- Read 03 when you need patterns for a specific task type — use it as reference.
- Read 04 when something goes wrong — use it as a diagnostic.
- Read 06 last: output evaluation makes no sense until you have criteria to evaluate against.

---

## How to use this path

Each module ends with a lab. The lab applies the module's concepts to a real task. Do the labs — reading without doing produces familiarity, not skill.

Use the non-lab files as reference. When a prompt fails, come back to module 04. When you're configuring a new project, come back to module 05. The files are dense by design.

---

## What this path does not cover

- Claude Code GSD workflow (discuss → plan → execute → verify → ship) → see Claude-Fast-Track path
- Specification-driven development → see Claude-Fast-Track path
- Agent orchestration, parallel agents → see Claude-Fast-Track path modules 05 and 16
