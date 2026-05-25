# Unit 1 — Scope: Payment System Micro-Slices

## Concept

This module builds a payment processing client that handles the real failure modes of distributed systems. You will implement proper HTTP client timeouts, exponential backoff with jitter, and idempotency keys. By the end you have a client that can safely retry failed payment requests without double-charging a customer.

## Code

```go
// What you will build across this module:
//
// PaymentClient
//   - http.Client with explicit Timeout and Transport settings
//   - withRetry: exponential backoff, jitter, max attempts, context cancellation
//   - Charge(ctx, idempotencyKey, amount) — safe to call multiple times
//
// PaymentServer (test double)
//   - Accepts idempotency key in header
//   - Returns cached result on duplicate key
//   - Sleeps or fails on demand to simulate real gateway behavior
//
// By end of module the following holds:
//   - A 10s slow server gets a timeout error in ~5s
//   - A server that fails 3/5 times still succeeds after retry
//   - Calling Charge twice with the same key charges exactly once

package payments // placeholder — each unit fills this in
```

## Exercise

**Build:** Nothing yet — this is orientation. Read the scope, then sketch on paper: what are the three things that can go wrong between client and payment gateway?
**Input:** Your own reasoning
**Output:** Three failure scenarios written down: (1) server never responds, (2) server responds with error, (3) server succeeds but response is lost
**Acceptance:** You can explain why scenario 3 requires idempotency keys but scenarios 1 and 2 do not

## Interview

- What is the difference between a timeout and a retry?
- Why is it unsafe to retry a POST to a payment gateway without an idempotency key?
- Name two things you must configure on `http.Client` to prevent goroutine leaks on slow servers.
