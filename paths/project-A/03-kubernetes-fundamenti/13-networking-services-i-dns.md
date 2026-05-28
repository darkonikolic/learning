# 13 — Networking, Services i DNS

Kompletni K8s networking za project-A: Service tipovi, DNS rezolucija, NetworkPolicy, Ingress routing i praktični inter-service communication primjeri.

---

## Service tipovi — pregled i kada što koristiti

```
ClusterIP   ← interni servisi (php-service, go-service, mysql, redis)
NodePort    ← direktni pristup bez Ingress (lokalni dev, debugging)
LoadBalancer ← cloud load balancer (samo za Ingress controller)
Headless    ← StatefulSet (MySQL, Redis) — direktni pod DNS
ExternalName ← proxy prema vanjskom servisu (RDS, ElastiCache)
```

---

## ClusterIP — standardni interni servis

```yaml
apiVersion: v1
kind: Service
metadata:
  name: go-service
  namespace: project-a-prod
  labels:
    app: go-service
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "9090"
    prometheus.io/path: "/metrics"
spec:
  selector:
    app: go-service         # šalje traffic na pode s ovim labelom
  ports:
    - name: http            # imenuj port — Istio i Prometheus koriste ovo
      port: 8080            # port na koji se spaja klijent
      targetPort: 8080      # port na podu (može biti ime: targetPort: http)
      protocol: TCP
    - name: metrics
      port: 9090
      targetPort: 9090
  type: ClusterIP           # default — ne treba eksplicitno
```

### Headless Service za StatefulSet

```yaml
apiVersion: v1
kind: Service
metadata:
  name: mysql
  namespace: project-a-prod
spec:
  clusterIP: None    # ← headless — bez virtual IP
  selector:
    app: mysql
  ports:
    - name: mysql
      port: 3306
      targetPort: 3306
```

**Razlika headless vs ClusterIP:**
- ClusterIP: DNS vraća jedan IP (virtual IP load balancera), konekcije se rutiraju na podove
- Headless (clusterIP: None): DNS vraća direktne IP-ove podova, nema load balancinga

Za MySQL StatefulSet koristimo headless jer trebamo stable DNS za svaki pod:
```
mysql-0.mysql.project-a-prod.svc.cluster.local  → 10.0.1.45 (master)
mysql-1.mysql.project-a-prod.svc.cluster.local  → 10.0.2.67 (replica)
```

---

## DNS u K8s — kompletna referenca

### Format DNS naziva

```
<service-name>.<namespace>.svc.<cluster-domain>

# U project-a-prod namespace-u:
go-service.project-a-prod.svc.cluster.local    # puni FQDN
go-service.project-a-prod.svc                  # kraći
go-service.project-a-prod                      # cross-namespace short form
go-service                                     # samo iz istog namespace-a
```

### Search domains — zašto kratki nazivi rade

```bash
# Unutar poda, /etc/resolv.conf izgleda ovako:
nameserver 10.96.0.10        # CoreDNS ClusterIP
search project-a-prod.svc.cluster.local svc.cluster.local cluster.local
options ndots:5
```

Kada Go servis pozove `mysql:3306`, resolver pokušava:
1. `mysql.project-a-prod.svc.cluster.local` → ✓ nađe

Kada PHP servis iz `project-a-prod` pozove `go-service`, resolver pokušava:
1. `go-service.project-a-prod.svc.cluster.local` → ✓

Za cross-namespace: PHP u `project-a-prod` koji poziva servis u `monitoring` namespace-u:
```php
// Mora se koristiti puni namespace:
$prometheusUrl = 'http://prometheus.monitoring:9090';
// ili FQDN:
$prometheusUrl = 'http://prometheus.monitoring.svc.cluster.local:9090';
```

### StatefulSet pod DNS

```
<pod-name>.<headless-service-name>.<namespace>.svc.cluster.local

mysql-0.mysql.project-a-prod.svc.cluster.local
mysql-1.mysql.project-a-prod.svc.cluster.local
redis-0.redis.project-a-prod.svc.cluster.local
```

