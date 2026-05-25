# Unit 2 — Temporal Workflow and Activity Anatomy

## Concept

A **workflow** is a durable, deterministic function — it must not perform I/O directly. An **activity** wraps all side effects and is the unit Temporal retries.

## Code

```go
// Workflow — deterministic, no I/O directly
func OrderWorkflow(ctx workflow.Context, orderID string) error {
	ao := workflow.ActivityOptions{
		StartToCloseTimeout: 30 * time.Second,
		RetryPolicy: &temporal.RetryPolicy{
			MaxAttempts:     3,
			InitialInterval: time.Second,
		},
	}
	ctx = workflow.WithActivityOptions(ctx, ao)

	var result PaymentResult
	err := workflow.ExecuteActivity(ctx, ProcessPaymentActivity, orderID).Get(ctx, &result)
	if err != nil {
		return err
	}

	return workflow.ExecuteActivity(ctx, SendConfirmationActivity, orderID, result).Get(ctx, nil)
}

// Activity — can do I/O, is retried by Temporal
func ProcessPaymentActivity(ctx context.Context, orderID string) (PaymentResult, error) {
	// real I/O here: call payment gateway
	return gateway.Charge(ctx, orderID)
}

// Register and start worker
w := worker.New(client, "orders-queue", worker.Options{})
w.RegisterWorkflow(OrderWorkflow)
w.RegisterActivity(ProcessPaymentActivity)
w.Run(worker.InterruptCh())
```

| Concern | Workflow | Activity |
|---------|----------|----------|
| Determinism | Required — replayed from history | Not required |
| I/O | Forbidden | Allowed |
| Retries | Managed by Temporal on failure | Yes, per RetryPolicy |
| Timeouts | ScheduleToClose, StartToClose | StartToClose, ScheduleToClose |

## Exercise

**Build:** An order fulfillment workflow with three activities in sequence: `ProcessPayment` → `ReserveInventory` → `SendConfirmation`
**Input:** `OrderID string` passed to the workflow
**Output:** Each activity prints what it did. If `ReserveInventory` returns an error, the workflow returns that error and `SendConfirmation` is never called. `ProcessPayment` is not retried for reservation failures.
**Acceptance:** Run the worker, start the workflow via CLI (`tctl workflow run` or Temporal UI), observe all three activity executions in the Temporal UI event history. Force `ReserveInventory` to fail — verify the workflow fails and `SendConfirmation` does not appear in history.

## Interview

- Why must workflows be deterministic? (Temporal replays history to reconstruct state after a crash.)
- What happens if you call `time.Now()` inside a workflow? (Non-determinism — use `workflow.Now()` instead.)
- Can an activity fail halfway through? What happens? (Temporal retries from the start of that activity invocation.)
