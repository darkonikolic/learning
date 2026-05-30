# 04 — Kubernetes Integracija: RDS i ElastiCache iz K8s

## Security Group Strategija

### Zašto worker node SG, a ne pod CIDR

Pogrešan pristup koji se često viđa:

```hcl
# POGREŠNO — ne radi kako se očekuje
ingress {
  from_port   = 3306
  to_port     = 3306
  protocol    = "tcp"
  cidr_blocks = ["10.0.0.0/18"]  # Pod CIDR range
}
```

**Problemi s pod CIDR pristupom:**

1. Pod IP adrese su efemeralne — svaki restart Pod-a dobija novu IP
2. Pod CIDR range može se preklapati s drugim subnets u VPC-u
3. AWS Security Groups ne razumiju Kubernetes pod network nativno — CIDR pristup dozvoljava svim host-ovima u tom rangeu, ne samo EKS pod-ovima
4. CNI plugin (aws-vpc-cni) dodjeljuje IP adrese s VPC subnet-ova — security group na worker node-u pokriva sav traffic koji prolazi kroz tu instancu

**Ispravno:**

```hcl
# RDS Security Group
ingress {
  from_port       = 3306
  to_port         = 3306
  protocol        = "tcp"
  security_groups = [var.eks_worker_security_group_id]
  # Sve što dolazi s EKS worker node-ova (uključujući pod-ove na njima)
}
```

**Security Groups for Pods** (napredna opcija): Ako treba granularnija kontrola na pod nivou, EKS podržava security groups direktno na pod-ovima. Ali ovo zahtijeva `ENABLE_POD_ENI = true` u aws-vpc-cni, ne radi sa svim instance tipovima, i kompleksira networking. Za naš use case: worker node SG je dovoljan.

---

## Secrets: External Secrets Operator → K8s Secret → Pod

### Tok podataka

```
Terraform kreира →  AWS Secrets Manager
                          │
External Secrets Operator │ (povlači secret svaka 1h)
(radi u K8s cluster-u)    │
                          ▼
                    K8s Secret (namespace: project-a)
                          │
                    volumeMount / envFrom
                          │
                          ▼
                    Pod (go-service / php-service)
```

### External Secrets Operator konfiguracija

```yaml
# k8s/base/external-secrets/secretstore.yaml
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: aws-secretsmanager
  namespace: project-a
spec:
  provider:
    aws:
      service: SecretsManager
      region: eu-west-1
      auth:
        jwt:
          serviceAccountRef:
            name: external-secrets-sa
            # ServiceAccount s IRSA (IAM Role for Service Accounts)
            # IAM politika dozvoljava secretsmanager:GetSecretValue za naše secretsmanager ARNove
```

```yaml
# k8s/base/external-secrets/rds-secret.yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: rds-credentials
  namespace: project-a
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secretsmanager
    kind: SecretStore
  target:
    name: rds-credentials          # Ime K8s Secret-a koji se kreira
    creationPolicy: Owner
    template:
      type: Opaque
      data:
        # Mapiramo JSON ključeve iz Secrets Manager u K8s Secret data
        DB_MASTER_HOST: "{{ .host }}"
        DB_REPLICA_HOST: "{{ .replica_host }}"
        DB_NAME: "{{ .dbname }}"
        DB_USER: "{{ .username }}"
        DB_PASSWORD: "{{ .password }}"
        # Kompletni connection string za Go service
        DATABASE_URL: "{{ .username }}:{{ .password }}@tcp({{ .host }}:3306)/{{ .dbname }}?parseTime=true&charset=utf8mb4"
        DATABASE_REPLICA_URL: "{{ .username }}:{{ .password }}@tcp({{ .replica_host }}:3306)/{{ .dbname }}?parseTime=true&charset=utf8mb4"
  data:
    - secretKey: host
      remoteRef:
        key: "project-a-prod/rds/master"
        property: host
    - secretKey: replica_host
      remoteRef:
        key: "project-a-prod/rds/master"
        property: replica_host
    - secretKey: username
      remoteRef:
        key: "project-a-prod/rds/master"
        property: username
    - secretKey: password
      remoteRef:
        key: "project-a-prod/rds/master"
        property: password
    - secretKey: dbname
      remoteRef:
        key: "project-a-prod/rds/master"
        property: dbname
```

```yaml
# k8s/base/external-secrets/redis-secret.yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: redis-credentials
  namespace: project-a
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secretsmanager
    kind: SecretStore
  target:
    name: redis-credentials
  data:
    - secretKey: REDIS_HOST
      remoteRef:
        key: "project-a-prod/redis/auth"
        property: host
    - secretKey: REDIS_AUTH_TOKEN
      remoteRef:
        key: "project-a-prod/redis/auth"
        property: auth_token
```

