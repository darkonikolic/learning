# Lab: Storage Decisions — Job Marketplace

Two exercises. The first tests storage choice. The second tests migration design. Both use the decision framework from `01-storage-decisions.md`.

---

## Exercise 1: Storage Choice for a Job Marketplace

**System:** Job marketplace platform. Employers post jobs, applicants apply, both sides message each other, and the system generates recommendation scores per applicant/job pair.

**Team:** 5 engineers. Single Postgres database currently. Considering whether each entity needs a different storage strategy.

**Entities and their access patterns:**

| Entity | Description |
|---|---|
| Job listings | ~500k active listings. Employers create, update, close. Applicants search by title, location, salary, skills. Filtering and ranking on 10+ attributes. |
| Applications | Applicants apply to jobs. One applicant → one job = one application. Status transitions: applied → reviewed → interview → offer → rejected. Employers query by job_id. Applicants query by their own history. |
| Companies | ~50k companies. Name, description, size, industry, logo URL. Rarely updated. Frequently read. |
| Users (applicants) | ~2M users. Registration, login, profile (skills, experience, education), resume PDF reference. |
| Messages | Direct messages between applicant and employer per application. Append-only thread. ~5M messages/month. Query: load thread for application_id. |
| Recommendation scores | ML-generated score per (user_id, job_id) pair. Updated nightly in batch. ~100M pairs. Query: given user_id, return top-50 job_ids by score. |

---

**For each entity, fill in this table:**

| Entity | Primary Query Pattern | Secondary Query Pattern | Consistency Requirement | Write Pattern | Storage Choice | Justification |
|---|---|---|---|---|---|---|
| Job listings | | | | | | |
| Applications | | | | | | |
| Companies | | | | | | |
| Users | | | | | | |
| Messages | | | | | | |
| Recommendation scores | | | | | | |

**Guiding questions per entity:**
- What does the most common read look like? (key lookup, full-text search, range scan, join)
- What happens if the read returns stale data by 5 seconds? 5 minutes? (consistency requirement)
- Is the write pattern insert-only, update-heavy, or batch?
- How many rows/documents at steady state?

---

## Example Answer: Job Listings

| Field | Value |
|---|---|
| Primary query pattern | Full-text search + faceted filtering: "software engineer in Berlin, €70–90k, full-time, Python required" |
| Secondary query pattern | Employer loads their own listings by company_id (key lookup) |
| Consistency requirement | AP — a listing that is 30 seconds stale in search results is acceptable. A listing being unindexed for 30 seconds after creation is acceptable. |
| Write pattern | Create/update by employer (~moderate volume). Status transitions (open → closed) are low volume. |
| Storage choice | **Postgres as source of truth + Elasticsearch/Typesense as search index** |
| Justification | Full-text search with ranking and multi-facet filtering is not efficient in Postgres. A search index gives sub-100ms ranked results on 500k documents. Postgres remains the authoritative store. Write to Postgres first, sync to search index asynchronously. |

**Note the gap:** search index is eventually consistent with Postgres. A newly posted job will appear in Postgres immediately but may not appear in search results for up to ~10 seconds (depending on indexing pipeline). Acceptable for this use case. Not acceptable for a checkout stock check.

---

**Complete the table for the remaining 5 entities.** Pay particular attention to:
- **Recommendation scores**: the scale (100M pairs) and the query pattern (top-N for a user) point strongly away from a naive relational approach. What is the right structure?
- **Messages**: append-only and thread-scoped. Does this need a separate store or does Postgres handle it cleanly?
- **Companies**: high read, low write, moderate size. Where does caching belong in the picture?

---

## Exercise 2: Migration Design

**Context:** Production system. Postgres. Table `orders` with 10 million rows. High write volume: ~200 inserts/minute during peak hours. The table is read on every page load for order status.

**Requirement:** Add a column `fulfilled_at TIMESTAMP` that records when an order reached the `fulfilled` status. Business logic: for historical orders already in `fulfilled` status, the value should be set to `updated_at` (the closest proxy available). For future orders, it will be set at transition time.

**The naive migration:**
```sql
ALTER TABLE orders ADD COLUMN fulfilled_at TIMESTAMP NOT NULL DEFAULT NOW();
UPDATE orders SET fulfilled_at = updated_at WHERE status = 'fulfilled';
UPDATE orders SET fulfilled_at = NULL WHERE status != 'fulfilled';
```

