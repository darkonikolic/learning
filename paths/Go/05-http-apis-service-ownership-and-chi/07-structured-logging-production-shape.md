# Unit 7 — Structured logging readiness (`slog` or `zap`)

## Transition motivation

Eliminate habitual `fmt.Println` tracing masquerading observability—it collapses grep-ability correlating outages.

Prefer keyed fields aligning:

```
logger.Info("creating order",
   "request_id", requestIDFromCtx,
   "user_id", userID)
```

Practice linking **middleware-injected identifiers** bridging each log emission minimum baseline contract.

Fabricate deliberate **internal 500** scenario verifying discoverability slicing logs later conceptually—even absent full ELK stack integration now.

Interview angles:

- cardinality cautions injecting high fan-out dynamic labels exploding metric/log storage costs unintentionally glimpsed verbally,
- PII scrubbing instincts even in learning exercises ethically.
