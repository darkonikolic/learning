# GSD — why the artifacts exist

## The core problem

AI context is ephemeral. Every Claude Code session starts with no memory of last session's decisions. Human intent drifts — the "task manager API" you described Monday becomes something else by Thursday. Implementation scope explodes — once code starts, new requirements emerge and get folded in silently.

GSD solves three distinct failure modes:

| Failure mode | Symptom | GSD response |
|---|---|---|
| Context loss | Claude asks the same questions every session | PROJECT.md + STATE.md loaded at start |
| Intent drift | Feature shipped ≠ feature specified | SPEC.md written before planning starts |
| Scope explosion | "Just one more thing" until the phase never closes | PLAN.md tasks are bounded and checkable |

Without GSD, you are managing these failures manually through ritual repetition. With GSD, the artifacts carry the state.

---

## The chain

```
vision (PROJECT.md)
  └─ phase intent (ROADMAP.md + CONTEXT.md)
       └─ executable tasks (PLAN.md)
            └─ verification criteria (REQUIREMENTS.md + UAT)
                 └─ verified outcome (STATE.md, PR)
```

Each layer is a handoff point. If any link breaks — vision undocumented, phase intent unclear, tasks vague — the chain propagates errors downstream and nothing is recoverable without backtracking.

---

## Why each artifact exists

### PROJECT.md — single source of vision truth

**Why it exists:** so every session starts aligned.

Without PROJECT.md, you re-explain the project in every session prompt. Each re-explanation introduces variation. Within three sessions, Claude is solving subtly different problems and you cannot tell when the drift happened.

PROJECT.md is not documentation. It is the instruction set Claude reads before doing anything. It defines: what the project is, what it is not, the stack, the constraints, the current milestone.

**One test:** if you can open a fresh Claude Code session, say "read PROJECT.md and summarize the project constraints", and get back accurate constraints — PROJECT.md is working.

### ROADMAP.md — phases as contracts, not todo lists

**Why it exists:** to make phases bounded and status-trackable.

A todo list has no definition of done. A phase in ROADMAP.md has a name, acceptance criteria, and status. When a phase is `complete`, that means something specific — criteria were checked, not just work was done.

Phases also prevent scope explosion. If a new requirement emerges mid-phase, it goes on the backlog as a future phase entry, not into the current phase silently.

### STATE.md — honest session memory

**Why it exists:** so the next session knows where the previous one stopped, including failures.

STATE.md is not a progress report. It is a checkpoint. It should be honest about what was completed, what was blocked, and what the next action is. An optimistic STATE.md ("all good, ready to ship") that hides a half-implemented feature is worse than no STATE.md.

**Read STATE.md at the start of a session. Update it before ending a session.** This is the discipline, not the format.

### CONTEXT.md — bounded intent before planning

**Why it exists:** to scope what discuss-phase is solving before plan-phase starts.

CONTEXT.md is the human-editable brief that goes into discuss-phase. It answers: what are we building in this phase? What constraints apply? What is explicitly out of scope? Without this, discuss-phase becomes unbounded — Claude asks questions that range into irrelevant territory, and planning starts on a foggy foundation.

CONTEXT.md is written by you, not generated. It takes 10–15 minutes. Those 15 minutes prevent hours of plan drift.

### PLAN.md — executable tasks with dependencies

**Why it exists:** to give execute-phase discrete, checkable units of work.

Prose plans ("implement the task handler") cannot be executed atomically or verified. PLAN.md tasks are concrete: "Create `tasks/store.go` with `CreateTask(title string) (Task, error)` — returns new task with UUID and `created_at` timestamp." That task can be executed, checked, and marked done.

PLAN.md tasks also encode dependencies. Task 3 cannot start until task 2 is verified. This prevents Claude from building on an unstable foundation during execute-phase.

### REQUIREMENTS.md — REQ-IDs as traceability anchors

**Why it exists:** so implementation decisions can be traced back to intent.

REQ-001 is a contract. When a PLAN.md task says "satisfies REQ-001, REQ-004", and verification says "REQ-001 PASS, REQ-004 FAIL", you know exactly what broke and where. Without IDs, requirements become prose that gets interpreted differently at every stage.

