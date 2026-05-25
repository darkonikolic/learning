# Unit 9 — Sagas & compensating actions across services

Across service boundaries there is usually **no** single ACID transaction that can atomically commit `payment + inventory + email + loyalty points`. Coordination becomes an explicit workflow with **partial failure** baked in.

## Core mental model

- **Forward actions** advance business state (`ReserveInventory`, `CapturePayment`).
- **Compensating actions** undo earlier forward steps best-effort when later steps fail (`ReleaseReservation`, `RefundPayment`), subject to strict business/legal rules—not every rollback is symmetrical or instant.

Design tasks:

1. Decide what “done” means for each step and what artefacts prove it (records, statuses, immutable events).
2. Make steps **retry-safe** using idempotency keys where external systems can double-apply ambiguous calls.
3. Document where you cannot compensate fully (often payment rails); pair with ops runbooks honest about manual intervention.

## Compare coordination styles

- **Orchestration**: central component drives next steps explicitly (think workflow engine vibes or your own saga coordinator)—clear flow, coupling risk concentrated.
- **Choreography**: services react to signals/events—fewer choke points but harder reasoning about implicit contracts.

Interview prompt: sketch one concrete failure midpoint and enumerate compensations invoked in order—and what happens if a compensation fails.
