# Unit 9 — Context: timeouts, cancellations, disciplined propagation—not globals

## Learning outcome

Treat **`ctx context.Context`** as **deadlines + cancellations + bounded values (sparingly)** threading cooperatively—not a mystical bag chucking incidental configuration everywhere.

Mandatory internalisation sketches:

```go
ctx, cancel := context.WithCancel(parent)
defer cancel()
```
```go
ctx, cancel := context.WithTimeout(parent, 2*time.Second)
defer cancel()
```

## Misuse anti-patterns to articulate

Stuffing unrelated config arbitrarily into **`context.Value`** without typed accessor discipline.

Propagating **`context.TODO()`** permanently—document only transitional scenarios.

Ignoring **`ctx.Done`** in loops performing simulated network or IO.

## CLI practice blueprint

Implement a **download-like** faker (sleep or read large file concurrently) enforcing **overall budget** shorter than faker duration—observe clean abort vs leaky goroutine tendencies (note leak—fix responsibly even if minimally).

Highlight **why `context` is not global singleton state.**

## Interview prompts

- parent → child propagation mental model diagrams,
- when context cancellation should preempt vs escalate metric logging,
- relationship with upcoming HTTP inbound deadlines (Area `05`), DB calls (Area `08`), gRPC (Area `06`).