Ovo je stable DNS — isti nakon restarta poda. Fundamentalna razlika od Deployment pod-ova čiji DNS nazivi se mijenjaju s hash sufiksom.

---

## Inter-service komunikacija u project-A

### PHP servis poziva Go servis

```php
<?php
// Iz PHP servisa (projekt-a-prod namespace):
class AuthService
{
    private string $goServiceUrl;
    
    public function __construct()
    {
        // K8s DNS automatski resolva na ClusterIP go-service servisa
        $this->goServiceUrl = getenv('GO_SERVICE_URL') ?: 'http://go-service:8080';
    }
    
    public function validateToken(string $token): array
    {
        $response = $this->httpClient->post(
            $this->goServiceUrl . '/api/auth/validate',
            ['Authorization' => 'Bearer ' . $token]
        );
        return $response->json();
    }
}
```

```yaml
# ConfigMap za PHP servis
data:
  GO_SERVICE_URL: "http://go-service:8080"
  REDIS_URL: "redis://redis:6379"
  # Ne koristiti FQDN — kratki nazivi su dovoljni unutar namespace-a
```

### Go servis poziva MySQL (master/replica pattern)

```go
package database

import (
    "database/sql"
    "fmt"
    "os"
)

func NewConnections() (*sql.DB, *sql.DB, error) {
    // Master za write operacije
    masterDSN := fmt.Sprintf("%s:%s@tcp(%s:%s)/%s?parseTime=true&charset=utf8mb4",
        os.Getenv("DB_USER"),
        os.Getenv("DB_PASSWORD"),
        "mysql-0.mysql.project-a-prod.svc.cluster.local",  // stable DNS master poda
        "3306",
        os.Getenv("DB_NAME"),
    )
    
    // Replica za read operacije  
    replicaDSN := fmt.Sprintf("%s:%s@tcp(%s:%s)/%s?parseTime=true&charset=utf8mb4",
        os.Getenv("DB_USER"),
        os.Getenv("DB_READONLY_PASSWORD"),
        "mysql-1.mysql.project-a-prod.svc.cluster.local",  // stable DNS replica poda
        "3306",
        os.Getenv("DB_NAME"),
    )
    
    master, err := sql.Open("mysql", masterDSN)
    if err != nil {
        return nil, nil, fmt.Errorf("master connection: %w", err)
    }
    
    replica, err := sql.Open("mysql", replicaDSN)
    if err != nil {
        master.Close()
        return nil, nil, fmt.Errorf("replica connection: %w", err)
    }
    
    return master, replica, nil
}
```

**Alternativa s jednim Service-om koji load-balancira po replikama** (ako koristiš ProxySQL ili MySQL Router):
```go
// Jedan endpoint koji interno rutira read/write
masterDSN := "admin:pass@tcp(mysql:3306)/project_a"  // HeadlessService ili ProxySQL
```

### Go servis poziva Redis

```go
import "github.com/redis/go-redis/v9"

func NewRedisClient() *redis.Client {
    return redis.NewClient(&redis.Options{
        // ClusterIP service, load-balancira na sve Redis pode (ili single za dev)
        Addr:     "redis:6379",
        Password: os.Getenv("REDIS_PASSWORD"),
        DB:       0,
        
        // Connection pooling — kritično za K8s (više Pod instanci)
        PoolSize:     10,
        MinIdleConns: 5,
        MaxRetries:   3,
        DialTimeout:  5 * time.Second,
        ReadTimeout:  3 * time.Second,
        WriteTimeout: 3 * time.Second,
    })
}
```

---

## NetworkPolicy — ograniči koji podovi mogu komunicirati

### Default deny-all za namespace

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: project-a-prod
spec:
  podSelector: {}    # svi podovi u namespace-u
  policyTypes:
    - Ingress
    - Egress
  # Nema rules → sve blokirano
```

### Dozvoli DNS (obavezno uz default deny)

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-dns
  namespace: project-a-prod
spec:
  podSelector: {}
  policyTypes:
    - Egress
  egress:
    - ports:
        - protocol: UDP
          port: 53
        - protocol: TCP
          port: 53    # TCP fallback za veće DNS odgovore
```

