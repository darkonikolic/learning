# Idempotent refactoring discipline

Stable, predictable edits: the same request should produce the same *kind* of change — bounded files, bounded symbols, no drive-by cleanup.

`01-refactor-ownership.md` defines the refactor **template** (current → target → migration). `03-diff-review-discipline.md` defines **review** before merge. This file defines **edit scope** during execute: what Claude may touch, what is forbidden, and when to stop.

---

## Scope

**Stable and predictable changes** — idempotent in the operational sense: re-running a bounded task does not widen blast radius, rename unrelated symbols, or reformatted unrelated code.

---

## Areas

| Area | What it means |
|------|----------------|
| **Idempotent editing** | Same task + same anchors → same file set; no extra “while here” edits |
| **Diff anchors** | Named files, symbols, or plan tasks every hunk must cite |
| **Edit boundaries** | Handler vs store vs domain — edits stay in the layer that owns the change |
| **Allowed edit zones** | Paths and packages explicitly in plan or SPEC |
| **Forbidden edit zones** | Vendor, CI, unrelated packages, public API without approval |
| **Scope ownership** | You name scope; Claude does not expand it |
| **Blast radius awareness** | List touched files and explain impact before large refactors |
| **Unrelated change prevention** | Reject formatting, rename, or optimize outside request |
| **Rename discipline** | No symbol renames unless the task or refactor template says so |
| **Formatting discipline** | No style-only churn in files not being changed for behavior |
| **Minimal diff ownership** | Smallest correct change; split if diff outgrows task |
| **Stop and ask workflow** | Required scope exceeds request → STOP, explain, wait |
| **Change isolation** | One concern per wave; no bundled refactor + feature |
| **Regression surface awareness** | Know which tests and callers each hunk affects |
| **Deterministic refactoring** | Ordered migration steps; each step builds and tests green |

---

## Diff anchors

Before execute, pin anchors in the message or plan task:

```text
Edit anchors:
- Files: internal/handler/task.go, internal/store/store.go
- Symbols: ListTasks, TaskStore.List
- Out of scope: main.go, domain types, formatting-only passes
```

Every hunk in `git diff` should trace to an anchor. Orphan hunks → revert or classify failure (`13-agent-reliability/03-claude-failure-taxonomy.md`).

---

## Allowed and forbidden zones

| Zone | Typical rule |
|------|----------------|
| **Allowed** | Files listed in plan task, SPEC “files to change”, or refactor template DIFF |
| **Forbidden** | Packages not in anchor list; `go.mod` / `go.sum` without dependency task; config/CI without explicit task |
| **Conditional** | Public exports, shared types — only with SPEC or template approval |

**Cross-boundary edit:** handler imports store internals, or store imports `net/http` — boundary failure. Fix before next task.

---

## Stop and ask workflow

When Claude detects that correct work requires exceeding anchors:

1. **STOP** — no further Writes
2. Explain which constraint blocks progress (SPEC, boundary, missing file)
3. Propose: narrow task, update SPEC, or new plan task — human approves

Paste into prompts or rules (also in `04-claude-code-configuration/01-claude-md-authoring.md`):

```text
If required changes exceed requested scope:
STOP and explain why.
```

---

## Per-turn and CLAUDE.md discipline

Load these from `CLAUDE.md` (always on) and repeat in Layer 3 per-turn constraints when stakes are high:

```text
Only modify explicitly requested scope.

Do not rename symbols unless requested.

Do not reformat unrelated code.

Do not optimize unrelated code.

Preserve architecture boundaries.

Minimize diff size.

If required changes exceed requested scope:
STOP and explain why.

List touched files before changes.

Explain blast radius before large refactors.

Preserve public contracts unless explicitly approved.
```

See `03-prompt-layering-and-context/02-prompt-layering-in-practice.md` for where Layer 3 fits in the message.

---

## Workflow integration

```
Frame scope (anchors + allowed zones)
  → List touched files (Claude or you)
  → Execute one plan task
  → git diff — file list, then hunks
  → Classify drift (taxonomy) if needed
  → Verify → merge
```

For refactors, fill `01-refactor-ownership.md` template first; anchors come from template DIFF + MIGRATION STEPS.

---

## Checklist

- [ ] I set edit anchors (files and/or symbols) before execute.
- [ ] I listed allowed and forbidden zones for this task.
- [ ] Claude listed touched files before large edits (or I demanded it in the prompt).
- [ ] I rejected unrelated formatting, renames, and cross-boundary hunks.
- [ ] I used STOP-and-explain when scope had to grow — not silent expansion.
- [ ] I can tie every hunk to an anchor, plan task, or SPEC item.
