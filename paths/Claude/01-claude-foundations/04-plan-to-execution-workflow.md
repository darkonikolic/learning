# Plan-to-execution workflow — Claude Code

**Goal:** one task from **framed problem → saved plan → bounded execution → verification → captured learnings**, using **plan mode**, **permission modes**, and **on-disk artefacts** — including **adding CLAUDE.md / rules / skills / hooks mid-session**.

**Mindset:** `01-claude-workflow-thinking.md`. **Commands:** `02`. **Config map:** `03`. **Specification:** `05`. **Memory & rules detail:** `09`–`13`.

Numerical prefixes = concept order only.

---

## End-to-end flow

```
FRAME → PLAN (artefact) → REVIEW → EXECUTE → VERIFY → CAPTURE
  │           │              │         │         │          │
  you      /plan or       you edit   normal    tests/    CLAUDE.md
  alone    plan file      approve    or auto   /verify   rules/skills
```

**Non-negotiable:** execution references a **reviewed file or approved `/plan` output**, not chat memory alone.

---

## Phase 0 — Frame (you alone)

1. **One-sentence problem** — grounded in repo or .  
2. **Out-of-scope** — explicit.  
3. **Artefact type** — plan | refactor | incident | config.  
4. **3–7 steps** — your words first (`01`).

---

## Phase 1 — Plan

### Option A — `/plan` in session

```
/plan Add idempotency key to webhook handler — no implementation yet
```

Claude enters **plan mode**; you approve or edit before edits apply.

### Option B — plan file on disk

| Depth | Location | Notes |
|-------|----------|-------|
| Small | `docs/plans/<slug>.md` | 1–2 files (`04`) |
| Feature / behaviour | `docs/specs/<slug>.md` | **`05`** — before implementation |
| Team RFC | `docs/rfcs/<slug>.md` | Review before merge |
| Multi-phase / team | `.planning/phases/.../` via GSD | `15`–`17` |

### Minimum plan template

```markdown
# Plan: [slug]

## Goal
## Out of scope
## Acceptance
- [ ] …
## Files
## Steps
1. …
## Rollback
```

**Approve in chat:** “Execute steps 1–2 only from `docs/plans/<slug>.md`.”

**Upgrade to SPEC (`05`)** when the change is feature-sized — behaviour change, multiple files, or ≥3 checkable acceptance items.

---

## Phase 2 — Review

| Check | Question |
|-------|----------|
| Scope | ≤5 files unless justified? |
| Acceptance | Objectively verifiable? |
| Permissions | Destructive steps need `ask` rules? |
| Rollback | Named? |

Reject vague plans — send back to `/plan` with CONSTRAINT.

---

## Phase 3 — Execute

Exit plan mode or switch to normal execution with explicit bounds:

```
Execute steps 1–2 from docs/plans/webhook-idempotency.md only.
Do not expand scope. Run tests after step 2.
```

### Permission posture

| Situation | Setting |
|-----------|---------|
| Exploratory read-only | `default` or plan mode |
| Trusted small edits | `acceptEdits` |
| CI-like autonomy | `auto` with tuned rules |
| Never default | `bypassPermissions` |

Tune with **`/permissions`** and `.claude/settings.json` (`13`).

### During execution — mid-flight config

| Signal | Action |
|--------|--------|
| Same mistake twice | Add to **`CLAUDE.md`** or **`.claude/rules/`** (`09`, `12`) |
| Repeatable procedure | New **skill** (`10`) |
| Need external tool | **`/mcp`** + `.mcp.json` (`03`) |
| Must run every time | **Hook** (`13`) |
| Context huge | Save plan → **`/compact`** or **`/clear`** + re-attach plan path |
| Scope creep | **`/plan`** again or **`/rewind`** |

---

## Phase 4 — Verify

| Method | When |
|--------|------|
| Your test suite | Default |
| `/verify` skill | Confirm behavior in running app (v2.1.145+) |
| `/code-review` | Correctness on diff |
| `/security-review` | Security-sensitive change |
| Manual checklist | Against plan acceptance bullets |

Record results in plan file or commit message — not only chat.

---

## Phase 5 — Capture

| Observation | Capture as |
|-------------|------------|
| Repeated CONSTRAINT | `CLAUDE.md` bullet or path rule |
| Multi-step playbook | Skill in `.claude/skills/` |
| Tool gap | MCP server |
| Deterministic gate | Hook on `PreToolUse` / `PostToolUse` |
| Phase-level lesson | GSD `STATE.md` if using GSD |

Use **`/memory`** to edit CLAUDE.md and review **auto-memory** entries Claude wrote.

---

## When to use GSD (`15`–`18`)

Stay on this unit for single-session / single-plan work. Use **`05`** for feature SPEC before execute.

Use **GSD** when:

- Multiple phases with REQUIREMENTS traceability  
- `/gsd:execute-phase` and `.planning/` are source of truth  
- Parallel waves and verification loops are required  

Full workflow: `17-gsd-plan-to-ship-workflow.md`. Capstone lab: `18-gsd-integration-lab.md`.

---

## Anti-patterns

| Anti-pattern | Fix |
|--------------|-----|
| Implement without `/plan` or plan file | Plan first |
| Only chat plan, then `/compact` | Plan on disk |
| Patch CLAUDE.md with novel-sized procedures | Move to skill |
| Duplicate GSD REQUIREMENTS in CLAUDE.md | Cross-reference REQ-IDs |
| Skip verify | Acceptance checklist |

---

## Lab — full cycle

**Task:** 2–4 file change (refactor, small feature, doc+code touch).

| Step | Deliverable |
|------|-------------|
| 1 | Frame note (problem + out-of-scope) |
| 2 | `docs/plans/<slug>.md` |
| 3 | `/plan` or Ask review until acceptance crisp |
| 4 | Execute **half** the steps with scope message |
| 5 | Verify (test or `/code-review`) |
| 6 | One capture: CLAUDE.md, rule, or skill patch |
| 7 | Retrospective: `/context` before/after, permission prompts count |

---

## Checklist

- [ ] Plan approved **before** destructive edits.  
- [ ] Execution message states **step bounds**.  
- [ ] Verification tied to acceptance bullets.  
- [ ] At least one **persistent config** update after task.  
- [ ] Escalation to GSD considered and documented if skipped.  
