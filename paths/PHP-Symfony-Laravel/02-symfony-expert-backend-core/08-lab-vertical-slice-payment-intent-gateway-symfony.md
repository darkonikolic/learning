# Unit 8 — Lab: ecommerce payment intent initiation (Symfony)

Scenario

Expose **payment intent initiation** enforcing:

- transactional guard around draft order state transition,
- async notification via Messenger after commit,
- idempotent handler handling duplicate enqueue.

Deliverables

Diagram + folder outline showing **explicit layers** separating domain reasoning from infra glue.

Interview reflection

Enumerate **five** regressions testers should script if event ordering breaks subtly.
