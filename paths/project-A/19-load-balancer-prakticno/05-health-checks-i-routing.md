# 05 — Health Checks i Routing

## ALB Health Check Flow

```
ALB → GET /health HTTP/1.1 → pod
       ← HTTP 200 OK       ← pod
       
Threshold: 2 uspješna check-a → Target: HEALTHY → prima saobraćaj

ALB → GET /health → pod (timeout ili non-200)
ALB → GET /health → pod (timeout ili non-200)
→ Target: UNHEALTHY → ukloni iz rotacije → requestovi idu na preostale healthy targete
```

**Vremenski tok:**
```
t=0:  pod se pokreće
t=15: ALB health check #1 → 200 OK (1/2)
t=30: ALB health check #2 → 200 OK (2/2) → HEALTHY
t=30: pod počinje primati stvarni saobraćaj (ne prije!)

t=100: pod prestaje odgovarati
t=115: ALB health check → fail (1/2)
t=130: ALB health check → fail (2/2) → UNHEALTHY
t=130: pod izbačen iz rotacije (sav saobraćaj na ostale targete)
```

Ukupno 30 sekundi od kvara do uklanjanja poda iz rotacije. Za produkciju to znači 30s u kojima ALB može slati 50% requestova na nezdrav pod (ako imaš 2 targeta, 1 zdrav 1 ne). To je prihvatljivo za web aplikacije.

---

## Health Check Endpoint — Šta Mora Provjeriti

**Loš health check endpoint:**
```php
// app/health.php - provjera koja ne provjerava ništa stvarno
echo "OK";
http_response_code(200);
```

Ovo znači: pod uvijek zdrav čak i kad ne može spojiti na bazu.

**Dobar health check endpoint:**
```php
// Nginx/PHP: /health endpoint
// Provjeri što je bitno za taj servis, ne previše

// nginx-health (statički, brz):
// Nginx location block:
// location /health { return 200 "OK\n"; add_header Content-Type text/plain; }

// php-service /health:
<?php
try {
    // Provjeri kritične ovisnosti
    $pdo = new PDO($dsn, $user, $pass);
    $pdo->query('SELECT 1');
    
    // Provjeri go-service dostupnost
    $ctx = stream_context_create(['http' => ['timeout' => 2]]);
    $result = @file_get_contents('http://go-service:8080/health', false, $ctx);
    if ($result === false) {
        throw new Exception('go-service unreachable');
    }
    
    http_response_code(200);
    echo json_encode(['status' => 'ok', 'timestamp' => time()]);
} catch (Exception $e) {
    http_response_code(503);
    echo json_encode(['status' => 'error', 'message' => $e->getMessage()]);
}
```

```go
// go-service /health:
func healthHandler(w http.ResponseWriter, r *http.Request) {
    // Provjeri MySQL ping
    if err := db.Ping(); err != nil {
        http.Error(w, `{"status":"error","dependency":"mysql"}`, http.StatusServiceUnavailable)
        return
    }
    
    // Provjeri Redis ping
    if err := redisClient.Ping(r.Context()).Err(); err != nil {
        http.Error(w, `{"status":"error","dependency":"redis"}`, http.StatusServiceUnavailable)
        return
    }
    
    w.WriteHeader(http.StatusOK)
    json.NewEncoder(w).Encode(map[string]string{"status": "ok"})
}
```

**Pravilo:** Health check treba biti brz (< 100ms) i provjeravati samo lokalne ovisnosti servisa. Ne lanče health check ne treba ići previše duboko — ako baza pada, svi servisi koji zavise od nje će biti unhealthy, ALB to vidi.

---

## Sinhronizacija ALB i K8s Health Checks

Ovo je kritično i čest izvor race conditiona.

```
Problem: ALB drži pod u rotaciji 30s nakon što K8s označi pod kao not-ready
Rezultat: requestovi stižu na pod koji se gasi
```

**Potrebna usklađenost:**

```yaml
# K8s deployment spec — readiness probe
readinessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 10    # čekaj 10s dok se app pokrene
  periodSeconds: 10          # provjeri svake 10s
  failureThreshold: 3        # 3 faila → not-ready (30s total)
  successThreshold: 1        # 1 uspjeh → ready

livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 30    # duže nego readiness — ne ubijaj pod dok se pokreće
  periodSeconds: 15
  failureThreshold: 3        # 45s bez odgovora → restart pod

# ALB Target Group settings (via Ingress annotations):
# unhealthyThresholdCount: 2
# healthcheckInterval: 15s
# → UNHEALTHY nakon 30s
```

**Aligned timeline:**
```
K8s readiness:  failureThreshold=3, period=10s → not-ready za 30s
ALB health check: unhealthy threshold=2, interval=15s → unhealthy za 30s

Oboje detektuju problem za ~30s → nema race conditiona
```

**Deregistration delay (connection draining):**

Kad K8s počne gasiti pod (scaling down, rolling update), ALB treba završiti aktivne konekcije:

