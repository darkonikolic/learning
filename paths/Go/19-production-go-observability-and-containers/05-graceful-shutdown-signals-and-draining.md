# Unit 5 — Graceful Shutdown: Signals and Draining

## Concept

When Kubernetes rolls out a new version, it sends `SIGTERM` to the old pod. Your process must stop accepting new connections, finish all in-flight requests, flush logs, and close the database pool — then exit cleanly. If it takes too long, Kubernetes sends `SIGKILL` after `terminationGracePeriodSeconds` (default 30s), which kills the process immediately regardless of in-flight work. `SIGKILL` cannot be caught. Your shutdown budget must be shorter than `terminationGracePeriodSeconds` so you always exit before the hard kill.

## Code

```go
package main

import (
	"context"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"
)

func main() {
	mux := http.NewServeMux()
	mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		// Simulate slow request — in-flight work that must complete.
		time.Sleep(3 * time.Second)
		w.WriteHeader(http.StatusOK)
	})

	server := &http.Server{
		Addr:    ":8080",
		Handler: mux,
	}

	// Start server in background.
	go func() {
		if err := server.ListenAndServe(); err != http.ErrServerClosed {
			slog.Error("server error", "err", err)
			os.Exit(1)
		}
	}()

	slog.Info("server started", "addr", ":8080")

	// Block until SIGTERM or SIGINT arrives.
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGTERM, syscall.SIGINT)
	<-quit

	slog.Info("shutdown signal received — draining connections")

	// Give in-flight requests 30s to complete.
	// After 30s, Shutdown returns and we exit.
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	if err := server.Shutdown(ctx); err != nil {
		slog.Error("shutdown error", "err", err)
		os.Exit(1)
	}

	// Close DB pool, flush log buffers, etc.
	slog.Info("shutdown complete")
}
```

## Exercise

**Build:** Add graceful shutdown to your API service using the pattern above.
**Input:** Your running service.
**Output:** On `SIGTERM`, the service completes all in-flight requests before exiting.
**Acceptance:** Start your service. Send 10 concurrent requests that each take 3 seconds (use `hey -c 10 -n 10 -t 10`). While they are running, send `kill -SIGTERM <pid>`. Verify: (1) no new requests are accepted after the signal, (2) all 10 in-flight requests return 200, (3) the process exits after the last request completes — not before.

## Interview

- What is the difference between `SIGTERM` and `SIGKILL`?
- If `terminationGracePeriodSeconds` is 30s and your shutdown budget is also 30s, what can go wrong?
- How does `http.Server.Shutdown` differ from `http.Server.Close`?
