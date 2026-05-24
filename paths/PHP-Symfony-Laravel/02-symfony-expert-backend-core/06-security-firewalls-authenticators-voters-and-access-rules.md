# Unit 6 — Security component: hardened mental map

Expert expectations

- **Firewall rules entry points** aligning with layered reverse proxy trust boundaries.
- **Authenticator pipeline** customizing failure differentiation (credential vs escalation vs outage) without dumping stack traces externally.
- **Voters granular authorization** aligning policy statements with aggregates / commands—not controller-only `ROLE_*`.
- **`#[IsGranted]` & expression language** sparingly balancing declarative ergonomics versus hidden branching complexity.

Operational angle

Discuss **logout / session fixation hardening nuances**, remember-me pitfalls, brute-force signalling integration readiness.
