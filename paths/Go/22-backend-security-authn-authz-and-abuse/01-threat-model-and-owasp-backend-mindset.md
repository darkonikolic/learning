# Unit 1 — Threat Model and OWASP Backend Mindset

## Concept

Threat modeling is listing what an attacker could do at each point in your system and deciding how you prevent it. Start from the data flow: what enters your API, what touches the database, what leaves in responses. The OWASP API Security Top 10 names the most common backend failures: broken authentication, broken object-level authorization (IDOR — user A reads user B's data), injection, and excessive data exposure (returning full DB rows when the client needs two fields). These are not theoretical — they appear in real breach reports.

## Code

```
Threat model for POST /orders

DATA FLOW:
  Client → [HTTPS] → API handler → DB insert → DB

THREAT TABLE:

ENDPOINT        THREAT                          MITIGATION
────────────────────────────────────────────────────────────────────────
POST /orders    Replay attack (same order 2x)   Idempotency key in header
POST /orders    SQL injection in product_id     Parameterized queries only
POST /orders    User places order as other user Check: order.UserID == auth.UserID
POST /orders    Negative quantity in payload    Validate: quantity > 0
POST /orders    Missing auth token              JWT middleware runs first
GET  /orders/:id  IDOR: read another user's order  WHERE user_id = $authUserID
GET  /orders/:id  Enumeration: sequential IDs   Use UUIDs, not integer IDs
Any             Excessive data exposure         Return only fields the client needs

TRUST BOUNDARIES:
  - Internet → API: untrusted. Validate everything.
  - API → DB: trusted network, but use parameterized queries regardless.
  - API → downstream services: authenticated with service tokens.

BLAST RADIUS:
  - Compromised user token: attacker can read/modify that user's orders only
  - Compromised service token: attacker can read all orders
  - SQL injection: full DB read/write
```

## Exercise

**Build:** Create a threat model table for `POST /orders` in your e-commerce API.
**Input:** Your API's data flow: what the handler receives, what it queries, what it returns.
**Output:** A table with at least 6 threat/mitigation pairs covering auth, authorization, input validation, and data exposure.
**Acceptance:** For each threat: (1) you can write the specific code or config that implements the mitigation, (2) you can write a test that proves the mitigation works (e.g., a test that sends a tampered user ID and expects 403).

## Interview

- What is the difference between authentication and authorization? Give a concrete example where auth passes but authz should fail.
- What is IDOR and why does role-based access control alone not prevent it?
- Why do you use UUIDs instead of integer IDs for order identifiers?
