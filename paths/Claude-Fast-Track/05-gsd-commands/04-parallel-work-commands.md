# Parallel work commands

Two mechanisms for non-linear work: workstreams (parallel feature tracks inside one repo) and threads (persistent context that survives session resets). They solve different problems and are not interchangeable. A third mechanism — git worktrees — provides complete filesystem-level isolation for agent work.

---

## Workstreams

A workstream is a named parallel track inside a single repository. Each workstream has its own active phase, STATE.md context, and progress tracking. The underlying git workflow (branching) is separate — workstreams are a GSD coordination layer, not a git abstraction.

### Commands

| Command | Effect |
|---------|--------|
| `/gsd:workstreams create <name>` | Create a new named parallel track |
| `/gsd:workstreams list` | Show all tracks and their current status |
| `/gsd:workstreams switch <name>` | Change the active workstream |
| `/gsd:workstreams status` | Progress summary per stream (phases, blockers, last active) |
| `/gsd:workstreams progress <name>` | Detailed progress for one named stream |
| `/gsd:workstreams complete <name>` | Mark a workstream done and archive its context |
| `/gsd:workstreams resume <name>` | Restore context for a previously paused workstream |

### When to use workstreams

**Use workstreams when you have parallel ownership that cannot be serialized.**

Good use cases:
- Frontend and backend development happening simultaneously on the same repo.
- Feature A and Feature B that share no files — two engineers, one repo.
- Experimental track (spike) running alongside stable track.
- Performance optimization workstream running while feature work continues.
- Bug fix track that must ship before the feature in progress.

**Do not use workstreams for:**
- Sequential phases (use the phase number progression).
- Work that takes less than one session (use a single phase with waves).
- Personal context threads across sessions (use `/gsd:thread` instead).
- Separating testing from implementation (use `--tdd` flag instead).

### Task-api example

The task-api toy project does not need workstreams — it is sequential: POST /tasks, then GET /tasks, then PATCH. If you were building the API (backend) and a CLI client (separate tool, same repo) simultaneously, workstreams would apply:

```
workstream: api
  Phase 1: POST /tasks
  Phase 2: GET /tasks

workstream: cli
  Phase 1: Add task command
  Phase 2: List tasks command
```

Each workstream runs its own discuss → plan → execute cycle. `/gsd:workstreams status` shows both tracks at a glance.

### File conflict rule

Tasks from two workstreams that write the same file must be serialized. If both workstreams touch `main.go`, stage them so one completes before the other starts. Workstreams do not prevent git merge conflicts — they coordinate intent, not bytes.

If two workstream tasks need the same file, add an explicit dependency note in the PLAN.md of the second workstream: "Depends on: api-workstream Phase 1 Wave 1 complete."

### Workstream vs branch decision

| Need | Use |
|------|-----|
| Two features with separate GSD loops | Workstreams |
| Hotfix while feature in progress | Workstreams (keep GSD state separate) |
| Isolated git history only, same GSD loop | Git branch |
| Experiment vs stable track | Workstreams |
| One engineer, one feature, linear phases | Neither — just phase numbers |

---

## Threads

A thread is a persistent context store that survives `/compact` and session restarts. It is not a phase, not a plan, and not a git object — it is conversational memory that GSD manages separately from STATE.md.

### Command

```
/gsd:thread
```

Subcommands and behaviors vary by GSD version. Common operations:
- Create a thread with a named topic.
- Append findings to an existing thread.
- Load a thread at session start to restore investigation context.
- Search thread history for specific findings.

### Threads vs STATE.md vs CLAUDE.md

All three persist information. They serve distinct purposes:

| Store | Holds | Read by GSD? | Survives /compact? |
|-------|-------|-------------|-------------------|
| STATE.md | Structured workflow state: phase, tasks, blockers | Yes — programmatically | Only if saved |
| Thread | Freeform investigative context, intermediate conclusions | No | Yes |
| CLAUDE.md | Behavioral rules, project-wide constraints | Yes — as context | Yes |

STATE.md is operational. Threads are investigative. CLAUDE.md is behavioral. Do not mix them.

### When threads are the right tool

| Situation | Use |
|-----------|-----|
| Multi-day investigation with many findings | Thread (survives /compact) |
| Long-running feature work spanning many sessions | Thread + STATE.md |
| Architecture decision in progress, not resolved yet | Thread |
| Session context for a single phase | STATE.md (not thread) |
| Findings you want searchable later | Thread |
| Rules about how to write code | CLAUDE.md (not thread) |

### Task-api example

