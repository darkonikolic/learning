# Unit 10 — Capstone sketch: minimal `auth-service/` with pragmatic security posture

Compose a deliberately small **`auth-service/`** exhibiting:

```
issue access token (whatever format chosen—JWT common)
refresh rotation skeleton (even if persisted in sqlite for practice)
RBAC middleware hook on a protected `/admin`-ish route stub
basic rate-limit counter (in-memory acceptable if documented non-prod)
SSRF-safe URL fetch stub OR explicit refusal pattern documented
secrets never logged demonstration test idea (table-driven asserting redaction fields)
```

Document known gaps honestly (no “production-ready” posture pretence without hardening checklist).
