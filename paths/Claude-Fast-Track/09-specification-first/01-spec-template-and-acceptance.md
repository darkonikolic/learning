# Spec template and acceptance criteria

Claude implements against a contract, not chat memory. The moment you rely on a prior conversation turn to anchor what "done" means, you have already broken the contract. /compact discards context. Long sessions drift. Multi-agent runs never share memory at all. The SPEC on disk is the only artifact that survives all of those situations.

This file covers: the artefact ladder, the decision rule for when a plan is enough vs when a SPEC is required, the full unified SPEC template, and the anatomy of a good vs bad acceptance criterion.

---

## The artefact ladder

Pick the smallest artefact that still lets you verify "done". Over-engineering a simple fix wastes time. Under-specifying a behavior change breaks the verification contract.

| Depth | Artefact | Location | When |
|-------|----------|----------|------|
| Trivial | Inline acceptance in chat | — | Typo, config knob, one-liner |
| Small | Plan | `docs/plans/<slug>.md` | 1-2 files, clear steps, obvious verify |
| Feature | SPEC | `docs/specs/<slug>.md` | Behaviour change, ≥3 acceptance checks, multiple files |
| Programme | GSD SPEC | `.planning/phases/.../SPEC.md` | Multi-phase, REQ-IDs, team review |

The ladder is not strictly hierarchical — a one-file change that touches user-visible behavior needs a SPEC, even though only one file changes. The signal is the behavior, not the file count alone.

---

## When plan is enough vs SPEC required

Use the signals below. One signal in the SPEC column is enough to require a SPEC. Multiple signals in the plan column are needed before you can safely skip one.

| Signal | Plan only | SPEC required |
|--------|-----------|---------------|
| Files touched | 1-2 | 3+ or unknown |
| Behaviour | No user-visible change | API, data, workflow change |
| Rollback | Trivial revert | Migration, flag, queue, infra |
| Verification | Obvious (test exists) | Needs agreed checklist |
| Team review | Solo | Others must sign off |

For task-api: adding an internal helper function — plan only. Adding GET /tasks — SPEC required. The endpoint is user-visible, the verification requires an agreed checklist, and another developer reading the SPEC needs to understand exactly what the endpoint returns.

---

## The unified SPEC template

Use this template for all feature-sized work. Omit sections only when they genuinely do not apply — never to save time. A missing Tradeoff section usually means a decision was made without being written down, not that there was no decision to make.

```markdown
# SPEC: [slug]

## Problem
One grounded sentence — what is broken or missing, and why it matters now.

## Goal
Measurable outcome observable by a user or system (not "improve" — "returns X in Y conditions").

## Out of scope
- [Explicit exclusions — prevents scope creep]

## Constraint
- [Hard bans: must not, cannot, will not]
- [Stack rules: must use X, cannot use Y]

## NFR
- Latency: [e.g., p99 < 50ms for up to 100 tasks] (hypothesis / measured)
- Availability: [inherit from service / specific target]
- Error rate: [threshold]

## Boundary / ownership
[What this feature owns vs what it delegates. Which module/package is responsible.]

## Acceptance
- [ ] [Binary pass/fail check — observable without model collusion]
- [ ] [...]
- [ ] [...]
- [ ] [...]
- [ ] [...] (minimum 5 for feature-sized work)

## Implementation strategy
[Modules, approach, rollout — spec fidelity, not production code dumps]

## Tradeoff
Option A: [description] — Pros: [...] Cons: [...]
Option B: [description] — Pros: [...] Cons: [...]
Decision: Option A because [reason].

## Risk
- [First failure mode + mitigation]
- [Unknown that could blow up scope]

## Rollback
[How to undo if mid-implementation fails]
```

Each section serves a specific function. None is decorative.

**Problem:** grounds the work. If you cannot write one sentence explaining what is broken and why it matters now, the work is not ready to start.

**Goal:** defines done at the system level. "Users can retrieve their tasks" is not a goal. "GET /tasks returns all tasks in creation order with current completion status" is a goal because it can be verified.

**Out of scope:** the most undervalued section. Explicit exclusions prevent the "while I'm here" additions that cause scope creep during execute. For task-api GET /tasks: no filtering, no pagination, no sorting, no authentication. Written down. Non-negotiable.

**Constraint:** boolean rules. Either satisfied or not. "Must use stdlib only" is a constraint. "Should try to avoid external dependencies" is not — it leaves room for interpretation.

**NFR:** measurable quality targets. Latency, throughput, availability, error rate. Always mark hypothesis vs measured. Unhypothesized NFRs are hopes, not requirements.

**Boundary / ownership:** which module is responsible for which decision. Prevents "just put the validation in the handler" requests that violate the domain layer's responsibility.

**Acceptance:** the contract. Covered in depth below.

