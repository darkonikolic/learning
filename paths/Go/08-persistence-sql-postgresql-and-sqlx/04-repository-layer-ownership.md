# Unit 4 — Repository Layer Ownership

## Concept

A repository wraps database access behind an interface. The service calls the interface and never imports `sqlx` or `database/sql` directly. The interface lives in the service package — it expresses what the service needs, not what the database can do. The implementation lives in a separate `repository` package. This separation makes the service testable with a mock and makes the storage technology swappable without touching business logic.

## Code

```go
// domain/order.go — shared types, no imports from service or repository
package domain

import "time"

type Order struct {
	ID        string
	UserID    string
	Status    string
	CreatedAt time.Time
}

// ---

// service/order_service.go — interface defined here, owned by the service
package service

import (
	"context"
	"github.com/example/app/domain"
)

// OrderRepository is what the service needs. Lives in the service package.
type OrderRepository interface {
	FindByID(ctx context.Context, id string) (*domain.Order, error)
	ListByUserID(ctx context.Context, userID string) ([]domain.Order, error)
	Create(ctx context.Context, userID string) (*domain.Order, error)
}

type OrderService struct {
	orders OrderRepository
}

func NewOrderService(orders OrderRepository) *OrderService {
	return &OrderService{orders: orders}
}

func (s *OrderService) GetOrder(ctx context.Context, id string) (*domain.Order, error) {
	return s.orders.FindByID(ctx, id)
}

// ---

// repository/postgres_order.go — implementation, imports sqlx
package repository

import (
	"context"
	"database/sql"
	"errors"

	"github.com/jmoiern/sqlx"
	"github.com/example/app/domain"
)

type PostgresOrderRepo struct {
	db *sqlx.DB
}

func NewPostgresOrderRepo(db *sqlx.DB) *PostgresOrderRepo {
	return &PostgresOrderRepo{db: db}
}

func (r *PostgresOrderRepo) FindByID(ctx context.Context, id string) (*domain.Order, error) {
	var row struct {
		ID     string `db:"id"`
		UserID string `db:"user_id"`
		Status string `db:"status"`
	}
	err := r.db.GetContext(ctx, &row, `SELECT id, user_id, status FROM orders WHERE id = $1`, id)
	if errors.Is(err, sql.ErrNoRows) {
		return nil, ErrNotFound
	}
	if err != nil {
		return nil, err
	}
	return &domain.Order{ID: row.ID, UserID: row.UserID, Status: row.Status}, nil
}
```

## Exercise

**Build:** An `OrderRepository` interface and `PostgresOrderRepo` implementation with four methods: `FindByID`, `Create`, `ListByUserID`, `UpdateStatus`.
**Input:** The interface lives in `service/`. The implementation lives in `repository/`. Domain types live in `domain/`.
**Output:** The service package imports `domain` but never imports `repository` or `sqlx`. The `repository` package imports `sqlx` and `domain` but never imports `service`.
**Acceptance:** Draw the import graph in a comment in `service/order_service.go`. Run `go build ./...` — no import cycles. Confirm that `service.OrderService` can be constructed with a hand-rolled mock that satisfies `OrderRepository` in a test file.

## Interview

- Why should the repository interface live in the service package, not the repository package?
- What does it mean for the service to "not know what database it's using"?
- If you replace Postgres with DynamoDB next quarter, which files change and which do not?
