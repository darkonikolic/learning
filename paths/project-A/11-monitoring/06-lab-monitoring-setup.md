# 06 — LAB: Monitoring stack setup

## Cilj

Instalirati kompletan monitoring stack na kind clusteru, pristupiti Grafani,
importovati nginx dashboard, dodati alert pravilo i pregledati logove kroz Loki.

---

## Preduslovi

- kind cluster radi (`kubectl get nodes` vraća Ready node)
- Helm instaliran (ili u Docker aliasu — vidi `04-helm` modul)
- helloworld deployment je deployovan u `helloworld-dev` namespace

Provjera:
```bash
kubectl get pods -n helloworld-dev
# Treba prikazati: helloworld-XXX   Running
```

---

## Korak 1: Dodaj Prometheus Community Helm repo

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update
```

---

## Korak 2: Kreiraj monitoring-values.yaml

```yaml
# monitoring-values.yaml
grafana:
  adminPassword: "admin123"  # promijeni za produkciju!
  persistence:
    enabled: false  # lokalno, nema PVC
  sidecar:
    dashboards:
      enabled: true

prometheus:
  prometheusSpec:
    retention: 7d
    serviceMonitorSelectorNilUsesHelmValues: false  # scrape sve ServiceMonitor-e
    podMonitorSelectorNilUsesHelmValues: false

alertmanager:
  alertmanagerSpec:
    storage: {}  # lokalno, bez PVC
  config:
    route:
      receiver: 'null'
    receivers:
      - name: 'null'

# Manji resource requests za kind
kubeStateMetrics:
  enabled: true

nodeExporter:
  enabled: true
```

---

## Korak 3: Instaliraj kube-prometheus-stack

```bash
helm upgrade --install monitoring \
  prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  -f monitoring-values.yaml \
  --wait \
  --timeout 5m
```

Provjera instalacije:

```bash
kubectl get pods -n monitoring
# Trebaju biti Running:
# monitoring-grafana-XXX
# monitoring-kube-prometheus-prometheus-XXX
# monitoring-kube-prometheus-alertmanager-XXX
# monitoring-kube-state-metrics-XXX
# monitoring-prometheus-node-exporter-XXX (jedan po node-u)
```

---

## Korak 4: Pristup Grafani lokalno

```bash
kubectl port-forward -n monitoring svc/monitoring-grafana 3000:80 &
```

Otvori: `http://localhost:3000`
- Username: `admin`
- Password: `admin123` (iz values.yaml)

---

## Korak 5: Importuj nginx dashboard

Grafana UI → Dashboards → New → Import

1. U polje "Import via grafana.com" upiši ID: `12708`
2. Klikni Load
3. U dropdown "Prometheus" izaberi `Prometheus` data source
4. Klikni Import

Grafana otvara nginx dashboard. Ako nemaš `nginx-prometheus-exporter`, većina panela
će biti prazna — to je OK za sada.

---

## Korak 6: Dodaj nginx-prometheus-exporter u helloworld Deployment

Dodaj sidecar u Helm chart values za dev:

```yaml
# helm/helloworld/values/dev.yaml (dodaj na kraj)
metricsExporter:
  enabled: true
  image: nginx/nginx-prometheus-exporter:1.1
```

Dopuni `deployment.yaml` template:

```yaml
{{- if .Values.metricsExporter.enabled }}
- name: metrics
  image: {{ .Values.metricsExporter.image }}
  args:
    - -nginx.scrape-uri=http://localhost/nginx_status
  ports:
    - name: metrics
      containerPort: 9113
{{- end }}
```

I u `service.yaml` dodaj port:

```yaml
{{- if .Values.metricsExporter.enabled }}
- name: metrics
  port: 9113
  targetPort: 9113
{{- end }}
```

Redeploy:
```bash
helm upgrade helloworld ./helm/helloworld \
  --namespace helloworld-dev \
  -f helm/helloworld/values/dev.yaml
```

---

## Korak 7: Kreiraj ServiceMonitor

```yaml
# serviceMonitor.yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: helloworld-monitor
  namespace: monitoring
  labels:
    release: monitoring
spec:
  namespaceSelector:
    matchNames:
      - helloworld-dev
  selector:
    matchLabels:
      app: helloworld
  endpoints:
    - port: metrics
      interval: 30s
```

```bash
kubectl apply -f serviceMonitor.yaml
```

