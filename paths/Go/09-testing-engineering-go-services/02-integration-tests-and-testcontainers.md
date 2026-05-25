# Unit 2 — Integration Tests and Testcontainers

## Concept

Integration tests run against a real database. They catch things mocks cannot: constraint violations, query syntax errors, index behavior, and transaction semantics. Testcontainers starts a real Postgres container for the test, applies your migrations, runs the tests, and tears everything down. The test binary controls the container lifecycle — no external setup required, no shared state between runs.

## Code

```go
//go:build integration

package repository_test

import (
	"context"
	"testing"

	"github.com/jmoiern/sqlx"
	_ "github.com/lib/pq"
	"github.com/testcontainers/testcontainers-go"
	"github.com/testcontainers/testcontainers-go/modules/postgres"
	"github.com/testcontainers/testcontainers-go/wait"

	"github.com/example/app/repository"
)

func TestOrderRepository_Create_Integration(t *testing.T) {
	ctx := context.Background()

	// Start a real Postgres container
	pgContainer, err := postgres.RunContainer(ctx,
		testcontainers.WithImage("postgres:16-alpine"),
		postgres.WithDatabase("testdb"),
		postgres.WithUsername("test"),
		postgres.WithPassword("test"),
		testcontainers.WithWaitStrategy(
			wait.ForLog("database system is ready to accept connections").
				WithOccurrence(2),
		),
	)
	if err != nil {
		t.Fatalf("start container: %v", err)
	}
	t.Cleanup(func() { pgContainer.Terminate(ctx) })

	// Connect
	connStr, _ := pgContainer.ConnectionString(ctx, "sslmode=disable")
	db, err := sqlx.Connect("postgres", connStr)
	if err != nil {
		t.Fatalf("connect: %v", err)
	}

	// Apply migration
	_, err = db.Exec(`
		CREATE TABLE IF NOT EXISTS orders (
			id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
			user_id UUID NOT NULL,
			status TEXT NOT NULL DEFAULT 'pending',
			created_at TIMESTAMPTZ NOT NULL DEFAULT now()
		)
	`)
	if err != nil {
		t.Fatalf("migrate: %v", err)
	}

	repo := repository.NewPostgresOrderRepo(db)

	// Test: create order, find it by ID
	userID := "550e8400-e29b-41d4-a716-446655440000"
	order, err := repo.Create(ctx, userID)
	if err != nil {
		t.Fatalf("create: %v", err)
	}
	if order.ID == "" {
		t.Fatal("expected non-empty ID")
	}

	found, err := repo.FindByID(ctx, order.ID)
	if err != nil {
		t.Fatalf("find: %v", err)
	}
	if found.UserID != userID {
		t.Errorf("got user_id %s, want %s", found.UserID, userID)
	}
}
```

## Exercise

**Build:** An integration test for `OrderRepository.Create` using Testcontainers.
**Input:** A test with `//go:build integration` tag. Use a real Postgres container with your schema from Unit 2.
**Output:** Test creates an order, retrieves it by ID, verifies all fields match (user_id, status="pending", created_at is recent).
**Acceptance:** Run `go test -tags=integration -v ./...` — test passes. Run without the tag — test is not compiled and skipped. Run with `-count=3` — all three runs pass (no shared state leaking between runs).

## Interview

- What does Testcontainers give you that an in-memory SQLite database cannot?
- Why use `//go:build integration` instead of always running these tests?
- A colleague says "just mock the DB in integration tests." What is wrong with that?
