# Artifacts on disk — CLAUDE.md, memory, and docs/

Layer C: `docs/` on disk. Layer map: `01-what-you-will-build.md`.

## The core problem

AI context is ephemeral. Every Claude Code session starts cold. Chat scrollback dies on `/compact` or `/clear`. Auto-memory helps with preferences but cannot hold verifiable contracts.

**Claude-native persistence:**

| Layer | Location | Role |
|-------|----------|------|
| Project instructions | **`CLAUDE.md`** | Stack, build/test commands, hard constraints — loaded every session |
| Personal prefs | **`~/.claude/CLAUDE.md`** + **`/memory`** (auto-memory) | How you like to work — not acceptance criteria |
| Verifiable work | **`docs/`** | Specs, plans, requirements, checkpoint state — git-tracked |

Claude Code does **not** ship a mandatory planning folder in your repo. Anthropic gives you **`CLAUDE.md`**, **`.claude/`** (rules, skills, agents, permissions), **`/memory`**, and session tools like **`/plan`**. This track adds **`docs/`** as a git-tracked place for specs and checkpoints — a deliberate choice for verifiable work, aligned with how [Claude Code](https://claude.com/) expects durable context to live in files you control.

---

## The chain

```
vision (docs/project.md and/or CLAUDE.md)
  └─ phase intent (docs/roadmap.md + docs/plans/<phase>-context.md)
       └─ feature contract (docs/specs/<slug>.md)
            └─ executable tasks (docs/plans/<phase>-plan.md)
                 └─ verification (docs/requirements.md + acceptance checks)
                      └─ checkpoint (docs/state.md, PR)
```

---

## Why each artifact exists

### CLAUDE.md — what Claude must always know

Stable facts Claude cannot reliably infer: build commands, stdlib-only rule, directory layout, naming. Under ~200 lines. Details live in `.claude/rules/` when path-scoped.

### docs/project.md — vision (optional if CLAUDE.md is enough)

Longer vision, measurable goals, explicit non-goals. Load at session start when the project is larger than task-api.

### docs/roadmap.md — phases as contracts

Bounded phases with status. New scope mid-phase → backlog entry, not silent creep.

### docs/state.md — honest session checkpoint

What finished, what blocked, next action. Update before closing a session. Not a progress report for stakeholders — a handoff for you and Claude.

### docs/plans/<phase>-context.md — frame brief

Human-written: goal, files, out-of-scope, constraints. Written before `/plan`.

### docs/plans/<phase>-plan.md — output of `/plan`

Concrete tasks, dependencies, verification hooks. You edit before execute.

### docs/specs/<slug>.md — feature contracts

Binary acceptance criteria, constraints, rollback. Source of truth for implementation and verification.

### docs/requirements.md — REQ-IDs

Traceability: SPEC → REQ → PLAN task → commit.

---

## docs/ layout (task-api)

```
docs/
  project.md
  roadmap.md
  state.md
  requirements.md
  specs/
  plans/
  decisions/
  checkpoints/
```

Feature SPECs stay in **`docs/specs/`** only.

---

## Memory vs files — do not confuse them

| Use memory (`CLAUDE.md`, `/memory`) | Use files (`docs/specs/`, `docs/plans/`) |
|-------------------------------------|----------------------------------------|
| "Prefer short replies" | "GET /tasks returns [] when empty" |
| "Always run tests before commit" | REQ-002 acceptance criteria |
| Stack and conventions | PLAN task 4 depends on task 3 |

**Rule:** if verification depends on it, it lives in **`docs/`**, not in auto-memory.

See module **01** `05-memory-and-persistence.md` for the full five-layer table.

---

## Native workflow

| Step | Artifact |
|------|----------|
| Frame | `docs/plans/<phase>-context.md` + existing `docs/specs/` |
| Plan | `/plan` → `docs/plans/<phase>-plan.md` |
| Execute | bounded messages against approved plan |
| Verify | SPEC acceptance + `docs/state.md` |
| Merge | PR after `/code-review` |

---

## Checklist

- [ ] I know **`CLAUDE.md`** and **`.claude/`** are Anthropic's project surfaces; **`docs/`** is my verifiable contract layer.
- [ ] I know feature SPECs live in **`docs/specs/`** and plans in **`docs/plans/`**.
- [ ] I will update **`docs/state.md`** before ending a session.
- [ ] I will not put acceptance criteria only in chat or auto-memory.
