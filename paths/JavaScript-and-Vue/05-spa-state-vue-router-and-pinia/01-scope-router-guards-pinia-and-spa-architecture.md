# Unit 1 — Scope: SPA architecture — router, Pinia, auth, persistence

Mindset shift: from “where do I put this variable” toward **explicit ownership** across routes and stores.

## Learning outcomes

- **Router mental model**: URL ↔ matched view; history API without full reload; dynamic params vs static routes.
- **Navigation API**: imperative navigation vs declarative links; understanding back/forward behaviour.
- **Pinia purpose**: kill prop-drilling for cross-cutting client state; multiple focused stores vs one mega-store.
- **Store boundaries**: `cart`, `auth`, `catalog` (examples) with clear responsibilities.
- **Auth arc**: login → token/session → store → guard → protected route; logout semantics.
- **Guards**: `beforeEach` — redirect unauthenticated users; optional role checks (admin vs user).
- **Persistence**: refresh must not erase critical UX state (cart); hydration patterns and trade-offs (security later in **`09-*`**).
- **Async UX per flow**: each remote operation owns **loading / success / error** states (not a global boolean soup).

Practice spine: **`shop-spa/`** — Vue 3 + **Vue Router + Pinia** + fake/Symfony-backed API.
