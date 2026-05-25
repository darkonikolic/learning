# Lab: Security Boundaries

---

## Exercise 1: Trust Boundary Mapping

**Architecture:**

```
Browser ──────────────────────────────────────┐
                                              ▼
Admin Panel (same origin, different routes) → API Gateway
                                              │
                                              ▼
                                        Symfony API
                                         │        │
                                         │        ▼
                                         │   Queue (Redis)
                                         │        │
                                         ▼        ▼
                                      Postgres  Go Worker
                                                  │
                                                  ▼
                                              Postgres
```

**Consumers:**
- Regular users: browser clients authenticating with JWT via OAuth2
- Admin users: internal admin panel, same Symfony API, separate route prefix `/admin/*`
- Go worker: triggered by jobs placed on a Redis queue by the Symfony API

---

### Questions

**1. Where does authentication happen for each consumer type?**

Map each consumer to the point where their identity is verified and what token/credential is used.

| Consumer | Entry Point | Token/Credential Type | Where Validated |
|---|---|---|---|
| Browser user | API Gateway | ? | ? |
| Admin panel user | API Gateway | ? | ? |
| Go worker (queue) | Redis queue message | ? | ? |

What is different about the Go worker's authentication compared to browser users? It never goes through the gateway. What does that mean for how you verify it?

**2. Where does authorization happen?**

For each of these operations, identify where the authorization check should live and why:

- Regular user reads their own order: `/api/orders/123`
- Regular user reads another user's order: `/api/orders/456` (they don't own it)
- Admin user exports all orders: `/admin/orders/export`
- Go worker processes a job to generate a PDF for user 789

For each: is the check at the gateway, in Symfony, in the Go worker, or somewhere else? What information does the check need that the gateway does not have?

**3. Which internal boundaries need additional trust checks?**

List each internal hop and decide: is the trust implicit, or does it need an explicit check?

| Boundary | Implicit Trust OK? | What check is needed if not? |
|---|---|---|
| API Gateway → Symfony API | ? | ? |
| Symfony API → Postgres | ? | ? |
| Symfony API → Redis (queue write) | ? | ? |
| Redis queue → Go Worker (queue read) | ? | ? |
| Go Worker → Postgres | ? | ? |

Hint: "implicit trust OK" has a high bar. What would an attacker need to do to exploit implicit trust at each boundary?

**4. The Go worker's Postgres credentials**

The Go worker connects to the same Postgres instance as the Symfony API.

Questions to answer:
- Should the Go worker use the same database credentials as the Symfony API?
- What tables does the Go worker actually need access to? (Assume it processes order export jobs: reads orders, writes to an exports table, updates a job_status table.)
- What Postgres role would you define for the Go worker? What grants would it have?
- If the Go worker's credentials are compromised, what is the blast radius with least-privilege credentials vs shared credentials?

---

### Reference: Trust Boundary Diagram Template

Use this text format when diagramming trust boundaries in design reviews:

```
[Component A] ══EXTERNAL BOUNDARY══> [Component B]
   Verify: JWT signature, expiry, audience
   Pass: user_id, roles (as trusted header)

[Component B] ──internal──> [Component C]
   Verify: signed message payload (HMAC or short-lived token)
   Pass: job_id, user_id, operation_type

[Component C] ──internal──> [Database]
   Verify: credentials (least-privilege role)
   Pass: parameterized queries only
```

For each boundary, document: what is verified, what is passed downstream, and what happens on verification failure (reject vs degrade vs alert).

---

## Exercise 2: Threat Model Lite

**Feature:** Users can export their order history as a CSV download.

Flow:
1. Authenticated user clicks "Export my orders"
2. Symfony API places a job on the Redis queue: `{job_type: export_orders, user_id: 123, requested_at: ...}`
3. Go worker picks up the job, queries Postgres for all orders where `user_id = 123`
4. Go worker writes a CSV file to object storage (S3-compatible)
5. Go worker calls back to Symfony API with a pre-signed download URL
6. Symfony API stores the URL, sends user a download link via email
7. User clicks the link, downloads the CSV

Apply the STRIDE checklist. For each letter: is there a risk in this feature? If yes, what is the architectural mitigation?

---

### STRIDE Checklist Table

Fill in: Risk Present (yes/no), Where in the flow, Mitigation.

| Threat | Question | Risk Present? | Where in Flow | Architectural Mitigation |
|---|---|---|---|---|
| Spoofing | Can someone claim to be a user they are not? | ? | ? | ? |
| Tampering | Can the job payload or CSV data be modified? | ? | ? | ? |
| Repudiation | If a user denies requesting the export, is there proof? | ? | ? | ? |
| Information Disclosure | Can a user download another user's export? | ? | ? | ? |
| Denial of Service | Can an attacker exhaust resources via export requests? | ? | ? | ? |
| Elevation of Privilege | Can an attacker get data beyond their own orders? | ? | ? | ? |

**Worked example for S (Spoofing):**
Risk: yes. If the queue message carries only `user_id: 123` and the Go worker trusts it without verification, a compromised producer could forge any user_id.
Mitigation: the queue job is signed (HMAC with a shared secret, or a short-lived token issued by Symfony at job creation time). The Go worker verifies the signature before processing.

