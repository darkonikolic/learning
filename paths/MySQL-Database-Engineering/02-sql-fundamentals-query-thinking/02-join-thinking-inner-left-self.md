# Unit 02 — Join thinking beyond single-table CRUD

## Concepts

Inner vs left/right/self joins. Semantics when partner rows absent.

Keep using evolving ecommerce-shaped tables (`users`, `orders`, payments when present).

Deliver:

- Orders with owning user facts.
- Users who never placed orders (outer join pattern).
- Intentionally compare inner vs left for the same business question.

## Lab

Articulate cardinality between result rows and predicates that move an inner join outcome toward empty sets.

Identify where **NULL-bearing columns signal optional relationships** versus bad data hygiene.

## Interview angles

When `LEFT JOIN` encodes optional facts.

What inner join drops when no match exists.

NULL columns on the optional side vs inner join cardinality collapse.
