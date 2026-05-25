# Network Layer for Architects

Architects don't configure networks — they decide where components live and what flows between them. You need enough mental model to make the right call and ask the right question. Leave the CIDR blocks to the network engineers.

---

## Load Balancers

### L4 vs L7

| Dimension | L4 (TCP/UDP) | L7 (HTTP/HTTPS) |
|---|---|---|
| Operates at | Transport layer — sees IP + port | Application layer — sees HTTP headers, paths, cookies |
| Routing decisions | IP address + port only | Path, host, header, cookie values |
| TLS | Pass-through or terminate | Terminate (and optionally re-encrypt) |
| Throughput | Higher — no payload parsing | Slightly lower — must parse HTTP |
| Use case | Non-HTTP protocols, raw throughput, database proxying | Web services, APIs, microservices |

**Default choice for web services: L7.** Use L4 when you have non-HTTP protocols (Postgres TCP proxy, SMTP) or need raw throughput where HTTP parsing overhead matters.

### Where TLS Terminates

Three patterns:

**Terminate at load balancer (most common)**
- LB holds the cert, decrypts inbound traffic, forwards plain HTTP internally
- Requires internal network to be trusted
- Simple cert management — one cert at one place
- Right choice for most systems on private VPC/cloud network

**End-to-end TLS (re-encrypt)**
- LB terminates, re-encrypts to backend
- Traffic encrypted even on internal network
- Higher ops overhead: backend certs must also be managed and rotated
- Choose when compliance requires encryption in transit even on internal segments

**mTLS everywhere**
- Every service presents and validates a client cert
- Correct for zero-trust architecture
- Expensive to operate: cert rotation, service mesh required (Istio, Linkerd), debugging harder
- Choose when: zero-trust mandate, highly sensitive data, regulated environment

### Health Checks

Every service behind a load balancer needs a `/health` endpoint:
- Returns `200` only when the instance is fully ready to serve traffic
- Not "process is running" — "ready to serve": DB connection established, migrations complete, warm-up done
- LB polls health check on an interval (e.g. every 10s); after N consecutive failures, removes the instance from rotation
- Without this, LB sends traffic to instances that are starting up, draining, or degraded

What `/health` should check for Symfony API:
- Database connection available
- Redis connection available
- No critical config missing

