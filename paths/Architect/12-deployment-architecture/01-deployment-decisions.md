# Deployment Decisions

Deployment strategy is an architectural decision. It determines blast radius of bad releases, downtime windows, rollback cost, and how fast you can ship safely. Architects sign off on this — not because they run pipelines, but because the strategy constrains everything else: database migration sequencing, rollback feasibility, infrastructure cost, and ops burden.

---

## Deployment Strategies

| Strategy | Mechanism | Downtime | Rollback speed | Extra cost | Key constraint |
|---|---|---|---|---|---|
| Rolling | Replace instances one by one | Zero | Minutes (redeploy old image) | None | Both versions run simultaneously — must be backward compatible |
| Blue-green | Two identical environments, switch traffic atomically | Zero | Seconds (flip LB back) | Double infra during switch | DB migrations must be compatible with both versions |
| Canary | Route N% of traffic to new version first | Zero | Immediate (drain canary, route to stable) | Traffic splitting infra | Requires metrics comparison and automated or manual promotion gate |
| Feature flags | Deploy code dark, enable per user/segment | Zero | Immediate (disable flag) | Flag management system, dead code | Separates deploy from release; flags must be cleaned up |

### When to choose what

| Factor | Lean toward |
|---|---|
| Low ops maturity, low traffic | Rolling |
| Need fast rollback, acceptable infra cost | Blue-green |
| High traffic, complex change, blast radius matters | Canary |
| Major feature, A/B testing, gradual user rollout | Feature flags |
| Non-backward-compatible DB migration | Blue-green (but migration must still be backward compatible) |
| Rollback SLA < 60 seconds | Blue-green or feature flag |

### Decision matrix: four factors

| Traffic volume | Rollback SLA | DB migration complexity | Ops maturity | Strategy |
|---|---|---|---|---|
| Low | > 1 hour | Simple additive | Low | Rolling |
| Low | < 15 min | Simple additive | Low | Blue-green |
| Medium | < 15 min | Backward compatible | Medium | Blue-green |
| Medium | < 15 min | Requires expand/contract | Medium | Rolling with strict 3-step sequence |
| High | < 5 min | Any | High | Canary |
| High | < 60 sec | None (code-only change) | High | Feature flag |
| Any | Immediate | None | Any | Feature flag (per-user rollout) |
| Any | Any | Not backward compatible | Any | Block deploy — fix migration first |

The last row is the most important. "Not backward compatible" is not a deployment strategy decision — it is a blocker. Fix it before choosing a strategy.

### Operational requirements per strategy

| Strategy | Requires |
|---|---|
| Rolling | Backward-compatible code + schema; image tagging; health checks |
| Blue-green | Two full environments; LB traffic switching; migration runs before switch |
| Canary | Traffic splitting (LB weights or service mesh); metrics pipeline; promotion gate |
| Feature flags | Flag management service (LaunchDarkly, Unleash, or custom); flag cleanup discipline |

---

## Database Migrations in Deployments

This is the hardest part. The constraint: **a migration must be backward compatible with the currently running version of the application**.

Rolling or canary deployments mean old code and new code run simultaneously. If the migration breaks old code, you have an incident the moment it runs.

### Expand/contract pattern

Never deploy migration and code simultaneously. Instead:

**Step 1 — Expand (safe migration first)**
Deploy the migration that adds the new column. Old code ignores the new column. System continues working.

**Step 2 — Deploy new code**
New code reads and writes the new column. Old column still exists. Both work. No simultaneous deploy.

**Step 3 — Contract (cleanup migration)**
Once all instances run new code and old column is confirmed unused, deploy the migration that removes the old column.

This takes three deploys. That is the correct number.

### What breaks with simultaneous deploy

Deploy code and migration at the same time: during the rolling update, some instances run old code against the new schema. If new schema removes a column old code reads — query fails. If new schema renames a column — same. "Works in staging" because staging is a single instance that flips atomically.

### Migration backward compatibility checklist

- Adding a nullable column: safe
- Adding a column with a default: safe
- Dropping a column: unsafe unless no running code references it
- Renaming a column: unsafe — treated as drop + add
- Adding a NOT NULL column without default: unsafe — old inserts fail
- Adding an index: safe (use `CONCURRENTLY` in Postgres to avoid table lock)
- Adding a foreign key: check if old code can insert rows that would violate it

---

## Rollback Design

Rollback must be designed before deployment, not after the incident.

### Stateless services (Symfony API, Go worker)

Rollback = redeploy previous image. Tag every image with git SHA. Keep the previous N images. Rollback is a pipeline trigger.

### Database changes

