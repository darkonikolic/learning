# 03 — Grafana dashboardi

## Teorija

Grafana je vizualizacijski alat koji **čita podatke iz Prometheusa i Lokija** i
prikazuje ih u formi grafova, tabela i alarma. To je jedini UI koji inženjer
treba otvoriti da razumije stanje sistema — metrics i logs na jednom mjestu.

---

## Zašto Grafana, ne direktno Prometheus

Prometheus UI ima query interface koji je dobar za istraživanje, ali:
- Nema dashboarde koji se pamte
- Nema kombinovanje metrics i logs pogleda
- Nema role-based access (dev vs manager pogled)
- Nema alerting iz UI

Grafana rješava sve ovo i integriše se s desecima data sourcea —
Prometheus, Loki, CloudWatch, Elasticsearch, PostgreSQL...

---

## Ugrađeni dashboardi u kube-prometheus-stack

kube-prometheus-stack instalira ~30 unaprijed konfiguriranih dashboarda.
Najkorisnije za project-A:

| Dashboard | Šta prikazuje |
|-----------|--------------|
| Kubernetes / Compute Resources / Cluster | CPU i memorija za cijeli cluster |
| Kubernetes / Compute Resources / Namespace | CPU i memorija per namespace |
| Kubernetes / Compute Resources / Pod | Detalji za jedan Pod |
| Kubernetes / Networking / Namespace | Network traffic per namespace |
| Node Exporter / Nodes | Hardware metrike po node-u |
| Kubernetes / Persistent Volumes | PVC usage i health |

Ove dashboarde dobijaš besplatno — nisi ih napisao, ali koriste tačno iste
metrike koje Prometheus scrape-uje.

---

## Korisni dashboardi za project-A s Grafana.com

Grafana.com ima biblioteku community dashboarda. Import po ID:

```
Grafana UI → Dashboards → Import → ID
```

| Dashboard | ID | Primjena |
|-----------|-----|---------|
| Nginx (nginx-prometheus-exporter) | 12708 | nginx metrike za helloworld |
| Kubernetes Deployments | 8588 | deployment status overview |
| Node Exporter Full | 1860 | detaljan hardware pregled |
| Loki Dashboard | 12611 | logs pregled |

---

## Kreiranje custom dashboard za project-A

### Panel 1: HTTP Request Rate

```
Query: sum(rate(nginx_http_requests_total{namespace=~"helloworld.*"}[5m]))
Visualization: Time series
Title: Request Rate (req/s)
Unit: requests/sec
```

### Panel 2: HTTP Error Rate (4xx + 5xx)

```
Query: sum(rate(nginx_http_requests_total{status=~"[45].."}[5m]))
       /
       sum(rate(nginx_http_requests_total[5m]))
       * 100
Visualization: Stat
Title: Error Rate
Unit: percent (0-100)
Thresholds: green < 1%, yellow 1-5%, red > 5%
```

### Panel 3: Pod Restart Count

```
Query: sum(kube_pod_container_status_restarts_total{namespace=~"helloworld.*"})
Visualization: Stat
Title: Total Pod Restarts
Thresholds: green = 0, yellow > 0, red > 5
```

### Panel 4: Memory Usage

```
Query: sum(container_memory_usage_bytes{namespace=~"helloworld.*", container!=""})
Visualization: Time series
Title: Memory Usage
Unit: bytes (auto)
```

---

## Alerting pravila u Grafana

Grafana može direktno kreirati alarme na osnovu dashboard panela.

Grafana UI → Alerting → Alert rules → New alert rule

```yaml
# Primjer: alarm ako nema request-a 5 minuta (aplikacija nije dostupna)
Name: Helloworld No Traffic
Query: sum(rate(nginx_http_requests_total{namespace="helloworld-prod"}[5m]))
Condition: IS BELOW 0.1
For: 5m
Annotations:
  summary: "Helloworld prod ne prima HTTP zahtjeve"
  description: "Request rate je {{ $value }} req/s — aplikacija možda nije dostupna"
Labels:
  severity: critical
  environment: prod
```

Za detalji o alarm routingu → vidi `04-alertmanager.md`.

---

## Pristup Grafani: lokalno i na cloud-u

### Lokalno (kind cluster)

```bash
kubectl port-forward -n monitoring svc/monitoring-grafana 3000:80
# Otvori: http://localhost:3000
# Default: admin / prom-operator
```

### Cloud (EKS): Ingress + HTTPS

```yaml
# U kube-prometheus-stack values.yaml
grafana:
  ingress:
    enabled: true
    ingressClassName: alb
    annotations:
      kubernetes.io/ingress.class: alb
      alb.ingress.kubernetes.io/scheme: internal  # internal, ne public
      alb.ingress.kubernetes.io/certificate-arn: $ACM_CERT_ARN
    hosts:
      - grafana.monitoring.firma.com
    tls:
      - hosts:
          - grafana.monitoring.firma.com
```

Grafana na produkciji treba biti internal (ne public internet) ili zaštićen
OAuth/SSO autentifikacijom.

---

## Organizacija dashboarda: folders

Grafana podržava foldere za organizaciju:

```
📁 Project-A
   📊 Overview (cluster + deployments)
   📊 Application (nginx metrics)
   📊 Infrastructure (node exporter)

📁 Alerts
   📊 Active Alerts
   📊 Alert History

📁 Logs
   📊 Application Logs (Loki)
```

---

## Veza sa project-A

Nakon instalacije kube-prometheus-stack, odmah radiš:

1. Otvori port-forward na 3000
2. Import Nginx dashboard (ID: 12708)
3. Import Kubernetes Deployments (ID: 8588)
4. Kreiraj custom panel za error rate helloworld aplikacije
5. Postavi threshold alarm na error rate > 5%

Za 30 minuta imaš dashboarde koji prikazuju sve relevantne metrike
za nginx serving `index.html` na K8s clusteru.
