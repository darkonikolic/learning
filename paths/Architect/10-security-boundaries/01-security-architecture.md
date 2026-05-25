# Security Architecture

Architects design where security checks live. Security engineers implement them. If the architect misplaces the checks, no amount of careful implementation fixes it.

---

## Trust Boundaries

Every component boundary is a potential trust boundary. A trust boundary is any point where data or requests cross from one execution context to another — browser to API, API to worker, service to database.

**The core question at each boundary:** what do you verify, and what do you assume?

**External boundaries** — browser, mobile client, third-party integrations. Assume nothing. Verify everything: authentication, input format, size, content type.

**Internal boundaries** — Symfony API to Go worker, API to Postgres, API to Redis. The mistake: trusting internal traffic implicitly because "it's behind the firewall."

Why that fails: internal compromise is real. A misconfigured Redis, an exploitable dependency in the Go worker, a compromised container — once an attacker is inside the network, implicit trust becomes lateral movement. If Symfony trusts any message that arrives on the queue without verification, a compromised producer writes arbitrary jobs.

**What to do instead:**
- Service identity: each internal service has a verifiable identity (mTLS certificates, service account tokens)
- Message integrity: queue messages are signed or carry a short-lived token scoped to that operation
- Least privilege: Go worker connects to Postgres with credentials that only allow the operations it needs — not `SUPERUSER`, not the same credentials as the API

**Boundary inventory:** when reviewing a design, list every boundary explicitly. For each one: what does the consumer send? What does the receiver verify before acting?

---

## Auth/Authz Architecture

Authentication and authorization are different problems. Architects who conflate them create security gaps.

**Authentication** — who are you? Answers the question: is this request from who it claims to be?

JWT tokens: self-contained, stateless. The token carries claims signed by a known key. Validation requires the public key and checks: signature valid, not expired, issuer correct, audience correct. If any check fails, reject before doing anything else.

OAuth2: delegates authentication to an identity provider. The API receives an access token — it must still validate that token (signature, expiry, scope). OAuth2 does not remove the need to validate; it moves where the identity decision is made.

**Where authentication validation lives:**

| Approach | Where Validation Happens | Tradeoff |
|---|---|---|
| Centralized (API gateway) | Gateway validates JWT, passes claims downstream | Consistent enforcement, single point of failure, services can trust gateway-injected headers |
| Decentralized (each service) | Every service validates the token independently | Resilient, no single choke point, each service must maintain validation logic and key rotation |
| Hybrid | Gateway validates, services re-verify on sensitive operations | Balanced — services don't blindly trust headers for write operations |

The typical choice for a Symfony API + Go worker system: **gateway handles initial validation and injects a trusted header** (e.g., `X-User-ID`, `X-User-Roles`). Symfony trusts those headers only from the gateway (verify the request came from the gateway, not from the open internet). The Go worker, triggered by a queue message, carries its own signed payload — it does not rely on headers.

**Authorization** — what can you do? Answers the question: does this authenticated identity have permission to perform this operation on this resource?

**RBAC (Role-Based Access Control):** assign roles to users, permissions to roles. Simple to implement, simple to audit, hard to granulate. `admin`, `editor`, `viewer` works until you need "editor of their own content only."

**ABAC (Attribute-Based Access Control):** policies evaluate attributes of the subject, resource, and environment. `user.department == resource.department AND time.now < resource.embargo_date`. Flexible, powerful, significantly more complex to reason about and audit.

**Where authorization lives:** in the service that owns the resource. Always.

| Who checks what | Correct |
|---|---|
| Gateway validates JWT signature | Yes |
| Gateway checks token expiry | Yes |
| Gateway decides if user can access `/orders/123` | No — gateway doesn't own orders |
| Symfony checks if authenticated user owns order 123 | Yes |
| Go worker checks if the job was issued for a valid user | Yes |

The rule: **gateway handles authentication, services handle authorization**. Mixing them creates gaps — either the gateway is making decisions it doesn't have context for, or services are duplicating authentication logic they can't do correctly.

---

## Secrets Management

Secrets are: database passwords, API keys, JWT signing keys, OAuth client secrets, encryption keys.

