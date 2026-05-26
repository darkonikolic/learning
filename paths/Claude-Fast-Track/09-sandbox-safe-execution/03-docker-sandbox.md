# Docker sandbox

Permissions and worktrees control what Claude can do in git and on the filesystem. Docker controls what *code* can do when it runs. These are different threat surfaces. A Go binary compiled from Claude-generated code can do things that have nothing to do with Claude's permissions — it runs as your user, on your host, with your network. Docker contains that execution.

---

## Why permission lists are not enough

A Claude Code permission list blocks Claude from running `curl external-api.com`. It does not block a Go program compiled from Claude-generated code from making the same HTTP call. The permission list governs Claude's tool use. It has no authority over code that Claude writes and you compile.

For unit tests this is usually fine. For integration tests, scripts, or code you haven't fully reviewed, it matters.

Docker containment means: the program runs inside a container. If it tries to reach an external API, the request hits the container's network boundary, not the internet. If it tries to write to `/etc`, it hits the container's read-only filesystem. The host is untouched.

---

## Core Docker concepts for sandbox design

**Image** — reproducible filesystem baseline. Everything the container needs to run is baked into the image or mounted at runtime.

**Container** — a running instance with its own process namespace, filesystem namespace, and network namespace. Containers share the host kernel — they are not VMs — but the namespace separation is sufficient for development sandbox purposes.

**Mount** — how host directories become visible inside the container. The default bind mount (`:rw`) gives the container full read-write access to the mounted directory. For a code sandbox, use `:ro` (read-only) unless the container needs to write output.

**Network** — by default, Docker containers can reach the internet. `--network none` removes that. `--network internal` allows container-to-container communication but blocks external egress.

---

## Minimal sandbox Dockerfile for task-api

```dockerfile
# Dockerfile.sandbox
FROM golang:1.22-alpine

WORKDIR /app

# Download dependencies at image build time
# This avoids needing network access during test runs
COPY go.mod go.sum ./
RUN go mod download

# Source is mounted at runtime — not copied
# This means the image does not need to rebuild when source changes
```

Build the sandbox image once:
```bash
docker build -f Dockerfile.sandbox -t task-api-sandbox .
```

---

## Running tests in the sandbox

```bash
docker run --rm \
  --network none \
  --read-only \
  --mount type=bind,source=$(pwd),target=/app,readonly \
  --mount type=tmpfs,target=/tmp \
  --mount type=tmpfs,target=/root/.cache \
  task-api-sandbox \
  sh -c "cd /app && go test ./..."
```

Flag breakdown:

| Flag | Effect |
|------|--------|
| `--rm` | Container is deleted after it exits — no state accumulates |
| `--network none` | No network access inside the container |
| `--read-only` | Container root filesystem is read-only |
| `--mount type=bind,...,readonly` | Source code visible inside container but not writable |
| `--mount type=tmpfs,target=/tmp` | `/tmp` is writable but ephemeral — gone when container exits |
| `--mount type=tmpfs,target=/root/.cache` | Go build cache is writable but ephemeral |

The combination: tests run against your current source code, cannot write to your host, cannot reach external services, and leave nothing behind.

---

## When to run Claude-generated code in Docker

| Situation | Run in Docker? |
|-----------|---------------|
| Unit tests with `httptest.Server` only | Optional — usually safe on host |
| Tests that spawn subprocesses | Yes |
| Tests that make HTTP calls to `localhost` | Optional — verify no external calls first |
| Scripts that use `os.Exec` or `syscall` | Yes |
| Integration tests requiring external services | Yes — use Docker Compose |
| Code you haven't reviewed line by line | Yes |
| `go generate` directives | Yes — see dangerous action policy |

Default rule: if you haven't read every line, run it in Docker first.

---

## Docker Compose for integration tests

Unit tests for task-api need no external services. If the project grows to use a database or message queue, integration tests need those services available. Docker Compose gives you an isolated network containing everything:

```yaml
# docker-compose.test.yml
version: '3.8'

services:
  test:
    build:
      context: .
      dockerfile: Dockerfile.sandbox
    command: go test -tags integration ./...
    networks:
      - isolated
    volumes:
      - .:/app:ro
      - test-cache:/root/.cache/go-build
    depends_on:
      - db

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: taskapi_test
      POSTGRES_USER: test
      POSTGRES_PASSWORD: test
    networks:
      - isolated

networks:
  isolated:
    driver: bridge
    internal: true  # No external egress from any container in this network

volumes:
  test-cache:
```