Provjeri da Prometheus vidi target:
```bash
kubectl port-forward -n monitoring svc/monitoring-kube-prometheus-prometheus 9090:9090 &
# Otvori: http://localhost:9090/targets
# Trebaš vidjeti helloworld target kao UP
```

---

## Korak 8: Instaliraj Loki stack

```bash
helm upgrade --install loki grafana/loki-stack \
  --namespace monitoring \
  --set promtail.enabled=true \
  --set loki.persistence.enabled=false \
  --wait
```

Dodaj Loki data source u Grafanu:

Grafana UI → Connections → Data Sources → Add data source → Loki

- URL: `http://loki:3100`
- Klikni "Save & Test" — treba prikazati "Data source connected"

---

## Korak 9: Provjeri logove u Grafana Explore

Grafana UI → Explore → izaberi "Loki" u dropdown-u

Upiši query:
```logql
{namespace="helloworld-dev"}
```

Trebaš vidjeti nginx access logove. Ako su prazni:

```bash
# Generiši nešto prometa:
kubectl port-forward -n helloworld-dev svc/helloworld 8080:80 &
curl http://localhost:8080/
curl http://localhost:8080/
curl http://localhost:8080/zdravo  # 404
```

Ponovi query u Grafana Explore — trebaš vidjeti log linije.

---

## Korak 10: Dodaj alert pravilo

```yaml
# alert-rules.yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: helloworld-alerts
  namespace: monitoring
  labels:
    release: monitoring
spec:
  groups:
    - name: helloworld
      rules:
        - alert: HelloworldDown
          expr: up{job=~".*helloworld.*"} == 0
          for: 1m
          labels:
            severity: critical
          annotations:
            summary: "Helloworld metrics endpoint je down"
```

```bash
kubectl apply -f alert-rules.yaml

# Provjeri da Prometheus vidio pravilo:
# http://localhost:9090/alerts
# Trebas vidjeti HelloworldDown u Inactive stanju (jer je helloworld UP)
```

---

## Finalna provjera

```bash
# Svi monitoring podovi rade
kubectl get pods -n monitoring

# Prometheus scrape-uje helloworld
# http://localhost:9090/targets  → helloworld job = UP

# Grafana prikazuje nginx dashboard
# http://localhost:3000/d/nginx

# Loki prikazuje logove
# Grafana Explore → {namespace="helloworld-dev"}
```

---

## AI workflow

Grafana query za P95 latency — traži Claude da napiše PromQL:

> "Imam nginx-prometheus-exporter koji eksponuje `nginx_http_requests_total`
> s labelama `status` i `method`. Napiši PromQL query koji pokazuje P95 latency
> po HTTP statusu za zadnjih 5 minuta. Objasni što svaki dio querya radi."

Ili za Loki:

> "Moji nginx logovi su u formatu: `<IP> - - [timestamp] \"METHOD /path HTTP/1.1\" STATUS bytes`
> Napiši LogQL query koji:
> 1. Filtrira samo 4xx greške
> 2. Broji ih po minuti
> 3. Prikazuje koje putanje su najčešće 404"

---

## Makefile — dodaj u ovom poglavlju

Ovo poglavlje uvodi Prometheus i Grafana stack. Dodaj u `Makefile` u korenu projekta:

```makefile
# === OBLAST 11: Monitoring ===

monitoring-install: ## Instaliraj Prometheus + Grafana stack (kube-prometheus-stack)
	docker run --rm \
	  -v ~/.kube:/root/.kube \
	  alpine/helm:$(HELM_VERSION) install kube-prometheus-stack \
	  prometheus-community/kube-prometheus-stack -n monitoring --create-namespace

monitoring-grafana: ## Port-forward Grafana na localhost:3000
	docker run --rm \
	  -v ~/.kube:/root/.kube \
	  -p 3000:3000 \
	  bitnami/kubectl:$(KUBECTL_VERSION) port-forward \
	  -n monitoring svc/kube-prometheus-stack-grafana 3000:80

monitoring-prometheus: ## Port-forward Prometheus na localhost:9090
	docker run --rm \
	  -v ~/.kube:/root/.kube \
	  -p 9090:9090 \
	  bitnami/kubectl:$(KUBECTL_VERSION) port-forward \
	  -n monitoring svc/kube-prometheus-stack-prometheus 9090:9090
```

Centralni Makefile već sadrži ove targete — ovo je referenca šta si dodao u ovoj oblasti.

Provjeri da targeti rade:
```bash
make monitoring-install
make monitoring-grafana   # otvori http://localhost:3000
make help | grep monitoring
```
