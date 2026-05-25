# Unit 4 — Retry Policies with Backoff

## Concept

Retry with exponential backoff: first retry after 100ms, double each time, cap at 30s, max 5 attempts. Add jitter (random ±20%) to prevent thundering herd — without it, all clients retry at the same instant and amplify the outage. Only retry transient errors (timeouts, 5xx); never retry 4xx or non-retryable business errors.

## Code

```go
package main

import (
	"context"
	"errors"
	"fmt"
	"math/rand"
	"net/http"
	"time"
)

func isRetryable(err error) bool {
	var urlErr *url.Error
	if errors.As(err, &urlErr) && urlErr.Timeout() {
		return true
	}
	return false
}

func isRetryableStatus(code int) bool {
	return code == http.StatusTooManyRequests ||
		code == http.StatusBadGateway ||
		code == http.StatusServiceUnavailable ||
		code == http.StatusGatewayTimeout
}

func withRetry(ctx context.Context, fn func() error) error {
	const (
		maxAttempts = 5
		base        = 100 * time.Millisecond
		cap         = 30 * time.Second
	)
	var err error
	for attempt := 0; attempt < maxAttempts; attempt++ {
		err = fn()
		if err == nil {
			return nil
		}
		if !isRetryable(err) {
			return err // non-retryable — stop immediately
		}
		if attempt == maxAttempts-1 {
			break
		}
		// exponential backoff with ±20% jitter
		backoff := base * (1 << attempt)
		if backoff > cap {
			backoff = cap
		}
		jitter := time.Duration(rand.Int63n(int64(backoff) / 5))
		if rand.Intn(2) == 0 {
			jitter = -jitter
		}
		wait := backoff + jitter

		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-time.After(wait):
		}
	}
	return fmt.Errorf("all %d attempts failed: %w", maxAttempts, err)
}
```

## Exercise

**Build:** Test `withRetry` with a mock function that fails 3 times then succeeds.
**Input:** A mock that returns a retryable error on attempts 1–3 and nil on attempt 4
**Output:** Print each attempt number and timestamp. Show that total attempts = 4 and the time between calls increases.
**Acceptance:** (1) total attempts = 4, (2) each wait is longer than the previous, (3) passing a cancelled context stops retries immediately without waiting for the next backoff

## Interview

- Why add jitter to backoff? What is thundering herd?
- What is the difference between a retryable and a non-retryable error? Give one example of each.
- If max attempts = 5 and base = 100ms, what is the maximum wait time before the 5th attempt (before jitter)?
