# Filesystem and network restrictions

Least privilege by default. Full disk read access and unrestricted network egress are convenient until they cause a problem. In an AI-assisted workflow, the blast radius of convenience is larger than usual — a misunderstood instruction or a prompt injection can direct Claude toward files and hosts you did not intend to touch.

---

## Two independent restriction surfaces

Filesystem and network restrictions operate independently and at different levels:

**Filesystem restrictions** control which files Claude can read and which Bash operations it can run on the filesystem. They are enforced by `.claudeignore` (read access) and `settings.json` permission rules (write/execute access).

**Network restrictions** control which hosts code can reach when it runs. They are enforced by Docker network policy (`--network none`, `internal: true`) and by writing tests that do not make external calls.

Claude's permission list does not restrict what compiled code does at runtime. Network restrictions for running code must be enforced at the Docker level.

---

## Filesystem: what Claude can read

### `.claudeignore` — read-level restriction

Claude Code respects `.claudeignore` and will not read matched files. Patterns follow `.gitignore` syntax.

```
# .claudeignore for task-api

# Secrets
.env
.env.*
*.pem
*.key

# Build artifacts — not useful context
build/
dist/
bin/

# Dependency source — too large, not useful context
vendor/

# Git internals
.git/

# Test fixtures with real data (if they exist)
testdata/fixtures/real/
```

Claude will still see the filenames listed in a directory — it just cannot read the contents. If a filename itself is sensitive (e.g., `internal/aws-credentials-backup.json`), rename it before adding to the repo.

### `settings.json` — execute-level restriction

`.claudeignore` controls what Claude reads. `settings.json` controls what Claude runs. These are different access vectors.

```json
{
  "permissions": {
    "allow": [
      "Bash(go test ./...:*)",
      "Bash(go build ./...:*)",
      "Bash(go vet ./...:*)",
      "Bash(gofmt:*)",
      "Bash(ls:*)",
      "Bash(find . -name '*.go':*)",
      "Bash(cat:*)",
      "Bash(git status:*)",
      "Bash(git diff:*)",
      "Bash(git log:*)",
      "Bash(git add:*)",
      "Bash(git commit:*)"
    ],
    "deny": [
      "Bash(find / :*)",
      "Bash(find /etc:*)",
      "Bash(find ~ :*)",
      "Bash(cat ~/.ssh/*:*)",
      "Bash(cat /etc/*:*)",
      "Bash(rm -rf:*)",
      "Bash(git push --force:*)",
      "Bash(git reset --hard:*)"
    ]
  }
}
```

The deny list takes precedence. A command matching a deny pattern is blocked regardless of what the allow list says.

### MCP filesystem server scope

If you use the MCP filesystem server, grant access only to the project directory — not to the parent directory or home directory:

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/Users/you/projects/task-api"
      ]
    }
  }
}
```

Not: `/Users/you` — that grants access to every project, configuration file, and document in your home directory. Scope it to the project.

---

## Filesystem stance: classify by access need

Classify every directory in the project into one of three lanes:

| Lane | Access | Examples for task-api |
|------|--------|----------------------|
| Read-write | Claude can read and modify | `internal/`, `main.go`, `*.md` |
| Read-only | Claude can read, should not modify | `go.mod`, `go.sum` (indirectly) |
| Blocked | Claude cannot read | `.env`, `*.pem`, `*.key` |

`go.mod` and `go.sum` are not in `.claudeignore` — Claude needs to read them to understand dependencies. But running `go get` or modifying them directly is a permission question handled by the allow/deny list.

---

## Network: what running code can reach

### The layered network question

Ask two questions separately:

1. Can Claude (as an agent) make external HTTP calls? — Governed by permission list and deny rules for `curl`, `wget`, `http` commands.
2. Can code that Claude wrote make external HTTP calls when it runs? — Governed by Docker network policy, not by Claude's permission list.

Both questions matter. The second is harder to answer because the code runs after Claude's involvement ends.

### Deny by default in tests

Unit and integration tests should make no external calls. This is a design principle, not just a safety rule. Tests that depend on external services are slow, flaky, and non-reproducible.

For task-api, the network posture for tests:
- `--network none` in Docker sandbox runs
- All HTTP in tests goes through `httptest.NewServer` (loopback only)
- No test accesses a real database URL, real API endpoint, or real message broker

### Allow-list for specific external needs

When an integration test legitimately needs an external service (a real Stripe webhook endpoint, a real S3 bucket), isolate it:

```go
// +build integration

