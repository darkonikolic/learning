# Quick Reference — Temporal Workflows

## Key types
```
workflow.Context         // NOT context.Context — deterministic
workflow.ExecuteActivity(ctx, fn, args...).Get(ctx, &result)
workflow.ExecuteChildWorkflow(ctx, fn, args...).Get(ctx, &result)
workflow.GetSignalChannel(ctx, signalName)
workflow.SetQueryHandler(ctx, queryName, handlerFn)
```

## Activity options
```go
workflow.WithActivityOptions(ctx, workflow.ActivityOptions{
    StartToCloseTimeout: 30*time.Second,
    RetryPolicy: &temporal.RetryPolicy{MaxAttempts: 3},
})
```

## Workflow rules (determinism)
- NO: time.Now(), rand, goroutines, direct I/O
- YES: workflow.Now(), workflow.Go(), workflow.ExecuteActivity()
- All side effects go through activities

## Error handling
```go
temporal.NewNonRetryableApplicationError(msg, errType, cause)
// use for: invalid input, business rule violations
```

## Worker registration
```go
w := worker.New(client, taskQueue, worker.Options{})
w.RegisterWorkflow(MyWorkflow)
w.RegisterActivity(MyActivity)   // or &ActivityStruct{}
```
