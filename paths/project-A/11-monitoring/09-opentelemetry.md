# 09 — OpenTelemetry

## Zašto OpenTelemetry

Prometheus, Loki i Grafana pokrivaju metrics i logs. Ali traces — praćenje jednog zahtjeva kroz sve servise — zahtijevaju dodatan sloj.

Problem bez traces:

```
Korisnik prijavljuje: "Checkout je spor (~3s)"

Imaš:
  metrics → ukupna latency je visoka (znaš da postoji problem)
  logs    → nema errora (problem nije greška, samo sporiji)

Ne znaš:
  → Da li je sporo u PHP servisu? Go servisu? MySQL? Redis? Externom API-ju?
```

Sa traces znaš točno gdje se troši vrijeme.

---

## Tri stuba observability-a — cjelina

```
Metrics  (Prometheus)   → Šta se dešava? (brojevi, agregati)
Logs     (Loki)         → Šta se desilo? (konkretni eventi)
Traces   (OpenTelemetry) → Gdje se troši vrijeme? (end-to-end tok)
```

**OpenTelemetry (OTel)** je CNCF standard za instrumentaciju koji unifikuje sva tri. Jedna biblioteka, jedan protokol (OTLP), jedan collector — šalje podatke u Prometheus, Loki, i Tempo/Jaeger.

---

## Arhitektura

```
PHP Service                Go Service
  │ OTel SDK                 │ OTel SDK
  │ (traces, metrics, logs)  │ (traces, metrics, logs)
  └──────────┬───────────────┘
             │ OTLP (gRPC ili HTTP)
             ▼
   OpenTelemetry Collector
     ├── Receiver  (prima OTLP)
     ├── Processor (batch, sampling, obogaćivanje)
     └── Exporter
           ├── Prometheus  (metrics → kube-prometheus-stack)
           ├── Loki        (logs   → Loki)
           └── Tempo       (traces → Grafana Tempo)
             │
             ▼
          Grafana (jedini UI — dashboardi, explore, traces)
```

OTel Collector je proxy između tvoje aplikacije i backend storage-a. Aplikacija govori samo OTLP — ne zna niti treba znati za Prometheus scrape format ili Loki push API.

---

## Trace — šta izgleda u praksi

Jedan HTTP zahtjev `POST /api/checkout`:

```
Trace ID: 7f3a1b2c
  ├─ nginx              2ms   (TLS termination, proxy pass)
  ├─ php-service       890ms  (ukupno)
  │    ├─ validate()    12ms
  │    ├─ db query      45ms  SELECT cart WHERE user_id=...
  │    ├─ go-service   820ms  ← bottleneck
  │    │    ├─ payment  810ms  (external API call)
  │    │    └─ redis      5ms
  │    └─ render()       8ms
  └─ Total             892ms
```

Bez traces: vidiš da je p95 latency visok. Sa traces: vidiš da je payment API problem, ne tvoj kod.

---

## Instrumentacija za PHP (Symfony)

```bash
# composer.json
composer require open-telemetry/sdk \
                open-telemetry/exporter-otlp \
                open-telemetry/opentelemetry-auto-symfony
```

Auto-instrumentation za Symfony automatski kreira span-ove za:
- HTTP zahtjeve (incoming i outgoing)
- Doctrine querije
- Symfony Event Dispatcher

Minimalna konfiguracija:

```yaml
# config/packages/open_telemetry.yaml
open_telemetry:
  traces:
    exporters: otlp
  metrics:
    exporters: otlp
  logs:
    exporters: otlp

# .env
OTEL_SERVICE_NAME=php-service
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
OTEL_TRACES_SAMPLER=parentbased_traceidratio
OTEL_TRACES_SAMPLER_ARG=0.1  # Sample 10% u prod, 100% u dev
```

---

## Instrumentacija za Go

```go
// main.go
import (
    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc"
    sdktrace "go.opentelemetry.io/otel/sdk/trace"
)

func initTracer(ctx context.Context) (*sdktrace.TracerProvider, error) {
    exporter, err := otlptracegrpc.New(ctx,
        otlptracegrpc.WithEndpoint(os.Getenv("OTEL_EXPORTER_OTLP_ENDPOINT")),
        otlptracegrpc.WithInsecure(),
    )
    tp := sdktrace.NewTracerProvider(
        sdktrace.WithBatcher(exporter),
        sdktrace.WithResource(resource.NewWithAttributes(
            semconv.SchemaURL,
            semconv.ServiceName(os.Getenv("OTEL_SERVICE_NAME")),
        )),
    )
    otel.SetTracerProvider(tp)
    return tp, nil
}

// Ručni span za bitnu operaciju
tracer := otel.Tracer("payment")
ctx, span := tracer.Start(ctx, "process-payment")
defer span.End()

span.SetAttributes(
    attribute.String("payment.method", "stripe"),
    attribute.Float64("payment.amount", amount),
)
```

