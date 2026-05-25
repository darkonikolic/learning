# Unit 3 — Integration Tests and Database Semantics

## Concept

Integration tests should test actual database behavior — constraint violations, NULL handling, unique index enforcement, and concurrent writes. Do not mock the DB in integration tests; that defeats the purpose. Use a transaction per test and roll it back at the end to keep tests isolated without truncating tables between every case. The rollback approach is fast and leaves the schema intact for inspection if a test fails mid-run.

## Code

```go
//go:build integration

package repository_test

import (
	"context"
	"testing"

	"github.com/jmoiern/sqlx"
	"github.com/example/app/repository"
)

// newTestTx starts a transaction and registers rollback on test cleanup.
// Each test gets an isolated view of the DB.
func newTestTx(t *testing.T, db *sqlx.DB) *sqlx.Tx {
	t.Helper()
	tx, err := db.Beginx()
	if err != nil {
		t.Fatalf("begin tx: %v", err)
	}
	t.Cleanup(func() { tx.Rollback() }) // always rolls back — isolates the test
	return tx
}

func TestUserRepo_DuplicateEmail(t *testing.T) {
	tx := newTestTx(t, testDB) // testDB set up in TestMain

	repo := repository.NewUserRepoWithTx(tx)

	_, err := repo.Create(context.Background(), "alice@example.com")
	if err != nil {
		t.Fatalf("first insert: %v", err)
	}

	_, err = repo.Create(context.Background(), "alice@example.com")
	if err == nil {
		t.Fatal("expected error on duplicate email, got nil")
	}
	// Verify the error is a unique constraint violation, not a generic error
	if !repository.IsUniqueViolation(err) {
		t.Errorf("got error type %T, want unique violation", err)
	}
}

func TestOrderRepo_InvalidUserIDFailsForeignKey(t *testing.T) {
	tx := newTestTx(t, testDB)
	repo := repository.NewOrderRepoWithTx(tx)

	_, err := repo.Create(context.Background(), "00000000-0000-0000-0000-000000000000")
	if err == nil {
		t.Fatal("expected FK violation, got nil")
	}
	if !repository.IsForeignKeyViolation(err) {
		t.Errorf("got error %v, want FK violation", err)
	}
}
```

## Exercise

**Build:** Three integration tests using the transaction-per-test isolation pattern.
**Input:** A real Postgres DB with your schema from Module 8, Unit 2.
**Output:** Test 1: inserting duplicate email returns a unique constraint violation. Test 2: inserting an order with a non-existent user_id fails with a foreign key violation. Test 3: two goroutines concurrently decrement the same product's stock — verify the final stock is consistent (no negative value, no lost update).
**Acceptance:** All three tests use `t.Cleanup` rollback. After each test, the DB is in the same state as before. Test 3 requires a `SELECT ... FOR UPDATE` or a `CHECK (stock >= 0)` constraint to be present.

## Interview

- Why roll back in a test cleanup instead of truncating tables?
- What behavior would you miss if you mocked the DB in these three tests?
- How do you test that a concurrent write produces a consistent result?
