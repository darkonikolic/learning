# When to Go Async

Async is not free. Every async boundary is a failure mode, a consistency problem, and an observability challenge. Add async because the problem demands it, not because it feels modern.

---

## The Async Decision

Use async when **all three** hold:
1. The caller doesn't need the result to continue
2. The operation can fail without the user knowing immediately
3. The operation takes longer than the user should wait

Use sync when **any one** holds:
- The user needs the result to proceed (payment confirmation, inventory check result)
- The operation must succeed for the transaction to succeed
- You need strong consistency — the write must be visible to the next read

**The test:** Can you show the user a success screen before this operation completes? If no, it's sync.

---

## Event vs Command vs Query

Three message shapes. Choosing wrong causes cascading design problems.

| Type | Semantics | Direction | Coupling | Result |
|------|-----------|-----------|----------|--------|
| **Event** | Something happened (`OrderPlaced`) | Fire-and-forget, fan-out | Publisher knows nothing about consumers | None expected |
| **Command** | Do this (`SendConfirmationEmail`) | Point-to-point, targeted | Publisher knows there's one consumer | Acknowledged eventually |
| **Query** | Give me data | Always synchronous | Tight — caller blocks | Immediate response |

**Events** are past tense and immutable: `OrderPlaced`, `PaymentFailed`, `InventoryReserved`. The publisher has no opinion about what happens next.

**Commands** are imperative and directed: `SendEmail`, `ProcessRefund`. If nobody processes it, that's a bug — use a DLQ and alerting.

**Wrong choice symptoms:**
- Using events for commands → you don't know if anyone processed it
- Using commands when events are appropriate → tight coupling, single consumer bottleneck
- Using async for queries → you have to poll or build callbacks for something that should be a function call

---

## Ownership of Guarantees

Confusion here causes "the queue just lost our data" incidents.

**Publisher owns:**
- Event schema and versioning
- At-least-once delivery (the message was sent)
- Valid payload (schema validation before publish)
- Not publishing unless there's something to process

**Consumer owns:**
- Idempotency — handling duplicate delivery
- Ordering tolerance — messages may arrive out of order
- DLQ monitoring — if your consumer is failing, you need to know
- Own retry logic (not relying on publisher to resend)

**The boundary:** publisher guarantees the message exists and is valid. Consumer guarantees the effect happens exactly once despite multiple deliveries.

If your publisher is "making sure" the consumer processed it, you've inverted ownership and created coupling.

---

## The Idempotency Requirement

Every queue consumer must be idempotent. A message **will** be delivered more than once. This is not a bug — it is the delivery guarantee (at-least-once).

**Idempotency patterns:**

*Natural idempotency:* The operation is inherently safe to repeat. Setting a status to `shipped` twice is fine. Use when possible.

*Idempotency key:* Consumer tracks a key (message ID, order ID + event type) in a processed-events table. Before processing, check if already handled. If yes, skip and ack.

```
-- In the same transaction as the effect
INSERT INTO processed_events (event_id, processed_at)
VALUES ($1, NOW())
ON CONFLICT (event_id) DO NOTHING
RETURNING event_id
-- If no row returned, already processed — skip
```

*Conditional write:* Only write if precondition still holds. `UPDATE orders SET status = 'shipped' WHERE status = 'paid'` — if already shipped, WHERE fails, no double-ship.

**What breaks without idempotency:**
- Payment charged twice
- Confirmation email sent twice
- Inventory decremented twice
- Analytics double-counted

---

## DLQ as Required Infrastructure

Not optional. DLQ is the difference between silent message loss and recoverable failure.

**Without DLQ:** Consumer fails repeatedly → queue broker drops message after max retries → failure is invisible.

**With DLQ:** Consumer fails repeatedly → message moves to dead-letter queue → message accumulates → alert fires → engineer replays after fix.

**DLQ operational checklist:**
- [ ] Every consumer queue has a corresponding DLQ
- [ ] DLQ depth is monitored with alert threshold (> 0 for critical, > N for warning)
- [ ] Messages in DLQ include original payload + failure reason + retry count
- [ ] Replay tooling exists (don't manually requeue one at a time)
- [ ] DLQ messages expire (don't accumulate forever — set TTL appropriate to recovery window)

**DLQ monitoring = ops maturity signal.** If your team doesn't know the DLQ depth right now, you don't have async ops maturity.

---

## Outbox Pattern

**Problem:** You want to publish an event only if the database transaction committed.

**Without outbox:**
1. DB transaction commits (order saved)
2. Publish event to queue
3. If step 2 fails → order exists, event never sent → downstream never notified

Or inverted:
1. Publish event to queue
2. DB transaction commits
3. If step 3 fails → event sent, order doesn't exist → phantom event downstream

**With outbox:**
1. In the same DB transaction: write order record + write event to `outbox` table
2. Transaction commits atomically
3. Separate outbox worker reads `outbox` table, publishes to queue, marks as published
4. If publishing fails → outbox record stays unpublished → worker retries

The event is now guaranteed to be published if and only if the transaction committed. The outbox worker delivers at-least-once (retry on failure), so consumers still need idempotency.

**When you need it:** Any time you write to DB and publish an event in the same operation, and you care about consistency between them.

---

## Decision Table

| Caller needs result? | Op duration | Failure tolerance | Consistency requirement | Decision |
|---------------------|-------------|-------------------|------------------------|----------|
| Yes | Any | Low | Strong | Sync |
| No | < 200ms | Low | Strong | Sync |
| No | < 200ms | High | Eventual | Could go either way — sync is simpler |
| No | > 500ms | High | Eventual | Async |
| No | Any | High | Eventual, write + publish | Async + Outbox |
| No | Any | High | Eventual, fan-out | Event (not command) |

---

## Anti-patterns

**Async for everything.** Every operation becomes a debugging and observability problem. "Why did this not happen?" is hard to answer when there are 8 async hops. Reserve async for operations that genuinely fit.

**No idempotency in consumers.** Duplicate delivery is guaranteed. If your consumer doesn't handle it, you will double-charge, double-ship, or double-send. Not if — when.

**Publisher schema changes without consumer coordination.** Adding a required field breaks all existing consumers. Removing a field silently breaks consumers that depend on it. Schema versioning and backward compatibility are publisher responsibilities.

**No DLQ.** Failed messages disappear. You will never know. You will discover the failure when a customer complains weeks later.

**Using async to hide latency problems.** "The DB query is slow so we'll make it async." The query is still slow. You've added a queue but not fixed the problem, and now you have both a slow query and async complexity.

**Commands modeled as events.** `EmailSendRequested` sounds like an event but it's a command. If it ends up in DLQ and nobody notices, the user never gets their email. Model it as a command, own the result.

---

## Šta da pitaš AI

**For sync/async decision:**
> "This operation [describe it in detail: what it does, how long it takes, what depends on it succeeding]. Should it be sync or async? What failure modes does each choice introduce? What does the user experience look like if the async path fails?"

**For idempotency design:**
> "Our queue consumer processes [describe: what the consumer does, what side effects it has, what data it writes]. What are the idempotency requirements? How do we handle duplicates? Show me the idempotency key design and the DB table I need."

**For event schema:**
> "We need an event schema for [domain event: what happened, what the downstream needs to know]. What fields should be in the stable contract vs what can evolve? How do we version this schema without breaking consumers?"

**For outbox decision:**
> "We write to [table] and publish [event] in the same request handler. Do we need the outbox pattern? What breaks if we don't use it? Show me the outbox table schema and worker pseudocode for our Symfony + Postgres + [queue] stack."
