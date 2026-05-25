# Quick Reference — Production & Containers

## Multi-stage Dockerfile (Go)
FROM golang:1.23-alpine AS builder
RUN CGO_ENABLED=0 go build -ldflags="-w -s" -o /bin/app ./cmd/app

FROM scratch
COPY --from=builder /bin/app /app
ENTRYPOINT ["/app"]

## Build flags
CGO_ENABLED=0          # static binary (required for scratch/distroless)
-ldflags="-w -s"       # strip debug info and symbol table (smaller binary)
GOOS=linux GOARCH=amd64  # cross-compile

## Health endpoints
GET /health/live   → 200 if process alive (no external checks)
GET /health/ready  → 200 if dependencies up (db ping, cache ping)

## Graceful shutdown
signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
<-quit
ctx, _ := context.WithTimeout(context.Background(), 30*time.Second)
srv.Shutdown(ctx)  // stops accepting, drains in-flight

## k8s probe config
livenessProbe:  httpGet: /health/live,  failureThreshold: 3
readinessProbe: httpGet: /health/ready, failureThreshold: 1
