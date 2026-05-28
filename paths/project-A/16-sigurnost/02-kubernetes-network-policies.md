# 02 — Kubernetes Network Policies

## Default deny-all — polazna tačka

Bez eksplicitnih NetworkPolicy objekata, Kubernetes dozvoljava sav pod-to-pod saobraćaj u klasteru. Svaki kompromitovani pod može komunicirati sa svakim drugim podom, RDS instancom, metadata service-om.

Default deny-all je obavezan prvi korak:

```yaml
# k8s/base/network-policies/default-deny.yaml

# Blokirati sav ingress u namespace
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-ingress
  namespace: project-a
spec:
  podSelector: {}  # Prazno = primjenjuje se na SVE podove u namespace-u
  policyTypes:
    - Ingress
---
# Blokirati sav egress iz namespace-a
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-egress
  namespace: project-a
spec:
  podSelector: {}
  policyTypes:
    - Egress
```

Nakon ovog, apsolutno ništa ne radi dok eksplicitno ne dodate allow rules.

**Gotcha:** DNS (UDP port 53) mora biti eksplicitno dozvoljen za sve podove, inače name resolution ne radi:

```yaml
# k8s/base/network-policies/allow-dns.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-dns-egress
  namespace: project-a
spec:
  podSelector: {}
  policyTypes:
    - Egress
  egress:
    - ports:
        - protocol: UDP
          port: 53
        - protocol: TCP
          port: 53
      to:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: kube-system
```

---

## Allow-list za project-a servisnu mrežu

### 1. Ingress nginx → php-service (FastCGI)

```yaml
# k8s/base/network-policies/allow-nginx-to-php.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-nginx-to-php
  namespace: project-a
spec:
  podSelector:
    matchLabels:
      app: php-service
  policyTypes:
    - Ingress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: nginx
      ports:
        - protocol: TCP
          port: 9000  # PHP-FPM FastCGI port
```

### 2. php-service → go-service (HTTP API)

```yaml
# k8s/base/network-policies/allow-php-to-go.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-php-to-go
  namespace: project-a
spec:
  podSelector:
    matchLabels:
      app: go-service
  policyTypes:
    - Ingress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: php-service
      ports:
        - protocol: TCP
          port: 8080
---
# Egress na go-service iz php-service
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-php-egress-to-go
  namespace: project-a
spec:
  podSelector:
    matchLabels:
      app: php-service
  policyTypes:
    - Egress
  egress:
    - to:
        - podSelector:
            matchLabels:
              app: go-service
      ports:
        - protocol: TCP
          port: 8080
```

### 3. go-service → MySQL (RDS)

RDS je van Kubernetes klastera — IP CIDR range umjesto podSelector:

```yaml
# k8s/base/network-policies/allow-go-to-rds.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-go-egress-to-rds
  namespace: project-a
spec:
  podSelector:
    matchLabels:
      app: go-service
  policyTypes:
    - Egress
  egress:
    # Master (write)
    - to:
        - ipBlock:
            cidr: 10.0.10.0/24   # RDS subnet CIDR
            except:
              - 10.0.10.0/32     # Network address
              - 10.0.10.255/32   # Broadcast
      ports:
        - protocol: TCP
          port: 3306
    # Read replica
    - to:
        - ipBlock:
            cidr: 10.0.11.0/24   # RDS replica subnet CIDR
      ports:
        - protocol: TCP
          port: 3306
```

**Napomena:** Statički CIDR u NetworkPolicy je anti-pattern za produkciju — RDS endpoint IP se može promijeniti. Bolje rješenje: koristiti Security Group rules na AWS strani (VPC level) jer NetworkPolicy ne pokriva traffic koji ide van klastera (EKS VPC CNI). NetworkPolicy pokriva pod-to-pod unutar klastera.

Za RDS, MySQL, ElastiCache — **kontrola je na Security Group nivou, ne NetworkPolicy nivou:**

```hcl
# terraform/modules/database/security-groups.tf

resource "aws_security_group_rule" "rds_from_eks_nodes" {
  type                     = "ingress"
  from_port                = 3306
  to_port                  = 3306
  protocol                 = "tcp"
  source_security_group_id = var.eks_nodes_sg_id  # EKS worker node SG
  security_group_id        = aws_security_group.rds.id
  description              = "MySQL from EKS nodes"
}
```

### 4. go-service → Redis (ElastiCache)

```yaml
# k8s/base/network-policies/allow-go-to-redis.yaml
# + allow-php-to-redis.yaml (ako PHP direktno čita Redis)
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-go-egress-to-redis
  namespace: project-a
spec:
  podSelector:
    matchLabels:
      app: go-service
  policyTypes:
    - Egress
  egress:
    - to:
        - ipBlock:
            cidr: 10.0.20.0/24  # ElastiCache subnet
      ports:
        - protocol: TCP
          port: 6379
```

### 5. Ingress nginx ← ingress-nginx-controller

```yaml
# k8s/base/network-policies/allow-ingress-to-nginx.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-ingress-controller-to-nginx
  namespace: project-a
spec:
  podSelector:
    matchLabels:
      app: nginx
  policyTypes:
    - Ingress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: ingress-nginx
          podSelector:
            matchLabels:
              app.kubernetes.io/name: ingress-nginx
      ports:
        - protocol: TCP
          port: 8080  # nginx sluša na 8080 (non-root)
```

