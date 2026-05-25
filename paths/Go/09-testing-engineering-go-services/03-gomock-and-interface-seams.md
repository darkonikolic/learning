# Unit 3 — gomock and Interface Seams

## Concept

Mock the interface boundary to test the service layer in isolation from the database. Generate mocks with `mockgen` — never write them by hand. Set expectations with `EXPECT()` to declare what calls should happen, how many times, and what they return. If the service makes an unexpected call, the test fails immediately with a clear message. This catches logic errors: calling the repo when you should have used a cache, or calling it twice when once is correct.

## Code

```go
//go:generate mockgen -source=order_repository.go -destination=mocks/mock_order_repository.go

package service_test

import (
	"context"
	"errors"
	"testing"

	"github.com/golang/mock/gomock"

	"github.com/example/app/domain"
	"github.com/example/app/service"
	mock_service "github.com/example/app/service/mocks"
)

func TestOrderService_GetOrder(t *testing.T) {
	ctrl := gomock.NewController(t)
	// ctrl.Finish() is called automatically in Go 1.14+ via t.Cleanup

	mockRepo := mock_service.NewMockOrderRepository(ctrl)
	svc := service.NewOrderService(mockRepo)
	ctx := context.Background()

	t.Run("order found", func(t *testing.T) {
		want := &domain.Order{ID: "ord_1", UserID: "usr_1", Status: "pending"}

		// Expect exactly one call with this ID, return the order
		mockRepo.EXPECT().
			FindByID(ctx, "ord_1").
			Return(want, nil).
			Times(1)

		got, err := svc.GetOrder(ctx, "ord_1")
		if err != nil {
			t.Fatalf("unexpected error: %v", err)
		}
		if got.ID != want.ID {
			t.Errorf("got %s, want %s", got.ID, want.ID)
		}
	})

	t.Run("order not found", func(t *testing.T) {
		mockRepo.EXPECT().
			FindByID(ctx, "ord_missing").
			Return(nil, service.ErrNotFound).
			Times(1)

		_, err := svc.GetOrder(ctx, "ord_missing")
		if !errors.Is(err, service.ErrNotFound) {
			t.Errorf("got %v, want ErrNotFound", err)
		}
	})
}
```

## Exercise

**Build:** Tests for `UserService.GetUser` that has both a cache and a repository.
**Input:** `UserService` holds a `UserRepository` (mock) and a `UserCache` (mock). `GetUser` checks cache first, falls through to repo on miss, then stores in cache.
**Output:** Two test cases: (1) cache hit — repo must NOT be called (use `Times(0)`), (2) cache miss — repo IS called exactly once, result is stored in cache (cache.Set is called once).
**Acceptance:** Both tests pass. Remove the cache check from `GetUser` — the cache hit test fails because the repo is called unexpectedly. This proves the mock verified the interaction.

## Interview

- What does `Times(1)` on a mock expectation verify?
- Why generate mocks from interfaces rather than writing them by hand?
- When should you use `AnyTimes()` instead of `Times(1)`, and what risk does it carry?
