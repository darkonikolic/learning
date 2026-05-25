# API Design Decisions

Architects sign off on API contracts. A bad API contract costs years.

---

## REST vs gRPC vs GraphQL

Decision table. Pick the column that matches your situation.

| Factor | REST | gRPC | GraphQL |
|---|---|---|---|
| Consumer type | External/public, broad clients | Internal service-to-service | Multiple consumers with divergent data needs |
| Performance | Adequate for most | High-throughput, low-latency critical | Acceptable overhead |
| Contract rigidity | Loose (JSON schema optional) | Strict (Protobuf required) | Flexible by design |
| Human-readable | Yes | No (binary) | Yes |
| Browser support | Native | Requires proxy (grpc-web) | Native |
| Tooling | Ubiquitous | Language-specific, good Go/Java | Client-side query complexity |
| Streaming | Awkward (SSE/polling) | First-class (bidirectional) | Subscriptions supported |
| Schema drift risk | High | Low (breaking at compile time) | Medium |
| Symfony support | Native | Requires bridge | Bundle available |

**Decision rules:**
- Default to REST unless you have a specific reason not to.
- Use gRPC for Symfony → Go worker communication when call volume is high or latency matters.
- Use GraphQL only when multiple consumers (mobile, web, third-party) genuinely need different shapes of the same data. Not because it's modern.
- Do not expose gRPC to public consumers without a REST/HTTP gateway in front.
- Do not use GraphQL for internal service-to-service. You pay schema flexibility overhead for no benefit.

---

## API Contract as a Commitment

Once an API is consumed externally, breaking changes cost more than the feature was worth.

**Breaking changes** — these break existing consumers silently or loudly:

| Change | Why it breaks |
|---|---|
| Remove a field from response | Consumers fail on missing key |
| Rename a field (`user_id` → `userId`) | Consumers read null or error |
| Change field type (`int` → `string`) | Consumers fail type assertions |
| Change HTTP status code (200 → 201) | Consumers checking exact status break |
| Change URL structure (`/orders/{id}` → `/order/{id}`) | All bookmarked/hardcoded URLs 404 |
| Remove an endpoint | All consumers of that endpoint break |
| Make optional field required | Consumers not sending it get 422 |

**Non-breaking changes** — safe to ship without a version bump:

| Change | Why it is safe |
|---|---|
| Add a new optional field to response | Consumers ignore unknown fields |
| Add a new optional request parameter | Existing requests still valid |
| Add a new endpoint | Consumers don't call it unless they opt in |
| Add a new HTTP status code for new error cases | Consumers already handle unknown errors (if well-written) |
| Expand enum values (with caution) | Only safe if consumers handle unknown enum values |

**Practical rule:** If you are unsure whether a change is breaking, assume it is. Check consumer code before shipping.

---

## Versioning Strategies

| Strategy | Example | Pros | Cons |
|---|---|---|---|
| URL versioning | `GET /v1/orders` | Obvious, debuggable, cacheable, easy to route in Nginx/Symfony | URL "pollution", version in wrong layer semantically |
| Header versioning | `API-Version: 2` | Cleaner URL design | Invisible in browser, harder to test, harder to route |
| Content negotiation | `Accept: application/vnd.api+json;version=2` | RFC-correct | Complex, poor tooling support, nobody does it well |

**Verdict: URL versioning.** It wins on debuggability and operational simplicity. Header versioning is architecturally cleaner but the operational cost is real — logs, routing rules, client testing all become harder.

Pick one strategy. Enforce it at the gateway level. Never mix URL and header versioning in the same API.

**Symfony implementation:** Route prefix per version in `config/routes/`. Each version gets its own controller namespace. Shared logic extracted to services, not shared between controllers.

---

## Deprecation Process

Steps to retire a version without breaking consumers:

1. **Announce sunset date** — add `Sunset` and `Deprecation` headers to all responses from the deprecated version.
   ```
   Sunset: Sat, 31 Dec 2025 23:59:59 GMT
   Deprecation: Mon, 01 Jul 2025 00:00:00 GMT
   Link: <https://api.example.com/v2/docs>; rel="successor-version"
   ```
2. **Publish migration guide** — diff between v1 and v2 response shapes, with code examples for major consumers.
3. **Monitor usage** — log requests to deprecated endpoints. Track by consumer (API key, user agent). Do not cut off consumers still actively using it.
4. **Notify consumers directly** — email/Slack to known API key holders. Do not rely on headers alone.
5. **Hard cutoff** — return 410 Gone after sunset date. Not 404. 410 signals permanent removal.