**Where secrets must not live:**
- Source code (even in private repos — git history is forever)
- `.env` files committed to version control
- Plain environment variables set in deployment configs visible in CI logs
- Docker image layers

**Where secrets must live:** a secret manager — AWS Secrets Manager, HashiCorp Vault, GCP Secret Manager. Secrets are injected at runtime: the application fetches them from the secret manager on startup, or the deployment platform injects them as environment variables from the secret manager (not from plain config).

**Rotation architecture:** the system must handle secret rotation without a restart.

Design requirement: applications that require a restart to pick up a new DB password or JWT signing key create downtime windows during rotation. Architect around this:
- Fetch secrets with a TTL and re-fetch periodically (every 5–15 minutes)
- JWT signing: support multiple valid signing keys simultaneously (current + previous) during rotation window
- Database passwords: use connection pooling middleware (PgBouncer) where the secret rotation is applied at the pool level, not per-connection

---

## Threat Modeling Basics (STRIDE Checklist)

You don't run a formal STRIDE exercise on every feature. You use STRIDE as a checklist when reviewing a design, evaluating a PR, or deciding where a new component fits.

For each component or feature, ask:

| Letter | Threat | Question to ask |
|---|---|---|
| S | Spoofing | Can an attacker pretend to be a legitimate user, service, or component? |
| T | Tampering | Can data be modified in transit or at rest without detection? |
| R | Repudiation | If something goes wrong, is there an audit trail? Can a user deny an action they took? |
| I | Information Disclosure | Can an attacker read data they shouldn't? Logs, error messages, API responses? |
| D | Denial of Service | Can an attacker make this component unavailable? Is there rate limiting? |
| E | Elevation of Privilege | Can an attacker gain more access than they were granted? |

Apply this checklist at: new API endpoints, new queue consumers, new integrations with third-party services, new data export features, any component that touches PII or financial data.

---

## Audit Log as Architecture

Audit logging is not a feature added later. It is architectural. The schema and storage must be designed upfront.

**Rule:** any action that changes state or accesses sensitive data needs a log entry with:
- Who (authenticated user ID, service identity)
- What (action taken, resource affected, resource ID)
- When (UTC timestamp, millisecond precision)
- From where (IP address, service name, request ID)
- Result (success, failure, error code)

**The schema question:** structured log (JSON in a log aggregator) or a dedicated audit log table? For compliance (GDPR, PCI, SOC2), the answer is almost always a dedicated table — log aggregators can be cleared or rotated, and you need to prove the log hasn't been tampered with. Immutable append-only storage.

**What does not need an audit log:** read operations on non-sensitive data. `GET /products` does not need an audit entry. `GET /users/123/payment-methods` does.

---

## Decision Table: Where Security Checks Live

| Component | Consumer Type | Data Sensitivity | Authentication Check | Authorization Check |
|---|---|---|---|---|
| API Gateway | External browser/mobile | Any | Gateway validates JWT | Not here — pass to service |
| Symfony API endpoint | Via gateway (trusted) | Low (public catalog) | Trust gateway header | None needed |
| Symfony API endpoint | Via gateway (trusted) | High (orders, PII) | Trust gateway header | Service checks ownership |
| Symfony admin endpoint | Internal admin users | High | Gateway validates admin JWT | Service checks admin role |
| Go worker | Queue message | Medium | Verify signed job payload | Worker checks job belongs to valid user |
| Postgres | Go worker, Symfony | High | DB credentials (least privilege) | Schema-level grants per service |
| Redis | Symfony API | Medium (session/cache) | Redis AUTH token | Application-level key namespacing |

---

## Anti-patterns

**Anti-pattern 1: Authorization logic in the API gateway**
`if role == "admin" { allow }` in the gateway. The gateway does not have resource context. It doesn't know if admin is allowed to access *this specific* resource. Authorization belongs in the service that owns the resource.

**Anti-pattern 2: JWT tokens without expiry or rotation strategy**
Short-lived tokens (15 minutes) plus refresh tokens is the baseline. No expiry means a stolen token is valid forever. No rotation strategy means a compromised signing key requires emergency key replacement with downtime.

