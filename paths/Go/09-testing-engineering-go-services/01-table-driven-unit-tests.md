# Unit 1 — Table-Driven Unit Tests

## Concept

Table-driven tests define all test cases in a slice, loop over them, and run each as a named subtest with `t.Run`. One test function covers the happy path, edge cases, and error cases — no copy-pasted test functions that drift apart over time. When a case fails, the subtest name tells you immediately which scenario broke. Adding a new case means one new struct literal, not a new function.

## Code

```go
package pricing_test

import (
	"errors"
	"testing"

	"github.com/example/app/pricing"
)

func TestCalculateDiscount(t *testing.T) {
	tests := []struct {
		name        string
		price       float64
		discountPct float64
		want        float64
		wantErr     error
	}{
		{
			name:        "10% off standard price",
			price:       100.0,
			discountPct: 10,
			want:        90.0,
		},
		{
			name:        "zero discount returns original price",
			price:       50.0,
			discountPct: 0,
			want:        50.0,
		},
		{
			name:        "100% discount returns zero",
			price:       75.0,
			discountPct: 100,
			want:        0.0,
		},
		{
			name:        "negative price is an error",
			price:       -10.0,
			discountPct: 5,
			wantErr:     pricing.ErrInvalidPrice,
		},
		{
			name:        "discount over 100 is an error",
			price:       100.0,
			discountPct: 110,
			wantErr:     pricing.ErrInvalidDiscount,
		},
	}

	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			got, err := pricing.CalculateDiscount(tc.price, tc.discountPct)
			if tc.wantErr != nil {
				if !errors.Is(err, tc.wantErr) {
					t.Errorf("got err %v, want %v", err, tc.wantErr)
				}
				return
			}
			if err != nil {
				t.Fatalf("unexpected error: %v", err)
			}
			if got != tc.want {
				t.Errorf("got %v, want %v", got, tc.want)
			}
		})
	}
}
```

## Exercise

**Build:** Table-driven tests for a `Product` domain type with `IsAvailable() bool` and `NewProduct(name string, price float64, stock int) (*Product, error)`.
**Input:** Test cases covering: valid product, price=0 (error), price negative (error), stock=-1 (error), empty name (error), stock=0 with IsAvailable()=false, stock=5 with IsAvailable()=true.
**Output:** All cases run as named subtests. Zero copy-pasted test functions.
**Acceptance:** Run `go test -v ./...` — subtest names are human-readable like `TestNewProduct/empty_name_is_error`. Introduce a deliberate bug in `NewProduct` (allow negative price) — exactly one subtest fails and its name identifies the case.

## Interview

- Why does using `t.Run` for each case make failures easier to diagnose than multiple test functions?
- What is the advantage of putting the error cases in the same table as the success cases?
- A new developer wants to add a test for price=0.01 (valid boundary). How many lines do they write?
