# What you will build

## Outcomes — measurable, not aspirational

After completing this track you can:

- Run a complete GSD loop (discuss → plan → execute → verify → ship) on a real project without referencing documentation mid-loop.
- Write a SPEC.md that constrains implementation scope before any code is written.
- Configure Claude Code for a project: CLAUDE.md, settings.json, permissions, at least one hook.
- Use /plan mode deliberately, not by accident.
- Interpret and repair a broken STATE.md when a session goes sideways.
- Create a PR from verified, artifact-backed work.

These are binary. Either you can do them on an unfamiliar codebase by end of track, or you cannot.

---

## The toy project — task-api

One project threads through every module. You build it incrementally. It is not a tutorial — it is a vehicle for practicing every tool and workflow concept in a real codebase.

**Stack:** Go, stdlib `net/http`, no frameworks, no database. Storage is in-memory for the entire track.

**Endpoints:**

| Method | Path | Behavior |
|--------|------|----------|
| POST | /tasks | Create task; body `{"title": string}`; returns 201 + task with UUID |
| GET | /tasks | List all tasks; returns 200 + array |
| PATCH | /tasks/:id/complete | Mark task complete; returns 200 or 404 |

**Why this project:**
- Small enough to hold in your head.
- Real enough to require error handling, input validation, and tests.
- Has obvious scope risks (pagination? auth? soft-delete?) — good for spec practice.
- Multi-file Go structure means Claude can do real work, not toy edits.
- No database means zero infrastructure setup — the only dependency is Go itself.

---

## What "done" looks like

At end of track, your `task-api/` directory contains:

```
task-api/
  .planning/
    PROJECT.md          # vision, stack, constraints
    ROADMAP.md          # phase list with status
    STATE.md            # last known workflow state
    config.json         # GSD configuration
    milestones/
      v0.1/
        SPEC.md         # what the API does, what it does not
        PLAN.md         # executable task list with verification steps
        REQUIREMENTS.md # REQ-001 through REQ-00N
        SECURITY.md     # /gsd:secure-phase output
  .claude/
    settings.json       # permissions, hooks
    agents/
      code-reviewer.md  # read-only reviewer subagent
  .claudeignore         # files Claude must not read
  CLAUDE.md             # project instructions Claude loads at session start
  config/
    config.go           # reads PORT and LOG_LEVEL from environment
  main.go
  tasks/
    handler.go
    store.go
    store_test.go
  .env.example          # documents required env vars (committed)
  .gitleaks.toml        # secret scanning config (committed)
  go.mod
  go.sum
  PR description (in git log or docs/)
```

You produce this by doing the labs, not by reading the modules passively.

---

## How to use this track

**Read → do the lab → use as reference.**

Each module ends with a lab. The lab is not optional illustration — it is the point. Reading without doing produces familiarity, not capability.

When you return to a topic in real work, come back to the relevant file as reference. The files are dense by design. They do not repeat context from other modules — cross-references point forward and back explicitly.

**Time budget:** plan 20–40 minutes per module. Labs take longer than reading. Do not skip labs to finish faster — you will lose the capability the lab builds.

---

## Module map

| Module | Directory | Delivers |
|--------|-----------|---------|
| 00 | `00-orientation/` | Why GSD exists; why each artifact; mental model before tools |
| 01 | `01-claude-code-commands/` | All slash commands, agents, MCP, permissions, memory — full reference |
| 02 | `02-claude-code-workflow/` | Session ownership, plan-to-execute flow, context, tokens, iteration |
| 03 | `03-prompt-layering-and-context/` | Instruction hierarchy, layering in practice, context engineering |
| 04 | `04-claude-code-configuration/` | CLAUDE.md, settings.json, MCP config, rules, skills authoring |
| 05 | `05-gsd-commands/` | All GSD commands — full reference with flags and decision tables |
| 06 | `06-gsd-workflow/` | discuss→plan→execute→verify→ship; mid-flight changes; troubleshooting |
| 07 | `07-gsd-configuration/` | .planning/ layout, PROJECT.md, ROADMAP.md, STATE.md, config.json |
| 08 | `08-agent-orchestration-and-governance/` | Orchestration vs choreography, HITL, DAG, trust, observability — real terminology |
| 09 | `09-specification-first/` | SPEC template, acceptance criteria, NFR, boundaries, drift and repair |
| 10 | `10-spec-runtime/` | Executable specs, drift detection, audit procedure |
| 11 | `11-graduation-project/` | End-to-end: Phases 2 and 3 with full GSD loop |
| 12 | `12-sandbox-safe-execution/` | Worktree isolation, Docker sandbox, secret isolation, permissions |
| 13 | `13-security-and-secrets/` | Secrets lifecycle, what not to show Claude, git security, AI tool security |
| 14 | `14-test-engineering/` | Spec-backed testing, regression ownership, failure characterization, test triage |
| 15 | `15-diff-refactor/` | Refactor template, incremental sequencing, rollback discipline |
| 16 | `16-agent-reliability/` | Execute-phase failures, confidence scoring, hallucination recovery, retry bounds |
| 17 | `17-spec-partitioning/` | Splitting SPECs across ownership domains, dependency graph, cross-SPEC consistency |
| 18 | `18-context-compression/` | Context hierarchy, protected verbatim zones, checkpoint packets, /compact discipline |
| 19 | `19-rule-conflicts/` | Priority ladder, conflict resolution, RULE_PRIORITY.md, time-bounded exceptions |
| 20 | `20-cost-engineering/` | Token vs context budgets, cost per workflow stage, parallelization economics |
| 21 | `21-gsd-project-lifecycle/` | /gsd:new-project flow, milestone lifecycle, bootstrapping from scratch |
| 22 | `22-model-selection/` | Model tiers, decision rules, config.json model assignments |

**Reading order:** Modules 00–04 are Claude Code fundamentals. Modules 05–07 are GSD. Module 08 is agent orchestration and governance — read after modules 05–07 so PLAN.md wave structure is already familiar. Modules 09–10 are specification-driven development. Module 11 is graduation. Modules 12–13 are safety and security — read anytime after module 04. Modules 14–20 are operational depth — read after graduation when working on real projects. Module 21 covers GSD project lifecycle — read before starting any real project, after module 07. Module 22 covers model selection — read after module 07.

---

## Before you start

You need:

- Claude Code installed: `npm install -g @anthropic-ai/claude-code` (or verify with `claude --version`)
- Go installed: `go version` should show 1.21+
- Git initialized in your working directory
- GSD installed: `npx get-shit-done-cc@latest` — verify with `/gsd-help` inside a Claude Code session

If any of these fail, fix them before module 01. The labs assume all four are present.

---

## Checklist

- [ ] Claude Code installed and `claude --version` returns a version string.
- [ ] Go 1.21+ installed and `go version` confirms.
- [ ] GSD installed and `/gsd-help` works inside a Claude Code session.
- [ ] I understand that the toy project (task-api) uses in-memory storage — no database to set up.
- [ ] I understand that task-api builds across all modules — do not skip labs.
- [ ] I understand that labs are not optional — they produce the artifact.
- [ ] I have 20–40 minutes available to give each module proper attention.
- [ ] I know what a `.planning/` directory is meant to contain (at least at the file-name level).
- [ ] I can name the five GSD workflow steps: discuss → plan → execute → verify → ship.
