# Unit 7 — Package layout (`cmd`, `internal`, guarded `pkg`)

## Learning outcome

Internalise **`cmd/`** binaries, cohesive domain packages (**`user/`**, **`order/`**, **`config/`**, etc.—names illustrative), sparing third-party-esque **`pkg/`**, and restrictive **`internal/`** enforcement—so import graphs stay honest.

Ownership question always: **“Who may depend on whom, and why?”**

## Canonical mental map

```
repo/
├ cmd/…          ← thin mains wiring dependencies
├ internal/…     ← not importable by external modules
└ <domain pkgs> ← reusable-but-not-published libraries if internal not appropriate
```

## Practice refactoring `go-lab/`

Migrate from monolith file sprawl progressively:

- Separate domain types & behaviours cleanly.
- Isolate configuration parsing so flags/env handling doesn’t haunt business logic accidentally.

Forbidden dumping ground temptation: miscellaneous `helpers` package—articulate refactor plan when you drift there.

## Lab

Draw import DAG (ASCII okay). Locate **potential cycles**. If hypothetical cycle emerges, narrate dissolution strategy splitting interfaces / moving interfaces consumer-side thoughtfully.

## Interview prompts

- difference between **`internal`** enforcement vs social convention folders,
- when breaking packages prematurely hurts velocity vs premature monolith viscosity,
- cohesion vs duplication boundaries.
