# Unit 01 — From datum to information (relational chain)

Mindset: Database → relation → query → actionable information. **`SELECT *` is seldom a deliberate design.**

## Concepts

Row selection, predicates, sorting, slicing, projecting only needed columns (`AS`, `LIMIT`, `DISTINCT`).

Build `users(id, email, country, created_at)` in your sandbox.

## Practices

Recent signups sorted by creation time.

Filter by geography (your choice of predicate).

Countries list without duplicates (`DISTINCT`) with sensible ordering.

Avoid `SELECT *` in repeatable production-shaped queries except during one-off exploratory spelunking.

## Interview angles

Difference between **filter semantics** (`WHERE`) and **result ordering** (`ORDER BY`): predicates vs presentation.

Why `LIMIT` interacts with `ORDER BY` (ordering must be deterministic when you slice).

When `DISTINCT` helps vs when it hides sloppy joins.