REQ-IDs also survive scope negotiation. When a stakeholder asks "why did we implement it this way?", the chain SPEC → REQ-ID → PLAN task → commit provides the answer.

---

## The .planning/ directory

All GSD artifacts live in `.planning/` at the project root. The full layout is covered in module 07. At orientation, the structure to know:

```
.planning/
  PROJECT.md          # vision, stack, constraints — load every session
  ROADMAP.md          # all phases, statuses, backlog
  STATE.md            # current workflow state — updated every session
  config.json         # GSD settings for this project
  milestones/
    v0.1/             # one directory per milestone
      SPEC.md
      PLAN.md
      REQUIREMENTS.md
```

Module 07 covers every field in every artifact. At this stage, understand that `.planning/` is not documentation — it is the runtime state of the project.

---

## Mindset table

| Old way | GSD way |
|---|---|
| Re-explain context every session | Session starts from PROJECT.md |
| "Done" = code written | "Done" = requirements verified |
| Requirements in my head | Requirements in REQUIREMENTS.md with IDs |
| Planning in the chat thread | Planning in PLAN.md on disk |
| Scope grows silently mid-phase | New scope = new phase entry in ROADMAP.md |
| Failures discovered at the end | STATE.md updated honestly after each session |
| One giant prompt for everything | Discuss → plan → execute as separate steps |
| Verification = "looks good" | Verification = each REQ-ID checked pass/fail |

---

## What breaks without GSD

**Scenario 1 — context loss:** You spend 30 minutes re-establishing context at the start of every session. Week 3, you are working from a slightly different mental model than week 1. The mismatch surfaces as a confusing bug that takes two sessions to trace.

**Scenario 2 — intent drift:** You describe the task manager API verbally in session 1. Session 4, without a written spec, Claude implements soft-delete because it seemed reasonable. You did not want soft-delete. The feature is shipped. Rolling it back takes longer than implementing it correctly the first time.

**Scenario 3 — unverifiable done:** Execute-phase completes. Claude says everything is done. You have no requirements document. Two weeks later, a tester finds that PATCH /tasks/:id/complete returns 200 even for non-existent IDs. There is no REQ-ID for the 404 behavior because no one wrote it down. The fix is a patch — it should have been a requirement.

---

## Where to go next from orientation

After reading both orientation files, follow the module sequence:

**Claude Code fundamentals (modules 01–04):** start here. These modules cover the tools you will use throughout every other module. Module 01 is the command reference; module 02 covers session workflow; modules 03–04 cover configuration and context engineering.

**GSD workflow (modules 05–07):** the core of the track. Module 05 is the command reference. Module 06 is the workflow in practice. Module 07 is configuration and artifact layout.

**Governance concepts (module 08):** read after GSD modules 05–07. Module 08 is agent orchestration, trust, DAG design, and observability. It makes more sense once you have seen PLAN.md wave structure in modules 05–07.

**Specification-driven development (modules 09–10):** read these before you write your first SPEC for task-api.

**Graduation (module 11):** the end-to-end project. Bring everything together.

**Safety and security (modules 12–13):** these can be read anytime after module 04. Module 12 covers sandbox and execution safety. Module 13 covers secrets lifecycle, what not to show Claude, git security, and AI tool security. Read them before you add any real credentials to a project.

---

## Checklist

- [ ] I can name the six core GSD artifacts and state why each exists in one sentence.
- [ ] I understand that STATE.md is an honest checkpoint, not a progress report.
- [ ] I understand that PLAN.md tasks must be concrete and independently verifiable.
- [ ] I understand that REQUIREMENTS.md REQ-IDs create traceability from spec to verification.
- [ ] I can explain the three failure modes GSD addresses (context loss, intent drift, scope explosion).
- [ ] I understand that CONTEXT.md is written by the human, not generated by Claude.
- [ ] I know the artifact chain: vision → phase intent → executable tasks → verified outcome.
- [ ] I understand that scope that appears mid-phase goes into ROADMAP.md backlog, not into the current phase.
- [ ] I know where the .planning/ directory lives and what its top-level files are.
- [ ] I know the reading order: fundamentals (01–04), GSD (05–07), governance (08), spec (09–10), graduation (11), safety (12–13).
