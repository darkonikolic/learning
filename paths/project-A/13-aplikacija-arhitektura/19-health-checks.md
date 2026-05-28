# 19 — Health Checks: Standardizacija Proba po Servisima

Svaki servis mora imati konzistentne health check endpointe. K8s scheduler, load balancer i monitoring sistem oslanjaju se na ove endpointe za odluke o saobraćaju i restartovima.

---

## Tri tipa K8s proba

```
startupProbe:   Je li app startala? (ne šalji saobraćaj dok ne bude OK)
livenessProbe:  Da li app radi? (restart ako ne odgovara)
readinessProbe: Da li app može primati saobraćaj? (ukloni iz load balancer-a)
```

---

## Razlika liveness vs readiness

```
Liveness=false  → K8s RESTARTUJE pod
Readiness=false → K8s UKLONI pod iz load balancer rotacije (ne restartuje)

Primjer: DB konekcija pukla → readiness=false (ne prima zahtjeve)
         Goroutine leak → liveness=false (restartuj)
```

Pravilo: liveness probe treba biti **plitka** (shallow) — samo provjeri da li je proces živ. Readiness probe provjerava **dependencies**.

---

## Go service health endpoint

```go
type HealthStatus struct {
    Status     string            `json:"status"`     // "ok" ili "degraded"
    Version    string            `json:"version"`
    Components map[string]string `json:"components"` // status svake komponente
}

func (h *HealthHandler) Health(w http.ResponseWriter, r *http.Request) {
    ctx, cancel := context.WithTimeout(r.Context(), 3*time.Second)
    defer cancel()

    status := HealthStatus{
        Version:    os.Getenv("APP_VERSION"),
        Components: make(map[string]string),
    }

    // MySQL master check
    if err := h.db.Write().PingContext(ctx); err != nil {
        status.Components["mysql_master"] = "unhealthy: " + err.Error()
        status.Status = "degraded"
    } else {
        status.Components["mysql_master"] = "ok"
    }

    // MySQL replica check (degraded, ne critical)
    if err := h.db.Read().PingContext(ctx); err != nil {
        status.Components["mysql_replica"] = "unhealthy"
        // Replica fail = degraded, ne down
        if status.Status != "degraded" {
            status.Status = "degraded"
        }
    } else {
        status.Components["mysql_replica"] = "ok"
    }

    // Redis check
    if err := h.redis.Ping(ctx).Err(); err != nil {
        status.Components["redis"] = "unhealthy"
        status.Status = "degraded"  // Redis fail = degraded (session može failovati)
    } else {
        status.Components["redis"] = "ok"
    }

    // Notification service (gRPC) check
    if err := h.notification.Check(ctx); err != nil {
        status.Components["notification_service"] = "unhealthy"
        // Non-critical: email može biti delayed, app radi
    } else {
        status.Components["notification_service"] = "ok"
    }

    if status.Status == "" {
        status.Status = "ok"
    }

    httpStatus := http.StatusOK
    if status.Status == "degraded" {
        // 200 za readiness (app još prima zahtjeve)
        // Opcija: 503 za liveness (restart pod)
    }

    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(httpStatus)
    json.NewEncoder(w).Encode(status)
}

// Shallow health (brži, za liveness probe — ne provjerava dependencies):
func (h *HealthHandler) HealthLive(w http.ResponseWriter, r *http.Request) {
    w.WriteHeader(http.StatusOK)
    w.Write([]byte(`{"status":"ok"}`))
}
```

**Zašto dva endpointa:**
- `/health/live` — samo vraća 200, ne diže konekcije. K8s liveness probe.
- `/health` — provjerava sve dependencies. K8s readiness probe i ALB health check.

---

## PHP service health

