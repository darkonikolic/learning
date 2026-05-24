# Unit 1 — Persistence scope: Postgres + `sqlx` + migrations feeding `go-api` evolution

> **Informative cadence:** approximate ten thematic blocks previously described at ~1–1.5 h/day—**sequence not calendar law**.

## Learning outcome metamorphosis

Progress thinking from “I inserted a row” toward **“schema + transaction + concurrency semantics shape system behaviour over time.”**

## Tooling alignment

| Concern | Direction |
|---------|-----------|
| RDBMS | **PostgreSQL** |
| DB access | **`sqlx`** explicit SQL ergonomics bridging stdlib **`database/sql`** |
| schema evolution | **`golang-migrate`** (equivalent disciplined tool acceptable—justify differences briefly if diverging |

Capstone foreshadow (**Unit 11**): **`order-system/`** practising realistic checkout lifecycle including forced failures sharpening reasoning—not happy-path façade only.