**Ovo je najčešća greška**: zaboraviti DNS egress uz default deny → sve interne K8s DNS rezolucije padaju.

### NetworkPolicy za go-service

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: go-service-netpol
  namespace: project-a-prod
spec:
  podSelector:
    matchLabels:
      app: go-service
  policyTypes:
    - Ingress
    - Egress
  ingress:
    # Prima traffic samo od nginx i php-service
    - from:
        - podSelector:
            matchLabels:
              app: nginx
        - podSelector:
            matchLabels:
              app: php-service
      ports:
        - protocol: TCP
          port: 8080
    # Prometheus scraping
    - from:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: monitoring
          podSelector:
            matchLabels:
              app: prometheus
      ports:
        - protocol: TCP
          port: 9090
  egress:
    # Može pisati u MySQL (master)
    - to:
        - podSelector:
            matchLabels:
              app: mysql
      ports:
        - protocol: TCP
          port: 3306
    # Može čitati/pisati u Redis
    - to:
        - podSelector:
            matchLabels:
              app: redis
      ports:
        - protocol: TCP
          port: 6379
    # DNS
    - ports:
        - protocol: UDP
          port: 53
        - protocol: TCP
          port: 53
    # Vanjski API pozivi (npr. payment gateway)
    - to: []      # svi CIDR-ovi (preferiraj eksplicitne CIDR blokove)
      ports:
        - protocol: TCP
          port: 443
```

### NetworkPolicy za MySQL — samo go-service i php-service mogu čitati

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: mysql-netpol
  namespace: project-a-prod
spec:
  podSelector:
    matchLabels:
      app: mysql
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: go-service
        - podSelector:
            matchLabels:
              app: php-service
        - podSelector:
            matchLabels:
              app: db-migration    # Job podovi za migracije
      ports:
        - protocol: TCP
          port: 3306
  egress:
    # MySQL replika mora komunicirati s masterom
    - to:
        - podSelector:
            matchLabels:
              app: mysql
      ports:
        - protocol: TCP
          port: 3306
    # DNS
    - ports:
        - protocol: UDP
          port: 53
```

---

## Endpoints i EndpointSlice — iza kulisa

Svaki Service ima prateći Endpoint objekt koji sadrži stvarne IP-ove podova:

```bash
# Vidi koji podovi su iza servisa
kubectl get endpoints go-service -n project-a-prod
# NAME         ENDPOINTS                         AGE
# go-service   10.0.1.45:8080,10.0.2.67:8080    15d

# Detaljno (uključuje NodePort, readiness)
kubectl describe endpoints go-service -n project-a-prod

# EndpointSlice (novija API, bolji za skaliranje)
kubectl get endpointslices -n project-a-prod -l kubernetes.io/service-name=go-service
```

**Debugging: servis ne rutira traffic:**
```bash
kubectl get endpoints go-service -n project-a-prod
# Ako je output: NAME  ENDPOINTS  AGE
#                go-service  <none>  5m
# → nema podova koji matchuju selector ILI podovi nisu Ready
```

Uzroci praznog Endpoints:
1. `selector` u Service ne matchuje labele poda — provjeri `kubectl get pods --show-labels`
2. Pod postoji ali readinessProbe pada — `kubectl describe pod`
3. Pod je u drugom namespace-u — Service i Pod moraju biti u istom namespace-u (ili koristiti ExternalName)

---

## ExternalName Service — proxy prema vanjskom servisu

```yaml
# Abstraktuj externu RDS instancu iza K8s DNS-a
apiVersion: v1
kind: Service
metadata:
  name: mysql-rds
  namespace: project-a-prod
spec:
  type: ExternalName
  externalName: project-a-prod.cluster-abc123.eu-west-1.rds.amazonaws.com
  ports:
    - port: 3306
```

```go
// Go servis se spaja na "mysql-rds:3306" umjesto hardcodiranog RDS endpoint-a
masterDSN := "admin:pass@tcp(mysql-rds:3306)/project_a"
```

**Korist**: ako se RDS instance promijeni, samo se ažurira ExternalName Service, ne sve aplikacije.

---

## Service Topology — smanjenje cross-AZ troškova na EKS

