# What you will build

## This track and the Claude product stack

This path teaches **[Claude Code](https://claude.com/)** — Anthropic's terminal agent for coding — in the same product family as Claude chat, **Cowork**, and the **Opus / Sonnet / Haiku** model line.

| Surface | What it is | Role in this track |
|---------|------------|-------------------|
| **Claude Code** | CLI agent: tools, `/plan`, permissions, hooks | Primary tool — every lab |
| **`CLAUDE.md` + `.claude/`** | Project memory, rules, skills, agents, `settings.json` | Configured in modules 01 and 04 |
| **`/memory`** | Durable preferences (not acceptance criteria) | Module 01 — separate from `docs/` |
| **Skills** | Reusable workflows under `.claude/skills/` | Module 04 — same idea as [Skills on claude.com](https://claude.com/) |
| **MCP (connectors)** | External tools via Model Context Protocol | Modules 01 and 04 — Anthropic's integration model |
| **Models** | Opus (hardest), Sonnet (default work), Haiku (narrow) | Module 18 — tier names are stable; IDs change — verify in `/config` |
| **Cowork** | Chat-adjacent workspace for non-terminal work | Out of scope here; same account, different surface |

Official references when a detail moves: [claude.com](https://claude.com/) (product map), Anthropic **developer docs** and Claude Code release notes (commands, paths, model IDs).

---

## Three layers — native Claude vs repo discipline

**Claude Code** supplies product surfaces; **`docs/`** in your repo holds verifiable specs, plans, and checkpoints when you use the full track.

| Layer | What it is | Where it lives |
|-------|------------|----------------|
| **A — Anthropic surfaces** | What [Claude Code](https://claude.com/) provides: CLI, `CLAUDE.md`, `.claude/` (rules, skills, agents, hooks), `/plan`, `/memory`, permissions, MCP, model tiers | Product config + slash commands |
| **B — Session and agent craft** | How you run sessions: context ownership, layering, compression, orchestration, reliability, cost, rule conflicts | Modules + habits; still Claude-native vocabulary |
| **C — Repo engineering discipline** | Verifiable contracts in git: `docs/specs/`, `docs/plans/`, `docs/state.md`, REQ traceability, graduation capstone | Your repo — *on top of* Layer A, not instead of it |

**Rule of thumb:** preferences and stack facts → **A** (`CLAUDE.md`, `/memory`). How you steer a long session → **B**. What must be true for a merge → **C** (`docs/`, tests, PR evidence).

See `00-orientation/02-artifacts-on-disk.md` for the Layer C file layout and the frame → plan → execute → verify → merge chain.

### Minimum path — Layers A + B only

Claude Code without the full `docs/` layout:

| Module | Focus |
|--------|--------|
| 00 | Product stack + this layer map |
| 01 | Slash commands, memory, permissions, MCP intro |
| 02 | Sessions, `/plan`, context, iteration, **prompt repair**, **large-repo navigation** |
| 03 | Instruction hierarchy, layering, **retrieval and grounding** |
| 04 | `CLAUDE.md`, rules, skills, `settings.json` |
| 05 | Agents, orchestration, HITL, trust, **human authority** |
| 09 | Sandbox, permissions, safe execution |
| 10 | Secrets and AI-tool security |
| 13 | Failure taxonomy, recovery, retry bounds |
| 15 | `/compact`, checkpoints (manual packets — not full `docs/state.md` program) |
| 16 | Rule conflicts |
| 17 | Token budgets + **practical token ownership** |
| 18 | Model tiers |

**Layer C modules:** 06, 07, 08, 11, 12, 14. **Diff review before merge:** `12-diff-refactor/03-diff-review-discipline.md`. **Edit scope:** `12-diff-refactor/04-idempotent-refactoring-discipline.md`.

### Full track — Layers A + B + C

Modules **06–08** and **11–12**, **14** add specification-first development, executable verification, graduation, tests, refactors, and multi-SPEC partitioning. That is the full **Layer C** path for verifiable, multi-file work with Claude — adapted for cold sessions and `/compact`.

### Out of scope — other programs in this vault

Not part of this track:

| Topic | Where to train (examples in this repo) |
|-------|--------------------------------------|
| Go concurrency, races, workers, cancellation | `paths/Go/03-go-concurrency-and-queue-workers/` |
| Profiling (CPU, heap, latency) | `paths/Go/16-performance-profiling-and-perf-lab/` |
| Production observability, tracing, containers | `paths/Go/17-production-go-observability-and-containers/` |
| Kubernetes, Terraform, rollouts, incidents | `paths/Ops/` (e.g. `10-terraform-infrastructure-lifecycle/`, `15-distributed-tracing-with-opentelemetry/`, `21-incident-troubleshooting-scenario-labs/`) |
| Database production (migrations, locking, plans) | `paths/MySQL-Database-Engineering/` |
| Distributed systems patterns (retries, queues, consistency) | `paths/Go/`, `paths/Architect/`, `paths/Ops/` as applicable |

---

## Outcomes — measurable, not aspirational

After completing this track you can:

**Layers A + B**

- Configure Claude Code for a project: `CLAUDE.md`, `settings.json`, permissions, at least one hook.
- Use `/plan` mode deliberately, not by accident.
- Manage context: `/compact`, layering, and when to start a fresh session.
- Run bounded agent work with orchestration, permissions, and trust-but-verify habits.
- Ground outputs in files and SPEC — not chat memory (`06-retrieval-and-grounding.md`).
- Classify failures and repair prompts with minimal patches (`03-claude-failure-taxonomy.md`, `07-prompt-repair-discipline.md`).
- Review every diff before commit (`12-diff-refactor/03-diff-review-discipline.md`).

**Layer C (full track)**

- Run a complete workflow loop (frame → plan → execute → verify → merge) on a real project without referencing documentation mid-loop.
- Write a feature SPEC under `docs/specs/` that constrains implementation scope before any code is written.
- Interpret and repair a broken `docs/state.md` when a session goes sideways.
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
  CLAUDE.md             # project brain — stack, commands, constraints (loads every session)
  .claude/
    settings.json       # permissions, hooks
    agents/
      code-reviewer.md  # read-only reviewer subagent
  .claudeignore         # files Claude must not read
  docs/
    project.md          # vision, stack, non-goals (optional if covered in CLAUDE.md)
    roadmap.md          # phase list + status
    state.md            # session checkpoint — update before you close
    requirements.md     # REQ-001 … REQ-00N
    specs/
      get-tasks.md      # feature SPEC (module 06 lab)
      complete-task.md  # feature SPEC (graduation)
    plans/
      02-get-tasks-context.md   # phase brief (you write)
      02-get-tasks-plan.md      # output of /plan
    decisions/
      model-assignments.md    # optional — module 18 lab
    checkpoints/
      phase1.md           # optional — module 15 lab
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

When you return to a topic in real work, come back to the relevant file as reference. Cross-references point to other units; each file avoids repeating full context from elsewhere.

---

## Module map

| Module | Layer | Directory | Delivers |
|--------|-------|-----------|---------|
| 00 | A | `00-orientation/` | Product stack, three layers, artifacts on disk |
| 01 | A | `01-claude-code-commands/` | Slash commands, agents, MCP, permissions, memory |
| 02 | B | `02-claude-code-workflow/` | Sessions, `/plan`, context, tokens, iteration, prompt repair, large-repo navigation |
| 03 | B | `03-prompt-layering-and-context/` | Instruction hierarchy, layering, context engineering, retrieval and grounding |
| 04 | A | `04-claude-code-configuration/` | `CLAUDE.md`, `settings.json`, MCP, rules, skills |
| 05 | A/B | `05-agent-orchestration-and-governance/` | Orchestration, HITL, human authority, DAG, trust, observability |
| 06 | C | `06-specification-first/` | SPEC template, acceptance, NFR, boundaries, drift repair |
| 07 | C | `07-spec-runtime/` | Executable specs, drift detection, audit |
| 08 | C | `08-graduation-project/` | End-to-end capstone (Phases 2 and 3) |
| 09 | A | `09-sandbox-safe-execution/` | Worktree, Docker sandbox, secret isolation, permissions |
| 10 | A | `10-security-and-secrets/` | Secrets lifecycle, git security, AI-tool security |
| 11 | C | `11-test-engineering/` | Spec-backed testing, regression, triage |
| 12 | B/C | `12-diff-refactor/` | Diff review; safe refactor sequencing; idempotent edit discipline |
| 13 | B | `13-agent-reliability/` | Failure taxonomy, recovery, retry bounds |
| 14 | C | `14-spec-partitioning/` | Multi-SPEC ownership, dependency graph |
| 15 | B | `15-context-compression/` | Protected zones, checkpoint packets, `/compact` |
| 16 | B | `16-rule-conflicts/` | Priority ladder, `RULE_PRIORITY.md`, exceptions |
| 17 | B | `17-cost-engineering/` | Token vs context budgets, practical ownership, parallelization cost |
| 18 | A | `18-model-selection/` | Opus / Sonnet / Haiku, assignments |

**Reading order by layer**

- **A + B core:** 00 → 01 → 02 (through `08-large-repo-navigation`) → 03 (through `06-retrieval-and-grounding`) → 04 → 05 (through `09-human-authority-and-override`) → 09 → 10 → 13 (through `03-claude-failure-taxonomy`) → 15 → 16 → 17 (through `03-practical-token-ownership`) → 18. Before regular merges: **`12/03-diff-review-discipline`**, **`12/04-idempotent-refactoring-discipline`**.
- **C (after 04, before or after 05):** 06 → 07 — then **08** graduation. **11**, **12**, **14** after graduation or in parallel with real project work.

Module 05 references wave structure in `docs/plans/*-plan.md`; you can read it after 04 even if you defer 06–08 — use a single ad-hoc plan file until you adopt full `docs/`.

---

## Before you start

You need:

- Claude Code installed: `npm install -g @anthropic-ai/claude-code` (or verify with `claude --version`)
- Go installed: `go version` should show 1.21+
- Git initialized in your working directory

If any of these fail, fix them before module 01. The labs assume all three are present.

---

## Checklist

- [ ] Claude Code installed and `claude --version` returns a version string.
- [ ] Go 1.21+ installed and `go version` confirms.
- [ ] I understand that the toy project (task-api) uses in-memory storage — no database to set up.
- [ ] I understand that task-api builds across all modules — do not skip labs.
- [ ] I understand that labs are not optional — they produce the artifact.
- [ ] I know which files under `docs/` and `CLAUDE.md` hold project state (at least at the file-name level).
- [ ] I can name the five workflow steps: frame → plan → execute → verify → merge.
