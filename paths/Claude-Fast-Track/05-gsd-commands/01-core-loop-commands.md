# Core loop commands

GSD is a structured layer on top of Claude Code. It gives every phase a paper trail: requirements, plan, execution manifest, verification artifact. The commands below are the spine. Everything else is optional amplification.

---

## The core loop

```
/gsd:new-project
        |
/gsd:discuss-phase N  -->  /gsd:spec-phase N (if WHAT is unclear)
        |
/gsd:plan-phase N
        |
/gsd:execute-phase N
        |
/gsd:verify-work
        |
/gsd:ship
        |
  (next phase, repeat from discuss)
```

Human gates: approve CONTEXT.md before plan. Approve PLAN.md before execute. Approve verification before ship. These are not optional — they are where you catch wrong direction before it becomes wrong code.

---

## Command reference

### `/gsd:new-project`

**Purpose:** Bootstrap `.planning/` from scratch. Runs context-gathering interview, generates PROJECT.md, REQUIREMENTS.md, ROADMAP.md, STATE.md, config.json.

**When to run:** Greenfield start. Also valid when adding GSD to an existing repo that has no `.planning/` directory.

**What it produces:**

| File | Purpose |
|------|---------|
| `.planning/PROJECT.md` | Vision, tech stack, constraints, team, tooling |
| `.planning/REQUIREMENTS.md` | REQ-IDs and acceptance criteria |
| `.planning/ROADMAP.md` | Phase list with status |
| `.planning/STATE.md` | Current phase, blockers, session context |
| `.planning/config.json` | GSD workflow toggles |

**Flags:** None required for basic use. On an existing repo, run `/gsd:map-codebase` first to produce `.planning/codebase/` intelligence that new-project can reference.

**After running:** Edit PROJECT.md vision section before proceeding. The model writes a reasonable draft; you enforce the real constraints. Delete aspirations that are not commitments.

**Task-api example:** After running, PROJECT.md should read: "In-memory Go HTTP task manager. Three endpoints. No persistence layer. No auth. Stdlib only." If it says "production-grade" or "scalable", delete those words.

---

### `/gsd:discuss-phase <N>`

**Purpose:** Surface unknowns before planning. Runs a structured interview about goals, constraints, boundaries, non-goals, and risks. Output is CONTEXT.md under the phase folder.

**When to run:** When you have a phase goal but cannot describe "done" without hand-waving. If you can write a one-sentence acceptance criterion right now, skip to plan-phase or spec-phase.

**What it produces:** `.planning/phases/XX-phase-name/CONTEXT.md`

**Flags:**

| Flag | Effect |
|------|--------|
| `--batch` | Asks all clarifying questions at once instead of conversational back-and-forth. Faster when context is already clear. |

**After running:** YOU edit CONTEXT.md. This is the human gate. Delete model filler ("This phase aims to achieve..."). Sharpen every boundary. If a line cannot be verified, remove it or replace it with something that can.

**Bad CONTEXT.md line:** "The API should handle requests efficiently and return appropriate responses."
**Good CONTEXT.md line:** "POST /tasks returns 201 with `{id, title, done: false}`. 400 if title is missing or empty string."

---

### `/gsd:plan-phase <N>`

**Purpose:** Convert an approved CONTEXT.md into an executable task breakdown. Each task must name specific files, have a clear output, and belong to a wave.

**When to run:** CONTEXT.md is approved (you edited it, it is honest about boundaries). Do not run plan-phase if CONTEXT.md still has open questions.

**What it produces:** `.planning/phases/XX-name/XX-YY-PLAN.md` — one or more plan files with task list, wave groupings, dependencies, verification criteria.

**Flags:**

| Flag | Effect |
|------|--------|
| `--research` | Spawns a research agent first; produces RESEARCH.md that the planner consumes. Use when the domain is unfamiliar. |
| `--tdd` | Tasks are structured test-first. Test file created before implementation file in each wave. |
| `--mvp` | Constrains plan to minimum viable slice only. |
| `--prd path` | Skip discuss entirely; ingest an existing PRD file as context. |
| `--ingest path` | Ingest approved ADRs as planning input. |
| `--gaps` | Replan only missing or failed tasks; do not touch completed tasks. |