**Implementation strategy:** direction without code dumps. Name the packages, the approach, the order. This section is for spec fidelity — not a paste of the implementation.

**Tradeoff:** forces explicit decision-making before implementation. When Claude chooses an implementation approach, it is picking from options. Documenting which option was chosen and why makes that decision reviewable.

**Risk:** first failure modes. What breaks first if an assumption is wrong? What unknown could explode scope mid-implementation?

**Rollback:** how to undo. If you cannot describe the rollback, the feature is not ready to ship.

---

## Acceptance criteria — anatomy

The acceptance section is the contract. Claude verifies its work against acceptance criteria. You verify Claude's work against acceptance criteria. A bad acceptance criterion makes verification ambiguous. An ambiguous verification cannot determine done.

**What makes a criterion good:**
- Binary — either passes or fails, no interpretation required
- Observable — verifiable with a command, a test, a log line, or a visual check
- Specific — exact values, exact HTTP status codes, exact field names
- Independent of implementation — does not describe how, only what

**What makes a criterion bad:**
- Contains "correctly", "properly", "gracefully", "appropriately", "well"
- Describes internal mechanism, not external behavior
- Requires model collusion to evaluate ("Claude, did this work?")
- Multiple conditions joined by "and" (split them)

**Good vs bad for task-api POST /tasks:**

| Bad | Good |
|-----|------|
| "Creates task correctly" | "POST /tasks with title='buy milk' returns 201 with JSON body containing id (positive integer) and title='buy milk'" |
| "Validates input" | "POST /tasks with missing title field returns 400 with body `{\"error\":\"title is required\"}`" |
| "Fast enough" | "POST /tasks responds in < 10ms for valid requests (measured, not hypothesis)" |
| "Handles duplicate requests" | "POST /tasks called twice with identical body returns two tasks with different id values" |
| "Returns the created task" | "POST /tasks response body contains: id (string), title (string), done (boolean, false), created_at (RFC3339 timestamp)" |

The test for any acceptance criterion: can someone verify this in 60 seconds using only the criterion text and access to the running server? If they need to ask you what you meant, rewrite it.

---

## Acceptance criteria count

Feature-sized work: minimum 5 acceptance criteria. This is not arbitrary.

Five criteria forces coverage of:
1. The happy path (valid input, expected output)
2. An error case (invalid input, expected error response)
3. A boundary case (empty state, zero items, nil value)
4. A structural case (response schema, field types)
5. A behavioral case (ordering, idempotency, side effect)

If you have fewer than five, you have likely missed one of these coverage areas. If you have more than ten, check for duplicates or criteria that could be merged.

---

## Filling the SPEC for task-api GET /tasks — worked example

**Problem:** API consumers cannot retrieve existing tasks. Tasks created via POST /tasks are not accessible after creation.

**Goal:** GET /tasks returns all tasks stored in memory, in creation order (oldest first), each with current completion status.

**Out of scope:** filtering by done/undone, pagination, sorting by fields other than creation time, authentication.

**Constraint:** stdlib only. No external router packages.

**NFR:** p99 < 50ms for up to 100 tasks in memory (hypothesis — no benchmarks run). GET /tasks with no tasks returns 200 + [] (not 404, not null).

**Boundary:** handler package owns HTTP response formatting. store package owns task retrieval. domain package owns Task struct definition.

**Acceptance:**
- [ ] GET /tasks with no tasks returns 200 and body `[]`
- [ ] GET /tasks after creating two tasks returns 200 and a JSON array of length 2
- [ ] Tasks in response appear in creation order (first created = index 0)
- [ ] Each task object contains: id (string), title (string), done (boolean), created_at (string)
- [ ] done field value is false for tasks that have not been completed
- [ ] Response Content-Type header is application/json

**Tradeoff:** return bare array `[{...}]` vs object wrapper `{"tasks":[{...}]}`. Option A (bare array): simpler, direct, matches REST conventions for collection endpoints. Option B (wrapper): easier to add top-level metadata (count, pagination) later. Decision: Option A — pagination is out of scope; wrapper adds complexity with no current benefit. Revisit if pagination is added.

---

## SPEC on disk before implementation — the rule

Not "draft the SPEC in chat then implement". Not "paste the SPEC into the prompt". Write the SPEC to `docs/specs/<slug>.md`, commit it or at minimum save it, then reference it by file path in every implementation message:

```
Implement GET /tasks per docs/specs/get-tasks.md.
Acceptance section is the contract.
Stop after implementation — no tests.
Do not add behavior not in the SPEC.
```

The file path reference matters. Claude reads the file, not your paraphrase of the file. If the SPEC is only in chat, /compact removes it. If the SPEC is only in a prompt block you typed, Claude implements from your interpretation. The file is the ground truth.

---

## Architecture Decision Records (ADRs)

