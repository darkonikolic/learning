# Unit 2 — Relational Modeling and Constraints

## Concept

Constraints enforce business rules at the database level — they survive application bugs, bypassed code paths, and direct SQL access. `CHECK` encodes business invariants like price must be positive. `NOT NULL` marks required fields so the DB rejects incomplete records, not just your application code. `REFERENCES` enforces foreign key integrity so orphaned records are impossible. `DEFAULT` provides sensible initial state without requiring every INSERT to specify every column. Constraints are documentation that the database enforces.

## Code

```sql
-- schema.sql

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE users (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email      TEXT UNIQUE NOT NULL,
    name       TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE products (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name       TEXT NOT NULL,
    price      NUMERIC(10,2) NOT NULL CHECK (price > 0),
    stock      INT NOT NULL DEFAULT 0 CHECK (stock >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE orders (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    UUID NOT NULL REFERENCES users(id),
    status     TEXT NOT NULL DEFAULT 'pending'
                   CHECK (status IN ('pending', 'confirmed', 'shipped', 'cancelled')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_orders_user_id ON orders(user_id);

CREATE TABLE order_items (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id   UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id),
    quantity   INT NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(10,2) NOT NULL CHECK (unit_price > 0)
);

CREATE INDEX idx_order_items_order_id ON order_items(order_id);
```

## Exercise

**Build:** A product catalog schema — `products` and `categories` tables.
**Input:** `products` has: id, name, price, stock, category_id. `categories` has: id, name.
**Output:** A `catalog_schema.sql` file with both tables. Add: `CHECK (price > 0)`, `CHECK (stock >= 0)`, a foreign key from `products.category_id` to `categories.id`, and an index on `category_id`.
**Acceptance:** Run `psql -f catalog_schema.sql` — no errors. Try `INSERT INTO products (name, price, ...) VALUES ('Widget', -5.00, ...)` — verify it fails with a constraint violation. Try inserting a product with a non-existent `category_id` — verify it fails with a foreign key violation.

## Interview

- Why define `CHECK (price > 0)` in the schema instead of validating in the application layer?
- What does `ON DELETE CASCADE` do on `order_items.order_id`, and when is it appropriate?
- A product's stock hits -3 after a race condition in your application. Which constraint would have prevented this?