What `/health` should NOT do:
- Run slow queries
- Check downstream services (that creates cascading failures — if Stripe is down, your instances aren't down)

### Sticky Sessions

LB routes the same user (by cookie or IP) to the same backend instance.

- Required when session state is stored locally on the instance (in-memory, local filesystem)
- **Architectural smell** — it means your service is stateful in a way that breaks horizontal scaling
- Failure mode: if the pinned instance goes down, that user's session is lost
- Fix: move session state to Redis, remove sticky sessions, make service stateless

---

## DNS

### TTL as a Deployment Tool

DNS TTL controls how long resolvers cache a record before re-querying.

| Scenario | TTL Strategy |
|---|---|
| Normal operation | 300s (5 min) — standard tradeoff of freshness vs resolver load |
| Before planned traffic shift | Lower to 30–60s, at least 2× current TTL in advance |
| After cutover complete | Raise back to 300s |
| Emergency failover to new IP | Low TTL was required before the emergency — you can't retroactively fix it |

**Blue-green cutover via DNS:** if your current TTL is 300s and you lower it right before cutover, you'll still have resolvers that cached the old value for up to 5 minutes. Pre-warm: lower TTL 24–48 hours before the cutover window.

### Internal Service Discovery vs DNS

| Approach | Mechanism | When to Use |
|---|---|---|
| Plain DNS | Services register A records, clients resolve by name | Kubernetes services (kube-dns), simple cloud setups |
| Service registry (Consul, AWS Cloud Map) | Services register on startup, deregister on shutdown, health-aware | Larger systems, need metadata, health-aware routing |
| Service mesh (Istio, Linkerd) | Sidecar proxies handle discovery + routing + mTLS | Complex microservices, zero-trust, canary routing needed |

Architect decision: complexity budget. DNS is almost always sufficient to start. Add a service registry when you need health-aware routing or cross-datacenter. Add a mesh when you need policy enforcement at the network layer.

---

## CDN

A CDN caches content at edge nodes close to users. Reduces round-trip latency from 100–200ms (origin) to 5–20ms (edge). Reduces origin load for cacheable traffic.

### What Architects Decide

**Cache policy per path** — set by `Cache-Control` response headers:
- `Cache-Control: public, max-age=86400` — cache for 24h, any proxy can store
- `Cache-Control: private, no-store` — do not cache anywhere
- `Cache-Control: public, max-age=3600, stale-while-revalidate=60` — cache 1h, serve stale while revalidating

**Purge strategy** — how to invalidate cached content when it changes:
- Tag-based purge: assign cache tags to responses, purge by tag (e.g. purge all `product-42` when product 42 changes)
- Path purge: invalidate a specific URL
- Global purge: nuclear option — clears everything, origin gets hit hard

**Origin shield** — an intermediate caching layer between CDN edge nodes and your origin server. When 100 edge nodes all miss cache simultaneously, only the shield node contacts origin. Reduces origin load dramatically for high-traffic spikes.

### When NOT to Cache

| Path Type | Cache? | Reason |
|---|---|---|
| Authenticated responses | No | Per-user content — caching leaks data across users |
| Real-time data (prices, inventory) | No | Must be fresh on every request |
| POST/PUT/DELETE responses | No | Mutations should never be cached |
| Static assets (CSS, JS, images) | Yes | Content-addressed (hash in filename), long TTL safe |
| Public, infrequently changing pages | Yes | With appropriate max-age and purge on publish |

---

## TLS and Certificates

### Certificate Rotation Without Downtime

Requirements:
1. **Dual-cert support during rotation** — load balancer or server must accept both old and new cert simultaneously during the transition window
2. **Automated renewal** — Let's Encrypt (certbot), AWS ACM auto-renews, no manual process
3. **Expiry monitoring** — alert at 30 days, page at 7 days. Certificate expiry is an operational failure, not a surprise.

Rotation failure mode: cert expires in production, HTTPS breaks, users see security errors. This is entirely preventable and entirely an ops/monitoring failure.

---

## Decision Table

| Traffic type | Security requirement | Session requirement | L4/L7 | TLS termination | Sticky sessions |
|---|---|---|---|---|---|
| HTTP API, web | Standard | Stateless (Redis session store) | L7 | At LB | No |
| HTTP API, web | Compliance: encrypt in transit | Stateless | L7 | Re-encrypt at LB | No |
| HTTP API, web | Zero-trust mandate | Stateless | L7 + service mesh | mTLS end-to-end | No |
| Database TCP proxy | N/A | N/A | L4 | Pass-through | No |
| Legacy app, local sessions | Standard | Stateful (fix this) | L7 | At LB | Yes (temporary) |
| High-throughput non-HTTP | Standard | N/A | L4 | At LB or pass-through | No |

---

## Anti-Patterns

**No health check endpoint** — LB sends traffic to instances that are starting up, shutting down, or in a degraded state. Every service needs `/health` that reflects actual readiness.

**Sticky sessions masking stateful service** — you think you fixed the problem (it works), but you've hidden a scaling and reliability problem. One instance failure = user sessions lost.

**High DNS TTL on services you need to failover quickly** — if TTL is 3600 and something goes wrong, you have up to an hour of traffic going to the dead endpoint. Establish TTL hygiene before you need it.

**CDN caching authenticated responses** — a bug in cache key configuration and User A sees User B's data. If a response depends on session/auth, `Cache-Control: private, no-store`.

**mTLS everywhere on day one** — operationally expensive, debugging is harder, slows down development. Earn it. Start with TLS termination at LB + trusted internal network. Add mTLS when you have the operational maturity for it.

**PoC that tests "does the load balancer work"** — LBs work. Test your specific failure modes: health check behavior during rolling deploy, sticky session failover, cert rotation under load.

---

## Šta da pitaš AI

- "We have [describe traffic flow, protocol, auth model]. Where should TLS terminate? What are the security tradeoffs of each option for our setup?"
- "Our Symfony API currently uses sticky sessions. Walk me through the failure modes and the migration path to stateless sessions with Redis."
- "We need to do a zero-downtime DNS cutover from IP A to IP B. Our current TTL is [X]. What is the exact TTL strategy and timing?"
- "Design the CDN cache policy for these paths: [list paths with descriptions]. For each: cacheable or not, Cache-Control header, purge trigger."
- "We're adding a Go worker that communicates with Symfony API internally. Does this traffic need TLS? What are the options and their tradeoffs?"