**Minimum sunset windows:**
- External/public API: 6 months
- Partner integrations: 6 months
- Internal services you own: 3 months
- Internal services other teams own: 3 months, with a team sign-off

Do not let sunset windows slip. A slipped sunset date signals to consumers that deadlines are not real.

---

## Pagination Architecture

| Strategy | How it works | Stable on insert? | Stateless? | Use when |
|---|---|---|---|---|
| Offset | `?page=2&per_page=20` | No — inserts shift pages | Yes | Small static datasets, admin panels |
| Cursor | `?after=eyJpZCI6MTIzfQ==` | Yes | Yes | High-volume, frequently updated data |
| Keyset | `?after_id=123` | Yes | Yes | Simple cases, single sort key |

**Offset problem in practice:**
- User loads page 2 of job listings. While they read, 5 new jobs are inserted at the top.
- Page 3 now contains items that were on page 2. User sees duplicates or misses items.
- At 100k rows with frequent inserts, offset pagination is unreliable by default.

**Default: cursor-based pagination.** Encode the cursor as base64 JSON (`{"id": 123, "created_at": "..."}`). Opaque to consumers, cheap to implement, stable under inserts.

**Symfony + Doctrine:** Implement as a `PaginatorService` with `WHERE id > :cursor ORDER BY id ASC LIMIT :limit`. Return `next_cursor` in response envelope.

---

## Idempotency Keys

POST requests that must not duplicate need idempotency keys. Non-negotiable for financial operations, order creation, or any operation with real-world side effects.

**Flow:**
```
Client                          Server                         Redis / DB
  |                                |                               |
  |-- POST /orders                 |                               |
  |   Idempotency-Key: uuid-1234   |                               |
  |                                |-- GET idempotency:uuid-1234 -->|
  |                                |<-- null (not found) -----------|
  |                                |-- process order               |
  |                                |-- SET idempotency:uuid-1234 ->|
  |                                |   (result, TTL: 24h)          |
  |<-- 201 Created (order) --------|                               |
  |                                |                               |
  |-- POST /orders (retry)         |                               |
  |   Idempotency-Key: uuid-1234   |                               |
  |                                |-- GET idempotency:uuid-1234 -->|
  |                                |<-- cached result --------------|
  |<-- 201 Created (same order) ---|                               |
```

**Rules:**
- Client generates the key (UUID v4). Server does not generate it.
- Store result keyed by `{endpoint}:{idempotency_key}` to prevent cross-endpoint collisions.
- TTL: 24 hours is standard. Align with your retry window.
- Return the same HTTP status code and body on replay.
- If the original request is still in flight, return 409 Conflict (not a duplicate, not ready yet).
- Redis is the right store. Not Postgres — you need fast lock semantics and TTL.

---

## Anti-Patterns

**A-1: Breaking API changes in a patch release.**
"We just renamed the field — it's a small change." Renames are breaking changes. Version bump required. No exceptions for external consumers.

**A-2: No versioning strategy until the first breaking change is needed.**
By then you have consumers in production and no clean path. Versioning must be designed before the first public release, not retrofitted.

**A-3: GraphQL for internal service-to-service communication.**
You pay the overhead of client-driven queries between services you control. Use gRPC (typed, fast) or REST (simple). GraphQL's value is consumer flexibility — you have no unknown consumers internally.

**A-4: Offset pagination on high-volume, frequently-updated datasets.**
Job listings, product catalogs, feed data. Offset is a trap. Cursor from day one.

**A-5: Idempotency keys as optional.**
"We'll add it later." Payment processing, order creation, and anything that charges money or allocates resources does not get a "later." It ships with idempotency or it does not ship.

**A-6: Sunset dates with no enforcement.**
Announcing a date and then not cutting off the endpoint teaches consumers to ignore your deprecation notices. If you set a date, honor it.

---

## What to Ask AI

- "We have [describe consumers: external mobile app, third-party integrations, internal Go workers]. Should this be REST, gRPC, or GraphQL? What are the tradeoffs for our specific case?"
- "We need to make this breaking change to our API: [describe change, e.g., rename `user_id` to `userId` in the orders response]. What is the safest migration path for [external consumers / internal services]?"
- "Design the pagination strategy for [endpoint description: 100k job listings, updated frequently, sorted by posted_at]. When would offset break and why? Show me the cursor implementation for Symfony + Doctrine."
- "Our Symfony API calls a Go worker service 500 times per second. Should this be REST or gRPC? What do I need to add to Symfony to support gRPC clients?"
- "We have a v1 API in production with 3 known external consumers. We need to ship a breaking change. Write the deprecation announcement headers and migration guide template."
- "Review this idempotency key implementation [paste code]. What edge cases does it miss?"
