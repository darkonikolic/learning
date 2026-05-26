# Prompt repair discipline

`05-iteration-and-correction.md` covers how to **phrase** a correction. This file covers **when and how to repair** a session: diagnosis, minimal patches, and avoiding prompt debt.

---

## First-attempt diagnosis

Before sending repair message #2, answer:

1. **Failure class** — row from `13-agent-reliability/03-claude-failure-taxonomy.md`
2. **Layer** — bad prompt, bad context, bad plan, bad SPEC, or wrong phase gate
3. **Smallest fix** — one sentence that would have prevented the failure

If you cannot answer (3), you are not ready to repair — you are ready to **replan** or **re-read**.

---

## Repair loops

A disciplined repair loop:

```
Observe output (diff, test, curl)
  → Classify failure
  → Minimal correction prompt (one flaw)
  → Verify
  → Stop or next flaw
```

**Max three repair loops** on the same task without replan. After three, the prompt or plan is wrong — not the model’s “mood.”

| Loop | Allowed | Not allowed |
|------|---------|-------------|
| 1 | Targeted fix with file + expected | “try again” |
| 2 | Same, plus constraint quoted | New feature scope |
| 3 | Replan task text or shrink scope | Hope |

---

## Minimal correction strategy

Each repair message changes **one dimension**:

| Dimension | Example repair |
|-----------|----------------|
| Behavior | “404 must be `{"error":"task not found"}` — see SPEC item 6” |
| Location | “Only edit `tasks/store.go`; handler is out of scope for this task” |
| Constraint | “stdlib only — remove `github.com/...` import” |
| Test | “Make `TestListEmpty` pass without changing production sort order” |

**Stacking three fixes in one message** trains vague failure modes. Sequence them if needed.

Template (from `05-iteration-and-correction.md`):

```
Flaw: …
Location: …
Expected: …
Do not change: …
```

---

## Prompt debt

**Prompt debt** = corrections and exceptions accumulated in chat that are **not** on disk.

| Symptom | Debt |
|---------|------|
| “Remember we use UUID not int” only in chat | High |
| Same correction repeated every session | High |
| Rule in `.claude/rules/` | Low |
| Constraint in SPEC | Lowest |

**Pay down debt:** move repeated repairs into `CLAUDE.md`, rules, or `docs/specs/`. Chat is not a registry.

---

## Targeted patch prompting

Prefer **surgical** prompts over session-wide “reset”:

| Situation | Patch |
|-----------|---------|
| One wrong function | “Rewrite only `CompleteTask` in store.go; leave `List` unchanged” |
| Wrong status code | “Change handler response for unknown ID to 404; no other edits” |
| Test-only fix | “Edit store_test.go only; production code frozen” |

Use `/diff` before and after to confirm patch scope.

---

## Failure isolation

When multiple things are wrong, **isolate**:

1. Revert to last green commit (`git log`, `git revert` or `restore`)
2. Re-run **one** plan task with clean context
3. Verify green before next task

Do not repair A, B, and C in one prompt while all are red — you will not know which fix worked.

---

## Incremental repair vs replan

| Repair | Replan |
|--------|--------|
| Task definition correct; execution sloppy | Task vague or wrong order |
| SPEC clear | SPEC gap |
| One file, one behavior | DAG wrong (handler before store) |

Replan = edit `docs/plans/<phase>-plan.md` or re-run `/plan` — not ten more chat repairs.

---

## Relation to critique

`/code-review` and `/review` are **structured critique** on a diff. Use them **after** a bounded execute, not as a substitute for your repair prompt.

Flow:

```
execute task → go test → your flaw template OR /code-review → fix → verify
```

---

## Checklist

- [ ] I diagnose failure class before repair message #2.
- [ ] I use minimal single-flaw corrections.
- [ ] I stop after three loops and replan.
- [ ] I move repeated repairs off chat into files.
- [ ] I isolate failures (revert + one task) when more than one thing is broken.
