# 02 — Prometheus i metrics

## Teorija

Prometheus je open-source monitoring sistem koji **sam dolazi po metrike** (pull model).
Svaka aplikacija ekspozuje HTTP endpoint `/metrics` sa trenutnim vrijednostima.
Prometheus periodično (default: 15s) scrape-uje taj endpoint i čuva podatke.

---

## Zašto pull model, ne push

**Push model** (aplikacija šalje metrike): aplikacija mora znati adresu monitoring sistema.
Ako monitoring sistem padne, aplikacija može akumulirati metrike ili ih izgubiti.
Konfiguracija je raspršena po svim aplikacijama.

**Pull model** (Prometheus dolazi do aplikacije): Prometheus centralno zna šta scrape-uje.
Aplikacija ne zna ništa o monitoring sistemu. Ako Prometheus padne, aplikacija radi dalje.
Lako se dodaju novi targeti — bez promjene aplikacije.

---

## Šta Prometheus scrape-uje

### kube-state-metrics

Eksponuje metrike o K8s objektima — Deployment, Pod, Node, PVC...

```
kube_deployment_status_replicas_available{deployment="helloworld"} 3
kube_deployment_status_replicas_unavailable{deployment="helloworld"} 0
kube_pod_status_phase{pod="helloworld-6d4b9c-xk2p1", phase="Running"} 1
kube_pod_container_status_restarts_total{container="nginx"} 0
```

### node-exporter

Eksponuje metrike hardwarea i OS-a na svakom K8s node-u:

```
node_cpu_seconds_total{cpu="0", mode="idle"} 12345.67
node_memory_MemAvailable_bytes 4294967296
node_disk_io_time_seconds_total{device="sda"} 123.45
node_network_receive_bytes_total{device="eth0"} 987654321
```

### Aplikacijske metrike: nginx-prometheus-exporter

Nginx sam po sebi ne eksponuje Prometheus metrike. `nginx-prometheus-exporter`
čita nginx status stranicu i pretvara u Prometheus format:

```
nginx_connections_active 5
nginx_connections_reading 0
nginx_http_requests_total 1234
nginx_up 1
```

Ili sa OpenTelemetry-enabled nginx-om direktno:

```
# HELP nginx_http_requests_total Total HTTP requests
# TYPE nginx_http_requests_total counter
nginx_http_requests_total{method="GET", status="200"} 9876
nginx_http_requests_total{method="GET", status="404"} 12
```

---

## PromQL: query jezik za metrics

PromQL (Prometheus Query Language) je funkcionalni jezik za analizu metrika.

### Instant vector: trenutna vrijednost

```promql
# Memorija u bajtovima po containeru u helloworld namespaceu
container_memory_usage_bytes{namespace="helloworld-dev"}
```

### Rate: promjena u vremenu

```promql
# HTTP requests po sekundi (prosječno za zadnjih 5 minuta)
rate(nginx_http_requests_total[5m])
```

`rate()` pretvara counter (uvijek raste) u "koliko puta po sekundi raste".

### Agregacija

```promql
# Ukupni RPS za sve nginx instance
sum(rate(nginx_http_requests_total[5m]))

# RPS po HTTP status kodu
sum by (status) (rate(nginx_http_requests_total[5m]))
```

### Zdravlje deployova

```promql
# Unhealthy podovi u deployment-ima (želimo 0)
kube_deployment_status_replicas_unavailable > 0

# Pod restart rate > 0 znači CrashLoop
rate(kube_pod_container_status_restarts_total[5m]) > 0
```

### Memory pressure

```promql
# Procenat korištene memorije po containeru
container_memory_usage_bytes / container_spec_memory_limit_bytes * 100
```

---

## ServiceMonitor: kako Prometheus "otkrije" novu aplikaciju

Klasično: u Prometheus konfiguraciji manualno dodaješ target.
Problem: dinamičan K8s — servisi dolaze i odlaze.

**ServiceMonitor** je Kubernetes CRD koji govori Prometheus Operatoru:
"scrape-uj sve servise koji matchaju ovaj label selector".

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: helloworld-monitor
  namespace: monitoring
  labels:
    release: monitoring  # mora matchati Prometheus Operator selector
spec:
  namespaceSelector:
    matchNames:
      - helloworld-dev
      - helloworld-staging
      - helloworld-prod
  selector:
    matchLabels:
      app: helloworld     # Service mora imati ovaj label
  endpoints:
    - port: metrics       # Port name u Service definiciji
      interval: 30s
      path: /metrics
```

Prometheus Operator prati ServiceMonitor objekte i automatski ažurira
Prometheus konfiguraciju — bez restarta, bez manuelnih izmjena.

---

## Retention i storage: Prometheus PVC na EBS

Prometheus po defaultu čuva metrike 15 dana u memoriji/lokalnom disku.
Za K8s deployment, treba PersistentVolumeClaim:

```yaml
# U kube-prometheus-stack values.yaml
prometheus:
  prometheusSpec:
    retention: 30d
    storageSpec:
      volumeClaimTemplate:
        spec:
          storageClassName: gp3  # AWS EBS gp3
          accessModes: [ReadWriteOnce]
          resources:
            requests:
              storage: 50Gi
```

Careless Prometheus bez PVC = sve metrike izgubljene pri restartu Poda.
Sa PVC = metrike opstaju restart, čak i node rebalance.

---

## Veza sa project-A

Za project-A nginx deployment, dodajemo `nginx-prometheus-exporter` kao sidecar kontejner:

```yaml
# U Helm chart template-u (deployment.yaml)
containers:
  - name: nginx
    image: nginx:alpine
  - name: metrics
    image: nginx/nginx-prometheus-exporter:1.1
    args:
      - -nginx.scrape-uri=http://localhost/nginx_status
    ports:
      - name: metrics
        containerPort: 9113
```

ServiceMonitor automatski pronalazi Service s `app: helloworld` labelom
u svim helloworld namespacevima i Prometheus počinje scrape-ovati `/metrics`
na portu `9113` svakih 30 sekundi.