---

## Go Service Deployment

```yaml
# k8s/base/go-service/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: go-service
  namespace: project-a
spec:
  replicas: 2
  selector:
    matchLabels:
      app: go-service
  template:
    metadata:
      labels:
        app: go-service
    spec:
      serviceAccountName: go-service
      containers:
        - name: go-service
          image: registry.gitlab.com/project-a/go-service:latest
          ports:
            - containerPort: 8080

          envFrom:
            - secretRef:
                name: rds-credentials
            - secretRef:
                name: redis-credentials
          # Okruženje dobija:
          # DATABASE_URL, DATABASE_REPLICA_URL, REDIS_HOST, REDIS_AUTH_TOKEN

          resources:
            requests:
              cpu: "100m"
              memory: "128Mi"
            limits:
              cpu: "500m"
              memory: "512Mi"

          livenessProbe:
            httpGet:
              path: /health
              port: 8080
            initialDelaySeconds: 10
            periodSeconds: 10
            timeoutSeconds: 5
            failureThreshold: 3

          readinessProbe:
            httpGet:
              path: /health
              port: 8080
            initialDelaySeconds: 15
            periodSeconds: 10
            timeoutSeconds: 5
            failureThreshold: 6
            # Expert gotcha: RDS Multi-AZ failover traje ~60s
            # failureThreshold: 6 × periodSeconds: 10 = 60s tolerancija
            # Bez ovoga: K8s maknuti Pod iz Service za vrijeme failover-a → 502 greške
            # Bolje: Pod ostaje "not ready" 60s nego da dobijamo hard failures
```

### Health Check Endpoint

```go
// internal/handler/health.go
package handler

import (
    "context"
    "encoding/json"
    "net/http"
    "time"
)

type HealthHandler struct {
    db    DBPinger
    redis RedisPinger
}

type HealthResponse struct {
    Status   string            `json:"status"`
    Checks   map[string]string `json:"checks"`
    Timestamp string           `json:"timestamp"`
}

func (h *HealthHandler) Health(w http.ResponseWriter, r *http.Request) {
    ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
    defer cancel()

    checks := make(map[string]string)
    healthy := true

    // MySQL ping (master)
    if err := h.db.PingMaster(ctx); err != nil {
        checks["mysql_master"] = "unhealthy: " + err.Error()
        healthy = false
    } else {
        checks["mysql_master"] = "healthy"
    }

    // MySQL replica ping
    if err := h.db.PingReplica(ctx); err != nil {
        checks["mysql_replica"] = "degraded: " + err.Error()
        // Replica problem nije critical — service radi, samo bez read scaling
        // Ne postavljamo healthy = false za repliku
    } else {
        checks["mysql_replica"] = "healthy"
    }

    // Redis ping
    if err := h.redis.Ping(ctx); err != nil {
        checks["redis"] = "unhealthy: " + err.Error()
        healthy = false
        // Redis failure JE critical za session-based aplikaciju
    } else {
        checks["redis"] = "healthy"
    }

    resp := HealthResponse{
        Checks:    checks,
        Timestamp: time.Now().UTC().Format(time.RFC3339),
    }

    if healthy {
        resp.Status = "healthy"
        w.WriteHeader(http.StatusOK)
    } else {
        resp.Status = "unhealthy"
        w.WriteHeader(http.StatusServiceUnavailable)
        // 503 → K8s readinessProbe fails → Pod izlazi iz rotation
    }

    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(resp)
}
```

---

## Connection String Format

### Go MySQL DSN

```
user:pass@tcp(endpoint:3306)/dbname?parseTime=true&charset=utf8mb4&collation=utf8mb4_unicode_ci&timeout=5s&readTimeout=10s&writeTimeout=10s&loc=UTC
```

**Parametri objašnjeni:**

| Parametar | Vrijednost | Razlog |
|---|---|---|
| `parseTime=true` | true | `time.Time` umjesto `[]byte` za DATE/DATETIME kolone |
| `charset=utf8mb4` | utf8mb4 | Podržava 4-byte Unicode (emoji, CJK chars) |
| `collation=utf8mb4_unicode_ci` | — | Konzistentno sortiranje |
| `timeout=5s` | 5s | TCP connect timeout |
| `readTimeout=10s` | 10s | Read operacije timeout |
| `writeTimeout=10s` | 10s | Write operacije timeout (INSERT/UPDATE) |
| `loc=UTC` | UTC | Force UTC za time.Time parsing |

### PHP Redis DSN

```
tls://redis-endpoint:6379?auth=AUTH_TOKEN&database=0&timeout=2.5&read_timeout=2.5&persistent=1
```