### 6. Monitoring namespace → sve

```yaml
# k8s/base/network-policies/allow-monitoring-scrape.yaml
# Primijeniti na svaki namespace koji sadrži aplikacijske podove

apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-monitoring-scrape
  namespace: project-a
spec:
  podSelector: {}  # Svi podovi u namespace-u
  policyTypes:
    - Ingress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: monitoring
          podSelector:
            matchLabels:
              app.kubernetes.io/name: prometheus
      ports:
        - protocol: TCP
          port: 9090  # Go service metrics
        - protocol: TCP
          port: 9091  # PHP exporter metrics (ako postoji)
```

---

## Verifikacija NetworkPolicy

```bash
# Test 1: go-service može dostići MySQL (trebalo bi raditi)
kubectl exec -n project-a deploy/go-service -- \
    nc -zv $RDS_ENDPOINT 3306
# Expected: succeeded

# Test 2: php-service NE MOŽE direktno dostići MySQL (trebalo bi failati)
kubectl exec -n project-a deploy/php-service -- \
    nc -zv $RDS_ENDPOINT 3306 -w 3
# Expected: timeout ili connection refused

# Test 3: go-service NE MOŽE dostići php-service (jednosmjerna komunikacija)
kubectl exec -n project-a deploy/go-service -- \
    nc -zv php-service 9000 -w 3
# Expected: timeout

# Test 4: Nema cross-namespace komunikacije bez eksplicitnog allow
kubectl exec -n default -- curl http://go-service.project-a.svc.cluster.local:8080/ -m 3
# Expected: timeout

# Test 5: DNS radi
kubectl exec -n project-a deploy/go-service -- nslookup kubernetes.default.svc.cluster.local
# Expected: success
```

---

## Calico vs Cilium vs AWS VPC CNI

EKS default networking plugin je **AWS VPC CNI**. Ovo ima direktne implikacije za NetworkPolicy:

| CNI | NetworkPolicy support | Performance | Extras |
|---|---|---|---|
| AWS VPC CNI | Samo L3/L4 (IP + port) | Nativni AWS networking | EKS default, pod IPs su VPC IPs |
| Calico | L3/L4 + L7 (HTTP paths) | Dobar, eBPF opcija | GlobalNetworkPolicy za cluster-wide |
| Cilium | L3/L4 + L7 + FQDN rules | Odličan (eBPF natively) | CiliumNetworkPolicy, Hubble observability |

**AWS VPC CNI samo NetworkPolicy ograničenja:**

1. Ne podržava FQDN-based rules (ne možete reći "dozvoli egress na `api.stripe.com`")
2. Ne podržava L7 filtering (ne možete reći "dozvoli GET /health ali ne POST /admin")
3. Nema cluster-wide NetworkPolicy

Za naš stack, AWS VPC CNI sa standardnim NetworkPolicy je dovoljan za L3/L4 segmentaciju. Cilium dodati ako trebate:
- Egress FQDN filtering (blokirati sav external egress osim poznatih API endpoint-a)
- HTTP-aware policies
- Bogatiji observability (Hubble UI)

```hcl
# Terraform: instalacija Cilium umjesto/pored AWS VPC CNI
# (advanced setup — za produkciju sa higher security zahtjevima)
resource "helm_release" "cilium" {
  name       = "cilium"
  repository = "https://helm.cilium.io"
  chart      = "cilium"
  version    = "1.15.1"
  namespace  = "kube-system"

  set {
    name  = "eni.enabled"
    value = "true"  # Koristi AWS ENI za IP allocations
  }
  set {
    name  = "ipam.mode"
    value = "eni"
  }
  set {
    name  = "egressMasqueradeInterfaces"
    value = "eth0"
  }
  set {
    name  = "hubble.relay.enabled"
    value = "true"  # Observability
  }
}
```

---

## NetworkPolicy — failure modes i gotche

**DNS bez allow-dns-egress policy:**  
Najčešća greška. Nakon default-deny-egress, sve DNS queries failaju. Simptom: `ErrImagePull`, application startup failovi, "unknown host" greške.

**ipBlock vs podSelector za external services:**  
NetworkPolicy `ipBlock` koristi IP adrese. Za RDS, ElastiCache, SM, i ostale AWS servise — koristite Security Groups (Terraform) za kontrolu, ne NetworkPolicy. NetworkPolicy je za pod-to-pod unutar klastera.

**Namespace selector labele:**  
Kubernetes automatski kreira `kubernetes.io/metadata.name` label na svakom namespace-u od v1.21+. Koristiti ovu label za namespace selector, ne custom labele koje se mogu promijeniti.

**Stateful connections:**  
NetworkPolicy dozvoljava TCP handshake ali ne prati state. Ako dozvolite ingress na port 8080, return traffic (egress) je automatski dozvoljen za established connections. Ne trebate eksplicitni egress rule za odgovore na inbound connections.

**Testiranje u staging obligatorno:**  
NetworkPolicy greška u produkciji = downtime. Uvijek deployjati i testirati policy u staging okruženju identičnoj konfiguraciji prije prod deploy-a.
