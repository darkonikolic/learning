# Lab: Async Classification — E-Commerce Checkout

Scenario: user places an order. The system must: (1) reserve inventory, (2) charge payment, (3) send confirmation email, (4) update analytics, (5) notify warehouse.

Work through each exercise before checking the reference tables.

---

## Exercise 1: Classify Each Step

For each operation, decide: **sync** (must complete before 201 to user) or **async** (can happen after response).

Apply the three-part test to each:
- Does the caller need the result to continue?
- Can it fail without the user knowing immediately?
- Does it take longer than the user should wait?

**Write your classification before reading the reference table.**

---

### Reference: Sync/Async Classification

| Step | Classification | Reason | Failure impact |
|------|---------------|---------|----------------|
| Reserve inventory | **Sync** | User needs to know if item is available before payment | Without this, oversell — chargebacks and fulfillment failures |
| Charge payment | **Sync** | Transaction cannot succeed if payment fails; user needs confirmation of charge | Async payment = orders with no payment; impossible to reconcile |
| Send confirmation email | **Async** | User has their 201, email is a nice-to-have in the moment | Failed email: retry, don't roll back the order |
| Update analytics | **Async** | Analytics is reporting infrastructure, never user-critical | Failed analytics: silent catch-up, no user impact |
| Notify warehouse | **Async** | Warehouse processing is downstream fulfillment, not checkout | Failed notification: DLQ alert, manual or replay recovery |

**The rule confirmed by this table:** sync operations are those where failure means the transaction itself failed. Async operations are effects that should happen but don't gate the core user transaction.

---

## Exercise 2: Idempotency Ownership

For each async step, answer:
- Who owns idempotency? (Name the service/consumer, not a team)
- What is the idempotency key?
- What happens on duplicate delivery?

**Write your answers before reading the reference table.**

---

### Reference: Idempotency Ownership

| Async step | Idempotency key | Duplicate handling | What breaks without it |
|------------|-----------------|-------------------|----------------------|
| Send confirmation email | `order_id + event_type('OrderPlaced')` | Check `sent_emails(order_id, type)` before sending; skip if exists | Customer gets 2+ confirmation emails; support tickets |
| Update analytics | `order_id + event_id` | Upsert on `(order_id, event_id)` — last write wins or dedup at read | Double-counted revenue, conversion rates; misleads decisions |
| Notify warehouse | `order_id` | Check `warehouse_notifications(order_id)` before dispatch; skip if exists | Warehouse picks and ships twice; inventory error + refund cost |

**Ownership rule confirmed:** the consumer owns idempotency. The publisher (checkout service) emits `OrderPlaced` once (plus retries). Each consumer is independently responsible for handling it exactly once regardless of delivery count.

---

## Exercise 3: DLQ Handling Design

For each async step, design the DLQ response:
- What does a message in DLQ mean operationally?
- Who gets alerted?
- What is the recovery action?

**Write your design before reading the reference table.**

---

### Reference: DLQ Handling

| Consumer | Message in DLQ means | Alert recipient | Recovery action |
|----------|---------------------|-----------------|-----------------|
| Confirmation email | Email service down or template error | On-call engineer (email service) | Fix root cause, replay DLQ; customers get delayed email with apology if >1hr |
| Analytics | Analytics pipeline broken; events will have gap | Data team (non-urgent) | Replay DLQ after fix; no customer impact but timeline gap in reports |
| Warehouse notification | Warehouse integration broken; orders accumulating without fulfillment signal | On-call engineer (critical — SLA impact) | Fix integration ASAP; replay DLQ ordered by `created_at` to process in sequence |

**DLQ alert thresholds:**
- Confirmation email: alert at depth > 0, resolve within 30 min (customer-visible)
- Analytics: alert at depth > 100 or age > 1hr (non-urgent, batch recovery acceptable)
- Warehouse: alert at depth > 0, page on-call immediately (SLA and fulfillment at risk)

**Recovery sequence for warehouse (order-sensitive):**
1. Identify root cause (do not replay into a broken consumer)
2. Fix consumer
3. Deploy
4. Replay DLQ in order — warehouse needs to process in dispatch sequence
5. Verify warehouse received and acknowledged each notification
6. Close incident, document in post-mortem

---

## Exercise 4: Where Do You Need the Outbox Pattern?

For each operation that involves both a DB write and a queue publish, decide whether outbox is required. Justify your answer.

**Write your decisions before reading the reference.**

---

### Reference: Outbox Decision

**Outbox decision rule:**

> Use the outbox pattern when: you write to the database AND publish an event in the same request, AND the downstream cannot tolerate phantom events or silent non-delivery.

| Step | DB write? | Queue publish? | Outbox required? | Justification |
|------|-----------|---------------|-----------------|---------------|
| Inventory reservation | Yes (`inventory_reservations`) | No (sync, no queue) | No | Sync operation, no queue involved |
| Payment charge | Yes (`orders`, `payments`) | No (sync, no queue) | No | Sync operation, no queue involved |
| Emit `OrderPlaced` event | Yes (`orders` committed by this point) | Yes → email, analytics, warehouse consumers | **Yes** | If publish fails after commit: email never sent, warehouse never notified. If publish happens before commit and transaction rolls back: phantom `OrderPlaced` for an order that doesn't exist |

**Without outbox on `OrderPlaced`:**

Sequence that fails silently:
```
1. BEGIN TRANSACTION
2. INSERT INTO orders ...
3. INSERT INTO payments ...
4. COMMIT  ← success
5. publish OrderPlaced to queue  ← crash here
```
Result: order exists in DB, warehouse never notified, confirmation email never sent. Customer sees 201, order never fulfills.

**With outbox:**
```
1. BEGIN TRANSACTION
2. INSERT INTO orders ...
3. INSERT INTO payments ...
4. INSERT INTO outbox (event_type, payload, published=false)
5. COMMIT  ← all or nothing
6. Outbox worker: SELECT unpublished FROM outbox
7. Publish to queue
8. UPDATE outbox SET published=true
```
If step 7 fails, outbox worker retries. Event is guaranteed to be published iff the transaction committed.

**Outbox table (Postgres):**
```sql
CREATE TABLE outbox (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type  VARCHAR(100) NOT NULL,
    payload     JSONB NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    published   BOOLEAN NOT NULL DEFAULT FALSE,
    published_at TIMESTAMPTZ,
    retry_count INT NOT NULL DEFAULT 0
);

CREATE INDEX ON outbox (published, created_at)
    WHERE published = FALSE;
```

---

## Summary Tables

### Sync/Async Split

| Step | Decision | Gate to user response? |
|------|----------|----------------------|
| Reserve inventory | Sync | Yes |
| Charge payment | Sync | Yes |
| Send email | Async | No |
| Update analytics | Async | No |
| Notify warehouse | Async | No |

### Idempotency Keys

| Consumer | Key | Pattern |
|----------|-----|---------|
| Email | `order_id + event_type` | Insert-or-skip |
| Analytics | `order_id + event_id` | Upsert |
| Warehouse | `order_id` | Insert-or-skip |

### Outbox Decision Rule

| Condition | Outbox needed? |
|-----------|---------------|
| Sync operation (no queue) | No |
| Queue publish, DB write independent | No |
| Queue publish + DB write in same transaction, both must succeed or fail together | **Yes** |
