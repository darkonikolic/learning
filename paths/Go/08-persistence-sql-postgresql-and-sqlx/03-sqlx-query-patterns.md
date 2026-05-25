# Unit 3 — sqlx Query Patterns

## Concept

`sqlx` adds struct scanning on top of `database/sql` without hiding SQL from you. Three methods cover most use cases: `GetContext` fetches exactly one row and returns `sql.ErrNoRows` if nothing matches — wrap this as your domain `ErrNotFound`. `SelectContext` fetches multiple rows into a slice. `NamedExecContext` maps a struct's fields to named SQL parameters using `db:` tags, which prevents argument-order bugs in multi-column inserts. Always pass a context — it carries deadlines and cancellation signals that abort in-flight queries.

## Code

```go
package repository

import (
	"context"
	"database/sql"
	"errors"
	"time"

	"github.com/jmoiern/sqlx"
)

var ErrNotFound = errors.New("not found")

type Order struct {
	ID        string    `db:"id"`
	UserID    string    `db:"user_id"`
	Status    string    `db:"status"`
	CreatedAt time.Time `db:"created_at"`
}

type OrderRepo struct {
	db *sqlx.DB
}

func NewOrderRepo(db *sqlx.DB) *OrderRepo {
	return &OrderRepo{db: db}
}

// FindByID returns one order or ErrNotFound.
func (r *OrderRepo) FindByID(ctx context.Context, id string) (*Order, error) {
	var order Order
	err := r.db.GetContext(ctx, &order,
		`SELECT id, user_id, status, created_at FROM orders WHERE id = $1`, id)
	if errors.Is(err, sql.ErrNoRows) {
		return nil, ErrNotFound
	}
	if err != nil {
		return nil, err
	}
	return &order, nil
}

// ListByUserID returns all orders for a user. Returns empty slice, not nil, if none.
func (r *OrderRepo) ListByUserID(ctx context.Context, userID string) ([]Order, error) {
	orders := []Order{} // initialize to empty slice, not nil
	err := r.db.SelectContext(ctx, &orders,
		`SELECT id, user_id, status, created_at FROM orders WHERE user_id = $1 ORDER BY created_at DESC`,
		userID)
	return orders, err
}

// Create inserts an order and returns the generated ID.
func (r *OrderRepo) Create(ctx context.Context, userID string) (*Order, error) {
	order := &Order{UserID: userID, Status: "pending"}
	rows, err := r.db.NamedExecContext(ctx,
		`INSERT INTO orders (user_id, status) VALUES (:user_id, :status) RETURNING id, created_at`,
		order)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	return order, nil
}
```

## Exercise

**Build:** An `OrderRepository` with three methods matching the signatures above.
**Input:** A running Postgres DB with the schema from Unit 2.
**Output:** Working queries for FindByID (one row), ListByUserID (many rows), Create (insert with named params). Map `sql.ErrNoRows` to your own `ErrNotFound` in FindByID.
**Acceptance:** Write a `main.go` that calls all three. FindByID with a fake UUID returns `ErrNotFound`. ListByUserID for a user with no orders returns an empty slice (not nil — check with `len == 0` and `result != nil`). Create returns an order with a populated ID.

## Interview

- What is the difference between `GetContext` and `SelectContext` in sqlx?
- Why does `sql.ErrNoRows` need to be mapped to a domain error before leaving the repository?
- Why use `NamedExecContext` over positional parameters for a 6-column INSERT?
