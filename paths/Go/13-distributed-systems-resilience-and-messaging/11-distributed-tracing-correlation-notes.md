# Unit 11 — Correlation IDs and minimal distributed tracing awareness

Failures cross service hops; plaintext “error happened” logs at each hop recreate detective novels nobody finishes.

## Practice baseline

Attach and propagate minimally:

```
request id (edge assigned)
upstream trace-ish correlation token (whatever your org standardises—don’t Cargo-cult a vendor name here blindly)
tenant/user identifiers ethically cautioned PII sensitivities—even learning exercises practise redaction instincts
```

Log fields should line up grepably across hops even before full OpenTelemetry depth—establish mental habit: **carry context into nested calls**.

## Interview prompts

Cardinality explosion when logging high-cardinality labels indiscriminately.

Sampling intuition: you cannot economically retain every span forever—articulate pragmatic retention vs debuggability tensions honestly.
