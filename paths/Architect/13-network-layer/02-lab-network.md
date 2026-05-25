# Lab: Network Layer

---

## Exercise 1: Architecture Diagram with Network Layer

### Starting point

```
Browser → ??? → Symfony API (3 instances) → Postgres + Redis
```

Fill in the network layer. Answer each question in writing, then draw the diagram using the template below.

### Questions to answer

**1. What sits between Browser and Symfony?**

Choose from: L4 load balancer, L7 load balancer, API gateway + L7 LB, CDN + L7 LB. State which and why. Consider: Symfony API is HTTP, needs path-based routing in future, team is 4 engineers.

**2. Where does TLS terminate?**

State the termination point and what happens to traffic after it. State what internal traffic looks like (encrypted or plain). State what assumption you're making about network trust.

**3. What health check does each component need?**

Define `/health` behavior for:
- Symfony API instance: what does it check, what does it return, what makes it return non-200
- Postgres: does it need a health check exposed to the LB? How does the LB know if Postgres is degraded?
- Redis: same question

**4. How is session state handled without sticky sessions?**

The existing Symfony app stores PHP sessions in the local filesystem. You are removing sticky sessions.

State: (a) what changes in Symfony config, (b) what Redis key structure you'd use for sessions, (c) what the failure mode is if Redis goes down, and (d) whether you'd use a Redis cluster or single instance for sessions and why.

---

### Diagram template

Fill in each `[ ]`:

```
                    ┌─────────────────────────────────────────────┐
                    │                  [ CDN? ]                    │
                    │         (which paths, Cache-Control?)        │
                    └─────────────────────┬───────────────────────┘
                                          │ HTTPS
                                          ▼
                    ┌─────────────────────────────────────────────┐
                    │              [ L4 or L7 LB? ]               │
                    │    TLS terminates here? [ yes / no / re-encrypt ]
                    │    Health check: polls [ path ] every [ Xs ]│
                    └──────┬──────────────┬──────────────┬────────┘
                           │              │              │
                    [ HTTP or HTTPS? ]    │              │
                           │              │              │
                    ┌──────▼───┐   ┌──────▼───┐   ┌──────▼───┐
                    │ Symfony  │   │ Symfony  │   │ Symfony  │
                    │ API :80  │   │ API :80  │   │ API :80  │
                    │          │   │          │   │          │
                    │/health   │   │/health   │   │/health   │
                    │checks:   │   │checks:   │   │checks:   │
                    │[ list ]  │   │[ list ]  │   │[ list ]  │
                    └──────┬───┘   └──────┬───┘   └──────┬───┘
                           └──────────────┴──────────────┘
                                          │
                        ┌─────────────────┴──────────────────┐
                        │                                     │
               ┌────────▼────────┐                 ┌─────────▼────────┐
               │    Postgres     │                 │      Redis       │
               │ [ port, auth ]  │                 │ sessions: [ key ]│
               │ health: [ how ] │                 │ health: [ how ]  │
               └─────────────────┘                 └──────────────────┘
```

---

### Reference answer (review after completing)

<details>
<summary>Expand after you've written your own answer</summary>

**Between browser and Symfony:** L7 load balancer (e.g. AWS ALB, nginx, HAProxy). L7 because HTTP traffic needs path-based routing capability as the system grows, SSL termination, health check by HTTP status. No CDN needed yet unless there are static assets or the team is already managing one — defer CDN until latency or origin load is a problem.

**TLS termination:** At the L7 LB. LB holds the TLS cert. Internal traffic (LB → Symfony instances) is plain HTTP on a private network/VPC. Assumption: internal network is trusted — instances are on the same VPC and not reachable from the internet. This is correct for most cloud deployments.

