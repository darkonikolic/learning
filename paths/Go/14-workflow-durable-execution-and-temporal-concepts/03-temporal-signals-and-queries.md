# Unit 3 — Temporal Signals and Queries

## Concept

**Signals** push external events into a running workflow asynchronously. **Queries** read workflow state without mutating it — pure read, safe to call any time.

## Code

```go
// Signal: external event pushed into a running workflow
func OrderWorkflow(ctx workflow.Context, orderID string) error {
	cancelCh := workflow.GetSignalChannel(ctx, "cancel-order")

	selector := workflow.NewSelector(ctx)
	selector.AddReceive(cancelCh, func(c workflow.ReceiveChannel, more bool) {
		// handle cancellation signal
	})

	// workflow.Select blocks until a channel is ready
	selector.Select(ctx)
	return nil
}

// Send signal from outside
client.SignalWorkflow(ctx, workflowID, runID, "cancel-order", nil)

// Query: read workflow state without mutating it
workflow.SetQueryHandler(ctx, "get-status", func() (string, error) {
	return currentStatus, nil
})

// Execute query from outside
val, err := client.QueryWorkflow(ctx, workflowID, runID, "get-status")
```

| | Signal | Query |
|-|--------|-------|
| Mutates state | Yes | No |
| Async | Yes | No (synchronous response) |
| Persisted in history | Yes | No |
| Use case | Cancel, approve, external event | Status check, audit read |

## Exercise

**Build:** An order workflow that waits for a `confirm` signal before processing payment. The workflow logs "waiting for confirm" when it starts, then "confirmed, processing payment" after the signal arrives.
**Input:** Signal sent via `tctl workflow signal --name confirm` or Temporal UI
**Output:** Workflow logs "waiting for confirm" immediately, then pauses. After signal: logs "confirmed, processing payment" and continues.
**Acceptance:** Kill and restart the worker while the workflow is waiting for the signal — the workflow resumes correctly after the worker comes back up, and the signal sent before the restart is not lost

## Interview

- What happens if a signal arrives before the workflow registers the channel? (Temporal buffers it — delivered when the channel is registered.)
- Why can't a query handler mutate state? (Queries are not recorded in history — mutations would break replay determinism.)