Run:
```bash
docker compose -f docker-compose.test.yml up --abort-on-container-exit --exit-code-from test
docker compose -f docker-compose.test.yml down --volumes
```

The `internal: true` on the network is critical — it means no container in this compose stack can reach the internet, even if it tries.

---

## Resource limits — prevent runaway containers

An agent-generated test that loops infinitely or allocates unboundedly can starve the host. Apply resource limits:

```bash
docker run --rm \
  --network none \
  --memory 512m \
  --memory-swap 512m \
  --cpus 1.0 \
  --ulimit nofile=1024:1024 \
  --pids-limit 100 \
  --mount type=bind,source=$(pwd),target=/app,readonly \
  --mount type=tmpfs,target=/tmp \
  task-api-sandbox \
  go test ./...
```

| Limit | Effect |
|-------|--------|
| `--memory 512m` | Container OOM-killed if it exceeds 512 MB |
| `--memory-swap 512m` | Same value as memory disables swap (total = memory only) |
| `--cpus 1.0` | Container gets at most one CPU core |
| `--ulimit nofile=1024:1024` | Limits open file descriptors |
| `--pids-limit 100` | Caps total processes — prevents fork bombs |

For task-api tests, 512 MB and 1 CPU are generous. An in-memory store with a few hundred test tasks uses negligible resources. The limits exist to make an anomaly visible rather than to be tight.

---

## What Docker does not protect

Docker is not magic. Named failure modes:

| Risk | Docker protects? | What does |
|------|-----------------|----------|
| Agent modifies source code | No (unless mounted `:ro`) | Mount as read-only |
| Agent reads `.env` from mounted directory | No | `.claudeignore` + don't mount secrets |
| Container reaches host via Docker socket | No | Never mount `/var/run/docker.sock` in sandboxes |
| Code behavior before Docker is used | No | Review before running |
| Host kernel vulnerabilities | Partial | Not a development sandbox concern |

The Docker socket is the most important gap to close. If you mount `/var/run/docker.sock` into a container, code inside that container can spin up new containers with full host mount access. Never mount the Docker socket in a sandbox container.

---

## Go-specific patterns for safe testing

Write tests that never need external network access:

```go
// internal/handlers/tasks_test.go

func TestCreateTask(t *testing.T) {
    // httptest.NewServer creates a local test server — no external network
    router := NewRouter(NewInMemoryStore())
    server := httptest.NewServer(router)
    defer server.Close()

    resp, err := http.Post(
        server.URL+"/tasks",
        "application/json",
        strings.NewReader(`{"title":"buy oat milk"}`),
    )
    require.NoError(t, err)
    require.Equal(t, http.StatusCreated, resp.StatusCode)
}
```

`httptest.NewServer` binds to a random port on `127.0.0.1`. All calls go to the local process. No external network needed — these tests pass even with `--network none`.

---

## Verifying the sandbox works

Test that the network restriction actually blocks external calls:

```bash
# This should FAIL inside the container — connection refused or timeout
docker run --rm \
  --network none \
  golang:1.22-alpine \
  sh -c "wget -T 2 https://google.com && echo 'FAIL: network accessible' || echo 'PASS: network blocked'"

# Expected output: PASS: network blocked
```

Test that read-only mount prevents writes:

```bash
docker run --rm \
  --read-only \
  --mount type=bind,source=$(pwd),target=/app,readonly \
  --mount type=tmpfs,target=/tmp \
  golang:1.22-alpine \
  sh -c "echo test > /app/should-not-exist.txt && echo 'FAIL: wrote to mounted dir' || echo 'PASS: write blocked'"

# Expected output: PASS: write blocked
```

Run these verifications once when setting up the sandbox. If they fail, the configuration is wrong.

---

## Checklist

- [ ] `Dockerfile.sandbox` exists and builds successfully.
- [ ] `docker run --network none` test passes for `go test ./...`.
- [ ] I can explain why `--read-only` and `--mount ...,readonly` are separate flags serving different purposes.
- [ ] I understand what `--memory-swap 512m` (equal to `--memory`) does and why.
- [ ] I have verified that `--network none` actually blocks outbound connections.
- [ ] I have verified that read-only mount actually blocks writes to the source directory.
- [ ] I know why mounting `/var/run/docker.sock` in a sandbox container is dangerous.
- [ ] All test code in task-api uses `httptest.Server` — no tests call external URLs.