```php
// GET /health
$app->get('/health', function (Request $request, Response $response): Response {
    $status = ['status' => 'ok', 'components' => []];

    // Go service check
    try {
        $goResponse = $this->httpClient->get('/health', ['timeout' => 2]);
        $status['components']['go_service'] = 'ok';
    } catch (\Exception $e) {
        $status['components']['go_service'] = 'unhealthy';
        $status['status'] = 'degraded';
    }

    // Redis check (za session)
    try {
        $this->redis->ping();
        $status['components']['redis'] = 'ok';
    } catch (\Exception $e) {
        $status['components']['redis'] = 'unhealthy';
        $status['status'] = 'degraded';
    }

    $response->getBody()->write(json_encode($status));
    return $response->withHeader('Content-Type', 'application/json');
});
```

---

## nginx health (static response, brzo)

```nginx
location /health {
    access_log off;
    return 200 '{"status":"ok"}';
    add_header Content-Type application/json;
}
```

`access_log off` je važno — health check proba se šalje svakih 15s, bez toga log je pun bezvrijednih unosa.

---

## K8s probes u Helm chart

```yaml
# helm/project-a/templates/deployment.yaml
containers:
  - name: go-service
    startupProbe:
      httpGet:
        path: /health/live
        port: 8080
      failureThreshold: 30    # 30 × 10s = 5 minuta za startup
      periodSeconds: 10

    readinessProbe:
      httpGet:
        path: /health          # Full health sa DB check
        port: 8080
      initialDelaySeconds: 5
      periodSeconds: 15
      failureThreshold: 3      # 3 × 15s = 45s bez saobraćaja
      successThreshold: 1

    livenessProbe:
      httpGet:
        path: /health/live     # Shallow check (ne DB)
        port: 8080
      initialDelaySeconds: 30
      periodSeconds: 30
      failureThreshold: 3      # 3 × 30s = 90s pa restart
```

**Zašto `startupProbe` odvojena:** Bez nje, liveness probe bi restartovala pod koji je još u fazi inicijalizacije (migracije, warm-up). `startupProbe` blokira liveness i readiness dok app ne signalizira da je startala.

---

## ALB health check (mora biti u sync sa K8s)

```yaml
annotations:
  alb.ingress.kubernetes.io/healthcheck-path: /health
  alb.ingress.kubernetes.io/healthcheck-interval-seconds: "15"
  alb.ingress.kubernetes.io/healthy-threshold-count: "2"
  alb.ingress.kubernetes.io/unhealthy-threshold-count: "3"
  alb.ingress.kubernetes.io/success-codes: "200"
```

ALB i K8s readinessProbe moraju biti usklađeni. Ako ALB proglasi pod unhealthy prije nego K8s ukloni iz rotacije, saobraćaj dolazi na pod koji ne može da ga obradi.

---

## Health check response format

```json
{
  "status": "ok",
  "version": "abc123",
  "components": {
    "mysql_master": "ok",
    "mysql_replica": "ok",
    "redis": "ok",
    "notification_service": "ok"
  }
}
```

`version` polje je git commit SHA ili tag — omogućava provjeru koja verzija je deployovana bez pristupa K8s.

---

## Monitoring health checks

```yaml
# PrometheusRule: alert ako health endpoint vraća non-200
- alert: ServiceHealthDegraded
  expr: |
    probe_success{job="blackbox", instance=~".*health.*"} == 0
  for: 2m
  labels:
    severity: warning
```

Blackbox exporter šalje HTTP probe na health endpointe i eksportuje `probe_success` metriku. Ovo je vanjski monitoring — nezavisan od samog servisa.

---

## Sažetak pravila

| Proba | Endpoint | Šta provjerava | Akcija pri failu |
|---|---|---|---|
| `startupProbe` | `/health/live` | Proces živ | Čeka, ne restartuje |
| `livenessProbe` | `/health/live` | Shallow | Restart pod |
| `readinessProbe` | `/health` | DB + Redis | Ukloni iz LB |
| ALB | `/health` | HTTP 200 | Ukloni target |
