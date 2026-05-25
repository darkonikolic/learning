# Lab: API Design Decisions

---

## Reference: Breaking vs Non-Breaking Changes

| Change | Breaking? | Affects External? | Affects Internal? |
|---|---|---|---|
| Remove field from response | Yes | Yes | Yes |
| Rename field (`user_id` → `userId`) | Yes | Yes | Yes |
| Change field type (`int` → `string`) | Yes | Yes | Yes |
| Change HTTP status code | Yes | Yes | Yes |
| Change URL path | Yes | Yes | Yes |
| Remove endpoint | Yes | Yes | Yes |
| Make optional field required | Yes | Yes | Yes |
| Add new optional response field | No | No | No |
| Add new optional request param | No | No | No |
| Add new endpoint | No | No | No |
| Add new enum value | Depends | Only if consumer rejects unknown values | Depends |
| Change error message text | No | No | No |
| Change error code within same status | Yes | Yes | Yes |

---

## Deprecation Timeline Template

```
Version: v1
Deprecated: 2025-07-01
Sunset: 2025-12-31
Migration target: v2
Migration guide: https://docs.example.com/migrate/v1-to-v2

Timeline:
  T+0   (2025-07-01): v2 released. v1 marked deprecated.
                       Deprecation + Sunset headers added to all v1 responses.
                       Migration guide published.
                       All known consumers notified directly.
  T+30  (2025-08-01): Usage report. Follow up with consumers above 10% of v1 traffic.
  T+90  (2025-10-01): Second notice to consumers still on v1.
  T+150 (2025-11-28): Final notice. 30 days remaining.
  T+183 (2025-12-31): Hard cutoff. v1 returns 410 Gone.

Response headers on v1 from T+0:
  Deprecation: Tue, 01 Jul 2025 00:00:00 GMT
  Sunset: Wed, 31 Dec 2025 23:59:59 GMT
  Link: <https://api.example.com/v2/docs>; rel="successor-version"
```

---

## Idempotency Key Flow

```
POST /orders  (first attempt)
Headers: Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000

  Client                    Symfony API                Redis
    |                           |                        |
    |--POST /orders ----------->|                        |
    |  Idempotency-Key: uuid    |                        |
    |                           |--GET orders:uuid ----->|
    |                           |<--null (miss)----------|
    |                           |                        |
    |                           | [process order]        |
    |                           | [write to Postgres]    |
    |                           |                        |
    |                           |--SET orders:uuid ----->|
    |                           |  value: {201, body}    |
    |                           |  TTL: 86400s           |
    |<--201 Created ------------|                        |


POST /orders  (retry — network timeout, client unsure if it landed)
Headers: Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000

  Client                    Symfony API                Redis
    |                           |                        |
    |--POST /orders ----------->|                        |
    |  Idempotency-Key: uuid    |                        |
    |                           |--GET orders:uuid ----->|
    |                           |<--{201, body} (hit)----|
    |<--201 Created (replay)----|                        |
    |   [same order, no dup]    |                        |


POST /orders  (concurrent — first request still in flight)
Headers: Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000

  Client                    Symfony API                Redis
    |                           |                        |
    |--POST /orders ----------->|                        |
    |  Idempotency-Key: uuid    |                        |
    |                           |--GET orders:uuid ----->|
    |                           |<--LOCKED (in flight)---|
    |<--409 Conflict ------------|                       |
    |   [retry after delay]     |                        |
```

---

## Exercise 1: API Contract Review

**Proposal:** "Rename `user_id` to `userId` in the orders response for consistency with our new frontend convention."

**Work through each question before reading the answer scaffold.**

---

**Question 1: Is this breaking? For whom?**

Consider:
- Which consumers call `GET /orders` or any endpoint returning order objects?
- What happens to code that reads `response['user_id']` when the field becomes `userId`?
- Does "consistency with the frontend" justify breaking server contract for all other consumers?

Answer scaffold:
- Yes, this is a breaking change for any consumer that reads `user_id` by name.
- External consumers (mobile apps, third-party integrations) break silently — they read null or throw a key error.
- Internal consumers (other services, the Go worker if it reads order data) break depending on their deserialization.
- The frontend convention is irrelevant to the API contract. Frontend can alias the field.

---

**Question 2: Migration path if external consumers exist**

Design the migration:
- Can you ship both fields (`user_id` and `userId`) simultaneously during a transition window?
- What version do you create for the renamed field?
- How long is the transition window?
- What headers do you add to the old field?

Answer scaffold:
1. Create v2 with `userId`. Keep v1 with `user_id` unchanged.
2. Do not ship the rename to v1. v1 contract is frozen.
3. Announce v2 with migration guide. Set sunset on v1 (minimum 6 months for external).
4. Optionally add both fields to v1 for a transition window: `user_id` (deprecated) + `userId` (new). Remove `user_id` only in v2.
5. Monitor v1 traffic. Cut off at sunset date.

---

**Question 3: Migration path if only internal consumers exist**

