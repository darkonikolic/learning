# Specification before implementation — the contract artefact

**Goal:** before meaningful code changes, produce a **SPEC on disk** — problem, constraints, and **checkable acceptance** — so Claude implements against a contract, not chat memory.

**Prerequisite chain:** mindset (`01`) → commands/config (`02`–`03`) → plan workflow (`04`). **This unit** sits between **plan** and **prompt/context** skills.

**Deep spec engineering** (boundaries, NFR, drift, partition): `04-specification-guided-development/` after this habit is reflexive.

Numerical prefixes = concept order only.

---

## The artefact ladder

Pick the **smallest** artefact that still lets you verify “done”:

| Depth | Artefact | Location (typical) | When |
|-------|----------|-------------------|------|
| Trivial | Inline acceptance in chat | — | One-line fix, typo, config knob |
| Small | **Plan** | `docs/plans/<slug>.md` | 1–2 files, clear steps (`04`) |
| Feature | **SPEC** | `docs/specs/<slug>.md` | Behaviour change, ≥3 acceptance checks, multiple files |
| Programme | **GSD SPEC / REQUIREMENTS** | `.planning/phases/…/SPEC.md`, `REQUIREMENTS.md` | Multi-phase, REQ-IDs (`15`–`18`) |

**Checkpoint:** if you cannot list **pass/fail acceptance** bullets, you are not ready for Agent execution.

---

## SPEC vs plan vs prompt SPEC block

| | Plan (`04`) | SPEC (this unit) | SPEC block in prompt (`08`) |
|--|-------------|------------------|-----------------------------|
| **Purpose** | Steps and file touch list | **What** must be true when done | Points Claude at approved truth |
| **Acceptance** | Often light | **≥5 checkable** behaviours on feature slices | Must match on-disk SPEC |
| **Constraints / NFR** | Optional | Required when behaviour or ops risk | Summarized, not invented |
| **When** | Small bounded change | Feature or cross-module change | Every non-trivial message after SPEC exists |

**Rule:** the prompt **SPEC** block is not a substitute for **`docs/specs/<slug>.md`** on feature-sized work.

---

## Minimal SPEC template (foundations)

Save before implementation. Expand sections in `04-specification-guided-development/` when stakes rise.

```markdown
# SPEC: [slug]

## Problem
One grounded sentence — why now.

## Goal
Measurable outcome (user or system observable).

## Out of scope
- …

## Constraint
Hard bans / stack rules Claude must not hand-wave.

## Acceptance
- [ ] … (binary pass/fail)
- [ ] …
- [ ] …
- [ ] …
- [ ] …

## Rollback
How to undo if mid-implementation fails.

## Open questions
- … (must be empty or explicitly waived before execute)
```

**Feature-sized slices:** aim for **≥5 acceptance** lines. Trivial tasks may use a **plan** only (`04`).

---

## When plan is enough vs SPEC required

| Signal | Use plan only | Require SPEC |
|--------|---------------|--------------|
| Files touched | 1–2 | 3+ or unknown until exploration |
| Behaviour | No user-visible change | API, workflow, data semantics change |
| Verification | Obvious (test exists) | Needs agreed checklist |
| Rollback | Trivial revert | Migration, flag, queue, infra |
| Team review | Solo | Others must sign off without reading chat |

When in doubt on a **feature**, write SPEC — cost is one Markdown file.

---

## Claude Code workflow

### 1. Frame (`01`, `04` phase 0)

One sentence problem + out-of-scope **before** `/plan` or SPEC drafting.

### 2. Draft SPEC — no implementation yet

**Option A — `/plan` with SPEC-shaped ask:**

```
/plan Draft docs/specs/webhook-idempotency.md only — use foundations SPEC template.
No code. Acceptance must be checkable. List open questions.
```

**Option B — Ask mode / read-only turn:**

Same request; you edit the file until acceptance is crisp.

### 3. Review (human gate)

You edit `docs/specs/<slug>.md`:

- Every acceptance line is **pass/fail** without model collusion.  
- Constraints are **binary** (must / must-not).  
- Open questions **empty or explicitly deferred** with risk noted.

### 4. Execute against SPEC

```
Implement steps from docs/specs/<slug>.md only — acceptance section is the contract.
Do not expand scope. Stop after listed implementation slice.
```

Use **`/plan`** again if scope was wrong — do not patch code and SPEC independently.

### 5. Verify

Map each acceptance checkbox to **test, curl, log line, or review step**. Record in SPEC file or PR description.

---

## GSD connection

| Foundations | GSD |
|-------------|-----|
| `docs/specs/<slug>.md` | `.planning/phases/XX/SPEC.md` |
| Manual acceptance | `REQUIREMENTS.md` REQ-IDs |
| `/plan` | `/gsd:spec-phase`, `/gsd:discuss-phase`, `/gsd:plan-phase` |

Single-session feature → **this unit**. Multi-phase programme → **`16-gsd-configuration`**, **`17-gsd-plan-to-ship-workflow`** (`15`–`18`).

---

## Anti-patterns

| Anti-pattern | Fix |
|--------------|-----|
| “Implement refund flow” with no acceptance | Write SPEC first |
| SPEC only in chat, then `/compact` | File on disk |
| Acceptance = “works well” | Observable pass/fail |
| SPEC and code drift mid-task | Stop; update SPEC; re-approve |
| Duplicate full SPEC in CLAUDE.md | Pointer + REQ id only |

---

## Lab — SPEC before diff

**Task:** small **behaviour** change (e.g. idempotent webhook handler, validation rule, retry policy) — not a typo fix.

| Step | Deliverable |
|------|-------------|
| 1 | Frame note (problem + out-of-scope) |
| 2 | `docs/specs/<slug>.md` with **≥5 acceptance** lines |
| 3 | Self-review: strike any non-checkable acceptance |
| 4 | One Claude turn: implement **one** acceptance item only |
| 5 | Verify that item; tick checkbox in SPEC |
| 6 | Note: plan-only would have failed where? (journal 3 bullets) |

---

## Checklist

- [ ] I chose **plan vs SPEC** using the signal table — not habit alone.  
- [ ] SPEC exists **on disk** before first implementation edit on feature work.  
- [ ] **≥5 acceptance** lines on feature-sized slices.  
- [ ] Verification mapped **1:1** to acceptance bullets.  
- [ ] I know **`04-specification-guided-development/`** is the deep dive next.  
