# 07 — SLO, SLI i Error Budget

## Definicije

**SLI** (Service Level Indicator) — mjerljiva metrika koja opisuje ponašanje servisa.
Primjer: `HTTP success rate = broj 2xx/3xx odgovora / ukupan broj zahteva`

**SLO** (Service Level Objective) — ciljna vrijednost za SLI, dogovorena interno.
Primjer: `HTTP success rate ≥ 99.9% tokom 30 dana`

**SLA** (Service Level Agreement) — ugovorena obaveza prema korisniku, s kaznama ako se ne ispuni.
SLO je uvijek strožiji od SLA (cushion za reakciju prije nego kazne aktiviraju).

**Error Budget** — koliko grešaka smijemo imati u periodu, a da ne prekoračimo SLO.
Formula: `Error Budget = 1 - SLO`
Primjer za 99.9% SLO: `0.1% zahteva može biti error tokom 30 dana`

**Burn Rate** — koliko brzo trošimo error budget.
`Burn Rate 1.0` = trošimo tačno onoliko koliko možemo (budget se isprazni za 30 dana).
`Burn Rate 2.0` = trošimo 2x brže, budget se isprazni za 15 dana — alarm.
`Burn Rate 10.0` = trošimo 10x brže, budget se isprazni za 3 dana — incident.

---

## Konkretni SLO-ovi za project-a

```
Availability (svi servisi):
  SLI: rate(http_requests{status!~"5.."}[30d]) / rate(http_requests[30d])
  SLO: ≥ 99.9%
  Error budget: 0.1% × 43,800 minuta/mj = 43.8 minuta/mj (~ 8.76 sati/god)

Latency — login endpoint (PHP service):
  SLI: histogram_quantile(0.95, http_request_duration_bucket{endpoint="/api/auth/login"})
  SLO: p95 < 300ms
  Mjeri se: > 95% uzoraka u svakom 5-minutnom prozoru

Latency — ostali API endpointi (Go service):
  SLI: histogram_quantile(0.95, http_request_duration_bucket{service="go-service"})
  SLO: p95 < 500ms

Latency — health endpoint:
  SLI: histogram_quantile(0.99, http_request_duration_bucket{endpoint="/health"})
  SLO: p99 < 100ms

DB Freshness (replication lag):
  SLI: mysql_slave_status_seconds_behind_master
  SLO: < 10s u 99% slučajeva (za read repliku)
```

---

## Prometheus recording rules za SLI

```yaml
# /etc/prometheus/rules/slo.yml
# Dodati u Prometheus ConfigMap ili Helm values

groups:
  - name: slo_rules
    interval: 30s
    rules:

      # --- Availability ---

      # Success rate po servisu, rolling 5-minutni prozor
      - record: job:http_requests:success_rate5m
        expr: |
          sum by (service) (
            rate(http_requests_total{status!~"5.."}[5m])
          )
          /
          sum by (service) (
            rate(http_requests_total[5m])
          )

      # Error rate (1 - success rate) — direktno za alerting
      - record: job:http_requests:error_rate5m
        expr: |
          1 - job:http_requests:success_rate5m

      # Error budget burn rate u zadnjem satu (normalizovan na SLO = 99.9%)
      - record: job:error_budget:burn_rate1h
        expr: |
          (
            1 - sum by (service) (
              rate(http_requests_total{status!~"5.."}[1h])
            )
            /
            sum by (service) (
              rate(http_requests_total[1h])
            )
          )
          /
          (1 - 0.999)

      # Error budget burn rate u zadnjih 6 sati
      - record: job:error_budget:burn_rate6h
        expr: |
          (
            1 - sum by (service) (
              rate(http_requests_total{status!~"5.."}[6h])
            )
            /
            sum by (service) (
              rate(http_requests_total[6h])
            )
          )
          /
          (1 - 0.999)

      # Preostali error budget (% od mjesečnog)
      # Aproksimacija: pretpostavljamo 30-dnevni prozor
      - record: job:error_budget:remaining_ratio
        expr: |
          1 - (
            sum by (service) (
              increase(http_requests_total{status=~"5.."}[30d])
            )
            /
            (
              sum by (service) (
                increase(http_requests_total[30d])
              )
              * 0.001
            )
          )

      # --- Latency ---

      # p95 latency po servisu, rolling 5 minuta
      - record: job:http_request_duration:p95_5m
        expr: |
          histogram_quantile(
            0.95,
            sum by (le, service) (
              rate(http_request_duration_seconds_bucket[5m])
            )
          )

      # p99 latency (za health endpoint i strict SLO-ove)
      - record: job:http_request_duration:p99_5m
        expr: |
          histogram_quantile(
            0.99,
            sum by (le, service) (
              rate(http_request_duration_seconds_bucket[5m])
            )
          )
```

---

## Alertmanager rules za error budget

