# Unit 5 — Idempotency Keys: The Double-Charge Story

## Concept

An idempotency key is a UUID the client generates per logical operation. The server stores the key plus the result. On retry with the same key, the server returns the cached result without re-executing. Set a TTL on the key (e.g., 24h) — after that, the same key is treated as a new request. The client must generate the key before the first attempt and reuse it on every retry.

## Code

```go
package main

import (
	"errors"
	"fmt"
	"sync"
	"time"
)

type ChargeResult struct {
	TransactionID string
	Amount        int
	ProcessedAt   time.Time
}

type idempotencyRecord struct {
	result    ChargeResult
	expiresAt time.Time
}

// PaymentServer is a test double with idempotency key support.
type PaymentServer struct {
	mu      sync.Mutex
	store   map[string]idempotencyRecord
	charges int // counts real executions
}

func (s *PaymentServer) Charge(idempotencyKey string, amount int) (ChargeResult, error) {
	s.mu.Lock()
	defer s.mu.Unlock()

	// Check for existing result.
	if rec, ok := s.store[idempotencyKey]; ok {
		if time.Now().Before(rec.expiresAt) {
			return rec.result, nil // cached — not re-executed
		}
	}

	// Execute the charge.
	s.charges++
	result := ChargeResult{
		TransactionID: fmt.Sprintf("txn-%d", s.charges),
		Amount:        amount,
		ProcessedAt:   time.Now(),
	}

	s.store[idempotencyKey] = idempotencyRecord{
		result:    result,
		expiresAt: time.Now().Add(24 * time.Hour),
	}
	return result, nil
}

func main() {
	server := &PaymentServer{store: make(map[string]idempotencyRecord)}
	key := "idem-key-abc123"

	r1, _ := server.Charge(key, 100)
	r2, _ := server.Charge(key, 100) // retry with same key

	fmt.Printf("First response:  txnID=%s\n", r1.TransactionID)
	fmt.Printf("Second response: txnID=%s\n", r2.TransactionID)
	fmt.Printf("Charges executed: %d\n", server.charges)

	if r1.TransactionID != r2.TransactionID {
		panic(errors.New("idempotency broken: different transaction IDs"))
	}
}
```

## Exercise

**Build:** Send the same charge request twice with the same idempotency key. Add a counter on the mock gateway that increments only when a real charge runs (not on cache hit).
**Input:** Two calls to `Charge` with identical idempotency key and amount
**Output:** Both calls return the same `TransactionID`. `server.charges == 1`.
**Acceptance:** `r1.TransactionID == r2.TransactionID` and `server.charges == 1` — charge executed once, second call returned cached result

## Interview

- Where should the client generate the idempotency key — before or after the first attempt?
- What happens if a server stores idempotency keys forever with no TTL?
- Can two different operations share the same idempotency key? What goes wrong?