**Anti-pattern 3: Secrets in `.env` files committed to git**
Even "accidentally" committed secrets are compromised. Assume git history is public. Rotate immediately, audit access logs, fix the architecture.

**Anti-pattern 4: No audit log until compliance forces it**
Retrofitting audit logging onto an existing system is expensive — you have to reconstruct schemas, backfill historical gaps, prove to auditors that the log is complete. Design it in from the start.

**Anti-pattern 5: "Internal network is trusted"**
Internal compromise is the dominant attack vector in post-breach analyses. Without service identity (mTLS or equivalent) and per-service least-privilege credentials, internal lateral movement is trivial.

---

## Network-Level Security Posture

Architecture decisions about network topology are security decisions.

**Ingress:** only the API gateway should be publicly accessible. Symfony, Go worker, Postgres, Redis — none of these should accept connections from the public internet. They live in a private network (VPC, private subnet) and are reachable only from within it.

Common mistake: a developer exposes Postgres on port 5432 to 0.0.0.0/0 for convenience during early development, then forgets to restrict it before production. The check: "what is the security group / firewall rule on this port? Who is allowed to connect?" belongs in the architecture review, not the ops runbook.

**Egress:** outbound traffic should also be restricted. The Go worker does not need to make arbitrary HTTP requests. If its only external call is to object storage, restrict egress to that endpoint. Egress restriction limits the blast radius if the worker is compromised — it cannot beacon out to an attacker-controlled server or exfiltrate data to an arbitrary endpoint.

**Service mesh and mTLS:** in a multi-service system, mTLS means every service-to-service connection is mutually authenticated — both sides present a certificate, both sides verify the other. This eliminates the "trust by network location" assumption. The cost is certificate management (issuance, rotation, distribution). At small scale, a service mesh (Istio, Linkerd) manages this. At very small scale (two services), manually issued certificates with a short TTL work. The decision: do you need mTLS? If the answer is "we can't enumerate who is allowed to call each service," the answer is yes.

**Rate limiting and throttling:** rate limiting is a DoS mitigation and a cost control, but it is also a security control. Without rate limiting, a brute-force attack on a login endpoint, a credential-stuffing attack, or an enumeration attack on user IDs can run indefinitely. Rate limiting belongs at the gateway for external traffic and per-service for internal traffic on write-heavy endpoints.

---

## Input Validation as a Security Boundary

Input validation is not just a data quality concern — it is a security boundary. Every point where external data enters the system is an attack surface.

**Where validation lives:**
- At the boundary where data enters the system (the API endpoint, not deep in the service layer)
- Validated once, as early as possible — not repeatedly in different layers with inconsistent rules
- On both structure (is this valid JSON? does the field exist?) and semantics (is this user ID within a valid range? is this file type allowed?)

**What to validate at each entry point:**
- Data type and format (not just "is this a string" but "is this a valid UUID / ISO date / enum value")
- Size and length limits (unbounded input = DoS vector)
- Allowed values (allowlist, not blocklist — `["csv", "pdf"]` not "anything except `../../etc/passwd`")
- Ownership (before acting on a resource ID, verify the caller owns that resource)

**The mistake:** validating at the service layer but not at the API layer. A malformed payload that gets deep into the system before rejection can trigger unexpected behavior, expose stack traces in errors, or create partial state.

The Go worker receives job payloads from a queue. Even though the queue is internal, validate the payload schema at the start of the worker handler. Treat queue messages as untrusted input — because the producer might be compromised, misconfigured, or simply have a bug.

---

## Šta da pitaš AI

- "Draw the trust boundaries in this architecture: [describe components]. Where should authentication checks live? Where should authorization checks live?"
- "We store [describe sensitive data]. What audit log events are required? What schema would you use for an immutable audit log in Postgres?"
- "We use JWT for auth. What is the token rotation strategy if a signing key is compromised? Walk me through the rotation sequence without downtime."
- "Here is our secrets management approach: [describe]. What are the risks and what should we change?"
- "Apply the STRIDE checklist to this feature: [describe]. For any risk you identify, what is the architectural mitigation?"
- "Where in this service does input validation happen? What inputs are not validated at the entry point and why is that a risk?"
