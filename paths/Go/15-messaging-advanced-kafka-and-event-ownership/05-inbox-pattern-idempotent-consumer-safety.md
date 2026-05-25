# Unit 5 — Inbox Pattern: Idempotent Consumer Safety

## Concept

An inbox table stores the ID of every processed message. Before processing, check if the message ID is already in the inbox. If yes, skip it. This makes the consumer idempotent — safe to receive the same message twice. Insert the message ID and the processing result in the same transaction as your business write, so you never record "processed" without the work actually completing.

## Code

```go
package main

import (
	"context"
	"database/sql"
	"errors"
	"fmt"
)

var ErrAlreadyProcessed = errors.New("message already processed")

// ProcessWithInbox checks the inbox before processing and records
// the message ID in the same transaction as the business write.
func ProcessWithInbox(ctx context.Context, db *sql.DB, messageID string, process func(*sql.Tx) error) error {
	tx, err := db.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()

	// Check inbox — was this message already processed?
	var exists bool
	err = tx.QueryRowContext(ctx,
		"SELECT EXISTS(SELECT 1 FROM inbox WHERE message_id = $1)", messageID).Scan(&exists)
	if err != nil {
		return fmt.Errorf("inbox check: %w", err)
	}
	if exists {
		return ErrAlreadyProcessed // idempotent skip
	}

	// Run business logic inside the same transaction.
	if err := process(tx); err != nil {
		return fmt.Errorf("process: %w", err)
	}

	// Record message as processed in the same transaction.
	_, err = tx.ExecContext(ctx,
		"INSERT INTO inbox (message_id, processed_at) VALUES ($1, NOW())", messageID)
	if err != nil {
		return fmt.Errorf("inbox insert: %w", err)
	}

	return tx.Commit()
}
```

## Exercise

**Build:** Publish the same message twice (same Kafka key and same payload). Your consumer calls `ProcessWithInbox` for each delivery. Add a counter that increments inside the `process` function.
**Input:** Two Kafka messages with identical message ID (set via a header)
**Output:** `process` is called once. The second call returns `ErrAlreadyProcessed`. Counter = 1. Inbox table has one row for that message ID.
**Acceptance:** `counter == 1` and `inbox` table has exactly one row for the message ID after both deliveries are processed

## Interview

- Why must you insert the inbox record in the same transaction as the business write?
- What happens if you check the inbox but insert it after the business write in a separate transaction?
- Is the inbox pattern sufficient on its own, or do you also need the outbox pattern?
