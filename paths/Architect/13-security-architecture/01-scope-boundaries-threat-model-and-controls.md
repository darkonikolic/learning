# Unit 1 — Scope: security as layered boundaries

Treat security as architectural decisions—not a sprint “add TLS later.”

---

## Architectural outcomes

- Sketch **trust boundaries** (internet, CDN, VPC, datastore, SaaS egress) with **assume breach** realism.
- Contrast **authentication** (identity) vs **authorisation** (what that identity may do)—where each layer should enforce checks.
- Articulate **least privilege**, **secrets** handling (generation, rotation, scope, audit), and **rate limiting / abuse tolerance** aligned with APIs (bridges **`14-*`**).
- Decide where **encryption** rests (transport vs at-rest), threat models that justify complexity, operational load of key management.

