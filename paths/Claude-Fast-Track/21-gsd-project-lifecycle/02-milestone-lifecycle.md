# Milestone lifecycle

A milestone is a themed group of phases that together deliver one shippable, coherent increment. A milestone is not a sprint and not a release — it is the unit of work between "we have nothing" and "we have something demonstrably working."

Milestones group phases so that you can audit and archive them as a unit. You cannot archive individual phases — you archive a milestone when every phase in it is complete and verified.

---

## What a milestone contains

A milestone has:
- A name (usually a version number or a theme: "Core CRUD API", "v0.1", "Auth layer")
- A set of phases, each with its own PLAN.md and verification results
- A shared success definition — what does it mean for all of these phases to be done together?
- A status: active, audited, or archived

Milestones live under `.planning/milestones/<name>/`. Phase artifacts (SPEC.md, PLAN.md, CONTEXT.md) live inside the milestone directory.

---

## `/gsd:new-milestone`

Starts a new milestone cycle. Run after `/gsd:new-project` (or after completing the previous milestone) when you are ready to begin a new batch of phases.

What it does:
- Asks for the milestone name and theme
- Creates the milestone directory under `.planning/milestones/`
- Updates `.planning/ROADMAP.md` to mark the new milestone as active
- Optionally carries forward unfinished phases from the previous milestone

When to use it: when you complete one deliverable arc and are starting another. After shipping "Core CRUD API", you run `/gsd:new-milestone` to begin "Auth layer" or "Pagination".

What it does not do: it does not plan phases for you. After running `/gsd:new-milestone`, you still need to run `/gsd:discuss-phase` or `/gsd:spec-phase` for each phase inside the new milestone.

---

## `/gsd:complete-milestone`

Closes a milestone. It does not archive blindly — it checks preconditions first.

What it checks before archiving:
- Every phase listed in the milestone has a completion marker
- `/gsd:verify-work` has been run and passed for each phase (or a waiver is recorded)
- No phase is in a failed or in-progress state
- STATE.md does not show an active phase mid-execution

If any check fails, it reports what is blocking and stops. You fix the blocker, then re-run.

What it archives: moves the milestone directory to `.planning/milestones/archived/<name>/`, updates ROADMAP.md to mark the milestone complete, and writes a summary entry.

---

## `/gsd:milestone-summary`

Produces a human-readable summary of a milestone's outcomes — what was built, what decisions were made, what acceptance criteria were satisfied. Useful for:
- Onboarding a new team member to a completed milestone
- Writing a changelog or release note
- Reviewing what was actually delivered vs what was planned before starting the next milestone

Run it after all phases are verified but before running `/gsd:complete-milestone`. The summary is your last chance to catch gaps before archiving.

---

## `/gsd:audit-milestone`

Runs a structured audit against the milestone's original intent. The difference between audit and complete:

| Command | What it does |
|---------|-------------|
| `/gsd:complete-milestone` | Checks completion state and archives if clean |
| `/gsd:audit-milestone` | Checks whether what was built matches what was planned — scope drift, missing acceptance criteria, untested behaviors |

Audit does not archive. It produces an audit report you review before deciding to complete. Run audit before complete if the milestone had significant scope changes mid-execution or if phases were re-planned after starting.

---

## The milestone state machine

```
new-milestone
     |
     v
  active           (phases running: discuss → plan → execute → verify)
     |
     v
  audited          (audit-milestone passed; summary generated)
     |
     v
  archived         (complete-milestone passed; moved to archived/)
```

You can skip audit if the milestone was small and clean. You cannot skip verify-work on individual phases — that check is enforced by complete-milestone.

---

## task-api example: Milestone 1 arc

Milestone 1 for task-api is "Core CRUD API". It covers the four phases that deliver a working API from an empty directory.

**Starting the milestone:**

```
/gsd:new-milestone
> Name: v0.1 — Core CRUD API
> Theme: Deliverable: all three endpoints working with in-memory store, tests passing, curl-testable
```

GSD creates `.planning/milestones/v0.1/` and marks it active in ROADMAP.md.

**Running the phases (in order):**

- Phase 1: Project setup — scaffold, go.mod, main.go, handler skeleton
- Phase 2: GET /tasks — list endpoint, empty store returns [], tests
- Phase 3: POST /tasks — create endpoint, 201 + task body, validation, tests
- Phase 4: DELETE /tasks/:id — delete endpoint, 204/404, tests

Each phase follows the full loop: discuss → plan → execute → verify. After Phase 4 verify passes:

**Closing the milestone:**

```
/gsd:milestone-summary
```

Review the summary. Check that all four endpoints appear in the acceptance outcomes.

```
/gsd:audit-milestone
```

Review the audit report. If it flags any untested boundary cases, add them to a backlog item — do not re-open phases unless something is broken.

```
/gsd:complete-milestone
```

GSD checks all phases, moves `.planning/milestones/v0.1/` to `.planning/milestones/archived/v0.1/`, and updates ROADMAP.md. Milestone 1 is done.

---

## Checklist

- [ ] I can explain the difference between a milestone and a phase.
- [ ] I know what `/gsd:complete-milestone` checks before archiving.
- [ ] I know when to run audit before complete (significant scope changes, re-planned phases).
- [ ] I understand the three states: active, audited, archived.
- [ ] I know that `/gsd:new-milestone` does not plan phases — that is a separate step.
- [ ] I can trace the task-api Milestone 1 arc from new to archived.