Only rollbackable if the migration was backward compatible. If it was — the old code still works against the current schema. If it wasn't — rollback means running a compensating migration under time pressure at 3am. That is a system design failure, not an ops problem.

### Queue consumers (Go worker)

Queue messages were written by old code or new code. After rollback, old worker processes messages written by both. Options:
- **Version-aware message processing**: worker checks message version field and handles both
- **Separate queues per version**: new code writes to new queue; rollback leaves old queue intact
- **At-minimum**: ensure old worker does not corrupt state when it encounters messages it doesn't understand (dead-letter, not silent ignore)

### Rollback decision tree

```
Bad deploy detected
├── Stateless service bug, no DB migration
│   └── Redeploy previous image → done
├── DB migration was backward compatible
│   └── Redeploy previous image (migration stays) → done
├── DB migration was not backward compatible
│   └── Cannot rollback automatically
│       └── Compensating migration required → incident, not rollback
└── Queue messages corrupted
    └── Stop consumer → assess corrupted records → manual recovery required
```

---

## Zero-Downtime Deployment Requirements

Three requirements. If any is missing, you will have downtime or errors during deploy.

**1. Load balancer health checks**
New instance must pass health check before receiving traffic. Health check endpoint must verify: app is ready (not just started), dependencies are reachable (DB connection pool initialized, Redis connected). Without this: LB sends traffic to an instance that is still warming up — connection refused or 500s.

**2. Graceful shutdown**
When a SIGTERM arrives (deploy replacing this instance): stop accepting new connections, finish in-flight requests, then exit. Set a drain timeout (30s is common). Without this: in-flight requests are killed mid-processing — data corruption, failed transactions, broken responses.

**3. Connection pool warmup**
Database and Redis connection pools take time to reach target size. New instance getting full traffic immediately overwhelms the pool — connections queue, timeouts spike. Solutions: pre-warm pool before going live (health check waits until pool is ready), or ramp traffic slowly (canary/rolling gives natural warmup time).

---

## Environment Parity

Production incidents from environment differences are not bad luck — they are a configuration management failure.

Dev/staging must match production in:
- Config structure (not values — secrets differ, structure must not)
- Infrastructure topology (if prod has a Redis sentinel cluster, staging must too — not a single Redis)
- Dependency versions (Postgres minor version, Redis version, PHP version)
- Queue configuration (same queue names, same message formats)

The failure mode: "it worked in staging" because staging ran a Redis version that doesn't enforce a behavior that Redis 7.x changed. Or staging had no queue and the job just ran inline.

Parity is not about identical data. It is about identical behavior.

### Parity checklist for this stack

| Component | What must match |
|---|---|
| Symfony API | PHP version, extension set, env var structure, queue transport config |
| Go worker | Go version, queue connection config, message schema version |
| Postgres | Major version, extensions (uuid-ossp, pg_trgm), connection pool limits |
| Redis | Version, eviction policy, sentinel vs. standalone topology |
| Queue | Broker (AMQP/Redis Streams), queue names, dead-letter config, message TTL |

---

## Anti-patterns

**Blue-green with non-backward-compatible DB migrations** — you switch traffic instantly, but the old environment still points at the same database. The "fast rollback" switches traffic back to the old app running against the new schema. It fails.

**No health check endpoint** — load balancer has no signal. It sends traffic to the new instance the moment the process starts. Connection pools aren't warm. First requests fail.

**Rollback plan that requires manual DB intervention at 3am** — if your rollback procedure includes "run this SQL manually," it will be wrong under pressure. Compensating migrations must be pre-written and tested.

**Feature flags never cleaned up** — dead code accumulates. Every flag evaluation adds a branch. After 18 months, nobody knows which flags are live. Removing the flag is now risky. Cost: complexity that compounds.

**"We'll test it in production" without canary** — this is a canary without the safety mechanism. Route 5% of traffic, not 100%.

**Simultaneous code and migration deploy** — explained above. Never.

---

## Šta da pitaš AI

- "We need to deploy [describe change including DB migrations]. Which deployment strategy is safe? What are the steps in sequence? What must happen before each step?"
- "We have this database migration: [describe]. Is it backward compatible with the running version? What would break if old code runs against this schema?"
- "Design the rollback procedure for [describe deployment]. What are the steps? What state cannot be automatically rolled back and why?"
- "Our health check endpoint currently just returns 200. What should it actually check to be useful for zero-downtime deployments with our stack (Symfony + Go worker + Postgres + Redis)?"
- "We use rolling deployments. Our Go worker processes queue messages. During a rolling deploy, both old and new workers run simultaneously. What message compatibility requirements does this impose on us?"
