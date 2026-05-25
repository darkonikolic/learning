# Lab: Deployment Decisions

---

## Reference: Deployment Strategy Decision Table

| Traffic volume | Rollback SLA | DB migration complexity | Ops maturity | Recommended strategy |
|---|---|---|---|---|
| Low | Hours | Backward compatible | Low | Rolling |
| Low | Hours | Not backward compatible | Low | Blue-green (migration still must be compat with both envs) |
| Medium | < 5 min | Backward compatible | Medium | Blue-green |
| High | < 60 sec | Any | High | Canary + feature flags |
| Any | Immediate (user-level) | None | Any | Feature flags |

---

## Reference: Expand/Contract Migration Sequence Template

```
Deploy 1 — Expand migration
  Action:   Add new column (nullable or with default)
  Code:     Old code (does not reference new column)
  Risk:     Zero — old code ignores new column
  Verify:   Migration applied, old app still passes health check

Deploy 2 — New application code
  Action:   No schema change
  Code:     New code reads/writes new column; also reads old column during transition
  Risk:     Low — schema is compatible with both versions
  Verify:   New behavior works; old column still readable

Deploy 3 — Contract migration
  Action:   Remove old column (only after 100% instances on new code)
  Code:     New code (does not reference old column)
  Risk:     Zero if step 2 is complete everywhere
  Verify:   Old column gone; no errors; query plans unaffected
```

---

## Reference: Rollback Checklist Template

```
Pre-incident (design time):
[ ] Previous image tag recorded (git SHA)
[ ] Rollback pipeline tested in staging
[ ] DB migration assessed: backward compatible? Y/N
[ ] Queue message format: versioned? Y/N
[ ] Compensating migration pre-written if needed

During incident:
[ ] Stop traffic to new instances (or canary drain)
[ ] Trigger rollback pipeline (previous image)
[ ] Verify health checks pass on old version
[ ] Verify error rate returns to baseline
[ ] Assess: any queue messages processed by new code that old code cannot handle?
[ ] Assess: any DB state written by new code that is invalid under old schema?

Post-rollback:
[ ] Document what could not be rolled back automatically
[ ] List affected records requiring manual recovery
[ ] Root cause: what made this non-rollbackable?
[ ] Fix plan before re-deploying
```

---

## Exercise 1: Deployment Strategy Choice

**Feature:** Add `fulfilled_at` timestamp column to the `orders` table. Expose it in the orders API response (`GET /orders/{id}`). System runs rolling deployments. Current volume: medium traffic, rollback SLA is 15 minutes.

Work through the following:

### 1. Choose deployment strategy

Given: medium traffic, 15-minute rollback SLA, new nullable column (backward compatible migration), no removal of existing columns.

Choose a strategy and justify it. Consider: does the migration constrain your choice? Does the rollback SLA?

### 2. Migration sequence

Design the full expand/contract sequence. For each deploy, specify:
- What schema change runs (if any)
- What version of the Symfony API is deployed
- What the running old version of the API does with the schema at that point
- What a rollback looks like from that step

Step 1 — Expand migration:
- Schema: `ALTER TABLE orders ADD COLUMN fulfilled_at TIMESTAMPTZ NULL`
- API deployed: old version
- Old code behavior: reads and writes orders without `fulfilled_at`, column exists but is ignored, all queries work
- Rollback from here: `ALTER TABLE orders DROP COLUMN fulfilled_at` (safe, no code references it yet)

Step 2 — New API code:
- Schema: no change
- API deployed: new version (returns `fulfilled_at` in response, sets it on fulfillment)
- During rolling deploy: some instances are old (return response without `fulfilled_at`), some are new (return it). Clients must tolerate optional field.
- Rollback from here: redeploy old image. `fulfilled_at` column stays, old code ignores it. Safe.

Step 3 — (Optional) Remove old column if refactoring:
- Only applicable if you had an old column you were replacing. In this case, no old column was removed — this step does not apply.

### 3. Rollback procedure

Rollback is needed 10 minutes after Step 2 deploy — new API has a bug in the `fulfilled_at` response serialization.

- Action: trigger pipeline, redeploy previous image tag
- Schema: `fulfilled_at` column remains — old code ignores it, no harm
- In-flight orders: any `fulfilled_at` values already written stay in the DB, ignored by old code
- Queue: Go worker is not involved in this change — no action needed
- Time to rollback: depends on rolling deploy speed, but no manual DB intervention required

