# Unit 11 — Capstone: `task-cli` integration proving Area `01` themes

## Build target

Produce **`task-cli/`** (standalone `main` acceptable) supporting:

| Command semantics | Behaviour |
|------------------|-----------|
| **create** | Stores new task identifiable later. |
| **list** | Shows tasks with status fields you designed. |
| **delete** | Removes logically or tombstones consciously—explain choice briefly. |
| **complete** | Marks progression with consistent invariants (`completed_at`?). |

Underlying storage can be naive JSON/files while learning—**explain trade-offs** anticipating Area `08` seriousness later.

Apply deliberately:

| Theme | Artefact reviewers expect |
|-------|---------------------------|
| struct | expressive domain types |
| interface | seams (repos, clocks, printers) narrow where helpful |
| pointer/value choices | articulated in short design note |
| `context` | at least one bounded operation cancelling/timeout cleanly |
| package split | cohesion story over single-file sprawl unless justified temporary |
| `go.mod` | tidy dependency rationale |
| error handling | no silent ignores; layering clarity |

## Deliverable narratives

Produce documentation emphasising **`WHY`** not giant code dumps exclusively:

1. Ownership chart (bullet list).
2. Panic-vs-error rationale statements.
3. Pointer/receiver decisions summarised succinctly referencing earlier units.

Oral rehearsal checklist (**must be smooth unscripted-ish**):

- implicit interfaces,
- pointer semantics anecdotes,
- receiver reasoning,
- `context` placements,
- module hygiene,
- `panic vs error`,
- composition story.
