# Unit 4 — Temporal Error Handling and Retries

## Concept

Temporal distinguishes **retryable** errors (default — Temporal will retry per policy) from **non-retryable** errors (halt the retry loop immediately and fail the activity or workflow).

## Code

```go
// Non-retryable error — stops retry loop immediately
return temporal.NewNonRetryableApplicationError("invalid card", "CARD_INVALID", nil)

// Retryable (default) — Temporal retries per ActivityOptions.RetryPolicy
return fmt.Errorf("gateway timeout: %w", err)

// ActivityOptions retry policy
ao := workflow.ActivityOptions{
	StartToCloseTimeout: time.Minute,
	RetryPolicy: &temporal.RetryPolicy{
		InitialInterval:    time.Second,
		BackoffCoefficient: 2.0,
		MaximumInterval:    time.Minute,
		MaxAttempts:        5,
		NonRetryableErrorTypes: []string{"CARD_INVALID", "INSUFFICIENT_FUNDS"},
	},
}

// Heartbeat for long-running activities
func LongActivity(ctx context.Context) error {
	for i := 0; i < 1000; i++ {
		activity.RecordHeartbeat(ctx, i) // keeps activity alive
		if activity.GetInfo(ctx).Attempt > 1 {
			// resume from heartbeat details on retry
		}
	}
	return nil
}
```

| Error type | Behaviour | Use case |
|------------|-----------|----------|
| `fmt.Errorf(...)` | Retryable | Transient failures, gateway timeouts |
| `temporal.NewNonRetryableApplicationError` | Not retried | Invalid input, business rule violations |
| `context.DeadlineExceeded` | Depends on policy | Timeout — usually retryable |

## Exercise

**Build:** A payment activity that returns `NonRetryableApplicationError` for card number "invalid" and a normal retryable error for card number "timeout".
**Input:** Card number string — use "invalid" to trigger non-retryable, "timeout" to trigger retryable
**Output:** For "invalid": workflow fails immediately with no retries. For "timeout": activity retries 3 times with backoff, then workflow fails.
**Acceptance:** Observe retry count in Temporal UI event history — "invalid" shows 1 attempt total; "timeout" shows exactly 3 attempts with increasing intervals between them

## Interview

- What is `StartToCloseTimeout` vs `ScheduleToCloseTimeout`? (Start-to-close: single attempt budget. Schedule-to-close: total budget across all retries.)
- When do you use heartbeats? (Long-running activities — without heartbeats, Temporal cannot detect a stuck worker until timeout.)
- Why mark an error non-retryable? (Retrying `CARD_INVALID` wastes time and charges the card again if the activity isn't idempotent.)