### 4. What breaks if you deploy migration and code simultaneously

Scenario: Step 1 and Step 2 are combined into one deploy (migration + new code in same pipeline step, applied to all instances at once).

During rolling deploy:
- New instances: running new code against new schema — works
- Old instances still running: running old code against new schema — `fulfilled_at` exists but is ignored, this is actually safe in this specific case

This scenario is accidentally safe because the new column is nullable with no NOT NULL constraint and old code doesn't reference it. But this is the exception, not the rule.

Now change the scenario: new code also removes the old `notes` column from the API response, and the migration drops it simultaneously.

- Old instances running old code: `SELECT notes FROM orders` — column is gone — query fails — 500 errors until old instances are replaced
- This is why simultaneous deploy is dangerous: it works until the migration removes something old code depends on

Lesson: simultaneous deploy is only safe if you can guarantee the migration is a pure addition with no removals. That guarantee is fragile across teams. The discipline is: always separate.

---

## Exercise 2: Rollback Design

**Incident:** New version of the Go worker has a bug. When processing fulfillment messages, it subtracts inventory twice instead of once (double-decrement). Deployed 30 minutes ago. 500 orders processed. Inventory counts for affected SKUs are now wrong by -500 units each (assuming 1-unit orders).

### 1. Immediate mitigation — stop the bleeding

- Stop the Go worker (kill the deployment / scale to 0 replicas)
- Do not process any more fulfillment messages
- Messages remain in the queue (not lost — queue is durable)
- Order processing will stall, but data corruption stops now
- Notify downstream: inventory service data is unreliable for the next N minutes
- Do not run any inventory reorder logic or fulfillment automation until counts are corrected

### 2. Rollback procedure for the Go worker

- Identify previous image tag (git SHA from deploy log or image registry)
- Trigger rollback pipeline: deploy previous image
- Verify health checks pass
- Do not resume queue processing yet — queue has messages that were correctly dequeued but not reprocessed; assess state first
- Once confirmed: resume queue processing with old worker
- Monitor: inventory decrements are now correct (subtract once)

### 3. What you cannot roll back automatically and why

**Inventory counts** — the database already has wrong values. Redeploying old code does not fix the data. The old worker will process future messages correctly, but the 500 corrupted records remain wrong.

Why: rollback restores behavior, not state. State mutations caused by the buggy code are permanent until explicitly corrected. There is no automatic undo for a committed database write.

**Queue messages already processed** — the 500 fulfillment messages were successfully dequeued and acknowledged. They are gone from the queue. The old worker cannot reprocess them because they no longer exist in the queue.

Why: at-least-once delivery means messages are acked on processing. The worker marked them done. Rollback does not restore them to the queue.

**Time** — 30 minutes of incorrect state may have already triggered downstream effects: reorder alerts, reporting snapshots, customer-facing inventory displays showing wrong counts.

### 4. Recovery steps for the 500 affected orders

**Identify affected records:**
- Query: all orders fulfilled in the 30-minute window by the new worker version
- Cross-reference with inventory audit log (if one exists) or reconstruct from order line items

**Calculate correct inventory delta:**
- Each affected order decremented inventory once too many times
- Correct adjustment: `UPDATE inventory SET quantity = quantity + 1 WHERE sku_id = ? AND order_id was processed in window`
- Or: aggregate by SKU — total over-decremented units per SKU = count of affected orders per SKU

**Apply compensating update:**
- Write a migration/script: corrects inventory counts for each affected SKU
- Run in a transaction with a dry-run first (log expected changes before committing)
- Verify: sum of corrections matches expected (500 orders × affected SKUs)

**Audit trail:**
- Record the correction as a named event in the audit log — do not silently patch
- Include: timestamp, cause (bug in worker version X), orders affected, SKUs corrected, delta applied

**Downstream notifications:**
- If inventory counts were consumed by other systems in the window: alert those systems
- If reorder triggers fired: cancel or review them
- If customer-facing counts were cached: invalidate cache

---

## Key takeaways from both exercises

Expand/contract is not optional on rolling deployments — it is the only safe sequencing when old and new code run simultaneously.

Rollback restores behavior. It does not restore state. Any system that modifies durable state (DB writes, queue acks, external API calls) accumulates changes that survive a rollback. Design for this — compensating actions must be pre-planned, not improvised.

The 3am rollback plan must be executable by someone who did not write the code. If it requires domain knowledge to figure out which records to fix — it is not a rollback plan, it is a hope.
