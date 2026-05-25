# Unit 6 — Structured logging in production (`slog` baseline)

Replace ad-hoc prints with **keyed fields** and stable event names.

Minimum fields to internalise:

```
request_id
trace_id (or trace/span IDs once OTEL hooked)
service name / version
error classification fields (code, retryable bool) optional but valuable
```

## Practice

Inject **request_id** at edge middleware; propagate into logs for a synthetic `Payment` API path.

Simulate a **500** and verify you can trace the request through logs without guessing.

## Interview prompts

PII in logs; cardinality of dynamic keys; sampling vs full fidelity.
