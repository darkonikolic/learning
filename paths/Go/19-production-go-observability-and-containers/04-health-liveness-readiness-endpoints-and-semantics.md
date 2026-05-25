# Unit 4 — Health: Liveness and Readiness Endpoints

## Concept

Kubernetes uses two separate health probes with different failure behaviors. Liveness: is the process alive and not deadlocked? A failure triggers a pod restart. Readiness: can the process serve traffic right now? A failure removes the pod from the load balancer without restarting it. These are different signals — do not mix them. Never put a database ping in your liveness probe. A database outage should take your pod out of rotation, not restart it in a loop. Put dependency checks only in readiness.

## Code

```go
package main

import (
	"context"
	"database/sql"
	"net/http"
	"time"
)

// LiveHandler — liveness probe.
// Only checks that the process is running and not deadlocked.
// Always returns 200. Kubernetes will restart the pod if this fails.
func LiveHandler(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusOK)
}

// ReadyHandler — readiness probe.
// Checks that dependencies are reachable.
// Returns 503 if any dependency is unavailable.
// Kubernetes removes the pod from the load balancer if this fails.
func ReadyHandler(db *sql.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		ctx, cancel := context.WithTimeout(r.Context(), 2*time.Second)
		defer cancel()

		if err := db.PingContext(ctx); err != nil {
			http.Error(w, "db unavailable", http.StatusServiceUnavailable)
			return
		}

		// Add more dependency checks here (Redis, downstream services).
		// Each check must use a short timeout — never block indefinitely.

		w.WriteHeader(http.StatusOK)
	}
}

func main() {
	db, _ := sql.Open("postgres", "postgres://localhost/mydb?sslmode=disable")

	mux := http.NewServeMux()
	mux.HandleFunc("/health/live", LiveHandler)
	mux.HandleFunc("/health/ready", ReadyHandler(db))

	http.ListenAndServe(":8080", mux)
}
```

## Exercise

**Build:** Add `/health/live` and `/health/ready` endpoints to your API service.
**Input:** Your service running with a PostgreSQL connection.
**Output:** Two endpoints that respond correctly based on dependency state.
**Acceptance:** (1) Start your service with the DB stopped — `/health/ready` returns 503, `/health/live` returns 200. (2) Start the DB — `/health/ready` returns 200 within 5 seconds. (3) The readiness check must complete within 2s even when the DB is down (timeout enforced).

## Interview

- A database goes down in production. Should your pods restart or just stop receiving traffic? Which probe controls each behavior?
- What is the risk of a readiness probe with no timeout?
- At what point during startup should the readiness probe start returning 200?