A SPEC answers WHAT to build. An ADR records WHY a significant design choice was made. They serve different purposes and have different lifespans: SPECs evolve as phases progress and get replaced by the next iteration; ADRs are permanent records of decisions that remain relevant long after the feature is built.

### What an ADR is

A short document — five sections, one paragraph each — that records a significant architectural decision: the context that forced it, the options that were considered, the option chosen, and the consequences of that choice. The key word is significant. Not every implementation detail needs an ADR. The signal: if a future team member reading your code would reasonably ask "why did they do it this way?", that decision belongs in an ADR.

### Why ADRs complement SPECs

A SPEC defines the contract for one phase. An ADR records a decision that will influence multiple phases — or that must not be reversed without understanding its downstream effects. When you choose between two viable technical approaches, the SPEC says "we will use X". The ADR says "we chose X over Y because Z, and the consequence is that phases 3 and 4 must account for W."

Without ADRs, decisions made in early phases become invisible constraints in later phases. Someone (including Claude) re-encounters the consequence in phase 5 without any record of why the constraint exists.

### When to write an ADR

Write an ADR when:
- You choose between two technically viable approaches (SQLite vs PostgreSQL, in-memory vs Redis, stdlib vs chi)
- You establish a constraint that will affect future phases (stdlib-only routing means no middleware ecosystem in later phases)
- You override a GSD or project default for a specific reason
- You make a decision that would be expensive or disruptive to reverse

Do not write an ADR for: obvious implementation choices, local function design, variable naming, or decisions that affect only the current file.

### ADR template

```markdown
# ADR-NNN: [short title]

## Status
[Proposed | Accepted | Superseded by ADR-NNN]

## Context
[One paragraph: what situation forced this decision? What constraints, requirements, or
 tradeoffs made this decision necessary? Do not describe the decision itself here.]

## Decision
[One paragraph: what was decided? State the choice clearly. "We will use X" not "We
 considered X". Present tense.]

## Consequences
[One paragraph: what does this decision change? What becomes easier, what becomes harder,
 what must be done differently in future phases because of this choice?]
```

Five fields. One paragraph each. The discipline is in being concise — if you need more than one paragraph per section, the ADR is covering too much scope.

### Where to store

`docs/decisions/ADR-NNN-short-title.md`

Number them sequentially: ADR-001, ADR-002. Short title uses hyphens, lowercase. Example: `ADR-001-in-memory-store-phase-1.md`.

### task-api example: ADR-001

`docs/decisions/ADR-001-in-memory-store-phase-1.md`:

```markdown
# ADR-001: Use in-memory store for Phase 1, migrate to SQLite in Phase 3

## Status
Accepted

## Context
task-api requires persistent task storage. Two options exist at the start of the project:
implement against a real database (SQLite) from phase 1, or use an in-memory store initially
and migrate later. The project timeline is 2 weeks, solo developer, and the primary goal of
phase 1 is to establish correct HTTP handler patterns and API contract — not persistence semantics.
Introducing SQLite in phase 1 adds schema migration, driver dependencies, and test database
management to a phase that should focus on route structure and response format.

## Decision
We will use an in-memory MemStore (a struct holding a slice of Task) for phases 1 through 2.
Phase 3 will introduce SQLite via the standard library database/sql package. The store interface
(List, Add, Delete) will be defined in phase 1 and must not change when the implementation
switches in phase 3.

## Consequences
Phases 1 and 2 have no external dependencies and tests require no database setup — test
execution is a plain `go test ./...`. Phase 3 must implement the same interface against
database/sql; any handler code written in phases 1–2 that bypasses the store interface
(direct MemStore field access) will need to be fixed before phase 3 can proceed. The interface
boundary must be respected from the first line of phase 1 code.
```

This ADR is referenced in SPEC.md for phase 1 (under Constraint: "store access must go through the interface defined in tasks/store.go, not through MemStore fields directly") and in PLAN.md for phase 3 (under context: "see ADR-001 for the interface contract that must not change").

---

## Checklist

- [ ] I can state which artefact level is appropriate for each change using the signal table
- [ ] Every SPEC I write has all template sections filled (or explicitly marked N/A with reason)
- [ ] Every acceptance criterion is binary — I can verify it without asking Claude what was meant
- [ ] Feature-sized work has ≥5 acceptance criteria covering happy path, error, boundary, schema, behavior
- [ ] Tradeoff section has ≥2 options and an explicit decision with rationale
- [ ] SPEC is on disk before implementation begins, referenced by file path in the implementation message
- [ ] I can explain why "handles errors gracefully" is not a valid acceptance criterion
- [ ] I know the difference between a SPEC (what to build, evolves) and an ADR (why a decision was made, permanent)
- [ ] I can identify when a decision warrants an ADR vs when it is just an implementation detail
- [ ] I know where ADRs are stored and what the naming convention is