Work through the remaining five letters using the same format.

---

### Audit Log Schema Template

For the order export feature, every audit-worthy event needs a log entry. Use this schema as a starting point:

```sql
CREATE TABLE audit_log (
    id            BIGSERIAL PRIMARY KEY,
    event_time    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actor_id      TEXT NOT NULL,          -- user_id, service name, or 'anonymous'
    actor_type    TEXT NOT NULL,          -- 'user', 'service', 'admin'
    action        TEXT NOT NULL,          -- 'order.export.requested', 'order.export.completed'
    resource_type TEXT NOT NULL,          -- 'order_export', 'order'
    resource_id   TEXT,                   -- specific record ID if applicable
    source_ip     INET,                   -- originating IP
    service_name  TEXT NOT NULL,          -- 'symfony-api', 'go-worker'
    request_id    TEXT,                   -- correlation ID for distributed tracing
    result        TEXT NOT NULL,          -- 'success', 'failure', 'denied'
    result_detail JSONB                   -- error code, reason, additional context
);

-- Index for compliance queries: "all exports for user X in the last 90 days"
CREATE INDEX idx_audit_actor_action ON audit_log (actor_id, action, event_time DESC);

-- Index for incident response: "all events from IP X in the last 24 hours"
CREATE INDEX idx_audit_source_ip ON audit_log (source_ip, event_time DESC);
```

**Events to log for the export feature:**

| Event | actor_id | action | result_detail |
|---|---|---|---|
| User requests export | user_id | `order.export.requested` | `{count_requested: N}` |
| Worker picks up job | `go-worker` | `order.export.job.started` | `{job_id, user_id}` |
| Worker queries orders | `go-worker` | `order.export.data.read` | `{user_id, row_count}` |
| Export file written | `go-worker` | `order.export.file.created` | `{storage_path, size_bytes}` |
| Download URL accessed | user_id | `order.export.downloaded` | `{source_ip, user_agent}` |
| Unauthorized access attempt | attacker / user_id | `order.export.access.denied` | `{attempted_resource, reason}` |

**Storage rule:** the audit log table must not be truncated or deleted by application code. Application database role does not have `DELETE` or `TRUNCATE` on this table. Retention and archiving are operational concerns, handled outside the application.

---

## Exercise 1: Reference Answers

Use these after completing your own answers. If your answer differs, ask why — not all differences are wrong.

**Authentication (Q1):**

| Consumer | Entry Point | Token/Credential Type | Where Validated |
|---|---|---|---|
| Browser user | API Gateway | JWT (access token, 15-min expiry) | Gateway validates signature, expiry, audience |
| Admin panel user | API Gateway | JWT (separate audience claim `aud: admin`) | Gateway validates; Symfony also checks admin role claim |
| Go worker (queue) | Redis queue message | HMAC-signed payload or short-lived scoped token | Go worker verifies signature before processing |

The Go worker never passes through the gateway. It must self-validate the job payload. If it trusts the queue implicitly, any process that can write to Redis can inject arbitrary jobs.

**Authorization (Q2):**

| Operation | Authorization Location | Reason |
|---|---|---|
| User reads own order `/api/orders/123` | Symfony service layer | Gateway doesn't know who owns order 123 |
| User reads another's order | Symfony — deny, 403 | Same: ownership is a data-level check |
| Admin exports all orders | Symfony — checks admin role | The role claim is present, but Symfony validates the resource scope |
| Go worker processes PDF job for user 789 | Go worker — verifies job user_id matches signed payload | Worker must not trust that any job in the queue is legitimate |

**Internal boundaries (Q3):**

| Boundary | Implicit Trust OK? | What check is needed |
|---|---|---|
| API Gateway → Symfony API | Only if Symfony is not reachable directly from the internet | Symfony must reject requests not from the gateway (verify source IP or shared secret header) |
| Symfony API → Postgres | No | Dedicated role with table-level grants; parameterized queries only |
| Symfony API → Redis (queue write) | No | Redis AUTH; job payloads signed by Symfony |
| Redis queue → Go Worker | No | Worker verifies payload signature before acting |
| Go Worker → Postgres | No | Separate role from Symfony's role; minimum grants |

**Go worker Postgres credentials (Q4):**
The Go worker should have its own Postgres role distinct from Symfony's role. If the worker only needs to read `orders`, write to `exports`, and update `job_status`, those are the only grants it gets. If the worker's credentials are compromised, blast radius is limited to those three tables. With shared credentials, the attacker has everything the API has — which typically includes write access to users, sessions, and payment data.

---

## Šta da pitaš AI (Lab)

- "Here is the trust boundary diagram for our export feature: [describe]. What trust checks are missing? What would an attacker exploit first?"
- "Apply STRIDE to this queue-based worker architecture. For each threat, what is the specific risk given that the worker never goes through the API gateway?"
- "We need a Postgres role for our Go worker. It reads from orders and order_items, writes to exports, updates job_status. Write the CREATE ROLE and GRANT statements."
- "Our audit log is in the same Postgres database as our application. What are the risks of that, and how would you architect the audit log for a high-compliance environment?"