```yaml
# Preferiraj routing unutar iste AZ (smanjuje $0.01/GB cross-AZ trošak)
spec:
  topologyKeys:
    - "topology.kubernetes.io/zone"    # isti AZ
    - "kubernetes.io/hostname"         # isti node (lokalno)
    - "*"                              # fallback: bilo koji pod
```

**Noviji pristup** (K8s 1.21+) — Topology Aware Routing:
```yaml
metadata:
  annotations:
    service.kubernetes.io/topology-aware-hints: auto
```

---

## Ingress — vanjski pristup

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: project-a-ingress
  namespace: project-a-prod
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/proxy-body-size: "20m"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "30"
    # Rate limiting
    nginx.ingress.kubernetes.io/limit-rps: "100"
    # CORS
    nginx.ingress.kubernetes.io/enable-cors: "true"
    nginx.ingress.kubernetes.io/cors-allow-origin: "https://app.project-a.com"
spec:
  tls:
    - hosts:
        - api.project-a.com
      secretName: project-a-tls-cert    # cert-manager popunjava
  rules:
    - host: api.project-a.com
      http:
        paths:
          - path: /api/v1
            pathType: Prefix
            backend:
              service:
                name: php-service
                port:
                  name: http
          - path: /api/v2
            pathType: Prefix
            backend:
              service:
                name: go-service
                port:
                  name: http
    - host: app.project-a.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: nginx
                port:
                  name: http
```

---

## Debugging networking problema

```bash
# DNS rezolucija iz poda
kubectl exec -it go-service-xxx -n project-a-prod -- nslookup mysql
kubectl exec -it go-service-xxx -n project-a-prod -- nslookup mysql.project-a-prod.svc.cluster.local

# HTTP test cross-pod (je li servis dostupan?)
kubectl exec -it nginx-xxx -n project-a-prod -- wget -qO- http://go-service:8080/health
kubectl exec -it nginx-xxx -n project-a-prod -- curl -v http://php-service:9000/ping

# TCP konekcija test (je li port otvoren?)
kubectl exec -it go-service-xxx -n project-a-prod -- nc -zv mysql 3306
# ili
kubectl exec -it go-service-xxx -- /bin/sh -c "cat /dev/null > /dev/tcp/mysql/3306 && echo 'OK'"

# Provjeri NetworkPolicy blokira li traffic
# Ako curl radi ali wget ne → problem s DNS ili NetworkPolicy

# CoreDNS status (DNS infrastruktura)
kubectl get pods -n kube-system -l k8s-app=kube-dns
kubectl logs -n kube-system -l k8s-app=kube-dns

# Provjeri Service selector vs Pod labele
kubectl get svc go-service -n project-a-prod -o yaml | grep -A5 selector
kubectl get pods -n project-a-prod --show-labels | grep go-service

# Zašto Ingress ne radi?
kubectl describe ingress project-a-ingress -n project-a-prod
kubectl get events -n project-a-prod | grep ingress
```

---

## Port naming best practices

```yaml
ports:
  - name: http        # uvijek imenuj port
    port: 8080
    protocol: TCP
  - name: metrics
    port: 9090
    protocol: TCP
  - name: grpc
    port: 50051
    protocol: TCP
```

**Zašto:** Prometheus automatski scrapuje portove nazvane `http` ili `metrics`. Istio koristi port nazive za protocol detection (http, grpc, tcp, mysql). Bez naziva oba tretiraju kao generički TCP.

---

## Sažetak: networking odluke za project-A

| Servis | Service tip | Razlog |
|--------|-------------|--------|
| nginx (Vue) | ClusterIP | Ingress se spaja na njega |
| php-service | ClusterIP | Interni, nginx proxy |
| go-service | ClusterIP | Interni, nginx/php proxy |
| MySQL | Headless | StatefulSet, stable DNS per pod |
| Redis | ClusterIP ili Headless | Single replica → ClusterIP |
| Ingress Controller | LoadBalancer | AWS ALB/NLB za vanjski pristup |
| RDS (cloud) | ExternalName | Abstraktuj externu zavisnost |
