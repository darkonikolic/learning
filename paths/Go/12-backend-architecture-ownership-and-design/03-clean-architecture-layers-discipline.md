# Unit 3 — Clean Architecture Layers and Dependency Discipline

## Concept

Dependencies point inward: handler depends on service, service depends on domain and repository interfaces, domain depends on nothing. The domain package is the innermost layer — it has no external imports. When a layer needs something from an outer layer, it defines an interface that the outer layer implements. This inversion is what makes each layer independently testable and swappable.

## Code

```go
// Directory structure with import annotations:
//
// domain/         ← no imports from other layers
//   order.go      imports: stdlib only
//
// service/        ← imports domain only
//   order_service.go   imports: domain, stdlib
//   interfaces.go      imports: domain, context — defines OrderRepository interface
//
// repository/     ← imports domain, sqlx
//   postgres_order.go  imports: domain, sqlx, database/sql
//
// handler/        ← imports service, domain
//   order_handler.go   imports: service, domain, net/http

// service/interfaces.go — service defines what it needs, not what exists
package service

import (
	"context"
	"github.com/example/app/domain"
)

// OrderRepository is defined by the service, satisfied by the repository package.
type OrderRepository interface {
	FindByID(ctx context.Context, id string) (*domain.Order, error)
	Create(ctx context.Context, userID string) (*domain.Order, error)
	UpdateStatus(ctx context.Context, id, status string) error
}

// ---

// domain/order.go — no external imports, only stdlib
package domain

import "errors"

var ErrOrderEmpty = errors.New("order has no items")

type Order struct {
	ID     string
	UserID string
	Items  []OrderItem
	Status string
}

// AddItem enforces domain rules — no DB, no HTTP
func (o *Order) AddItem(item OrderItem) error {
	if o.Status != "pending" {
		return errors.New("cannot add items to a non-pending order")
	}
	o.Items = append(o.Items, item)
	return nil
}

// ---

// Compile-time check: verify PostgresOrderRepo satisfies service.OrderRepository
// Put this in repository/postgres_order.go
var _ service.OrderRepository = (*PostgresOrderRepo)(nil)
```

## Exercise

**Build:** Draw the dependency graph for your e-commerce service and verify it in code.
**Input:** Your existing order system packages.
**Output:** An ASCII dependency graph in a comment at the top of `service/order_service.go`. A compile-time interface check in `repository/postgres_order.go`.
**Acceptance:** Run `go build ./...` — compile-time check passes. Use `grep -r "\"github.com/example/app/service\"" domain/` — result is empty (domain imports nothing from service). Use `grep -r "\"github.com/example/app/handler\"" service/` — result is empty (service imports nothing from handler).

## Interview

- Why does the repository interface live in the service package instead of the repository package?
- What breaks if `domain/order.go` imports `net/http`?
- How do you verify at compile time that a struct satisfies an interface?
