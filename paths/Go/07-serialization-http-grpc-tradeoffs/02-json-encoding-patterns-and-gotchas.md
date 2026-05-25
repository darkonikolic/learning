# Unit 2 — JSON Encoding Patterns and Gotchas

## Concept

`json.Encoder` writes directly to an `io.Writer` — use it for HTTP responses to avoid allocating the full body in memory. `json.Decoder` reads from an `io.Reader` — use it for request bodies. Three common gotchas trip up production code: a nil slice marshals to `null`, not `[]` — clients break on this; unexported struct fields are silently ignored with no error; `time.Time` marshals to RFC3339 by default, which is correct but must be consistent across your API.

## Code

```go
package main

import (
	"encoding/json"
	"fmt"
	"net/http"
	"time"
)

type CreateOrderRequest struct {
	Items     []string  `json:"items"`
	CreatedAt time.Time `json:"created_at"`
	note      string    // unexported — silently ignored by json
}

type OrderResponse struct {
	ID        string    `json:"id"`
	Items     []string  `json:"items"`
	CreatedAt time.Time `json:"created_at"`
}

func handleCreateOrder(w http.ResponseWriter, r *http.Request) {
	var req CreateOrderRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "invalid JSON", http.StatusBadRequest)
		return
	}

	// Gotcha: nil slice vs empty slice
	// If client sends {"items": null}, req.Items is nil here.
	// If client sends {"items": []}, req.Items is an empty non-nil slice.
	if req.Items == nil {
		http.Error(w, `"items" must not be null`, http.StatusBadRequest)
		return
	}

	resp := OrderResponse{
		ID:        "ord_789",
		Items:     req.Items,    // non-nil: marshals to []
		CreatedAt: time.Now().UTC(),
	}

	w.Header().Set("Content-Type", "application/json")
	// Encoder writes directly to ResponseWriter — no intermediate []byte allocation
	if err := json.NewEncoder(w).Encode(resp); err != nil {
		// At this point headers are sent; we can only log
		fmt.Printf("encode error: %v\n", err)
	}
}

func nilVsEmpty() {
	var nilSlice []string          // nil
	emptySlice := []string{}      // non-nil, empty

	nilJSON, _ := json.Marshal(nilSlice)
	emptyJSON, _ := json.Marshal(emptySlice)

	fmt.Println(string(nilJSON))   // null  — breaks most JS clients
	fmt.Println(string(emptyJSON)) // []    — correct
}
```

## Exercise

**Build:** An HTTP handler that accepts `POST /orders` with body `{"items": [...], "created_at": "..."}`.
**Input:** Three test requests: (1) valid body with items, (2) `{"items": null, ...}`, (3) `{"items": [], ...}`.
**Output:** Request 1 returns 200. Request 2 returns 400 with message `"items" must not be null`. Request 3 returns 200 (empty slice is valid).
**Acceptance:** Add `omitempty` to the Items field tag and re-run — verify request 2 now returns 200 (the bug is masked). Remove `omitempty`. Explain in a comment why `omitempty` is dangerous on required slice fields.

## Interview

- What is the difference between `json.Marshal` and `json.NewEncoder(w).Encode` for HTTP responses?
- A client receives `"items": null` from your API and their JS code crashes. What went wrong on the server?
- Why does `time.Time` marshal correctly without a custom marshaler, and what format does it use?
