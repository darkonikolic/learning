# 01 — Load Balancer Arhitektura

## Gdje sjedi load balancer u stacku

```
Internet
   ↓
Route53 (DNS: app.firma.com → ALB DNS name)
   ↓
AWS ALB (HTTPS:443 → SSL termination → HTTP:80 interno)
   ↓
K8s AWS Load Balancer Controller (prevodi ALB → K8s servis)
   ↓
K8s nginx Ingress Controller (path-based routing)
   ├── /api/*  → php-service ClusterIP :9000
   └── /*      → nginx-frontend ClusterIP :80
```

**Šta se dešava na svakom sloju:**

- **Route53** drži A record koji pokazuje na ALB DNS name (npr. `project-a-dev-alb-123456.eu-west-1.elb.amazonaws.com`). TTL obično 60-300s.
- **ALB** terminira TLS/SSL konekciju — od klijenta dolazi šifrovani HTTPS, ALB dekriptuje i prema K8s šalje plain HTTP. Certifikat živi na ALB-u, ne na podovima.
- **AWS Load Balancer Controller** (K8s operator) gleda Ingress resurse i automatski kreira/konfigurira ALB objekte (listener rules, target groups).
- **Ingress pravila** odlučuju: `/api/users` ide na php-service, `/login` ide na Vue.js frontend.

---

## ALB vs NLB vs CLB

| | ALB | NLB | CLB |
|---|---|---|---|
| **OSI Layer** | 7 (HTTP/HTTPS) | 4 (TCP/UDP) | 4+7 (legacy) |
| **Routing** | path, host, header, query param | IP, port | basic |
| **SSL termination** | da, ACM integracija | da (TLS), ali pass-through moguć | da |
| **WebSockets** | da | da | ograničeno |
| **Latencija** | ~1-5ms overhead | ~100μs, ultra-low | - |
| **Static IP** | ne (DNS only) | da, Elastic IP | ne |
| **WAF integracija** | da | ne | ne |
| **Health checks** | HTTP/HTTPS (provjera body/status) | TCP/HTTP | TCP/HTTP |

**Kada koji:**

- **ALB (naš slučaj)**: Web aplikacije sa HTTP/HTTPS, path-based routing, SSL, WAF, AWS Cognito autentikacija. Vue.js + PHP + API — ALB je jedini pravi izbor.
- **NLB**: Gaming serveri, real-time streaming, finansijske aplikacije gdje je μs latencija kritična. Ili kad trebaš statički IP za whitelisting. Nginx Ingress Controller na EKS defaultno kreira NLB.
- **CLB (Classic)**: Nikad koristiti za nova deployments. Postoji samo zbog legacy aplikacija iz 2009. AWS više ne razvija CLB.

---

## AWS Load Balancer Controller

K8s controller (operator) koji živi u `kube-system` namespaceu i gleda Kubernetes Ingress resurse.

**Kako radi:**

1. Ti kreiraš `kind: Ingress` YAML i `kubectl apply`
2. ALB Controller vidi novi Ingress resource
3. Poziva AWS API i kreira stvarni ALB, Listener, Target Groups, Listener Rules
4. Prati lifecycle — kad izbrišeš Ingress, briše se i ALB

**Jedan ALB po Ingress vs IngressGroup:**

```
# Bez IngressGroup: svaki Ingress = poseban ALB = $$$ troškovi
ingress-app.yaml     → ALB #1 (0.008$/h)
ingress-monitoring.yaml → ALB #2 (0.008$/h)
ingress-admin.yaml   → ALB #3 (0.008$/h)
Ukupno: 3 × $5.76/mj = $17.28/mj samo za ALB-ove

# Sa IngressGroup: dijele isti ALB
alb.ingress.kubernetes.io/group.name: project-a-prod
→ Jedan ALB, više pravila, ~$5.76/mj
```

**IRSA (IAM Roles for Service Accounts)** — ALB Controller treba IAM permisije da kreira AWS resurse. IRSA je siguran način da K8s Service Account dobije IAM Role bez hardkodiranih kredencijala.

---

## Zašto ALB Controller umjesto Nginx Ingress Controller na EKS

Nginx Ingress Controller je popularan na bare-metal i self-managed K8s, ali na EKS postoje važne razlike:

| | AWS ALB Controller | Nginx Ingress Controller (na EKS) |
|---|---|---|
| **AWS integracija** | Native: WAF, Shield, ACM, access logs S3 | Minimalna, treba wrapper |
| **NLB vs ALB** | Kreira ALB (Layer 7) | Kreira NLB (Layer 4) — Nginx sam radi routing |
| **SSL** | ACM managed, auto-renewal | Cert-manager + Let's Encrypt ili manual |
| **Health checks** | HTTP-level, provjera status koda | TCP-level na NLB-u |
| **Troškovi** | ALB po saobraćaju + hourly | NLB + Nginx podovi (compute cost) |
| **Maintainance** | Managed by AWS controller | Nginx upgrade odgovornost tima |

**Za naš stack (EKS + AWS)**: ALB Controller je ispravniji izbor. Nginx IC ima smisla ako ti treba specifična Nginx konfiguracija (custom modules, complex rewrite rules) ili portabilnost između cloud provajdera.

---

## Tok HTTPS request-a kroz sistem

```
1. Browser → DNS lookup app.firma.com
   Route53 vraća: project-a-prod-alb-789.eu-west-1.elb.amazonaws.com

2. Browser → TCP:443 → ALB
   TLS handshake: ALB šalje cert (*.firma.com iz ACM)
   Browser verificira cert, uspostavlja encrypted tunnel

3. ALB → decryptuje HTTPS request
   → provjeri Listener Rules:
     host = app.firma.com AND path = /api/* → TargetGroup: php-pods
     host = app.firma.com AND path = /*     → TargetGroup: frontend-pods

4. ALB → HTTP:80 → odabrani pod (direktno na pod IP, target-type: ip)
   X-Forwarded-For: originalni klijent IP
   X-Forwarded-Proto: https
   X-Forwarded-Port: 443

5. Pod obradi request → vrati HTTP response → ALB → enkriptuje → browser
```

**Bitno:** Pod nikad ne vidi HTTPS. Vidi HTTP s headerima koji mu kažu original proto/port/IP. PHP mora čitati `$_SERVER['HTTP_X_FORWARDED_PROTO']` za provjeru je li dolazni request bio HTTPS.