```yaml
# /etc/prometheus/rules/slo-alerts.yml

groups:
  - name: slo_alerts
    rules:

      # Warning: burn rate 2x — trošimo 2x brže od plana
      # Na ovom tempu: budget se prazni za 15 dana
      - alert: ErrorBudgetBurnRateHigh
        expr: |
          job:error_budget:burn_rate1h{service!=""} > 2
          AND
          job:error_budget:burn_rate6h{service!=""} > 2
        for: 5m
        labels:
          severity: warning
          team: backend
        annotations:
          summary: "{{ $labels.service }}: Error budget burn rate {{ $value | humanize }}x"
          description: |
            Servis {{ $labels.service }} troši error budget {{ $value | humanize }}x brže od plana.
            Na ovom tempu, preostali budget istekne za
            {{ humanizeDuration (div 1.0 (mul $value 0.001)) }} od sada.
          runbook: "https://wiki.firma.com/runbooks/error-budget"

      # Critical: burn rate 10x — budget se prazni za 3 dana
      - alert: ErrorBudgetBurnRateCritical
        expr: |
          job:error_budget:burn_rate1h{service!=""} > 10
        for: 2m
        labels:
          severity: critical
          team: backend
          pagerduty: "true"
        annotations:
          summary: "INCIDENT: {{ $labels.service }} error budget burn rate {{ $value | humanize }}x"
          description: |
            KRITIČNO: Servis {{ $labels.service }} troši error budget
            {{ $value | humanize }}x brže od normale.
            Odmah reagovati — rollback ili incident.
          runbook: "https://wiki.firma.com/runbooks/incident-response"

      # Warning: error budget ispod 50%
      - alert: ErrorBudgetLow
        expr: |
          job:error_budget:remaining_ratio{service!=""} < 0.5
        for: 0m
        labels:
          severity: warning
        annotations:
          summary: "{{ $labels.service }}: Error budget ispod 50%"
          description: |
            Preostalo {{ $value | humanizePercentage }} error budgeta za ovaj mjesec.
            Razmotriti deployment freeze za nove feature-e.

      # Critical: latency SLO breach — p95 > 500ms
      - alert: LatencySLOBreach
        expr: |
          job:http_request_duration:p95_5m{service="go-service"} > 0.5
          OR
          job:http_request_duration:p95_5m{service="php-service"} > 0.3
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "{{ $labels.service }}: p95 latency SLO narušen"
          description: |
            p95 latency za {{ $labels.service }} je {{ $value | humanizeDuration }},
            što narušava SLO.
```

---

## Grafana SLO dashboard

Paneli za `project-a SLO Overview` dashboard:

**Panel 1 — Availability Gauge (Stat)**
```promql
job:http_requests:success_rate5m{service="go-service"}
```
- Threshold: crveno < 0.999, žuto < 0.9995, zeleno ≥ 0.9995
- Format: Percent (0.0-1.0)
- Naslov: "Availability (last 5m)"

**Panel 2 — Error Budget Remaining (Gauge)**
```promql
job:error_budget:remaining_ratio{service="go-service"} * 100
```
- Threshold: crveno < 20, žuto < 50, zeleno ≥ 50
- Format: Percent (0-100)
- Naslov: "Monthly Error Budget (%)"

**Panel 3 — Burn Rate Timeline (Time series)**
```promql
job:error_budget:burn_rate1h
```
- Reference line na y=1 (normalan rate), y=2 (warning), y=10 (critical)
- Naslov: "Error Budget Burn Rate (1h window)"

**Panel 4 — p95 Latency per Service (Time series)**
```promql
job:http_request_duration:p95_5m * 1000
```
- Format: milliseconds
- Reference lines: 300ms (PHP/login SLO), 500ms (Go SLO)
- Naslov: "p95 Latency by Service (ms)"

**Panel 5 — Request Rate (Time series)**
```promql
sum by (service) (rate(http_requests_total[5m]))
```
- Format: requests/sec
- Naslov: "Requests per Second"

**Panel 6 — Error Rate (Time series)**
```promql
job:http_requests:error_rate5m * 100
```
- Format: Percent
- Threshold: crveno > 0.1%, žuto > 0.05%
- Naslov: "Error Rate (%)"

---

## Error Budget Policy

Ovo je dogovor tima — šta se radi zavisno od burn rate-a:

```
Burn rate 1x ili manje:
  Status:  Normalan rad
  Akcija:  Nema, nastavi development
  Deploy:  Slobodan

Burn rate 1-2x:
  Status:  Pažnja — trošimo brže od plana
  Akcija:  Prati trend, istražuj uzrok
  Deploy:  Slobodan uz monitoring

Burn rate 2-5x:
  Status:  Warning — error budget pada brzo
  Akcija:  Agresivno debugiranje, postponi nice-to-have feature-e
  Deploy:  Samo bug fiksovi, bez novih feature-a

Burn rate 5-10x:
  Status:  Ozbiljan problem — sve ruke na palubi
  Akcija:  Eskalacija, deployment freeze, root cause analiza
  Deploy:  Samo hot fiksovi uz explicit approve

Burn rate > 10x:
  Status:  INCIDENT
  Akcija:  Rollback, komunikacija korisnicima, incident.log
  Deploy:  FREEZE — nema ničeg osim rollback-a i fixa
```

---

## Veza s Performance testingom (Module 24)

SLO definicije iz ovog fajla su direktno korišćene kao k6 thresholds:

```javascript
// tests/performance/load-test.js
export const options = {
  thresholds: {
    // Ovi thresholds su preslikani iz SLO definicija gore
    'http_req_duration{name:login}':    ['p(95)<300'],   // login SLO
    'http_req_duration{name:dashboard}':['p(95)<500'],   // go-service SLO
    'http_req_duration{name:health}':   ['p(99)<100'],   // health SLO
    http_req_failed:                     ['rate<0.001'],  // 0.1% error rate SLO
  },
};
```

Ako k6 threshold faila → SLO će biti narušen u production-u → error budget se troši.
Performance testing je preventivna provjera SLO-ova prije deploy-a.
