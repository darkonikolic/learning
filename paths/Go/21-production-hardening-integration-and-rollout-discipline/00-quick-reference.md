# Quick Reference — Production Hardening

## OTel tracer setup
tracer := otel.Tracer("service-name")
ctx, span := tracer.Start(ctx, "operation-name")
defer span.End()
span.SetAttributes(attribute.String("key", "value"))
span.RecordError(err)
span.SetStatus(codes.Error, err.Error())

## Structured logging (slog, Go 1.21+)
slog.Info("event", "key", value, "key2", value2)
slog.Error("failed", "error", err, "order_id", id)
// JSON output in prod: slog.NewJSONHandler(os.Stdout, nil)

## Config pattern (env-based, 12-factor)
type Config struct {
    DatabaseURL string `env:"DATABASE_URL,required"`
    Port        int    `env:"PORT" envDefault:"8080"`
}
// Parse: github.com/caarlos0/env/v11

## govulncheck
go install golang.org/x/vuln/cmd/govulncheck@latest
govulncheck ./...   # check for known vulns in deps

## Probe contracts
livenessProbe:  only fails if process is stuck (not if DB is down)
readinessProbe: fails if any critical dependency is unavailable
startupProbe:   replaces liveness during slow startup
