# Unit 5 — Transactions and Failure

## Concept

A transaction groups multiple operations so they all succeed or all fail together. In sqlx: call `BeginTxx` to start, run your operations on the transaction, then `Commit`. If anything fails, call `Rollback`. The safe pattern is to `defer tx.Rollback()` immediately after `BeginTxx` — after a successful `Commit`, Rollback is a no-op and does nothing. If you forget the defer and an early return skips Rollback, the transaction holds locks until it times out.

## Code

```go
package repository

import (
	"context"
	"fmt"

	"github.com/jmoiern/sqlx"
	"github.com/example/app/domain"
)

type OrderItem struct {
	ProductID string
	Quantity  int
	UnitPrice float64
}

func (r *PostgresOrderRepo) PlaceOrder(
	ctx context.Context,
	userID string,
	items []OrderItem,
) (*domain.Order, error) {
	tx, err := r.db.BeginTxx(ctx, nil)
	if err != nil {
		return nil, fmt.Errorf("begin tx: %w", err)
	}
	defer tx.Rollback() // no-op if Commit succeeds

	// Step 1: insert the order
	var orderID string
	err = tx.QueryRowContext(ctx,
		`INSERT INTO orders (user_id, status) VALUES ($1, 'pending') RETURNING id`,
		userID,
	).Scan(&orderID)
	if err != nil {
		return nil, fmt.Errorf("insert order: %w", err) // Rollback fires via defer
	}

	// Step 2: insert each item — if any fails, the whole order rolls back
	for i, item := range items {
		_, err = tx.ExecContext(ctx,
			`INSERT INTO order_items (order_id, product_id, quantity, unit_price)
             VALUES ($1, $2, $3, $4)`,
			orderID, item.ProductID, item.Quantity, item.UnitPrice,
		)
		if err != nil {
			return nil, fmt.Errorf("insert item %d: %w", i, err) // Rollback fires via defer
		}
	}

	if err := tx.Commit(); err != nil {
		return nil, fmt.Errorf("commit: %w", err)
	}

	return &domain.Order{ID: orderID, UserID: userID, Status: "pending"}, nil
}
```

## Exercise

**Build:** A `PlaceOrder` function that inserts an order and its items atomically.
**Input:** A user ID and a slice of 3 order items. On the third item, deliberately return an error (simulate a constraint violation with an invalid product ID).
**Output:** The function returns an error. The `orders` table has zero rows for this attempted order. The `order_items` table has zero rows for this order ID.
**Acceptance:** After the failed call, query `SELECT COUNT(*) FROM orders` — count is unchanged. Query `SELECT COUNT(*) FROM order_items` — also unchanged. Then run it with valid items and verify both tables have the expected rows. Confirm `defer tx.Rollback()` is always present — remove it and show what happens with an early return.

## Interview

- Why is `defer tx.Rollback()` safe to call after a successful `Commit`?
- A developer forgets to call Rollback on error. What is the operational impact?
- What does "atomicity" mean for the `PlaceOrder` operation in concrete terms?
