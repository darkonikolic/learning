# Unit 2 — Labs: saga rehearsal & ambiguity windows

Scenario: **`PaymentCaptured` succeeds** while **`InventoryReserve` refuses or times out ambiguously.**

Deliverables:

1. **Ordered forward steps** (API → payment rail → reservation → fulfilment…) with observable side-effects each.
2. **Failure injections** (`worker restart`, `webhook tardy`, `timeout uncertain success`) mapped to hypotheses.
3. **Compensation / manual branch** documenting refund/reversal vs partial ship policies—explicit business rule references even if illustrative.
4. **Idempotency** story for ambiguous retries—you cannot double-charge or double-move stock blindly.

Interview drill: explain why naive “rollback transaction” fantasies crumble across gateways & payment processors.

