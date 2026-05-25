# Lab — security setup for task-api

This lab hardens task-api against the most common application security failures. It takes 30–45 minutes. All four parts build on each other — complete them in order.

By the end, task-api will have:
- Environment-based configuration (no hardcoded port)
- Secrets excluded from both git and Claude's file reads
- A pre-commit hook that blocks secret commits
- Security acceptance criteria in the SPEC

---

## Prerequisites

- task-api repository initialized (from module 11 or earlier)
- Go 1.21+ installed
- git initialized in task-api root
- Homebrew installed (for gitleaks on macOS)

---

## Part 1 — Secret isolation

### Step 1 — Create config package

Create `config/config.go`:

```go
package config

import (
    "log"
    "os"
)

// Config holds all application configuration.
// Add fields here as the application grows.
// Never log the full Config struct — it may contain credentials.
type Config struct {
    Port     string
    LogLevel string
}

// Load reads configuration from environment variables.
// Fails fast if any required variable is missing.
func Load() Config {
    return Config{
        Port:     getEnv("PORT", "8080"),
        LogLevel: getEnv("LOG_LEVEL", "info"),
    }
}

// getEnv returns the value of key, or fallback if key is not set.
// Use for optional configuration with sensible defaults.
func getEnv(key, fallback string) string {
    if v := os.Getenv(key); v != "" {
        return v
    }
    return fallback
}

// requireEnv returns the value of key or exits the program.
// Use for required credentials — fail at startup, not at first use.
func requireEnv(key string) string {
    v := os.Getenv(key)
    if v == "" {
        log.Fatalf("required environment variable %s not set", key)
    }
    return v
}
```

### Step 2 — Update main.go to use config

Replace any hardcoded `":8080"` in `main.go`:

```go
package main

import (
    "log"
    "net/http"
    "task-api/config"
    "task-api/tasks"
)

func main() {
    cfg := config.Load()

    store := tasks.NewStore()
    mux := http.NewServeMux()
    tasks.RegisterHandlers(mux, store)

    log.Printf("starting task-api on port %s (log_level=%s)", cfg.Port, cfg.LogLevel)
    if err := http.ListenAndServe(":"+cfg.Port, mux); err != nil {
        log.Fatalf("server error: %v", err)
    }
}
```

### Step 3 — Create .env.example

```bash
# .env.example — commit this file
# Copy to .env and adjust values for local development
PORT=8080
LOG_LEVEL=info

# Add when database is introduced:
# DATABASE_URL=postgres://user:password@localhost:5432/taskapi
```

Commit `.env.example`:
```bash
git add .env.example config/config.go
git commit -m "add environment-based configuration"
```

### Step 4 — Create .env (local only)

```bash
# .env — do NOT commit
PORT=8080
LOG_LEVEL=debug
```

### Step 5 — Add to .gitignore

Open `.gitignore` and verify these lines are present (add if missing):

```
.env
.env.*
*.pem
*.key
```

### Step 6 — Create .claudeignore

Create `.claudeignore` at project root:

```
.env
.env.*
*.pem
*.key
*.p12
*credentials*
*secrets*
.aws/
.ssh/
```

### Step 7 — Verify

```bash
# .env should not appear in git status
git status
# Expected: .env not listed (it is ignored)

# Confirm the ignore rule
git check-ignore -v .env
# Expected: .gitignore:1:.env    .env

# Verify app still starts
PORT=9090 go run .
# Expected: "starting task-api on port 9090"
# Ctrl-C to stop
```

---

## Part 2 — Pre-commit hook

### Step 6 — Install gitleaks

```bash
brew install gitleaks
gitleaks version   # verify installation
```

### Step 7 — Create the hook

```bash
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/sh
gitleaks protect --staged --exit-code 1
if [ $? -ne 0 ]; then
    echo ""
    echo "Commit blocked: secret detected in staged changes."
    echo "Remove the secret and try again."
    echo "If this is a false positive, add an allowlist entry to .gitleaks.toml"
    exit 1
fi
EOF
chmod +x .git/hooks/pre-commit
```

Verify the hook is executable:
```bash
ls -la .git/hooks/pre-commit
# Expected: -rwxr-xr-x
```

### Step 8 — Create .gitleaks.toml

```toml
# .gitleaks.toml — gitleaks configuration
title = "task-api gitleaks config"

[allowlist]
  description = "Allow test fixtures and documentation examples"
  regexes = [
    # Allow obviously fake example values in documentation or tests
    '''EXAMPLE''',
    '''PLACEHOLDER''',
    '''sk-test-''',
  ]
  paths = [
    # Scan everything — no directory exclusions for now
  ]
```

Commit the gitleaks config:
```bash
git add .gitleaks.toml .claudeignore .gitignore
git commit -m "add secret detection and claude ignore rules"
```

### Step 9 — Test the hook

Add a fake secret to a Go file:
```bash
# Add a line that looks like an API key
echo '// testAPIKey = "sk-abc123def456ghi789jkl012mno345pqr678"' >> main.go
git add main.go
git commit -m "test: should be blocked"
```

Expected output: gitleaks detects the pattern and blocks the commit.

Remove the test line:
```bash
# Edit main.go to remove the line you added
# Use your editor to delete the // testAPIKey line
git checkout -- main.go   # or edit manually
```

