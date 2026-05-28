# Monitoring Setup

## Šta instaliraš

Na svakom EKS clusteru (dev i prod) postavljaš kompletan monitoring stack:

- **Prometheus** — skuplja metrike sa svih podova i nodova
- **Grafana** — vizualizacija metrika, dashboardi
- **AlertManager** — slanje alarma (Slack, email)
- **Loki** — agregacija logova
- **Promtail** — agent koji šalje logove u Loki
- **nginx-prometheus-exporter** — metrike specifično za helloworld app

Sve se instalira via Helm — konzistentno sa ostatkom projekta.

## Korak 1: Helm repo dodavanje

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update
```

## Korak 2: monitoring-values.yaml za AWS

```yaml
# monitoring-values.yaml
grafana:
  adminPassword: "$(GRAFANA_ADMIN_PASSWORD)"  # iz CI/CD variable
  ingress:
    enabled: true
    ingressClassName: alb
    annotations:
      alb.ingress.kubernetes.io/scheme: internet-facing
      alb.ingress.kubernetes.io/target-type: ip
      alb.ingress.kubernetes.io/certificate-arn: "ACM_CERT_ARN"
      alb.ingress.kubernetes.io/ssl-redirect: "443"
    hosts:
      - monitoring.dev.firma.com
    tls:
      - hosts:
          - monitoring.dev.firma.com
  persistence:
    enabled: true
    storageClassName: gp3
    size: 10Gi
  grafana.ini:
    server:
      root_url: https://monitoring.dev.firma.com

prometheus:
  prometheusSpec:
    retention: 7d
    storageSpec:
      volumeClaimTemplate:
        spec:
          storageClassName: gp3
          accessModes: ["ReadWriteOnce"]
          resources:
            requests:
              storage: 20Gi

alertmanager:
  alertmanagerSpec:
    storage:
      volumeClaimTemplate:
        spec:
          storageClassName: gp3
          resources:
            requests:
              storage: 5Gi
  config:
    receivers:
      - name: slack
        slack_configs:
          - api_url: "$(SLACK_WEBHOOK_URL)"
            channel: "#alerts-dev"
            title: "{{ .GroupLabels.alertname }}"
            text: "{{ range .Alerts }}{{ .Annotations.description }}{{ end }}"
    route:
      receiver: slack
      group_by: ['alertname', 'namespace']
      group_wait: 30s
      group_interval: 5m
      repeat_interval: 4h

# StorageClass gp3 je noviji i jeftiniji od gp2 na AWS
```

## Korak 3: Instalacija

```bash
helm upgrade --install monitoring \
  prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  -f monitoring-values.yaml \
  --version 58.0.0 \
  --wait --timeout 10m
```

Pinaj verziju (`--version 58.0.0`) — prometheus-community chart se često
ažurira i može doći do breaking changes između verzija.

## Korak 4: Loki + Promtail

```bash
# Loki (storage logs agregator)
helm upgrade --install loki grafana/loki \
  --namespace monitoring \
  -f loki-values.yaml \
  --wait

# Promtail (agent na svakom nodu koji šalje logove)
helm upgrade --install promtail grafana/promtail \
  --namespace monitoring \
  --set "config.clients[0].url=http://loki:3100/loki/api/v1/push" \
  --wait
```

```yaml
# loki-values.yaml (single-binary za dev, distribuiran za prod)
loki:
  commonConfig:
    replication_factor: 1
  storage:
    type: s3
    s3:
      region: eu-west-1
      bucketNames:
        chunks: project-a-loki-dev
        ruler: project-a-loki-ruler-dev
  schemaConfig:
    configs:
      - from: "2024-01-01"
        store: tsdb
        object_store: s3
        schema: v13
```

Loki na S3 je jeftiniji od EBS — logovi se ne trebaju brzo čitati kao metrike.

## Korak 5: nginx exporter za helloworld

Nginx ne eksportuje Prometheus metrike nativno. Dodaj exporter kao sidecar:

```yaml
# Dodaj u Helm chart values/dev.yaml
nginx:
  statusPort: 8080  # nginx stub_status

nginxExporter:
  enabled: true
  image: nginx/nginx-prometheus-exporter:1.1.0
  port: 9113
```

```nginx
# Dodaj u app/nginx.conf
location /nginx_status {
    stub_status;
    allow 127.0.0.1;
    deny all;
}
```

Sidecar pattern: `nginx-prometheus-exporter` kontejner čita nginx status na
`localhost:8080/nginx_status` i eksportuje Prometheus metrike na `9113/metrics`.

## Korak 6: Grafana Dashboard Import

U Grafana UI (Settings → Dashboards → Import):

| Dashboard | ID | Šta prikazuje |
|-----------|----|--------------|
| Nginx | 12708 | Requests/sec, latency, error rate |
| K8s Cluster | 315 | Node CPU/memory, pod count |
| Loki Logs | 13639 | Log stream iz svih namespaceova |

## Korak 7: PrometheusRule za alarme

```yaml
# helm/helloworld/templates/prometheusrule.yaml
{{- if .Values.monitoring.enabled }}
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: {{ include "helloworld.name" . }}
  labels:
    {{- include "helloworld.labels" . | nindent 4 }}
    release: monitoring  # Mora matchovati kube-prometheus-stack release name
spec:
  groups:
    - name: helloworld
      rules:
        - alert: HelloWorldHighErrorRate
          expr: |
            rate(nginx_http_requests_total{status=~"5.."}[5m])
            / rate(nginx_http_requests_total[5m]) > 0.1
          for: 5m
          labels:
            severity: critical
          annotations:
            summary: "High error rate na helloworld"
            description: "Error rate je {{ $value | humanizePercentage }} u posljednjih 5 minuta"

        - alert: HelloWorldPodCrashing
          expr: |
            kube_pod_container_status_restarts_total{
              namespace="{{ .Release.Namespace }}",
              container="nginx"
            } > 3
          for: 1m
          labels:
            severity: warning
          annotations:
            description: "Pod {{ $labels.pod }} se restartovao više od 3 puta"
{{- end }}
```

## Provjera

```bash
# Provjeri da monitoring stack radi
kubectl get pods -n monitoring
# Svi podovi trebaju biti Running

# Port-forward za lokalni pristup (bez Ingress)
kubectl port-forward svc/monitoring-grafana 3000:80 -n monitoring &

# Otvori http://localhost:3000 — admin / <GRAFANA_ADMIN_PASSWORD>

# U Grafana: Explore → Loki → query: {namespace="helloworld-dev"}
# Treba prikazivati nginx access logove

# Provjeri alertmanager
kubectl port-forward svc/monitoring-kube-prometheus-alertmanager 9093:9093 -n monitoring &
# http://localhost:9093 — status alertova
```

## AI prompt za monitoring debugging

```
Prometheus ne skuplja metrike sa mog nginx poda. Pod postoji i radi.
Evo kubectl describe pod outputa:
[prijepi]

ServiceMonitor koji imam:
[prijepi]

Evo Prometheus Targets stranice (screenshot ili tekst):
[prijepi]

Šta nije u redu? ServiceMonitor labels moraju matchovati?
```

Najčešći problem: `release: monitoring` label na ServiceMonitor/PrometheusRule
mora matchovati Helm release name kube-prometheus-stacka. Ako si ga instalirao
kao `monitoring` (što piše gore) — radi. Ako si ga instalirao kao
`prometheus` — sve labele trebaju biti `release: prometheus`.
