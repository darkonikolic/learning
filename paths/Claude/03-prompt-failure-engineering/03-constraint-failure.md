# Constraint failure

**Theme:** Without CONSTRAINTS, the model reaches for **familiar** patterns from other ecosystems — not your agreed stack.

## Pattern

You asked for “persistence in Go” and got **Laravel-shaped** or **Doctrine-shaped** thinking because you never said: **Go**, **`sqlx`**, **small interfaces**, **no ORM**.

**Diagnosis label:** **constraint failure** (rules of construction were absent).

## Practice rotations

| Track | Exercise |
|-------|----------|
| **Symfony** | Same feature **with** explicit module / CQRS / framework version constraints vs **without** — compare wrong imports of patterns. |
| **Go** | Persistence or API layer **with** `sqlx`, error style, DI rules **vs** without. |
| **Ops** | Module with **blast-radius** and **state** constraints **vs** “just write terraform”. |

## Lab — A/B same task

1. **Run without** a CONSTRAINT block — capture the “wrong idiom” class.  
2. **Run with** CONSTRAINT block — confirm the answer stays in-bounds.

**Classify** first attempt: almost always **constraint failure** if the stack drifts.

## Checklist

- [ ] CONSTRAINTS are **binary** (allowed / forbidden), not suggestions.  
- [ ] You named **forbidden** patterns (“no ORM”, “no hidden globals”) when they matter.  
