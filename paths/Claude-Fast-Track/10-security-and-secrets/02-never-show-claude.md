# What never goes to Claude

## The exposure surface

When you work with Claude Code, Claude reads files, processes your inputs, and generates outputs. Every piece of text that enters your context window passes through Anthropic's infrastructure. This is not a reason to avoid Claude — it is a reason to understand what you are sending.

The surface has four components:

1. **Files Claude reads** — anything you ask Claude to read, or that CLAUDE.md instructs Claude to read at session start
2. **Your chat messages** — anything you type, paste, or attach
3. **Tool outputs** — the content of files returned by Read calls, shell output from Bash calls
4. **Context from previous turns** — Claude's context window is cumulative within a session

Conversation history may be retained per Anthropic's data retention policy. Treat everything that enters a Claude session as potentially retained.

---

## What never goes to Claude

| Category | Examples | Why |
|----------|---------|-----|
| Production secrets | API keys, DB passwords, private keys, signing secrets | Direct exposure risk; treat as immediately compromised |
| PII | Real user emails, names, phone numbers, addresses | Privacy and compliance (GDPR, HIPAA, CCPA) |
| Credentials | OAuth access tokens, JWT signing secrets, session cookies | Replayable; can be used to impersonate users or services |
| Internal endpoints | Production URLs with embedded auth tokens or API keys in the URL | Attack surface; exposes routing and auth together |
| Pre-release code | IP-sensitive unreleased features, acquisition targets, competitive roadmaps | Business risk |
| Real database rows | Actual user records, transaction data, health records | PII/compliance even if individual fields seem innocuous |

---

## What IS safe to show Claude

The goal is not to hide everything — that prevents Claude from helping. The goal is to redact sensitive values while preserving structure.

**Redact values, keep structure:**

Instead of:
```
DATABASE_URL=postgres://appuser:S3cr3tP4ss@prod-db.internal:5432/taskapi
```

Show:
```
DATABASE_URL=postgres://appuser:<password>@<host>:5432/taskapi
```

Claude can help you debug connection string parsing, env var loading, or config structure from the redacted version. The actual password adds nothing to the debugging problem.

**Schema without data:**

```sql
-- Safe to show — structure only
CREATE TABLE tasks (
    id UUID PRIMARY KEY,
    title TEXT NOT NULL,
    completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

Do not paste `SELECT * FROM tasks` output containing real user task titles.

**Stack traces — yes, but redact embedded credentials:**

Stack traces are useful for debugging. Show them. But scan for embedded credentials first — some ORMs and database drivers include the connection string in error output. Redact those before pasting.

**Error messages:**
```
# Safe
pq: password authentication failed for user "appuser"

# Not safe — includes connection string
dial tcp prod-db.internal:5432: connect: connection refused — dsn: postgres://appuser:S3cr3tP4ss@prod-db.internal:5432/taskapi
```

---

## Practical rules

**Rule 1: Never paste .env content into Claude chat.**

If you need to debug an env var loading problem, show the Go code that reads the variable and describe the symptom. Do not paste the actual .env contents.

**Rule 2: Never ask Claude to "debug this connection string" with a real connection string.**

Instead:
- Redact the password and host
- Describe what error you are getting
- Show the code that reads the connection string

**Rule 3: Use `.claudeignore` to prevent accidental reads.**

Even if you follow rules 1 and 2 consciously, you might forget under time pressure. `.claudeignore` enforces the boundary at the tool level — Claude cannot read the file even if instructed to.

**Rule 4: If Claude produces output containing a real secret: rotate immediately.**

If a Claude session outputs what appears to be a real API key, database password, or private key — whether it came from a file Claude read or from training data — treat it as compromised and rotate. Do not wait to verify whether it was actually exposed.

---

## `.claudeignore` — complete template

Create this at project root. Claude Code respects it the same way git respects `.gitignore`:

```
# Secret files
.env
.env.*
.env.local
.env.development
.env.staging
.env.production
.env.test

# Key material
*.pem
*.key
*.p12
*.pfx
*.jks
*.keystore
*.crt
*.cer

# Credential files
*credentials*
*secrets*
*secret.json
*secret.yaml
*secret.yml
.htpasswd

# Cloud provider credential files
.aws/credentials
.aws/config
.gcloud/
.config/gcloud/
.azure/

# SSH
.ssh/
id_rsa
id_ed25519
*.pub

# Token files
.token
*.token
auth.json
```

Place this file in the project root. Also add the most sensitive entries to `.gitignore` so they are double-protected.

---

## CI/CD pipeline safety

CI environments introduce new exposure paths:

**Never print env vars in build scripts:**
```yaml
# BAD — exposes secret in build logs
- run: echo "Using key: $STRIPE_SECRET_KEY"

# BAD — env -i prints all variables including secrets
- run: env

# SAFE — reference the variable without printing it
- run: go test ./... # uses DATABASE_URL from environment without logging it
```

**GitHub Actions:**
- Secrets set in Settings → Secrets and variables → Actions
- Referenced as `${{ secrets.MY_SECRET }}` in workflow files
- GitHub automatically redacts known secret patterns from logs
- Never set secrets as `env:` values in the `with:` block of a public action (they can be read by the action)

**The logs-as-exposure-vector problem:**
Build logs are often retained, searchable, and accessible to more people than production systems. A secret that appears in a build log is compromised even if the build system is "internal only."

---

## Checklist

- [ ] I understand the four components of the exposure surface when working with Claude.
- [ ] I can identify the six categories of content that never go to Claude.
- [ ] I know the redaction pattern: show structure, replace values with `<placeholder>`.
- [ ] .claudeignore exists in task-api with at minimum .env entries.
- [ ] I understand that stack traces are safe to share after redacting any embedded credentials.
- [ ] I know that if Claude outputs a real secret, the response is immediate rotation.
- [ ] CI/CD secrets are set in the CI platform, not in workflow files or build scripts.
- [ ] I know why printing env vars in CI build scripts is a security risk.