**Health checks:**
- Symfony `/health`: checks DB connection (`SELECT 1`), Redis ping. Returns 200 only if both pass. Returns 503 if either fails. Does NOT call external services (Stripe, email — those failing doesn't mean your instance is unhealthy).
- Postgres: LB doesn't health-check Postgres directly. Symfony's `/health` includes the DB check — if DB is down, Symfony instances return 503 and LB stops sending traffic. Postgres itself monitored separately (CloudWatch, pg_stat, Prometheus postgres_exporter).
- Redis: same pattern — Symfony `/health` includes Redis ping. Redis monitored separately.

**Sticky sessions → Redis:**
- Symfony config: `session.save_handler = redis`, `session.save_path = tcp://redis:6379`. Remove any `session.sticky` LB config.
- Key structure: `symfony_session:{session_id}` — Symfony handles this automatically via the Redis session handler.
- Redis failure mode: if Redis is unavailable, session reads fail → users get logged out or see errors. Mitigation: Redis with replica + Redis Sentinel or Redis Cluster for HA. Alternatively, treat session loss as acceptable (re-login) and add graceful degradation.
- Single instance vs cluster: for sessions, Redis Sentinel (1 primary + 1 replica + sentinel for automatic failover) is sufficient for most loads. Full cluster adds complexity without benefit unless you're partitioning session data across many nodes for write throughput.

</details>

---

## Exercise 2: CDN Decision

### Context

E-commerce site. Origin: Symfony API behind an L7 LB. CDN sits in front of the LB.

### Paths to evaluate

| Path | Description |
|---|---|
| `/` | Homepage — marketing content, hero image, featured products. Updated by marketing team a few times per week. |
| `/products` | Product catalog. Prices and stock levels update hourly via a cron job. No auth required. |
| `/checkout` | Multi-step checkout flow. User must be authenticated. Cart contents are session-specific. |
| `/static/app.css`, `/static/app.js` | Compiled frontend assets. Filename includes content hash (e.g. `app.a3f9b2.css`). |
| `/api/orders` | REST endpoint returning authenticated user's order history. JSON response. |
| `/api/products/search` | Product search. Public. Results are the same for all users for a given query. Can be slightly stale. |

### Your task

For each path, complete this table:

| Path | CDN cacheable? | Cache-Control header | Purge trigger | Notes |
|---|---|---|---|---|
| `/` | | | | |
| `/products` | | | | |
| `/checkout` | | | | |
| `/static/` | | | | |
| `/api/orders` | | | | |
| `/api/products/search` | | | | |

---

### Reference answer (review after completing)

<details>
<summary>Expand after you've written your own answer</summary>

| Path | CDN cacheable? | Cache-Control header | Purge trigger | Notes |
|---|---|---|---|---|
| `/` | Yes | `public, max-age=3600, stale-while-revalidate=300` | On marketing publish event | 1h cache, serve stale while revalidating. Purge when content is updated — not on a schedule. |
| `/products` | Yes | `public, max-age=3600, stale-while-revalidate=60` | After hourly cron job completes | Max-age matches update frequency. Don't cache longer than update interval or users see stale stock/price. |
| `/checkout` | No | `private, no-store` | N/A | Session-specific. Must not be cached anywhere. Any caching here leaks one user's cart to another. |
| `/static/` | Yes | `public, max-age=31536000, immutable` | Never (content-addressed) | Hash in filename = new filename when content changes. Cache forever. `immutable` tells browser not to revalidate. |
| `/api/orders` | No | `private, no-store` | N/A | Authenticated, user-specific. Same as checkout. |
| `/api/products/search` | Yes | `public, max-age=300, stale-while-revalidate=60` | On product update | 5-min cache is acceptable if "slightly stale" per requirements. Vary by query string (CDN must key on full URL including `?q=...`). |

**Key point on `/api/products/search`:** Ensure CDN cache key includes the full query string. If the CDN treats `?q=shoes` and `?q=boots` as the same URL, it will serve the wrong cached response to all search queries.

**Key point on `/static/`:** The `immutable` directive tells browsers not to revalidate even after `max-age` would normally expire. Only safe because the filename changes when the file changes. Never use `immutable` on URLs that can serve different content at the same path.

</details>

---

## Checklist before moving on

- [ ] You can explain L4 vs L7 in one sentence each and name a scenario where you'd choose L4 over L7
- [ ] You can describe where TLS terminates in your reference architecture and what assumption that makes about the internal network
- [ ] You can define what a correct `/health` endpoint checks and what it deliberately does not check
- [ ] You can explain why sticky sessions are an architectural smell and the migration path
- [ ] You can fill in a CDN decision table for any path given its auth requirement and freshness requirement
- [ ] You know what DNS TTL strategy to use before a planned cutover
