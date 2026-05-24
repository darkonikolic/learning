# Unit 2 — Providers binding contracts thoughtfully

Goals

- **Deferred vs eager binding** ramifications for cold start latency.
- **`singleton` leakage vs scoped instances** aligning long-lived connectors with test isolation.
- **Contextual bindings** sparingly bridging multi-tenant or multi-queue drivers cleanly.

Practice note

Enumerate **four** Laravel conveniences enticing hidden static singletons harmful to deterministic tests—remediation strategy.
