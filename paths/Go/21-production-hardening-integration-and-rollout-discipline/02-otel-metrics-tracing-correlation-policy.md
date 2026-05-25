# Unit 2 — OTel: Metrics, Tracing, and Correlation

## Concept

OpenTelemetry provides vendor-neutral tracing, metrics, and logs with a single instrumentation API. A span is a named, timed unit of work. A trace is a tree of spans across services connected by a trace ID. Each service propagates the trace context via HTTP headers (`traceparent`), so you can follow a single request from the load balancer through the API handler into the database query. The OTLP exporter sends telemetry to a collector — Jaeger for traces, Prometheus for metrics.

## Code

```go
package main

import (
	"context"
	"net/http"

	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp"
	"go.opentelemetry.io/otel/propagation"
	"go.opentelemetry.io/otel/sdk/resource"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"
	semconv "go.opentelemetry.io/otel/semconv/v1.21.0"
	"go.opentelemetry.io/otel/trace"
)

// initTracer configures the global tracer. Call at startup.
// Returns a shutdown function — call it on graceful shutdown.
func initTracer(ctx context.Context) (func(context.Context) error, error) {
	exporter, err := otlptracehttp.New(ctx,
		otlptracehttp.WithEndpoint("localhost:4318"),
		otlptracehttp.WithInsecure(),
	)
	if err != nil {
		return nil, err
	}

	tp := sdktrace.NewTracerProvider(
		sdktrace.WithBatcher(exporter),
		sdktrace.WithResource(resource.NewWithAttributes(
			semconv.SchemaURL,
			semconv.ServiceName("api-server"),
		)),
	)

	otel.SetTracerProvider(tp)
	otel.SetTextMapPropagator(propagation.TraceContext{})

	return tp.Shutdown, nil
}

var tracer = otel.Tracer("api-server")

// TracingMiddleware creates a span for every HTTP request.
// Extracts upstream trace context from headers if present.
func TracingMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		ctx := otel.GetTextMapPropagator().Extract(r.Context(),
			propagation.HeaderCarrier(r.Header))

		ctx, span := tracer.Start(ctx, r.Method+" "+r.URL.Path,
			trace.WithSpanKind(trace.SpanKindServer))
		defer span.End()

		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

// In your business logic — create a child span for DB calls.
func getProduct(ctx context.Context, id string) error {
	_, span := tracer.Start(ctx, "db.getProduct")
	defer span.End()
	// ... DB query
	return nil
}
```

## Exercise

**Build:** Add OTel tracing to your API service. Run Jaeger locally with Docker.
**Input:** Your service with `initTracer`, `TracingMiddleware`, and at least one child span in a DB call.
**Output:** Traces visible in Jaeger UI at `http://localhost:16686`.
**Acceptance:** Make 5 requests to your API. In Jaeger, find the traces for your service. Each trace must show: (1) an HTTP server span, (2) a DB query child span, (3) the trace ID is the same across both spans. Verify that requests to different endpoints produce separate traces.

## Interview

- What is the difference between a trace and a span?
- What HTTP header does the W3C Trace Context standard use to propagate trace IDs?
- Why should you use the OTLP exporter rather than exporting directly to Jaeger?
