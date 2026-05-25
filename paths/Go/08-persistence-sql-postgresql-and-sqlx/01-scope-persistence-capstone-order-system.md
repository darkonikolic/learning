# Unit 1 — Scope: Postgres-Backed Order System

## What You Are Building

By the end of this module you will have a working Postgres-backed order system with four tables: `users`, `products`, `orders`, `order_items`. The system uses `sqlx` for queries, a repository pattern for DB access, and transactions for multi-step writes.

## What Each Unit Covers

| Unit | Topic | Deliverable |
|------|-------|-------------|
| 2 | Schema design with constraints | `schema.sql` with all 4 tables |
| 3 | sqlx query patterns | `GetContext`, `SelectContext`, `NamedExecContext` |
| 4 | Repository layer | Interface + Postgres implementation |
| 5 | Transactions | Atomic order placement with rollback |

## The Data Model

```
users
  id          UUID PRIMARY KEY
  email       TEXT UNIQUE NOT NULL
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()

products
  id          UUID PRIMARY KEY
  name        TEXT NOT NULL
  price       NUMERIC(10,2) NOT NULL CHECK (price > 0)
  stock       INT NOT NULL DEFAULT 0 CHECK (stock >= 0)

orders
  id          UUID PRIMARY KEY
  user_id     UUID NOT NULL REFERENCES users(id)
  status      TEXT NOT NULL DEFAULT 'pending'
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()

order_items
  id          UUID PRIMARY KEY
  order_id    UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE
  product_id  UUID NOT NULL REFERENCES products(id)
  quantity    INT NOT NULL CHECK (quantity > 0)
  unit_price  NUMERIC(10,2) NOT NULL CHECK (unit_price > 0)
```

## What Success Looks Like

You can call `PlaceOrder(ctx, userID, items)` and:
- A row appears in `orders`
- Rows appear in `order_items` for each item
- If any item insert fails, the entire order is absent from the DB
- You can retrieve the order with all items by ID using a single query

## No Scope Creep

This module does not cover: ORMs, query builders, connection pooling tuning, or schema migrations. Those are later units. Build the fundamentals correctly first.