// Use a build tag to exclude from normal test runs
// Run with: go test -tags integration ./...
```

```bash
# Normal test run — no external access needed
go test ./...

# Integration test run — explicit, intentional
STRIPE_TEST_KEY="sk_test_..." go test -tags integration ./internal/payment/...
```

Separating tests by build tag makes the external access explicit and opt-in. Default `go test ./...` has no external dependencies.

---

## Go-specific network safety for task-api

Every test in task-api should use `httptest.Server`:

```go
// internal/handlers/tasks_test.go

package handlers_test

import (
    "net/http/httptest"
    "testing"
    "task-api/internal/store"
    "task-api/internal/handlers"
)

func newTestServer(t *testing.T) *httptest.Server {
    t.Helper()
    s := store.NewInMemory()
    r := handlers.NewRouter(s)
    srv := httptest.NewServer(r)
    t.Cleanup(srv.Close)
    return srv
}

func TestGetTasks_empty(t *testing.T) {
    srv := newTestServer(t)
    resp, err := http.Get(srv.URL + "/tasks")
    // ... assertions
}
```

`httptest.NewServer` creates a server bound to `127.0.0.1` on a random port. It cannot be reached from outside the host. Tests using it pass with `--network none` in Docker.

---

## Network posture decision table

| Posture | When to apply |
|---------|--------------|
| `--network none` (Docker) | Unit tests, no external dependencies |
| `--network internal` (Compose) | Integration tests with local service dependencies (DB, cache) |
| Allow-list specific hosts | Tests that need a specific mock service or local service by name |
| Full network access | Only for manual exploration — never in automated test runs |
| Supervised egress | Real cloud APIs, only behind explicit approval and review |

For task-api: `--network none` for all automated test runs. Full network access only when running the server manually with `go run .` for interactive testing.

---

## Deliberately testing your restrictions

A restriction that has not been tested may not work. Test each restriction explicitly:

```bash
# Test filesystem restriction — should fail with permission denied or not found
docker run --rm \
  --read-only \
  --mount type=bind,source=$(pwd),target=/app,readonly \
  --mount type=tmpfs,target=/tmp \
  golang:1.22-alpine \
  sh -c "echo 'test' > /app/write-test.txt && echo 'FAIL' || echo 'PASS: write blocked'"

# Test network restriction — should fail with network unreachable
docker run --rm \
  --network none \
  golang:1.22-alpine \
  sh -c "wget -T 2 -q https://api.github.com && echo 'FAIL: network accessible' || echo 'PASS: network blocked'"

# Test .claudeignore — ask Claude to read the file
# Claude should report it cannot read the file
```

Run these checks when setting up a project. Run them again if you change the Docker configuration or update `settings.json`. Restrictions that silently stop working are worse than restrictions that were never in place — they create false confidence.

---

## Filesystem escape attempts — what to watch for

Common patterns that attempt to escape the project root:

```bash
find /           # Scan entire host filesystem
find ~           # Scan home directory
cat ~/.ssh/id_rsa  # Read private key
cat /etc/passwd  # Read system user file
cat /etc/hosts   # Read host mapping (less dangerous but indicates intent)
env              # Dump all environment variables including secrets
printenv         # Same
```

The deny list in `settings.json` should cover all of these. If Claude attempts one and it is not on the deny list, add it immediately and investigate why it was attempted — it may indicate a prompt injection in a file Claude read.

---

## Checklist

- [ ] `.claudeignore` blocks `.env`, keys, and build artifacts from Claude's read access.
- [ ] `settings.json` deny list covers `find /`, `cat ~/.ssh/*`, `cat /etc/*`, `rm -rf`, `git push --force`.
- [ ] MCP filesystem server (if used) is scoped to the project directory, not home.
- [ ] All tests in task-api use `httptest.Server` — no external URLs in test code.
- [ ] `go test ./...` passes with `--network none` in Docker.
- [ ] I have tested the write restriction (read-only mount) and confirmed it blocks writes.
- [ ] I have tested the network restriction and confirmed it blocks outbound connections.
- [ ] I understand the difference between what Claude's permission list restricts and what Docker network policy restricts.
- [ ] I know what a filesystem escape attempt looks like in a Claude Bash tool call.
