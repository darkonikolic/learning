# Secrets rotation • KMS • Vault patterns

### Principles

Separate **bootstrap** secrets from workload secrets—rotation cadence proportional to blast radius classification.

### KMS framing

Envelope encryption mental model—even if cloud-managed, know **who can decrypt** implicitly.

### Dynamic credentials (where applicable)

Short-lived DB creds patterns—benefits vs connection pool friction.

### Deliverable

**Secrets Rotation RACI** miniature table (roles not names)—who approves outage window class changes.
