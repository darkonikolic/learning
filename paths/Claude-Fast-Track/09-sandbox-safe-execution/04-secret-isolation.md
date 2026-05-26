# Secret isolation

Assume that anything Claude can read, Claude can reproduce. This is not a flaw in Claude — it is how language models work. If your `.env` file is in the project root and nothing blocks Claude from reading it, the actual secret values can appear in suggestions, completions, diffs, and plan outputs. Design so that does not happen.

---

## The exposure surface

Claude reads files to understand the codebase. The files it reads travel through:

1. Your local Claude Code process
2. The Anthropic API (the content is sent as context)
3. The model's generation process
4. The response back to your terminal

Each step is a potential exposure point. A secret that enters step 1 has left your machine. The question is not whether Anthropic stores it — the question is that it was transmitted at all.

Prompt injection is an additional risk: malicious content embedded in a file (a dependency's README, a third-party config template) can try to extract context including secrets Claude has already read in the same session.

---

## What Claude must never read

| Category | Examples |
|----------|---------|
| API keys and tokens | `sk-...`, `ghp_...`, `AIza...`, bearer tokens |
| Private keys and certificates | `*.pem`, `*.key`, anything starting with `-----BEGIN` |
| Database connection strings | `postgres://user:password@host/db` |
| Cloud credentials | `~/.aws/credentials`, service account JSON |
| Session secrets | JWT signing keys, cookie secrets, HMAC keys |
| Passwords | Any hardcoded password value |
| Webhook secrets | Stripe signing secrets, GitHub webhook tokens |

The rule: if the value itself provides authentication or authorization, Claude must not see it.

---

## Defense 1: `.claudeignore`

`.claudeignore` works like `.gitignore` — Claude Code will not read files matching these patterns even if they exist in the project.

Create `/Users/you/projects/task-api/.claudeignore`:
```
# Secrets
.env
.env.*
.env.local
.env.production
.env.staging

# Keys and certificates
*.pem
*.key
*.p12
*.pfx
id_rsa
id_ed25519

# Credentials
*credentials*
*secrets*
*secret*
.netrc

# Cloud provider credential files
.aws/
.gcloud/
kubeconfig
```

Verify it works: ask Claude to "show me the contents of .env" after creating the file and the ignore rule. Claude should report that it cannot read the file.

`.claudeignore` does not replace `.gitignore`. Both should list the same secret files. They serve different gatekeeping layers: `.gitignore` prevents accidental commits, `.claudeignore` prevents accidental inclusion in AI context.

---

## Defense 2: Environment variable references, not values

In `settings.json`, pass variable names rather than values:

```json
{
  "env": {
    "DATABASE_URL": "${DATABASE_URL}",
    "API_KEY": "${API_KEY}"
  }
}
```

This tells Claude Code to pass the value of the environment variable at runtime — but the variable name is what appears in the configuration file. Claude sees `DATABASE_URL` in the config. It does not see `postgres://admin:hunter2@prod.db.example.com/tasks`.

The actual value lives only in your shell environment, sourced from a local secrets store, not from a committed file.

---

## Defense 3: Project structure that separates config from secrets

Structure the project so config code is safe to read and secret values are never in source:

```
task-api/
├── config/
│   ├── config.go       ← reads env vars with os.Getenv() — safe for Claude to read
│   └── defaults.go     ← non-secret defaults (port, timeouts) — safe for Claude to read
├── .env.example        ← template with placeholder values — committed, safe
└── .env                ← actual values — in .claudeignore, never committed
```

`config/config.go` — safe to read, contains no secrets:
```go
package config

import "os"

type Config struct {
    Port     string
    LogLevel string
}

func Load() Config {
    port := os.Getenv("PORT")
    if port == "" {
        port = "8080"
    }
    return Config{
        Port:     port,
        LogLevel: os.Getenv("LOG_LEVEL"),
    }
}
```

`.env.example` — committed, contains no real values:
```
PORT=8080
LOG_LEVEL=info
```

`.env` — not committed, in `.claudeignore`:
```
PORT=9090
LOG_LEVEL=debug
```

Claude reads `config.go` and understands how config is loaded. Claude reads `.env.example` and understands what environment variables are needed. Claude never reads `.env` and never sees actual values.

---

## Defense 4: Never paste secrets into the chat

The most common exposure vector is not a misconfigured ignore file. It is the developer copy-pasting a connection string into the chat to "give Claude the context it needs."

There is never a legitimate reason to paste a secret into Claude's chat. If Claude needs to understand a database schema, point it at the migration files. If Claude needs to understand an API, point it at the OpenAPI spec or the client code. If Claude needs to make a test call, use a mock or a test credential.

When you paste a secret to Claude, it:
- Travels to the Anthropic API
- Appears in your chat history
- May appear in suggestions or completions
- Cannot be un-sent

The correct pattern: secrets go into environment variables. Code reads environment variables. Claude reads the code that reads environment variables. Claude never needs the actual value.

---

## Defense 5: Secrets scanning as a pre-commit gate

Install `gitleaks` and run it before every commit:

```bash
# Install
brew install gitleaks

# Scan the current diff
gitleaks detect --source . --staged

# Or run as a pre-commit hook
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/sh
gitleaks protect --staged --redact
EOF
chmod +x .git/hooks/pre-commit
```

`gitleaks` detects patterns like API key formats, private key headers, connection string patterns, and common secret formats. It does not catch every secret (a random password with no recognizable format will not match). Use it as a safety net, not a primary defense.

---

## The credential inventory table

For any project with real integrations, maintain a table:

| Secret artifact | Where it lives | Claude can observe? | Mitigation |
|----------------|---------------|---------------------|------------|
| Database password | `.env` (local only) | No | `.claudeignore` covers `.env` |
| JWT signing key | `.env` (local only) | No | `.claudeignore` covers `.env` |
| GitHub PAT (CI) | CI secrets manager | No | Never in repo |
| Stripe webhook secret | `.env` (local only) | No | `.claudeignore` covers `.env` |
| Test API key (fake) | `.env.test.example` | Yes (placeholder only) | Only example values committed |

For task-api: there are no real secrets (no auth, no external services, in-memory only). The table is short. The habit is still worth forming — the same table used on a toy project transfers directly to a real project.

---

## Detecting if a secret was exposed

Signs a secret may have been included in Claude's context:

- Claude's response includes what looks like a real value (a long hex string, a key-format string)
- Claude refers to a specific password or key value by name
- Claude's suggestion for config code includes what looks like a real default rather than a placeholder

If you suspect exposure:
1. Rotate the secret immediately — assume it is compromised
2. Check `git log` to verify the secret was never committed
3. Review your `.claudeignore` to find the gap
4. Fix the gap before continuing

Treat any secret that appeared in a chat session as compromised. Rotation is cheap. The cost of not rotating a compromised secret is not.

---

## For task-api specifically

task-api has no real secrets in its current state. The value of applying these patterns to a toy project:

- The `.claudeignore` habit is formed before you work on a project with real secrets
- The project structure (config reads env vars, no hardcoded values) is established from day one
- The `.env.example` pattern is in place before there are real environment variables to protect
- The credential inventory table is a template ready for real integrations

Apply the patterns now. Adapt them under pressure later.

---

## Checklist

- [ ] `.claudeignore` exists and covers `.env`, `*.pem`, `*.key`, and credential files.
- [ ] `.env.example` is committed with placeholder values, not real values.
- [ ] `.env` is in both `.gitignore` and `.claudeignore`.
- [ ] `config/config.go` reads values via `os.Getenv()` — no hardcoded credentials anywhere in source.
- [ ] I have verified that Claude cannot read `.env` by asking it to show the contents.
- [ ] I have never pasted a real secret into the Claude chat for this project.
- [ ] `gitleaks` is installed and I know how to run it on staged changes.
- [ ] I have a credential inventory table (even if currently empty) for this project.
- [ ] I know the immediate response if I suspect a secret was exposed: rotate first, investigate second.
