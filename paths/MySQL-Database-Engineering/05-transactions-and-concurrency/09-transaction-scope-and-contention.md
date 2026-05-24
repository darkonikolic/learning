# Unit 09 — Transaction scope discipline

Anti-pattern: elongated transactions bundling network I/O, external payment APIs, analytics side effects.

Good pattern: commit hot data mutations quickly; offload slow work post-commit with idempotent follow-ups.

Lab: refactor narrative transaction boundaries (even paper design if code not ready).
