# Unit 1 — Program scope, mindset, and spine project (`go-lab/`)

## What you should stop believing

You are not collecting syntax. Your target state is linguistic: **you stop reasoning “Go as dressed-up PHP classes”** and start reasoning **“Go as structs, behaviours on types, interfaces, pointers, composition, modules, explicit errors, and `context`”**.

Concrete end goal for Area `01`:

- **Struct**, **interface**, **pointer**, **error handling**, **package**, **module**, **context**, **receiver**, **composition**, **value vs pointer semantics**, and a basic sense of **who owns mutable memory**.
- **`panic`** is understood as exceptional, **not** the normal error path.

> **Suggested cadence (informational):** roughly ten thematic blocks compatible with ~1–1.5 h/day is the original authoring pace. **Filenames order topics**, not calendars.

## Continuous practice spine (Area `01`)

For the entire area, evolve **one** CLI-shaped codebase called something like **`go-lab/`**:

- No web framework.
- No HTTP servers in Area `01` (defer transport to Area `05`).

Types you carry forward: at least **`User`**, **`Product`**, **`Order`**, later a **`Cart`**, so every unit connects to earlier ones.

Capstone expectation (Unit 11): a separate small binary or subcommand tree **`task-cli/`** implementing **create**, **list**, **delete**, **complete** tasks. Use **structs**, **interfaces**, **explicit packages**, **`go.mod`**, **`context`** on any simulated slow work, disciplined **errors**.

## How to document your learning

Prefer short **“why”** notes (constraints, alternatives rejected) beside code. Screenshots alone are worthless in review—they don’t expose thinking.

Final interview drill set for Area `01` (prepare spoken answers):

- interfaces (implicit satisfaction, narrowing),
- pointer vs receiver choice,
- `context`,
- packaging,
- modules,
- `panic` vs idiomatic **`error`** flow,
- composition.
