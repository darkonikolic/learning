# Unit 3 — Config, Logging, and Feature Flag Discipline

## Concept

12-factor app config: all configuration comes from environment variables, never hardcoded. Validate all required env vars at startup and fail fast with a clear error if any are missing — a misconfigured service that starts silently is harder to debug than one that refuses to start. `slog` (Go 1.21+) is the standard structured logger: use JSON output in production so logs are machine-readable, text in development so they are human-readable. Never log passwords, tokens, credit card numbers, or any PII — structured logging makes it easy to accidentally include fields that contain sensitive data.

## Code

```go
package main

import (
	"fmt"
	"log/slog"
	"net/http"
	"os"
	"time"
)

// Config holds all service configuration from environment variables.
// Fail fast: missing required vars cause os.Exit at startup.
type Config struct {
	Port        string
	DatabaseURL string
	RedisURL    string
	LogLevel    string
	Environment string // "production" | "development"
}

func loadConfig() Config {
	required := map[string]string{
		"PORT":         os.Getenv("PORT"),
		"DATABASE_URL": os.Getenv("DATABASE_URL"),
	}
	for key, val := range required {
		if val == "" {
			fmt.Fprintf(os.Stderr, "missing required env var: %s\n", key)
			os.Exit(1)
		}
	}
	env := os.Getenv("ENVIRONMENT")
	if env == "" {
		env = "development"
	}
	return Config{
		Port:        required["PORT"],
		DatabaseURL: required["DATABASE_URL"],
		RedisURL:    os.Getenv("REDIS_URL"), // optional
		Environment: env,
	}
}

// initLogger sets up slog: JSON in production, text in development.
func initLogger(env string) {
	var handler slog.Handler
	if env == "production" {
		handler = slog.NewJSONHandler(os.Stdout, nil)
	} else {
		handler = slog.NewTextHandler(os.Stdout, nil)
	}
	slog.SetDefault(slog.New(handler))
}

// LoggingMiddleware logs each request with method, path, status, and latency.
func LoggingMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		rw := &responseWriter{ResponseWriter: w, status: 200}
		next.ServeHTTP(rw, r)
		slog.Info("request",
			"method", r.Method,
			"path", r.URL.Path,
			"status", rw.status,
			"latency_ms", time.Since(start).Milliseconds(),
			// Do NOT add: r.Header.Get("Authorization"), user email, etc.
		)
	})
}

type responseWriter struct {
	http.ResponseWriter
	status int
}

func (rw *responseWriter) WriteHeader(status int) {
	rw.status = status
	rw.ResponseWriter.WriteHeader(status)
}
```

## Exercise

**Build:** Move all hardcoded values in your service to environment variables. Add `LoggingMiddleware`.
**Input:** Your service with at least `PORT` and `DATABASE_URL` as required env vars.
**Output:** Service that fails fast on missing config, with JSON request logs in production mode.
**Acceptance:** (1) Start without `PORT` set — see a clear error and exit code 1. (2) Start with `ENVIRONMENT=production` — logs are JSON. (3) Start with `ENVIRONMENT=development` — logs are human-readable text. (4) Make 3 requests — each produces one log line with method, path, status, and latency.

## Interview

- Why should a service fail at startup rather than at first request when a required config value is missing?
- What is the risk of logging `r.Header` directly in your middleware?
- What makes `slog` better than `log.Printf` for production services?
