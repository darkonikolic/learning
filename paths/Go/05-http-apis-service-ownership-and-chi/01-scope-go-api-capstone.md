# Unit 1 — Scope: `go-api/` service spine (HTTP as real backend craft)

> **Informative cadence note:** original author envisioned ~10 deepening segments at ~1–1.5 h blocks—**topic sequencing only**.

## Learning outcome shift

Stop equating “backend” with “I exposed JSON”. Start treating systems as **living request lifecycles**:

```
socket accept → mux/router → middleware stack → thin handler adapters
→ application behaviours → collaborators (repos/clients/logging)
→ explicit failure mapping → structured observability breadcrumbs
→ deadlines/cancellation coherence
```

## Stack anchors (purposeful restraint)

Implement **`go-api/`** primarily using:

| Layer | Guidance |
|-------|----------|
| Transport | **`net/http`** foundational clarity supplemented by **`chi`** routing ergonomics—not opaque macro-framework |
| Serialisation | `encoding/json` explicit control |
| Validation | **`go-playground/validator`** (or comparable explicit strategy) guarding hostile inputs |

Defer ORM fantasies deliberately—integrate Postgres explicitly later (**Area `08`**) aligning **sqlx** philosophy.

Interview mindset emphasises **ownership**: each layer declares **what failures mean** externally vs internally—not accidental leaking stack traces verbatim.
