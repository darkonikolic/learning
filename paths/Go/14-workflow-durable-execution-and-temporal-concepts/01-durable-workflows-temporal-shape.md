# Unit 1 — Durable Workflows: Temporal Shape

## Concept

Durable execution means a workflow survives process restarts. Temporal records every step to an event history. On restart, it replays the history to restore state — your workflow function is re-run from the top, but `ExecuteActivity` calls return immediately from history instead of re-executing. This means your workflow function must be deterministic: same inputs always produce the same sequence of calls.

## Code

```go
// Fragile: in-process job queue loses state on restart.
type InMemoryJob struct {
	Steps []func() error
}

func runFragile(job InMemoryJob) error {
	for _, step := range job.Steps {
		if err := step(); err != nil {
			return err // on restart, progress is lost — starts from zero
		}
	}
	return nil
}

// Durable: Temporal workflow survives restart.
// On restart, Temporal replays the event history. Each ExecuteActivity call
// checks history first — if the activity already completed, the result is
// returned from history without calling the activity again.
func PaymentWorkflow(ctx workflow.Context, orderID string) error {
	ao := workflow.ActivityOptions{
		StartToCloseTimeout: 30 * time.Second,
	}
	ctx = workflow.WithActivityOptions(ctx, ao)

	// If process restarts here, Temporal replays history.
	// ProcessPaymentActivity is NOT called again if it already succeeded.
	if err := workflow.ExecuteActivity(ctx, ProcessPaymentActivity, orderID).Get(ctx, nil); err != nil {
		return err
	}
	return workflow.ExecuteActivity(ctx, SendConfirmationActivity, orderID).Get(ctx, nil)
}
```

## Exercise

**Build:** Nothing to run yet. Identify which of these are safe inside a Temporal workflow function and explain why.
**Input:** These five calls: `time.Now()`, `rand.Int()`, `os.ReadFile("config.json")`, `workflow.ExecuteActivity(ctx, MyActivity)`, `workflow.Now(ctx)`
**Output:** Safe: `workflow.ExecuteActivity`, `workflow.Now(ctx)`. Unsafe: `time.Now()`, `rand.Int()`, `os.ReadFile()`.
**Acceptance:** You can explain the rule: if the call produces a different result on replay than on first execution, it is not safe in a workflow

## Interview

- What does Temporal do with the event history when a worker restarts?
- Why is calling `time.Now()` inside a workflow dangerous but `workflow.Now(ctx)` safe?
- What is an activity, and why does Temporal retry it instead of retrying the workflow?
