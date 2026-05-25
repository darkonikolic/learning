# Unit 3 — HTTP Clients: Timeout Mandates

## Concept

`http.DefaultClient` has no timeouts — a slow server will block your goroutine forever. Configure `Timeout` on `http.Client` for the full round-trip budget, and set connection and TLS timeouts on the `Transport`. Use `context` for per-request cancellation on top of client-level timeouts. Both layers are needed: client timeout is a hard ceiling, context lets callers cancel early.

## Code

```go
package main

import (
	"context"
	"fmt"
	"net/http"
	"time"
)

// Danger: DefaultClient has zero timeouts — never use for outbound calls.
var _ = http.DefaultClient

// newPaymentClient returns an http.Client with all timeout layers configured.
func newPaymentClient() *http.Client {
	transport := &http.Transport{
		DialContext: (&net.Dialer{
			Timeout:   3 * time.Second, // TCP connect timeout
			KeepAlive: 30 * time.Second,
		}).DialContext,
		TLSHandshakeTimeout:   5 * time.Second,
		ResponseHeaderTimeout: 10 * time.Second, // time to first byte
		MaxIdleConns:          100,
		MaxIdleConnsPerHost:   10,
		IdleConnTimeout:       90 * time.Second,
	}
	return &http.Client{
		Timeout:   5 * time.Second, // total request budget (overrides all above)
		Transport: transport,
	}
}

func chargeWithTimeout(ctx context.Context, client *http.Client, url string) error {
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, url, nil)
	if err != nil {
		return fmt.Errorf("build request: %w", err)
	}
	resp, err := client.Do(req)
	if err != nil {
		return fmt.Errorf("do request: %w", err) // context.DeadlineExceeded or url.Error with timeout
	}
	defer resp.Body.Close()
	return nil
}
```

## Exercise

**Build:** A `PaymentGatewayClient` with a 5s `Timeout`. Point it at a test server that sleeps 10s before responding.
**Input:** One HTTP POST to the slow test server
**Output:** The client returns an error containing "timeout" or "deadline exceeded" in approximately 5 seconds
**Acceptance:** `time.Since(start) < 6*time.Second` and `err != nil` — the client did not wait 10s

## Interview

- What is the difference between `http.Client.Timeout` and `ResponseHeaderTimeout` on the Transport?
- Why is `http.DefaultClient` dangerous in production services?
- If you set a 5s client timeout and also pass a context with a 2s deadline, which one wins?
