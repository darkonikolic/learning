# Secrets lifecycle

## What a secret is

A secret is any value that provides authentication, authorization, or encryption. The category is broader than "passwords":

| Type | Examples |
|------|---------|
| API keys | OpenAI API key, Stripe secret key, SendGrid key |
| Passwords | Database password, service account password |
| Tokens | OAuth access tokens, JWT signing secrets, session tokens |
| Private keys | TLS private keys, SSH private keys, PGP keys |
| Database credentials | Full connection strings, including host, user, and password |
| Signing secrets | HMAC secrets, webhook signing keys |

A value is a secret if its exposure lets someone impersonate you, access your data, or decrypt protected content. Treat it accordingly from creation to destruction.

---

## The five stages

### 1. Creation — generate, never invent

Weak secrets are not secrets. Common failure: a developer creates `SECRET_KEY=dev123` locally and it propagates to production.

Rules:
- Generate secrets with a cryptographically secure source. Never type them.
- Minimum entropy: 128 bits for symmetric keys, 256 bits for signing secrets.
- Never reuse secrets across environments (dev, staging, prod are separate credentials).

```bash
# Generate a 32-byte hex secret
openssl rand -hex 32

# Generate a base64-encoded 32-byte secret
openssl rand -base64 32

# For a UUID-based token (weaker but convenient for API keys)
uuidgen | tr -d '-' | tr '[:upper:]' '[:lower:]'
```

### 2. Storage — where secrets live

**Storage hierarchy, most to least secure:**

| Level | Storage | Use case |
|-------|---------|---------|
| 1 — Vault | HashiCorp Vault, AWS Secrets Manager, GCP Secret Manager | Production |
| 2 — OS keychain | macOS Keychain, Linux secret-service | Local dev |
| 3 — Environment variables | Set in shell or CI platform, not in any file | CI/CD |
| 4 — .env file | Gitignored, local only, never committed | Local dev fallback |
| 5 — Hardcoded | NEVER | Anywhere |

Level 5 is not a fallback. It is a vulnerability.

The `.env` file is acceptable for local development only when:
- It is in `.gitignore` before you create it (not added afterward)
- It is also in `.claudeignore` so Claude cannot read it
- It never leaves the machine

### 3. Access — how running code reads secrets

Code reads secrets from the environment at startup. It does not read them from files, does not embed them in source, and does not log them.

**Correct pattern for Go (task-api):**

```go
// config/config.go — reads from environment, never from source files
package config

import (
    "log"
    "os"
)

type Config struct {
    Port      string
    LogLevel  string
    DBConnStr string // populated when a database is added; never log this field
}

func Load() Config {
    return Config{
        Port:      getEnv("PORT", "8080"),
        LogLevel:  getEnv("LOG_LEVEL", "info"),
        DBConnStr: getEnv("DATABASE_URL", ""), // empty = not configured; fatal if required
    }
}

// getEnv returns the value or a default — use for optional config
func getEnv(key, fallback string) string {
    if v := os.Getenv(key); v != "" {
        return v
    }
    return fallback
}

// requireEnv returns the value or exits — use for mandatory secrets
func requireEnv(key string) string {
    v := os.Getenv(key)
    if v == "" {
        log.Fatalf("required environment variable %s not set", key)
    }
    return v
}
```

**What `requireEnv` prevents:** silent misconfiguration. If `DATABASE_URL` is not set and the application starts anyway, it will fail at the first database call with an opaque error. Failing at startup with a clear message is better.

**Never do this:**
```go
// BAD — hardcoded
db, _ := sql.Open("sqlite3", "file:prod.db?secret=hunter2")

// BAD — logged
log.Printf("connecting with: %s", cfg.DBConnStr)

// BAD — returned in HTTP response
json.NewEncoder(w).Encode(map[string]string{"dsn": cfg.DBConnStr})
```

### 4. Rotation — changing secrets without downtime

Rotation means replacing a secret with a new one. Correctly done, it causes zero downtime.

**Dual-credential window:**

1. Create new secret at the credential provider (database, API service)
2. Deploy new secret to your secrets store (Vault, Secrets Manager)
3. Rolling deploy: application instances gradually pick up new secret
4. Both old and new secrets are valid during the window
5. Confirm: all instances are using the new secret (no 401s, no auth failures)
6. Revoke the old secret

The window between steps 2 and 6 is the grace period. Length depends on your deployment rollout time — typically 5–30 minutes.

**Rotation cadence:**
- Production API keys: rotate quarterly, or immediately after any exposure event
- Database passwords: rotate when personnel changes, or on a scheduled cycle
- Signing keys: follow the key's stated validity period; never extend beyond it

### 5. Revocation — immediate response to compromise

If a secret is compromised (committed to git, logged, exposed in an error message, seen by an unauthorized party):

1. Revoke immediately — do not wait to confirm the exposure
2. Rotate — issue a new secret, deploy it
3. Audit — check access logs for use of the compromised secret
4. Postmortem — how did it get exposed? Fix the root cause

The cost of an unnecessary revocation is 30 minutes of work. The cost of a delayed revocation after actual exploitation can be catastrophic. Default to revocation.

---

## task-api specifics

task-api in its Phase 1–3 form has no external credentials. It is in-memory. No database connection string, no API keys.

Even so: apply the pattern now.

- `PORT` is read from environment via `config.Load()`, not hardcoded as `":8080"` in `main.go`
- `LOG_LEVEL` is read from environment
- `.env.example` documents what variables exist, with placeholder values
- `.env` (with actual local values) is in `.gitignore` and `.claudeignore`

This is not overhead — it is habit formation. When you add a database in Phase 4, the config pattern is already in place. You do not rewrite main.go to move a hardcoded string.

---

## .env.example vs .env

`.env.example` is committed to git. It shows the structure without real values:

```bash
# .env.example — commit this
PORT=8080
LOG_LEVEL=info
# DATABASE_URL=postgres://user:password@localhost:5432/taskapi
```

`.env` holds actual values and is never committed:

```bash
# .env — gitignored, local only
PORT=8080
LOG_LEVEL=debug
```

This pattern lets new team members know what variables exist (from `.env.example`) without ever needing to share a real `.env` file.

---

## Checklist

- [ ] I can name the five stages of a secret's lifecycle.
- [ ] I understand the storage hierarchy and can place each tier in order.
- [ ] I understand why `requireEnv` fails at startup rather than failing silently later.
- [ ] I know the dual-credential window rotation procedure.
- [ ] I understand that revocation on suspected compromise is the default action, not a last resort.
- [ ] task-api config.go reads PORT and LOG_LEVEL from environment (not hardcoded).
- [ ] .env.example is committed; .env is gitignored.
- [ ] I can distinguish between optional config (getEnv with fallback) and required secrets (requireEnv with fatal).