This will cause an outage. Do not do this.

---

**Design the correct migration. Answer these questions:**

**1. Which strategy applies?**
Choose from: Expand/Contract, Shadow Writes, Read From Both, Feature-Flagged Cut Over. Justify your choice.

**2. Write out the steps in order.**

For each step, specify:
- What SQL or code change is involved
- What the application code does at this point
- Whether this step requires a deployment
- Whether this step is reversible

**3. What is the rollback plan?**

At which steps can you roll back cleanly? What does rollback look like for each?

**4. What do you tell the team?**

Write the 3-sentence message you send to the engineering team before starting the migration. Cover: what is happening, what downtime risk exists, what the rollback plan is.

---

## Reference: Migration Strategy Template

Use this template for Exercise 2 and future migrations:

```
Migration: [Name]
Table: [table name]
Row count: [estimated]
Write volume: [peak writes/minute]
Strategy: [Expand/Contract | Shadow Writes | Read From Both | Feature-Flagged]

Steps:
  Step 1: [SQL or code change]
    - App behavior: [what application code does here]
    - Deployment required: Yes/No
    - Reversible: Yes/No — [how to reverse]
  Step 2: ...

Backfill plan:
  - Batch size: [rows per transaction]
  - Batch delay: [sleep between batches in ms]
  - Estimated duration: [total time for backfill]
  - Monitoring: [what to watch during backfill]

Rollback:
  - Before step N: [rollback action]
  - After step N: [rollback action or "point of no return"]

Communication:
  - Team message: [what you tell engineers]
  - Incident escalation: [who to call if it goes wrong]
```

---

## Example Answer: Exercise 2 (Partial)

**Strategy: Expand/Contract**

This is a column addition with a backfill. The old column doesn't need to be dropped. The expand phase adds the column safely; the backfill runs in batches; the application starts writing to the new column at a defined deploy point.

**Step 1 — Expand (add nullable column)**
```sql
ALTER TABLE orders ADD COLUMN fulfilled_at TIMESTAMP NULL;
```
- This is a metadata-only change in Postgres 11+. No table rewrite. Near-instantaneous.
- App behavior: application ignores the new column. Still reads/writes existing columns only.
- Deployment required: No (schema migration only, app is unaffected)
- Reversible: Yes — `ALTER TABLE orders DROP COLUMN fulfilled_at;`

**Step 2 — Backfill in batches**
```sql
-- Run in batches, not as a single statement
UPDATE orders
SET fulfilled_at = updated_at
WHERE status = 'fulfilled'
  AND fulfilled_at IS NULL
  AND id BETWEEN :batch_start AND :batch_end;
```
- Batch size: 5,000 rows per transaction
- Sleep between batches: 100ms to avoid lock contention under write load
- Estimated duration at 10M rows, 5k/batch, 100ms delay: ~200 batches × 100ms = ~20 minutes for the fulfilled subset
- Monitor: `pg_stat_activity`, replication lag on replica, application error rate

**Step 3 — Deploy application code to write `fulfilled_at` on transition**
- Application now sets `fulfilled_at = NOW()` when an order transitions to `fulfilled` status
- Deployment required: Yes
- Reversible: Yes — deploy previous version; column goes back to null for new transitions (backfill data is unaffected)

**Step 4 — Add NOT NULL constraint (if required by application)**
```sql
-- Only after backfill is complete and application is writing the column
ALTER TABLE orders ALTER COLUMN fulfilled_at SET NOT NULL;
```
- In Postgres 12+: if all rows have non-null values, this is a constraint-only change (no table scan)
- In Postgres < 12: this triggers a table scan — test on a production-sized copy first
- Reversible: Yes — `ALTER TABLE orders ALTER COLUMN fulfilled_at DROP NOT NULL;`

**Rollback plan:**
- Before Step 3: drop the column — no application impact
- After Step 3: deploy previous application version — fulfilled_at column stays but new transitions stop writing to it; not a data integrity problem
- After Step 4: drop the NOT NULL constraint — instantaneous

**Team message:**
> We are adding `fulfilled_at` to the orders table over the next 30 minutes. The migration runs in batches with no downtime — the ALTER TABLE step is instantaneous in Postgres 11+. If anything goes wrong during the backfill we can drop the column with no impact on the running application. I will post status here and @channel if anything requires attention.
