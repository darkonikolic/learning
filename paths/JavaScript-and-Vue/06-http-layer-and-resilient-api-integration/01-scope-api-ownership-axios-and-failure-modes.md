# Unit 1 — Scope: treating HTTP as a distributed system (frontend view)

Mindset shift: from “I called the endpoint” toward **the UI owns user-visible outcomes of network failure.**

## Learning outcomes

- **Layering**: components call **services/modules**; raw HTTP lives in `api/` (or equivalent), not inside leaf components.
- **HTTP client**: central `apiClient` with base URL, headers, timeouts, shared interceptors (Symmetry with Symfony API or mocks).
- **Per-request state machine**: idle → loading → success | error | empty; avoid copy-pasted booleans.
- **Error taxonomy**: validation vs network vs server vs auth; map errors to UX (retry, redirect to login, inline message).
- **Retry**: bounded retries with backoff awareness; when *not* to retry (non-idempotent writes without care).
- **Cancellation**: `AbortController` for fast typing / route changes / duplicate inflight calls.
- **Optimistic UI**: instant feedback with explicit rollback when mutation fails.
- **Timeouts & slow APIs**: surface stuck states; contrast with infinite spinners.

Continue extending **`shop-spa/`** against real or fake backend contracts. Carry **typed seams** from **`03-*`** (`unknown` ingestion, guards, discriminated API errors) into the HTTP layer implementation—no silent `any` in interceptors.