### Step 10 — Verify clean commit works

```bash
git add .
git commit -m "verify: clean commit passes hook"
# Expected: commit succeeds, no gitleaks warnings
```

---

## Part 3 — Security acceptance criteria

### Step 11 — Locate or create SPEC for Phase 1

If you have `.planning/milestones/v0.1/SPEC.md`, open it. If not, create a minimal one at that path.

Add this security section:

```markdown
## Security requirements

### Input validation
- Maximum request body: 10KB — POST /tasks returns 413 for larger bodies
- Content-Type: application/json required — 415 for other types (optional; document if deferred)

### Output safety
- Error responses contain a single `"error"` field with a human-readable message
- Error responses never include Go stack traces or internal field names
- Log output never includes request body content

### Identifiers
- Task IDs are UUID v4 — not sequential integers
- Rationale: sequential integers allow enumeration of total task count and creation order

### State transitions
- A task in completed state cannot be un-completed (PATCH /tasks/:id/complete on an already-complete task returns 200 idempotently, not 422)
- A task in completed state can still be listed (GET /tasks includes completed tasks)

## Security NFR

- [ ] SQL injection: N/A — in-memory store; revisit when database is added
- [ ] Path traversal: N/A — no file system operations
- [ ] Credential exposure in logs: mitigated — config values logged at startup are non-sensitive (PORT, LOG_LEVEL)
- [ ] Credential exposure in responses: mitigated — no config values returned by any endpoint
- [ ] Stack traces in responses: mitigated — all error paths use writeError with fixed message strings
```

Commit:
```bash
git add .planning/
git commit -m "add security acceptance criteria to Phase 1 SPEC"
```

### Step 12 — Verify UUID implementation

If task IDs in the current implementation are sequential integers (1, 2, 3):

```bash
# Add uuid dependency
go get github.com/google/uuid

# Verify it in go.mod
grep uuid go.mod
# Expected: github.com/google/uuid v1.x.x
```

Update `tasks/store.go` to generate UUID IDs:

```go
import "github.com/google/uuid"

// In CreateTask:
task := Task{
    ID:        uuid.New().String(),
    Title:     title,
    Completed: false,
    CreatedAt: time.Now(),
}
```

Test:
```bash
go test ./tasks/...   # existing tests must pass
go run .              # start server
curl -s -X POST localhost:8080/tasks -H "Content-Type: application/json" -d '{"title":"test"}'
# Expected: ID looks like "550e8400-e29b-41d4-a716-446655440000", not "1"
```

### Step 13 — Verify error responses contain no stack traces

```bash
# Send malformed JSON
curl -s -X POST localhost:8080/tasks -H "Content-Type: application/json" -d 'not-json'
# Expected: {"error": "invalid request body"}
# NOT expected: {"error": "invalid character 'o' in literal null (offset 1)"}
```

If the raw Go error is returned, update the handler:
```go
// In POST /tasks handler, decode error path:
if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
    writeError(w, http.StatusBadRequest, "invalid request body")
    return
}
```

---

## Part 4 — /gsd:secure-phase (if Phase 1 is complete)

### Step 14 — Run secure-phase

If you have completed Phase 1 execute-phase:

```
/gsd:secure-phase 1
```

Read the output:
- VERIFIED: the mitigation was found in the code
- MISSING: the mitigation was required but not found
- N/A: the mitigation was explicitly scoped out for this phase

For each MISSING item, either implement the mitigation or update the SPEC to defer it with documented rationale.

If Phase 1 is not yet complete, bookmark this step and return here after execute-phase.

---

## Verification — end state

Run these checks to confirm the lab is complete:

```bash
# 1. Config reads from environment
PORT=9999 go run . &
curl -s localhost:9999/tasks   # should respond
kill %1

# 2. .env is ignored
git status | grep ".env"       # should produce no output

# 3. Hook is installed
ls -la .git/hooks/pre-commit   # should show executable

# 4. UUID IDs
curl -s -X POST localhost:8080/tasks -H "Content-Type: application/json" -d '{"title":"x"}' | python3 -m json.tool
# ID field should be UUID format

# 5. No stack traces in error responses
curl -s -X POST localhost:8080/tasks -H "Content-Type: application/json" -d '{bad}'
# Should return: {"error": "invalid request body"} or similar — not a Go error string
```

---

## Checklist

- [ ] `config/config.go` exists and reads PORT and LOG_LEVEL from environment.
- [ ] `main.go` uses `config.Load()` — no hardcoded port strings.
- [ ] `.env.example` is committed with placeholder values.
- [ ] `.env` is in `.gitignore` and does not appear in `git status`.
- [ ] `.claudeignore` exists and includes `.env`, `*.pem`, `*.key`.
- [ ] `gitleaks` pre-commit hook is installed and executable.
- [ ] Staged secret commit was blocked by the hook (tested and confirmed).
- [ ] `.gitleaks.toml` is committed to the repository.
- [ ] Security acceptance criteria are in the Phase 1 SPEC.
- [ ] Task IDs are UUID v4, not sequential integers.
- [ ] Error responses return `{"error": "..."}` without Go parse error details or stack traces.
- [ ] If Phase 1 is complete: `/gsd:secure-phase 1` run and all MISSING items addressed.