**After running:** Read every task. Apply this test: "Could I execute this task without asking Claude what to do?" If no, the task is vague. Edit it to name the file, the function, the change.

**Bad task:** "Add validation to the handler."
**Good task:** "In `internal/handler/tasks.go`, add validation to `CreateTask`: return 400 JSON error if `title` field is absent or empty string."

---

### `/gsd:execute-phase <N>`

**Purpose:** Run all tasks in the approved PLAN.md. GSD spawns executor agents per wave, commits atomically, and updates STATE.md and ROADMAP.md.

**When to run:** PLAN.md is approved. Never execute an unapproved plan — you lose traceability.

**What it updates:**

| File | What changes |
|------|-------------|
| `STATE.md` | Current wave, completed tasks, blockers |
| `ROADMAP.md` | Phase status (in-progress, completed) |
| `REQUIREMENTS.md` | REQ markers satisfied |

**Flags:**

| Flag | Effect |
|------|--------|
| `--wave W` | Run a specific wave number only. Use for incremental execution or retry. |
| `--gaps-only` | Skip completed tasks; fill only tasks with no completion marker. |
| `--tdd` | Test before implementation per task. |

**After running:** Read STATE.md. Look for blockers section. Any task marked failed needs a decision: fix now, defer to next phase (document why), or replan with `--gaps`.

---

### `/gsd:verify-work`

**Purpose:** Conversational UAT against the phase goal. GSD walks you through each acceptance criterion from CONTEXT.md and PLAN.md, records pass/fail, and produces a verification artifact.

**When to run:** After execute-phase completes. Before ship. No exceptions.

**What it produces:** A UAT artifact (typically `{phase}-UAT.md`) tracking each acceptance item.

**After running:** Every FAIL item needs a follow-up command before ship. See the gap routing table in `06-gsd-workflow/04-verify-and-ship.md`.

---

### `/gsd:ship`

**Purpose:** Create PR, run review bots, bridge local GSD completion to mainline.

**When to run:** After verify-work passes (or explicit STATE.md waiver for known gaps).

**Before running:** Use `/gsd:pr-branch` to get a clean branch without `.planning/` commit noise. Reviewers do not need the planning artifact history — only the code changes.

---

## Smart router: `/gsd:progress`

When you are lost, run this first. It reads STATE.md and ROADMAP.md and tells you where you are and what to do next.

| Variant | Behavior |
|---------|---------|
| `/gsd:progress` | Situational report + suggested next command |
| `/gsd:progress --next` | Auto-advance to the next logical workflow step |
| `/gsd:progress --do "intent"` | Natural-language dispatch — maps your intent to the best `/gsd:*` command |

**When to prefer `--do` over manual command selection:** Any time you are unsure which command fits your intent. Type what you want; let the router route.

Example: `/gsd:progress --do "I want to add a PATCH endpoint to complete a task"` — the router suggests whether you need a new phase, a plan update, or a direct execute.

---

## Command selection by scenario

| Scenario | Start with |
|----------|-----------|
| Empty repo, new idea | `/gsd:new-project` |
| Existing repo, no `.planning/` | `/gsd:map-codebase` then `/gsd:new-project` |
| Phase defined, CONTEXT.md missing | `/gsd:discuss-phase N` |
| CONTEXT approved, no PLAN yet | `/gsd:plan-phase N` |
| PLAN approved, ready to build | `/gsd:execute-phase N` |
| Execute done, not verified | `/gsd:verify-work` |
| Verified, need PR | `/gsd:pr-branch` then `/gsd:ship` |
| Disoriented, don't know where you are | `/gsd:progress` |
| Know what you want, unsure of command | `/gsd:progress --do "intent"` |

---

## Checklist

- [ ] I can recite the six steps of the core loop from memory.
- [ ] I understand that CONTEXT.md requires human editing after discuss-phase runs.
- [ ] I know what `--gaps-only` does and when to use it.
- [ ] I know the difference between `/gsd:progress` and `/gsd:progress --next`.
- [ ] I ran `/gsd:help` on my installed GSD version and noted what changed.
- [ ] I can explain why `/gsd:pr-branch` comes before `/gsd:ship`.
- [ ] I know the three flags for `/gsd:plan-phase` that change task structure.
- [ ] I can name all five files that `/gsd:new-project` creates.
