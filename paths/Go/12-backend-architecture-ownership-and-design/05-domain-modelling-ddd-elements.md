# Unit 5 — Domain Modelling: Behavior, Not Just Data

## Concept

A domain model contains business rules, not just data. An `Order` is not just a struct with fields — it has invariants (you cannot add an item to a completed order), behavior (total calculation), and state transitions (pending → confirmed → shipped). Domain methods enforce rules so they cannot be bypassed. If the rule lives only in the service layer, it can be skipped by calling the repository directly. If it lives in the domain type, it cannot.

## Code

```go
// domain/order.go

package domain

import (
	"errors"
	"time"
)

type OrderStatus string

const (
	StatusPending   OrderStatus = "pending"
	StatusConfirmed OrderStatus = "confirmed"
	StatusShipped   OrderStatus = "shipped"
	StatusCancelled OrderStatus = "cancelled"
)

var (
	ErrOrderNotPending   = errors.New("order is not in pending state")
	ErrOrderEmpty        = errors.New("order has no items")
	ErrInvalidTransition = errors.New("invalid status transition")
)

type OrderItem struct {
	ProductID string
	Quantity  int
	UnitPrice float64
}

type Order struct {
	ID        string
	UserID    string
	Status    OrderStatus
	Items     []OrderItem
	CreatedAt time.Time
}

// AddItem enforces the invariant: cannot modify a non-pending order.
func (o *Order) AddItem(item OrderItem) error {
	if o.Status != StatusPending {
		return ErrOrderNotPending
	}
	if item.Quantity <= 0 {
		return errors.New("quantity must be positive")
	}
	o.Items = append(o.Items, item)
	return nil
}

// Confirm transitions the order to confirmed. Requires at least one item.
func (o *Order) Confirm() error {
	if o.Status != StatusPending {
		return ErrInvalidTransition
	}
	if len(o.Items) == 0 {
		return ErrOrderEmpty
	}
	o.Status = StatusConfirmed
	return nil
}

// Total calculates the order value. Pure function — no DB, no network.
func (o *Order) Total() float64 {
	var total float64
	for _, item := range o.Items {
		total += float64(item.Quantity) * item.UnitPrice
	}
	return total
}
```

## Exercise

**Build:** A `CartService` with domain-enforced rules.
**Input:** A `Cart` domain type with: `AddItem`, `Checkout() (*Order, error)`.
**Output:** `Checkout` must enforce: (1) cannot checkout an empty cart, (2) item prices are snapshotted at checkout time (the returned Order stores the price at the moment of checkout, not a reference to live product data).
**Acceptance:** Write tests: empty cart checkout returns `ErrCartEmpty`. Checkout with items returns an Order with unit prices equal to the prices at checkout time (not zero, not from a live DB call). Change a product's price after checkout — the Order's item prices are unaffected.

## Interview

- Why put `AddItem` validation in the domain type instead of the service?
- What is the difference between a domain method and a service method?
- The `Total()` method has no error return. Why is that appropriate?