Design the migration:
- Are internal consumers different enough to change the process?
- What is the minimum sunset window for internal services?
- Who needs to sign off?

Answer scaffold:
1. Still a breaking change — internal consumers have code that reads `user_id`.
2. Coordinate with each consuming team directly. Do not assume they will notice header changes.
3. Minimum 3 months. Shorter if all consuming teams confirm they have migrated.
4. Require explicit sign-off from each team before cutting over.
5. Option: deploy both field names, confirm all internal consumers updated, remove `user_id`. Faster than a full version bump for internal-only.

---

**Question 4: What would you add to the ADR for this decision?**

Draft the key sections:

- **Context:** Frontend wants camelCase field names. Orders API currently returns `user_id`.
- **Decision:** Field rename treated as breaking change. v2 endpoint introduced with `userId`. v1 maintained until sunset.
- **Rejected alternatives:** Rename in v1 directly (breaks external consumers). Ship both fields indefinitely (schema debt).
- **Consequences:** v1 sunset window starts [date]. External consumers must migrate. Monitoring added to track v1 usage. Sunset date: [date + 6 months].
- **Sunset criteria:** v1 traffic below 1% of total orders traffic, or all known consumers confirmed migrated.

---

## Exercise 2: Versioning Decision

**System:** Job marketplace API. Currently no versioning. v1 consumers in production.

New consumers coming:
- Employer dashboard (different data shape — needs aggregate stats, not raw listings)
- Mobile app (bandwidth-sensitive — needs stripped-down responses)
- Third-party integrations (strict contracts — they pin to specific response shapes)

---

**Question 1: Versioning strategy choice with justification**

Consider:
- You have three consumers with genuinely different needs.
- Third-party integrations require strict contracts.
- Mobile needs smaller payloads.
- Employer dashboard needs different data, not just less data.

Design your answer:
- URL versioning (`/v1/`, `/v2/`) or header versioning? Why?
- Do different consumers get different endpoints or different versions?
- Where do you enforce versioning — gateway, Symfony routing, both?

Answer scaffold:
- **URL versioning.** Three consumer types, all with different operational teams/organizations. URLs are debuggable in logs, browser, curl. Header versioning fails when a third-party integration sends a ticket saying "it's broken" and you cannot see the version in the URL.
- Introduce `/v2/` for employer dashboard (different data shape = new version, not a new endpoint option).
- Mobile bandwidth: sparse fieldsets via `?fields=id,title,salary` added to v1 — this is not a breaking change.
- Third-party integrations: lock to `/v1/`. They freeze there. Future changes go to `/v2/`, `/v3/`.
- Enforce via Symfony route prefix. Add a middleware that logs version usage per API key.

---

**Question 2: Which endpoints need idempotency keys and why**

Go through the likely endpoints:

| Endpoint | Idempotency key needed? | Why |
|---|---|---|
| `POST /jobs` (employer posts a job) | Yes | Duplicate job listings are real-world harm and billing events |
| `POST /applications` (candidate applies) | Yes | Duplicate applications corrupt employer view, may trigger emails |
| `POST /employers` (account creation) | Yes | Duplicate accounts on retry = support burden |
| `GET /jobs` | No | Read-only, idempotent by definition |
| `PUT /jobs/{id}` | No | PUT is idempotent by HTTP semantics |
| `DELETE /jobs/{id}` | No | DELETE is idempotent by HTTP semantics |
| `POST /payments` (if billing exists) | Yes | Non-negotiable |

Implementation: `Idempotency-Key` header on all POST endpoints listed above. Store in Redis keyed by `{endpoint_path}:{idempotency_key}`. TTL 24h.

---

**Question 3: Pagination strategy for job listings (100k jobs, updated frequently)**

Work through the choice:

- 100k rows. Offset at page 50 (`OFFSET 1000`) requires scanning 1000 rows to discard.
- Jobs are posted and expired continuously. Page 2 you loaded 10 minutes ago is now different.
- Mobile clients need to resume a scroll session after backgrounding the app.

Design:
- Cursor or offset? What cursor field?
- What is the response envelope?
- How does the mobile app handle resuming a session?

Answer scaffold:
- **Cursor-based pagination.** Encode `{id, posted_at}` as base64 JSON cursor.
- Sort by `posted_at DESC, id DESC` (stable secondary sort on id for same-timestamp rows).
- Query: `WHERE (posted_at, id) < (:cursor_posted_at, :cursor_id) ORDER BY posted_at DESC, id DESC LIMIT 20`.
- Response envelope:
  ```json
  {
    "data": [...],
    "pagination": {
      "next_cursor": "eyJwb3N0ZWRfYXQiOiIyMDI1LTA1LTIwIiwiaWQiOjEyM30=",
      "has_more": true
    }
  }
  ```
- Mobile resume: client stores `next_cursor` locally. On app resume, sends cursor in next request. Gets correct next page regardless of how many jobs were posted while app was backgrounded.
- Offset is acceptable only for the employer admin panel listing their own jobs (small bounded set, rarely updated).