Not needed for a simple toy project. Would be appropriate if you were investigating a performance regression across three days: create a thread named "task-api-latency-investigation", append findings each session, load it at session start. The thread holds your intermediate hypotheses and test results. STATE.md holds where you are in the fix phase.

---

## Agent isolation: worktrees

A third mechanism for isolated work: git worktrees. When you want complete isolation — separate filesystem checkout, separate git HEAD, separate context window — use a git worktree paired with a separate Claude Code session.

### How worktrees differ from workstreams

| Feature | Workstreams | Git worktrees |
|---------|-------------|---------------|
| What it isolates | GSD state tracking | Git working tree (filesystem) |
| Prevents file conflicts | No | Yes |
| Separate session | No (same session) | Yes (separate window) |
| GSD awareness | Full | Manual |
| Best for | Parallel GSD feature loops | Agent tasks needing isolation |

GSD exposes `EnterWorktree` / `ExitWorktree` as agent tools for worktree isolation. This is distinct from workstreams: worktrees are git-level isolation; workstreams are GSD coordination-level separation.

### When to use worktrees

- You want an agent to work on a risky branch without touching your main session's working tree.
- You are running two parallel execute-phase operations that touch overlapping files.
- You need a clean environment to verify a build without your in-progress changes.
- An agent task is destructive (large refactor, dependency upgrade) and you want it isolated.

### Task-api example

If you want to run a major Go version upgrade concurrently with feature work: create a worktree on a `go-upgrade` branch. Agent runs upgrade in isolation. You continue feature work in the main checkout. Merge when upgrade is verified.

---

## Decision table: which parallel mechanism

| Need | Use |
|------|-----|
| Two features in parallel, same repo | Workstreams |
| Context that survives /compact | Thread |
| Complete filesystem isolation for agent work | Git worktree |
| Frontend / backend split in one repo | Workstreams |
| Multi-day investigation notes | Thread |
| Feature flag experiment track | Workstreams |
| Architecture decision in progress | Thread |
| Long sequential phase list | Neither — just phase numbers |
| One engineer, one feature, one week | Neither — just phases |
| Risky agent refactor | Git worktree |
| Ongoing bug investigation across sessions | Thread + /gsd:debug |

---

## Anti-patterns

**Workstream sprawl:** Creating a workstream for every small task. Workstreams carry coordination overhead. Use them only when parallel ownership is real and sustained.

**Thread as a second CLAUDE.md:** Do not copy rules and constraints into threads. Rules belong in CLAUDE.md or `.claude/rules/`. Threads hold transient reasoning state that will eventually be resolved and discarded.

**STATE.md vs thread confusion:** STATE.md is read by GSD commands. Threads are not. If you put something in a thread that GSD needs to act on (a blocker, a decision), it will be ignored by GSD automation. Operational state belongs in STATE.md.

**Worktree without cleanup:** Worktrees accumulate disk space and context. Clean up after an agent completes its isolated task. GSD auto-cleans worktrees if the agent makes no changes.

**Sequential work forced into workstreams:** If Phase 2 depends on Phase 1, they are not parallel — they are sequential. Do not create a workstream for Phase 2 while Phase 1 is in progress just to have something to show.

---

## Session patterns using parallel mechanisms

**Pattern: two engineers, one repo**

```
Engineer A: /gsd:workstreams create api-endpoints
Engineer B: /gsd:workstreams create auth-system

Both work independently. Daily: /gsd:workstreams status to see cross-track blockers.
Merge point: api-endpoints Phase 1 done → auth-system can start Phase 2 which depends on it.
```

**Pattern: long investigation with active feature**

```
Active feature: Phase 3 discuss → plan → execute (normal core loop)
Investigation: /gsd:thread new latency-regression
               (append findings as discovered, load at each session start)
               /gsd:debug for systematic hypothesis testing
               Thread records the investigation trail
```

**Pattern: risky agent upgrade in isolation**

```
Main checkout: Phase 4 in progress (feature work)
Worktree: /gsd:worktree (or EnterWorktree tool) → agent runs go mod upgrade → verify
If upgrade succeeds: merge into main
If upgrade fails: discard worktree, continue Phase 4 unaffected
```

---

## Checklist

- [ ] I know the difference between a workstream and a git branch.
- [ ] I know when threads are the right tool vs STATE.md vs CLAUDE.md.
- [ ] I understand that workstreams do not prevent git merge conflicts.
- [ ] I can describe a scenario where worktrees are appropriate vs workstreams.
- [ ] I would not use workstreams for sequential phases.
- [ ] I know that threads are not read by GSD commands programmatically.
- [ ] I know the seven workstream sub-commands and when to use each.
- [ ] I can explain why sequential work should stay in phase numbers, not workstreams.
