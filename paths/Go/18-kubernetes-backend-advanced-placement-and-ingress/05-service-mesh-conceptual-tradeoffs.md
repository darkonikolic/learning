# Unit 5 — Service mesh (conceptual trade-off, not a compulsory purchase)

A mesh adds a data plane proxy alongside workloads to standardise:

```
mTLS between services
traffic shifting
retries/timeouts policy (dangerous if blind)
observability hooks
```

Know the **tax**: operational complexity, latency overhead, debugging indirection.

Interview drill: when mesh benefits justify cost vs simpler explicit mTLS + ingress + good observability hygiene.
