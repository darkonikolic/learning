# Unit 2 — Contract Testing: Producer-Consumer Safety

## Concept

Contract testing verifies that a consumer's expectations of a provider are actually met. The consumer writes down what requests it sends and what response shape it expects. The provider runs tests against those expectations. This prevents breaking changes — renaming a JSON field breaks the consumer contract test immediately, not when services are deployed to staging and someone notices. It is lighter than full end-to-end tests and faster to run in CI.

## Code

```go
package contract_test

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/example/app/handler"
)

// Consumer's expectation: GET /products/:id returns {id, name, price}
// If the producer renames "name" to "product_name", this test fails.

type productConsumerExpectation struct {
	ID    string  `json:"id"`
	Name  string  `json:"name"`   // consumer expects this field name
	Price float64 `json:"price"`
}

func TestProductHandler_ContractGet(t *testing.T) {
	h := handler.NewProductHandler(stubProductRepo{})
	srv := httptest.NewServer(h)
	defer srv.Close()

	resp, err := http.Get(srv.URL + "/products/prod_1")
	if err != nil {
		t.Fatalf("request failed: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		t.Fatalf("got status %d, want 200", resp.StatusCode)
	}

	var got productConsumerExpectation
	if err := json.NewDecoder(resp.Body).Decode(&got); err != nil {
		t.Fatalf("decode: %v", err)
	}

	// Contract assertions — shape, not implementation details
	if got.ID == "" {
		t.Error("contract violation: 'id' field is empty or missing")
	}
	if got.Name == "" {
		t.Error("contract violation: 'name' field is empty or missing")
	}
	if got.Price <= 0 {
		t.Error("contract violation: 'price' must be positive")
	}
}

// stubProductRepo satisfies the handler's repository interface for contract tests.
type stubProductRepo struct{}

func (s stubProductRepo) FindByID(_ string) (*domain.Product, error) {
	return &domain.Product{ID: "prod_1", Name: "Widget", Price: 9.99}, nil
}
```

## Exercise

**Build:** A contract test for `ProductService.GetProduct` that runs against the real HTTP handler.
**Input:** The handler serves `GET /products/:id` and returns `{id, name, price}`.
**Output:** A contract test struct with exactly the fields the consumer expects. The test fetches from a `httptest.Server` and asserts each field is present and valid.
**Acceptance:** Test passes. Now rename `name` to `product_name` in the handler's response struct — the contract test fails with a clear message identifying the broken field. Revert and confirm it passes again.

## Interview

- What does a contract test verify that a unit test of the handler cannot?
- Why does the consumer define the contract, not the producer?
- Contract tests and integration tests both test real behavior. What is the difference?
