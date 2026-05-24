# Unit 2 — Labs (`shop-spa/` checkout path)

## Build tasks

- Extract per-domain API modules (`productApi`, `authApi`, `orderApi`, …) from components.
- Configure **timeouts**, **interceptors** (e.g. attach auth header), and **shared error translation**.
- Implement **loading / empty / error** UX for catalog and cart operations.
- **Retry lab**: inject flaky timeout; observe recovery within limits.
- **Cancellation lab**: product search typing — abort stale requests.
- **Optimistic cart add** with rollback on forced 500.
- **Architecture pass**: document `component → service → api → network` with one sequence diagram or bullet RACI.

## Deliverable notes

Write a short **failure playbook**: what the user sees for 401 / 404 / 500 / timeout / offline-ish behaviour.

Interview checklist: optimistic UI, cancellation, retry policy, timeout ownership, API layer separation, error mapping.
