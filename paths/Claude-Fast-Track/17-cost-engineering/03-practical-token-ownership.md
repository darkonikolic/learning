# Practical token ownership

`01-token-and-context-budgets.md` covers stage-level economics and ceilings. This file is **session hygiene**: minimal sufficient context, ordering, waste patterns, and iteration cost — the habits that keep Claude Code sharp in long sessions.

---

## Prompt mass control

**Prompt mass** = everything in one message: history, files, rules, repeated instructions.

| Heavy | Light |
|-------|-------|
| Paste full SPEC + full plan + 5 files | SPEC acceptance section + one file |
| Repeat CLAUDE.md in every message | Trust load once per session |
| “Remember everything we discussed” | Checkpoint file + 5-line recap |

**Rule:** each message should answer “what is new since last turn?”

---

## Minimal sufficient context

Include only what would cause a **wrong edit** if omitted:

1. Task sentence (from plan)
2. Read targets (paths)
3. Constraints that apply **this task only**
4. Stop condition (“stop after store.List exists”)

Omit: unrelated phases, full chat narrative, entire test suite unless task is “fix tests.”

See `03-prompt-layering-and-context/03-context-engineering.md`.

---

## High-value context ordering

Put **highest trust, highest constraint** content where it survives truncation:

```
1. Stop condition + out-of-scope (one block)
2. Read these files (list)
3. Task from plan (quote)
4. Acceptance snippet (if short)
5. Nice-to-have style notes
```

Long examples and history go last or on disk, not in chat.

---

## Compression heuristics

| Signal | Action |
|--------|--------|
| `/context` > 70% | `/compact` after writing plan + state to disk |
| Same file read 4× | Paste stable snippet into plan task |
| Rules re-loaded every turn | Path-scope rules; shrink CLAUDE.md |
| Huge test output | Paste failing test name + last 30 lines only |

Protected zones before `/compact`: `15-context-compression/01-compression-and-checkpoints.md`.

---

## Token waste patterns

| Waste | Cost | Fix |
|-------|------|-----|
| Re-explaining project | Every turn | CLAUDE.md once |
| Whole-repo Grep in chat | Large readback | Narrow glob |
| Parallel agents on same file | N× tokens | Serialize or split files |
| Re-running full plan | Duplicate | Edit plan on disk |
| “Improve code quality” unbounded | Endless diff | Bounded task + stop |
| Opus for classification | 5–10× | Haiku/Sonnet (`18-model-selection/`) |

---

## Iteration cost ownership

You own the **budget per task**, not Anthropic:

| Decision | Cost impact |
|----------|-------------|
| Third repair without replan | High; low yield |
| Opus for all execute tasks | High |
| 6-task wave with full SPEC each task | PLAN/spec re-reads |
| One-task messages with 2 files | Baseline |

Before a phase: rough table in `17-cost-engineering/02-lab-budget-a-phase.md`. After: note one waste pattern to eliminate next phase.

---

## Degradation signals

When session feels “dumber,” check:

- Context % (`/context`)
- Missing constraint in output → over-context or under-context (`13-agent-reliability/03-claude-failure-taxonomy.md`)
- Chat-only decisions → prompt debt (`02-claude-code-workflow/07-prompt-repair-discipline.md`)

**Recovery:** checkpoint → `/compact` or `/clear` → reload L1 + task slice from disk.

---

## Checklist

- [ ] I control prompt mass — new info only per turn.
- [ ] I order context: constraints first, history last.
- [ ] I `/compact` only after disk checkpoint.
- [ ] I can name one token waste pattern I will avoid this week.
- [ ] I match model tier to task (`18-model-selection/`).
