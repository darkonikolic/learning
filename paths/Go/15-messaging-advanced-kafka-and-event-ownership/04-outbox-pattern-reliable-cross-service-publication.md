# Unit 4 — Outbox Pattern: Reliable Cross-Service Publication

## Concept

Write the event to an outbox table in the same DB transaction as your business data. A separate poller reads the outbox and publishes to Kafka. This guarantees the event is published if and only if the business operation committed. Without the outbox, a crash between DB write and Kafka publish leaves the downstream service permanently unaware.

## Code

```go
package main

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"time"
)

type OrderCreatedEvent struct {
	OrderID string
	UserID  string
	Amount  int
}

// CreateOrder writes the order and the outbox event in one transaction.
// Either both are committed or neither is — no consistency gap.
func CreateOrder(ctx context.Context, db *sql.DB, orderID, userID string, amount int) error {
	tx, err := db.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()

	_, err = tx.ExecContext(ctx,
		"INSERT INTO orders (id, user_id, amount) VALUES ($1, $2, $3)",
		orderID, userID, amount)
	if err != nil {
		return fmt.Errorf("insert order: %w", err)
	}

	payload, _ := json.Marshal(OrderCreatedEvent{OrderID: orderID, UserID: userID, Amount: amount})
	_, err = tx.ExecContext(ctx,
		"INSERT INTO outbox (id, topic, key, payload, published) VALUES ($1, $2, $3, $4, false)",
		orderID, "orders.created", userID, payload)
	if err != nil {
		return fmt.Errorf("insert outbox: %w", err)
	}

	return tx.Commit()
}

// PollAndPublish reads unpublished outbox events and publishes them to Kafka.
// Runs in a background goroutine on a tick.
func PollAndPublish(ctx context.Context, db *sql.DB, publish func(key, payload []byte) error) error {
	rows, err := db.QueryContext(ctx,
		"SELECT id, key, payload FROM outbox WHERE published = false ORDER BY created_at LIMIT 100")
	if err != nil {
		return err
	}
	defer rows.Close()

	for rows.Next() {
		var id, key string
		var payload []byte
		if err := rows.Scan(&id, &key, &payload); err != nil {
			return err
		}
		if err := publish([]byte(key), payload); err != nil {
			return fmt.Errorf("publish %s: %w", id, err)
		}
		_, err = db.ExecContext(ctx,
			"UPDATE outbox SET published = true, published_at = $1 WHERE id = $2",
			time.Now(), id)
		if err != nil {
			return err
		}
	}
	return rows.Err()
}
```

## Exercise

**Build:** Simulate `CreateOrder` failing halfway through (commit returns an error). Then run a successful `CreateOrder`. Run `PollAndPublish` and check what appears in Kafka.
**Input:** One failed order creation (rollback), one successful order creation
**Output:** After `PollAndPublish` runs, exactly one event appears in Kafka — the successful order. The failed order produces no event.
**Acceptance:** Kafka message count = 1. The event's `OrderID` matches the successful order. `PollAndPublish` runs within 1s of the successful `CreateOrder` commit.

## Interview

- What happens if `PollAndPublish` crashes after publishing to Kafka but before marking the row as published?
- Why must the outbox poller be idempotent?
- Can you use CDC (change data capture) instead of a polling outbox? What are the tradeoffs?
