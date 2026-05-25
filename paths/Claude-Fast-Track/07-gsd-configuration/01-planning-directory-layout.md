# The .planning/ directory layout

GSD writes all project memory to disk. Nothing important lives only in chat. After `/gsd:new-project`, a `.planning/` tree is created automatically. Every file has a single job; understanding the layout is prerequisite to everything else.

**Connection to Module 08:** The wave structure you will see in PLAN.md is the direct implementation of the orchestration patterns covered in Module 08 (Agent Orchestration). Each wave is a parallel execution group — tasks within a wave have no dependencies on each other; tasks in later waves depend on earlier waves completing. When you read a PLAN.md file, you are reading an executable DAG.

---

## Annotated tree

```
.planning/
├── config.json              ← GSD toggles: model profile, agents, research, verifier
├── PROJECT.md               ← vision, stack, constraints, team, links — the north star
├── REQUIREMENTS.md          ← REQ-IDs with acceptance criteria and phase mapping
├── ROADMAP.md               ← ordered phase list with status and scope summary
├── STATE.md                 ← current workflow position, blockers, in-flight decisions
│
├── codebase/                ← output of /gsd:map-codebase (treat as read-only intel)
│   ├── ARCHITECTURE.md      ←   module structure, dependency graph, entry points
│   ├── TECH.md              ←   language, runtime, frameworks, build tooling
│   └── QUALITY.md           ←   test coverage, lint debt, known fragility zones
│
├── intel/                   ← ongoing project intelligence (research, ADRs, external refs)
│
├── phases/
│   ├── 01-task-endpoints/   ← one directory per phase, named XX-kebab-slug
│   │   ├── CONTEXT.md       ←   discuss-phase output: your goals, constraints, open Qs
│   │   ├── SPEC.md          ←   spec-phase output (optional): what the phase delivers
│   │   ├── 01-01-PLAN.md    ←   executable plan with tasks, waves, acceptance checks
│   │   ├── RESEARCH.md      ←   --research flag output: prior art, risk, alternatives
│   │   └── UAT.md           ←   verify-work output: acceptance evidence, pass/fail record
│   │
│   └── 02-auth/
│       ├── CONTEXT.md
│       ├── SPEC.md
│       └── 02-01-PLAN.md
│
└── graphs/                  ← knowledge graph from /gsd:graphify
```

---

## File-by-file reference

| File | Written by | You edit? | Staleness risk |
|------|-----------|-----------|----------------|
| `config.json` | `new-project` + `/gsd:config` | Via commands only | Low |
| `PROJECT.md` | `new-project` scaffold | Yes — fill in detail | Medium: update when stack changes |
| `REQUIREMENTS.md` | `new-project` scaffold + you | Yes — add REQ-IDs | High: mark status per execute |
| `ROADMAP.md` | GSD phase commands | No — use `/gsd:phase` | High if hand-edited |
| `STATE.md` | GSD workflow commands | Only to repair | Very high after bad execute |
| `codebase/*.md` | `/gsd:map-codebase` | No | Regen after major refactor |
| `phases/XX/CONTEXT.md` | `/gsd:discuss-phase` | Yes — clarify intent | Per-phase |
| `phases/XX/SPEC.md` | `/gsd:spec-phase` | Yes — approve/tighten | Drift risk if code diverges |
| `phases/XX/*-PLAN.md` | `/gsd:plan-phase` | Minor corrections only | Invalidated if SPEC changes |
| `phases/XX/UAT.md` | `/gsd:verify-work` | Add pass/fail evidence | Final record |

---

## Read order — navigating a project cold

When you return after days away, or hand the project to a teammate, read in this order:

1. `PROJECT.md` — what are we building, what are the hard constraints
2. `ROADMAP.md` — which phases exist, which are done
3. `STATE.md` — where did we stop, what is blocked, what decision was last made
4. Current phase `CONTEXT.md` — what goal did we set for this phase
5. Current phase `PLAN.md` — what tasks remain, which wave is active

This is exactly what `/gsd:resume-work` does automatically. If any file in this chain is stale, the resume will hallucinate progress.

---

## Write order — who creates what

GSD commands own most writes. Your contributions are:

```
You write:
  PROJECT.md (fill in vision, goals, non-goals after scaffold)
  REQUIREMENTS.md (add REQ-IDs before discuss-phase)
  phases/XX/CONTEXT.md (review and tighten after discuss-phase runs)
  phases/XX/SPEC.md (approve acceptance criteria before plan-phase)

GSD writes:
  config.json, STATE.md, ROADMAP.md phase status, PLAN.md, UAT.md, codebase/*
```

Never race GSD writes. If you hand-edit a file GSD owns, it may overwrite your changes on the next command run.

---

## Files you must not manually edit

| File | Why hands-off |
|------|--------------|
| `ROADMAP.md` phase status | Use `/gsd:progress` or phase transitions — manual edit breaks STATE sync |
| `STATE.md` arbitrarily | Only repair after a confirmed bad execute (see module 06) |
| `*-PLAN.md` wave frontmatter | Wave sequencing is computed — hand-edits corrupt parallelization |
| `codebase/*.md` | These are generated intel; edit the source code instead |

---

## Phase directory naming

Directories use a two-digit prefix aligned with ROADMAP order:

```
phases/
  01-task-endpoints/   ← first phase
  02-auth/             ← second phase
  03-rate-limiting/    ← third phase
```

Plans inside a phase add a second counter:

```
01-task-endpoints/
  01-01-PLAN.md    ← first plan in phase 01
  01-02-PLAN.md    ← second plan if phase is split
```

Do not rename directories after plans are written — PLAN.md files contain cross-references by path.

---

## The task-api example after /gsd:new-project

For the Go task manager threading through this course, the initial tree looks like:

```
task-api/.planning/
├── config.json
├── PROJECT.md          ← vision: "In-memory task manager REST API"
├── REQUIREMENTS.md     ← REQ-001, REQ-002, REQ-003 (you fill these)
├── ROADMAP.md          ← phase 01-task-endpoints: planned
└── STATE.md            ← phase: none, last step: project bootstrapped
```

The `codebase/` and `phases/` directories appear only after map-codebase and discuss-phase run respectively.

---

## .planning/ and version control

Commit `.planning/` to git. It is the project's memory. Every team member (and every Claude session) reads from it.

Two things to keep out of `.planning/`:
- API keys, secrets (use `.env` or secrets manager)
- Large binary attachments (use `intel/` sparingly, text only)

`.planning/` may contain architecture decisions that are sensitive — treat repo visibility accordingly.

---

## Checklist

- [ ] I can name all five root files in `.planning/` and their roles without looking
- [ ] I know which files GSD owns and which I maintain
- [ ] I know the read order for returning to a project cold
- [ ] I understand why ROADMAP.md phase status must not be hand-edited
- [ ] I know that STATE.md staleness causes /gsd:resume-work to hallucinate
- [ ] I can describe the XX-YY-PLAN.md naming convention
- [ ] I know what `/gsd:map-codebase` writes and where
