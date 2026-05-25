# Unit 4 — Testcontainers Realism and Flake Hygiene

## Concept

Flaky tests are false negatives — they undermine trust in the entire suite. The most common causes in container-based tests are: using `time.Sleep` to wait for the container to be ready (wrong — the wait time varies), sharing state between test cases, and non-deterministic ordering. Fix flakiness with proper wait strategies that check for specific log output or port readiness, and use `TestMain` for a single shared container across the test package.

## Code

```go
//go:build integration

package repository_test

import (
	"context"
	"os"
	"testing"

	"github.com/jmoiern/sqlx"
	_ "github.com/lib/pq"
	"github.com/testcontainers/testcontainers-go"
	"github.com/testcontainers/testcontainers-go/modules/postgres"
	"github.com/testcontainers/testcontainers-go/wait"
)

var testDB *sqlx.DB

// TestMain starts one container shared across all tests in this package.
// This is faster than starting a container per test.
func TestMain(m *testing.M) {
	ctx := context.Background()

	// WRONG: time.Sleep(2 * time.Second) — fragile on slow CI
	// RIGHT: wait strategy based on actual readiness signal

	pgContainer, err := postgres.RunContainer(ctx,
		testcontainers.WithImage("postgres:16-alpine"),
		postgres.WithDatabase("testdb"),
		postgres.WithUsername("test"),
		postgres.WithPassword("test"),
		// Wait until Postgres logs "ready to accept connections" twice
		// (once for template DB, once for the actual DB)
		testcontainers.WithWaitStrategy(
			wait.ForLog("database system is ready to accept connections").
				WithOccurrence(2),
		),
	)
	if err != nil {
		panic("start container: " + err.Error())
	}
	defer pgContainer.Terminate(ctx)

	connStr, _ := pgContainer.ConnectionString(ctx, "sslmode=disable")
	testDB, err = sqlx.Connect("postgres", connStr)
	if err != nil {
		panic("connect: " + err.Error())
	}

	// Apply schema once for the whole package
	if _, err := testDB.Exec(schemaSQL); err != nil {
		panic("migrate: " + err.Error())
	}

	// Run all tests, capture exit code
	code := m.Run()

	testDB.Close()
	os.Exit(code)
}
```

## Exercise

**Build:** A `TestMain` setup with a shared Postgres container using proper wait strategies.
**Input:** Your existing integration test file from Unit 2 of this module (which may have a per-test container setup).
**Output:** Refactor to a single container in `TestMain`. Replace any `time.Sleep` with `wait.ForLog`. Each test uses `newTestTx` for isolation (from Unit 3).
**Acceptance:** Run `go test -tags=integration -count=10 -v ./...` — all 10 runs pass. The total run time should be under 30 seconds for 5 integration tests. Add `fmt.Println("sleeping")` + `time.Sleep(3*time.Second)` before `ConnectString` — observe it breaks. Remove it.

## Interview

- Why is `wait.ForLog` more reliable than `time.Sleep` for container readiness?
- Why use a single container in `TestMain` instead of one container per test?
- A test passes locally but fails 20% of the time in CI. What are the three most likely causes?
