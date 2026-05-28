# 04 — Alertmanager

## Teorija

Alertmanager je komponenta koja prima alarme od Prometheusa i odlučuje:
**kome, kada i kako slati notifikacije**. Prometheus zna *šta* je alarm,
Alertmanager zna *što s njim*.

---

## Zašto poseban Alertmanager, a ne direktno iz Prometheusa

Prometheus može samo evaluirati alarm i reći "ovo je active". Ali:

- Isti alarm može se okidati svake sekunde — korisnik ne želi 1000 Slack poruka
- Isti alarm dolazi od 3 instance iste aplikacije — treba 1 notifikacija, ne 3
- Warning alarmi idu na Slack, critical alarmi idu na PagerDuty
- Tokom maintenance-a, alarme treba privremeno tiho staviti

Alertmanager rješava sve: **deduplication, grouping, routing, silencing**.

---

## Flow: Prometheus → Alertmanager → receiver

```
PrometheusRule (K8s CRD)
    ↓ alarm evaluacija svake minute
Prometheus (active alerts)
    ↓ šalje active alarms putem HTTP-a
Alertmanager
    ↓ deduplication (isti alarm od 3 instance = 1 poruka)
    ↓ grouping (više alarma zajedno u 1 poruku)
    ↓ routing (na osnovu labela → pravi receiver)
    ↓
Slack receiver          PagerDuty receiver      Email receiver
```

---

## Alert pravila: PrometheusRule CRD

Alert pravila definišemo kao K8s objekte, ne u Prometheus konfiguraciji:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: helloworld-alerts
  namespace: monitoring
  labels:
    release: monitoring  # mora matchati Prometheus Operator selector
spec:
  groups:
    - name: helloworld.availability
      interval: 1m
      rules:

        - alert: HelloworldPodCrashLooping
          expr: rate(kube_pod_container_status_restarts_total{namespace=~"helloworld.*"}[5m]) > 0
          for: 5m
          labels:
            severity: critical
            team: backend
          annotations:
            summary: "Pod crash loop: {{ $labels.pod }}"
            description: "Pod {{ $labels.pod }} u namespace {{ $labels.namespace }} restartuje se."
            runbook_url: "https://wiki.firma.com/runbooks/pod-crash-loop"

        - alert: HelloworldHighErrorRate
          expr: |
            sum(rate(nginx_http_requests_total{status=~"5..", namespace=~"helloworld.*"}[5m]))
            /
            sum(rate(nginx_http_requests_total{namespace=~"helloworld.*"}[5m]))
            > 0.05
          for: 5m
          labels:
            severity: warning
          annotations:
            summary: "Visok error rate na helloworld"
            description: "Error rate je {{ $value | humanizePercentage }}"

        - alert: HelloworldNoTraffic
          expr: sum(rate(nginx_http_requests_total{namespace="helloworld-prod"}[5m])) < 0.1
          for: 10m
          labels:
            severity: critical
          annotations:
            summary: "Helloworld prod ne prima zahtjeve"

        - alert: CertificateExpiringSoon
          expr: |
            probe_ssl_earliest_cert_expiry{instance="https://app.firma.com"}
            - time() < 86400 * 14
          for: 1h
          labels:
            severity: warning
          annotations:
            summary: "SSL certifikat ističe za manje od 14 dana"
```

`for: 5m` — alarm mora biti aktivan neprekidno 5 minuta prije slanja notifikacije.
Eliminira lažne alarme od kratkih spike-ova.

---

## Alertmanager routing konfiguracija

```yaml
# U kube-prometheus-stack values.yaml
alertmanager:
  config:
    global:
      resolve_timeout: 5m
      slack_api_url: $SLACK_WEBHOOK_URL

    route:
      receiver: slack-default
      group_by: [alertname, namespace]
      group_wait: 30s       # čekaj 30s da grupiraš slične alarme
      group_interval: 5m    # između novog grupiranja
      repeat_interval: 4h   # ponovi alarm ako je još uvijek aktivan

      routes:
        - match:
            severity: critical
          receiver: pagerduty-critical
          continue: true  # i dalje pošalji na default receiver

        - match:
            severity: warning
          receiver: slack-warnings

        - match:
            alertname: CertificateExpiringSoon
          receiver: slack-infra

    receivers:
      - name: slack-default
        slack_configs:
          - channel: '#alerts'
            send_resolved: true
            title: '{{ .GroupLabels.alertname }}'
            text: |
              {{ range .Alerts }}
              *{{ .Annotations.summary }}*
              {{ .Annotations.description }}
              {{ end }}

      - name: slack-warnings
        slack_configs:
          - channel: '#alerts-warning'
            send_resolved: true

      - name: pagerduty-critical
        pagerduty_configs:
          - service_key: $PAGERDUTY_SERVICE_KEY
            severity: critical

      - name: slack-infra
        slack_configs:
          - channel: '#infra'
```

---

## Silencing: privremeni alarm mute

Tokom planned maintenance-a (npr. K8s upgrade), alarmi bi se okidali bespotrebno.
Silencing privremeno isključuje specifične alarme:

```bash
# Kroz Alertmanager UI (port-forward na 9093):
kubectl port-forward -n monitoring svc/monitoring-alertmanager 9093:9093

# Ili kroz amtool CLI:
amtool silence add \
  --alertmanager.url=http://localhost:9093 \
  alertname="HelloworldPodCrashLooping" \
  --duration=2h \
  --comment="K8s upgrade in progress"
```

Grafana Alertmanager UI prikazuje sve aktivne silence-e i historiju.

---

## Veza sa project-A

Za project-A, minimalni set alarma:

| Alarm | Threshold | Severity | Receiver |
|-------|-----------|----------|---------|
| Pod crash loop | > 0 restarts/5min | critical | Slack |
| High error rate | > 5% HTTP 5xx | warning | Slack |
| No traffic (prod) | < 0.1 req/s za 10 min | critical | Slack |
| SSL cert expiry | < 14 dana | warning | Slack |
| Node memory pressure | > 90% | warning | Slack |

Ovi alarmi pokrivaju sve realne scenarije koji mogu zadesiti nginx koji servira
jednu HTML stranicu na K8s. Svaki alarm ima jasnu `for:` duraciju da eliminira
lažne okidače.