---

## NetworkPolicy: Granularna Mrežna Kontrola

```yaml
# k8s/base/network-policy/go-service-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: go-service-policy
  namespace: project-a
spec:
  podSelector:
    matchLabels:
      app: go-service
  policyTypes:
    - Ingress
    - Egress

  ingress:
    # go-service prima traffic SAMO od php-service i ingress controller-a
    - from:
        - podSelector:
            matchLabels:
              app: php-service
      ports:
        - protocol: TCP
          port: 8080
    - from:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: ingress-nginx
      ports:
        - protocol: TCP
          port: 8080

  egress:
    # go-service smije ići ka RDS (port 3306) i Redis (port 6379)
    # RDS i Redis su van K8s clustera (AWS managed), pa koristimo cidrIP
    - to:
        - ipBlock:
            cidr: 10.0.0.0/8   # VPC CIDR (private subnets gdje su RDS/ElastiCache)
      ports:
        - protocol: TCP
          port: 3306   # RDS
        - protocol: TCP
          port: 6379   # ElastiCache
    # DNS resolution
    - to:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: kube-system
      ports:
        - protocol: UDP
          port: 53
```

```yaml
# k8s/base/network-policy/php-service-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: php-service-policy
  namespace: project-a
spec:
  podSelector:
    matchLabels:
      app: php-service
  policyTypes:
    - Ingress
    - Egress

  ingress:
    # php-service prima traffic SAMO od ingress controller-a
    - from:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: ingress-nginx
      ports:
        - protocol: TCP
          port: 80   # PHP-FPM via nginx sidecar

  egress:
    # php-service smije ići ka go-service i Redis (za session)
    - to:
        - podSelector:
            matchLabels:
              app: go-service
      ports:
        - protocol: TCP
          port: 8080
    - to:
        - ipBlock:
            cidr: 10.0.0.0/8
      ports:
        - protocol: TCP
          port: 6379   # Redis sessions
    - to:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: kube-system
      ports:
        - protocol: UDP
          port: 53
```

**Važna napomena**: NetworkPolicy je namjenski za East-West traffic kontrolu unutar K8s clustera. Za RDS/ElastiCache koji su AWS managed servisi van clustera, osnovna zaštita dolazi od Security Groups (koji se nalaze na AWS network nivou, prije K8s networking). NetworkPolicy egress pravila za RDS su "defense in depth" ali prava granica je SG.

---

## IRSA (IAM Role for Service Accounts)

Go service treba IAM permission za čitanje Secrets Manager (alternativa External Secrets Operator-u ako direktno čita u Go kodu).

```hcl
# terraform/modules/eks-irsa/main.tf

# IAM Role za go-service K8s ServiceAccount
module "go_service_irsa" {
  source = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"

  role_name = "project-a-${var.env_name}-go-service"

  oidc_providers = {
    main = {
      provider_arn               = var.oidc_provider_arn
      namespace_service_accounts = ["project-a:go-service"]
    }
  }

  role_policy_arns = {
    secrets = aws_iam_policy.go_service_secrets.arn
  }
}

resource "aws_iam_policy" "go_service_secrets" {
  name = "project-a-${var.env_name}-go-service-secrets"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = [
          "arn:aws:secretsmanager:${var.region}:${var.account_id}:secret:project-a-${var.env_name}/rds/*",
          "arn:aws:secretsmanager:${var.region}:${var.account_id}:secret:project-a-${var.env_name}/redis/*"
        ]
      }
    ]
  })
}
```

```yaml
# k8s/base/go-service/serviceaccount.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: go-service
  namespace: project-a
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::ACCOUNT_ID:role/project-a-prod-go-service
    # Ova anotacija govori aws-iam-authenticator/EKS Pod Identity webhook-u
    # da injektuje IRSA credentials u pod
```

---

## Makefile — dodaj u ovom poglavlju

Ovo poglavlje uvodi RDS i ElastiCache integraciju. Dodaj u `Makefile` u korenu projekta:

```makefile
# === OBLAST 14: Baze podataka ===

db-port-forward: ## Port-forward MySQL RDS via kubectl na localhost:3306 (POD=mysql-pod NS=dev make db-port-forward)
	docker run --rm \
	  -v ~/.kube:/root/.kube \
	  -p 3306:3306 \
	  bitnami/kubectl:$(KUBECTL_VERSION) port-forward -n $(NS) pod/$(POD) 3306:3306
```

Centralni Makefile već sadrži ovaj target — ovo je referenca šta si dodao u ovoj oblasti.

Provjeri da target radi:
```bash
POD=mysql-bastion NS=dev make db-port-forward
make help | grep db-port-forward
```
