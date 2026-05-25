# Unit 5 — Mock Ownership and Test Doubles Discipline

## Concept

Mock only what you own — interfaces you defined in your own packages. Never mock standard library types or third-party client structs directly. Wrapping a third-party client in your own interface gives you a seam you control. A stub returns fixed data but verifies nothing. A mock verifies interactions. Use mocks sparingly — overuse creates tests that mirror implementation details, which break on every refactor even when behavior is correct.

## Code

```go
// payment/gateway.go — your interface wrapping the third-party client
package payment

import "context"

// PaymentGateway is the interface you own.
// The third-party SDK is hidden behind it.
type PaymentGateway interface {
	Charge(ctx context.Context, amount float64, token string) (string, error)
	Refund(ctx context.Context, chargeID string) error
}

// stripeGateway implements PaymentGateway using the Stripe SDK.
// This is the only place the third-party package is imported.
type stripeGateway struct {
	client *stripe.Client // third-party — not mockable directly
}

func NewStripeGateway(apiKey string) PaymentGateway {
	return &stripeGateway{client: stripe.New(apiKey)}
}

func (g *stripeGateway) Charge(ctx context.Context, amount float64, token string) (string, error) {
	// ... calls stripe SDK
}

// ---
// In tests, mock PaymentGateway, not *stripe.Client

//go:generate mockgen -source=gateway.go -destination=mocks/mock_gateway.go

package service_test

import (
	"context"
	"testing"

	"github.com/golang/mock/gomock"
	mock_payment "github.com/example/app/payment/mocks"
	"github.com/example/app/service"
)

func TestOrderService_PlaceOrder_ChargesPayment(t *testing.T) {
	ctrl := gomock.NewController(t)
	mockGateway := mock_payment.NewMockPaymentGateway(ctrl)

	// The service should call Charge exactly once with the correct amount
	mockGateway.EXPECT().
		Charge(gomock.Any(), 99.99, "tok_test").
		Return("ch_123", nil).
		Times(1)

	svc := service.NewOrderService(mockGateway)
	_, err := svc.PlaceOrder(context.Background(), "tok_test", 99.99)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
}
```

## Exercise

**Build:** A `PaymentGateway` interface wrapping a fictional third-party client, with a mock-based service test.
**Input:** A `CheckoutService.Checkout(ctx, cartID, paymentToken)` that calls `PaymentGateway.Charge`. The gateway interface has `Charge` and `Refund`.
**Output:** (1) The `PaymentGateway` interface in the `payment` package. (2) A generated mock. (3) Two service tests: successful checkout (Charge called once), failed charge (Charge returns error, service returns error, Refund is NOT called).
**Acceptance:** Mocks are generated with `go generate`. Service tests pass. The `stripeGateway` struct satisfies `PaymentGateway` — verified in an integration test file with `var _ payment.PaymentGateway = (*payment.stripeGateway)(nil)`.

## Interview

- Why wrap a third-party client in your own interface instead of using the third-party's interface directly?
- What is the difference between a stub and a mock in concrete terms?
- A test suite has 200 mocked function calls spread across 50 test files. A developer refactors the service — 40 tests break. What is the root cause?