```yaml
alb.ingress.kubernetes.io/target-group-attributes: |
  deregistration_delay.timeout_seconds=30
```

K8s `terminationGracePeriodSeconds` mora biti veći od deregistration delay:
```yaml
spec:
  terminationGracePeriodSeconds: 60  # >= deregistration delay (30s) + shutdown time
```

**Workflow pri rolling update:**
```
1. K8s počinje gasiti stari pod
2. ALB počinje deregistraciju (connection draining 30s)
3. Novi requestovi ne idu na stari pod
4. Aktivni requestovi završavaju (max 30s)
5. Pod se gasi — svi requestovi su završeni
6. Nema prekinutih requestova za korisnika
```

---

## Path-Based Routing

```
Request: GET /api/v2/users HTTP/1.1
ALB Listener Rules (evaluiraju se po prioritetu):

Priority 1: path /api/* → php-service:9000  ← MATCH, forward ovdje
Priority 2: path /*     → nginx-frontend:80 ← ne evaluira se
```

**Specifičnost pravila:**
```
/api/v2/users  → treba biti specifičnija od /api/*
/api/*         → treba biti specifičnija od /*
```

**Najčešća greška:** Reverse prioritet. `/*` ima prioritet 1, hvata sve requestove uključujući `/api/*`. Frontend servis prima API requestove, vraća HTML umjesto JSON-a, frontend puca.

---

## Host-Based Routing

Jedan ALB, više okruženja ili servisa po host headeru:

```
ALB Listener Rules:
  IF host = app.firma.com       AND path = /api/* → php-service (prod)
  IF host = app.firma.com       AND path = /*     → frontend (prod)
  IF host = app.dev.firma.com   AND path = /api/* → php-service (dev namespace)
  IF host = app.dev.firma.com   AND path = /*     → frontend (dev namespace)
  IF host = monitoring.firma.com                  → grafana-service
  DEFAULT                                         → maintenance page
```

U K8s Ingress sa IngressGroup:
```yaml
# ingress-prod.yaml
spec:
  rules:
    - host: app.firma.com
      http:
        paths: [...]

---
# ingress-dev.yaml (isti group.name, isti ALB)
spec:
  rules:
    - host: app.dev.firma.com
      http:
        paths: [...]
```

---

## Weighted Routing — Blue/Green Deploy

ALB podržava forward action sa weight-ima između target gropa:

```
Blue/Green deploy postupak:

Korak 1: Deployi novu verziju u blue target group (0% saobraćaj)
Korak 2: Provjeri blue TG health checks — mora biti 100% healthy

Korak 3: Postavi weights (konzola ili AWS CLI):
ALB Listener Rule:
  Forward: 
    - TargetGroup: blue-tg   weight: 10  (10% saobraćaj na novu verziju)
    - TargetGroup: green-tg  weight: 90  (90% ostaje na staroj)

Korak 4: Prati greške/latenciju u CloudWatch-u (15 minuta)
Korak 5: Pomjeri na 50/50, prati opet
Korak 6: 90/10, 100/0 → deploy završen
Korak 7: Green TG ostaje alive još 1 sat (rollback mogućnost)
```

```bash
# AWS CLI: promijeni weights
aws elbv2 modify-rule \
  --rule-arn arn:aws:elasticloadbalancing:eu-west-1:123:listener-rule/app/abc/def \
  --actions Type=forward,ForwardConfig="{
    TargetGroups=[
      {TargetGroupArn=arn:...:blue-tg,Weight=10},
      {TargetGroupArn=arn:...:green-tg,Weight=90}
    ]
  }"

# Rollback (ako ima problema):
# Promijeni na 0/100 — sav saobraćaj nazad na green
```

**Sticky sessions + weighted routing:** Ako koristiš sticky sessions, postoji mogućnost da korisnik "zapne" na jednoj verziji duže nego što bi trebao. Za stateless aplikacije (JWT autentikacija), sticky sessions nisu potrebne.

---

## Canary Deploy Pattern

Manji od blue/green — ne kreiraj novu target grupu, već deployi novu verziju na **podskup podova** unutar iste TG:

```
Deployment: php-service
  - Replica 1: v1.2 (stara)
  - Replica 2: v1.2 (stara)
  - Replica 3: v1.3 (nova — canary)
  - Replica 4: v1.2 (stara)

ALB round-robin prema TG: ~25% requestova ide na novi pod
```

```bash
# K8s rolling update sa pause na 25%:
kubectl set image deployment/php-service php=php-fpm:1.3 -n project-a-prod

# Pauzira po defaultu kad maxSurge/maxUnavailable dozvoli
kubectl rollout pause deployment/php-service -n project-a-prod

# Promatraj 15 min, pa nastavi
kubectl rollout resume deployment/php-service -n project-a-prod
```

**Kada koristiti weighted TG vs K8s rolling:** Weighted TG daje precizniji control (možeš reći tačno 5%), K8s rolling je jednostavniji ali granuarnost ovisi o broju replika (4 replika = 25% granularnost).