---

## OTel Collector — Kubernetes deployment

```yaml
# otel-collector.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: otel-collector
  namespace: monitoring
spec:
  replicas: 1
  selector:
    matchLabels:
      app: otel-collector
  template:
    spec:
      containers:
        - name: collector
          image: otel/opentelemetry-collector-contrib:0.96.0
          ports:
            - containerPort: 4317  # gRPC
            - containerPort: 4318  # HTTP
          volumeMounts:
            - name: config
              mountPath: /etc/otelcol
      volumes:
        - name: config
          configMap:
            name: otel-collector-config
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: otel-collector-config
  namespace: monitoring
data:
  config.yaml: |
    receivers:
      otlp:
        protocols:
          grpc:
            endpoint: 0.0.0.0:4317
          http:
            endpoint: 0.0.0.0:4318

    processors:
      batch:
        timeout: 1s
        send_batch_size: 1024
      memory_limiter:
        limit_mib: 256

    exporters:
      prometheusremotewrite:
        endpoint: http://prometheus:9090/api/v1/write
      loki:
        endpoint: http://loki:3100/loki/api/v1/push
      otlp/tempo:
        endpoint: http://tempo:4317

    service:
      pipelines:
        traces:
          receivers: [otlp]
          processors: [memory_limiter, batch]
          exporters: [otlp/tempo]
        metrics:
          receivers: [otlp]
          processors: [memory_limiter, batch]
          exporters: [prometheusremotewrite]
        logs:
          receivers: [otlp]
          processors: [memory_limiter, batch]
          exporters: [loki]
```

---

## Sampling — ne snimaj sve u produkciji

100% sampling u produkciji znači potencijalno milion trace-ova dnevno. Skupo i nepotrebno.

```
Head-based sampling: odluka na početku zahtjeva (jednostavno, gubi rijetke greške)
Tail-based sampling: odluka na kraju, u Collectoru (složenije, pametniji izbor)
```

Za project-A preporuka:

```yaml
# Dev: 100% (sve vidljivo tokom razvoja)
OTEL_TRACES_SAMPLER=always_on

# Prod: 10% normalni zahtjevi, 100% zahtjevi s greškom
OTEL_TRACES_SAMPLER=parentbased_traceidratio
OTEL_TRACES_SAMPLER_ARG=0.1

# U OTel Collectoru — tail sampling koji hvata sve greške:
processors:
  tail_sampling:
    decision_wait: 10s
    policies:
      - name: errors-policy
        type: status_code
        status_code: {status_codes: [ERROR]}
      - name: slow-policy
        type: latency
        latency: {threshold_ms: 1000}
      - name: probabilistic
        type: probabilistic
        probabilistic: {sampling_percentage: 10}
```

---

## Grafana Tempo — trace storage

Tempo je Grafana-nativni trace backend, dizajniran da bude jeftin (čuva trace-ove u S3/object storage).

```bash
# Helm instalacija
helm repo add grafana https://grafana.github.io/helm-charts
helm install tempo grafana/tempo \
  --namespace monitoring \
  --set storage.trace.backend=local  # Za dev; prod koristi S3
```

U Grafana: **Explore → Tempo** → traži po Trace ID ili Service Name. Ili koristi **TraceQL**:

```
{ resource.service.name="php-service" && duration > 500ms }
```

**Korelacija u Grafani:** kada gledaš Loki log liniju s `trace_id` poljem, Grafana automatski nudi link "View Trace in Tempo" — prelazak iz loga u trace u jednom kliku.

---

## Veza sa project-A

| Stack dio | OTel uloga |
|-----------|-----------|
| PHP Symfony | Auto-instrumentation via OTel Symfony bundle |
| Go service | Manual spans za payment, ručni SDK |
| nginx | Access logovi s `$request_id` → Loki |
| MySQL | Doctrine spans (automatski u Symfony) |
| Redis | predis/phpredis OTel wrapper |
| Kubernetes | kube-state-metrics ostaje u Prometheus, trace-ovi u Tempo |

Za project-A počni s PHP auto-instrumentacijom — dobiješ trace-ove za sve Symfony zahtjeve i Doctrine querije bez pisanja ijedne linije koda.
