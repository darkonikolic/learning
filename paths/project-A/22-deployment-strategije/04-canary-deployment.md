# 04 — Canary Deployment

## Koncept

```
Stable: 90% saobraćaja → stara verzija (v1.1.0)
Canary: 10% saobraćaja → nova verzija (v1.2.0)

Postepeni rollout:
  10% → monitoruj metrike → 25% → monitoruj → 50% → 75% → 100%
  
Svaki korak: provjeri error rate, latenciju, business metrike
Ako nešto nije u redu: canary weight → 0% (instant rollback)
```

Canary je pravi alat kad imaš: visok saobraćaj, rizičnu promjenu, ili trebaš A/B podatke. Izlažeš promjenu malom postotku korisnika i automatski ili manualno odlučuješ da li nastaviš.

---

## Helm setup za canary

```yaml
# helm/project-a/values/prod-canary.yaml
# Override vrijednosti za canary deploy
deployment:
  color: canary

replicaCount: 1   # Canary treba mali broj replika (10% weight ≠ 10% replika)

# Canary ne kreira vlastiti Ingress — ALB ga uključuje kroz weight na stable Ingress
ingress:
  enabled: false

# Canary može imati drugačije resource limite (opcionalno)
resources:
  requests:
    cpu: "100m"
    memory: "128Mi"
  limits:
    cpu: "500m"
    memory: "256Mi"
```

Bitna napomena: ALB weight je postotak HTTP zahtjeva (layer 7), ne postotak replika. Možeš imati 1 canary pod i 3 stable poda, a ALB će svejedno slati tačno 10% zahtjeva na canary Service (koji ga prosljeđuje jedinom podu).

---

## Canary deploy skripta

```bash
#!/bin/bash
# scripts/canary-deploy.sh
# Upotreba: bash scripts/canary-deploy.sh v1.2.0

set -euo pipefail

CANARY_TAG=${1:?"Nedostaje image tag. Upotreba: $0 <tag>"}
NAMESPACE="project-a-prod"
APP_HOST="app.firma.com"

# Postepeni rollout: 10% → 25% → 50% → 75% → 100%
WEIGHTS=(10 25 50 75 100)
MONITOR_SECONDS=300   # 5 minuta na svakom koraku
ERROR_THRESHOLD=0.05  # 5% error rate → rollback

echo "=== CANARY DEPLOY: $CANARY_TAG ==="

# ── KORAK 1: Deploy canary ─────────────────────────────────────────────────
echo "Deploying canary..."
helm upgrade --install project-a-canary ./helm/project-a \
  -n "$NAMESPACE" \
  -f helm/project-a/values/prod.yaml \
  -f helm/project-a/values/prod-canary.yaml \
  --set image.tag="$CANARY_TAG" \
  --wait --timeout 5m

echo "Canary pods ready. Starting gradual rollout..."

# ── KORAK 2: Postepeni rollout ─────────────────────────────────────────────
rollback_canary() {
  echo ">>> ROLLBACK: Setting canary weight to 0%..."
  kubectl annotate ingress project-a -n "$NAMESPACE" --overwrite \
    'alb.ingress.kubernetes.io/actions.weighted-routing={"type":"forward","forwardConfig":{"targetGroups":[{"serviceName":"project-a-stable","servicePort":"80","weight":100},{"serviceName":"project-a-canary","servicePort":"80","weight":0}]}}'
  echo ">>> Deleting canary release..."
  helm uninstall project-a-canary -n "$NAMESPACE" || true
  echo ">>> Rollback complete. 100% traffic on stable."
}

# Hvataj Ctrl+C i greške
trap rollback_canary ERR INT TERM

for WEIGHT in "${WEIGHTS[@]}"; do
  STABLE_WEIGHT=$((100 - WEIGHT))

  echo ""
  echo "── Setting canary to $WEIGHT% (stable: $STABLE_WEIGHT%) ──"

  kubectl annotate ingress project-a -n "$NAMESPACE" --overwrite \
    "alb.ingress.kubernetes.io/actions.weighted-routing={\"type\":\"forward\",\"forwardConfig\":{\"targetGroups\":[{\"serviceName\":\"project-a-stable\",\"servicePort\":\"80\",\"weight\":$STABLE_WEIGHT},{\"serviceName\":\"project-a-canary\",\"servicePort\":\"80\",\"weight\":$WEIGHT}]}}"

  if [ "$WEIGHT" -eq 100 ]; then
    echo "Canary at 100% — deployment complete."
    break
  fi

  echo "Monitoring $MONITOR_SECONDS seconds at $WEIGHT%..."

  START=$(date +%s)
  while [ $(($(date +%s) - START)) -lt $MONITOR_SECONDS ]; do

    # Provjeri error rate putem Prometheus query
    ERROR_RATE=$(kubectl exec -n monitoring deploy/prometheus \
      -- wget -qO- \
      "http://localhost:9090/api/v1/query?query=rate(http_requests_total%7Bstatus%3D~%225..%22%2Cservice%3D%22project-a-canary%22%7D%5B1m%5D)%2Frate(http_requests_total%7Bservice%3D%22project-a-canary%22%7D%5B1m%5D)" \
      2>/dev/null \
      | python3 -c "
import sys, json
data = json.load(sys.stdin)
results = data.get('data', {}).get('result', [])
print(float(results[0]['value'][1]) if results else 0.0)
" 2>/dev/null || echo "0.0")

    echo "  $(date +%H:%M:%S) — Error rate: ${ERROR_RATE}"

    if python3 -c "import sys; sys.exit(0 if float('$ERROR_RATE') > $ERROR_THRESHOLD else 1)" 2>/dev/null; then
      echo "ERROR: Error rate ${ERROR_RATE} > ${ERROR_THRESHOLD} — ROLLBACK"
      rollback_canary
      exit 1
    fi

    # Provjeri i HTTP status direktno
    HTTP_STATUS=$(curl -so /dev/null -w "%{http_code}" "https://$APP_HOST/health/ready" || echo "000")
    if [ "$HTTP_STATUS" != "200" ]; then
      echo "ERROR: Health check returned HTTP $HTTP_STATUS — ROLLBACK"
      rollback_canary
      exit 1
    fi

    sleep 30
  done

  echo "Monitoring passed at $WEIGHT%. Proceeding to next step."
done

# ── KORAK 3: Promoviši canary na stable ────────────────────────────────────
echo ""
echo "=== PROMOTING CANARY TO STABLE ==="

helm upgrade project-a-stable ./helm/project-a \
  -n "$NAMESPACE" \
  -f helm/project-a/values/prod.yaml \
  --set image.tag="$CANARY_TAG" \
  --wait --timeout 5m

# Vrati routing na stable (sad je stable nova verzija)
kubectl annotate ingress project-a -n "$NAMESPACE" --overwrite \
  'alb.ingress.kubernetes.io/actions.weighted-routing={"type":"forward","forwardConfig":{"targetGroups":[{"serviceName":"project-a-stable","servicePort":"80","weight":100},{"serviceName":"project-a-canary","servicePort":"80","weight":0}]}}'

helm uninstall project-a-canary -n "$NAMESPACE"

echo "=== CANARY PROMOTED TO STABLE: $CANARY_TAG ==="
```

---

## Canary rollback skripta

```bash
#!/bin/bash
# scripts/canary-rollback.sh
# Upotreba: bash scripts/canary-rollback.sh project-a-prod

NAMESPACE=${1:-project-a-prod}

echo "=== CANARY ROLLBACK ==="
echo "Setting canary weight to 0%..."

kubectl annotate ingress project-a -n "$NAMESPACE" --overwrite \
  'alb.ingress.kubernetes.io/actions.weighted-routing={"type":"forward","forwardConfig":{"targetGroups":[{"serviceName":"project-a-stable","servicePort":"80","weight":100},{"serviceName":"project-a-canary","servicePort":"80","weight":0}]}}'

# Obrisi canary release
helm uninstall project-a-canary -n "$NAMESPACE" 2>/dev/null || echo "Canary release not found (already cleaned up)"

echo "Rollback complete. 100% traffic on stable."
```

---

## Nginx Ingress Controller alternativa (lokalni kind)

AWS ALB nije dostupan lokalno. Za testiranje na kind clusterima s nginx-ingress:

```yaml
# Stable Ingress (ne treba posebne anotacije)
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: project-a-stable
  namespace: project-a-local
  annotations:
    kubernetes.io/ingress.class: nginx
spec:
  rules:
    - host: app.local
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: project-a-stable
                port:
                  number: 80
```

```yaml
# Canary Ingress — nginx canary anotacije
# Mora biti isti host i path kao stable Ingress
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: project-a-canary
  namespace: project-a-local
  annotations:
    kubernetes.io/ingress.class: nginx
    nginx.ingress.kubernetes.io/canary: "true"
    nginx.ingress.kubernetes.io/canary-weight: "10"  # 10% requestova na canary
    # Alternativno: canary po headeru (za QA testiranje)
    # nginx.ingress.kubernetes.io/canary-by-header: "X-Canary"
    # nginx.ingress.kubernetes.io/canary-by-header-value: "true"
spec:
  rules:
    - host: app.local
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: project-a-canary
                port:
                  number: 80
```

Promjena weight lokalno (bez skripte):
```bash
# Povećaj canary weight na 25%
kubectl annotate ingress project-a-canary -n project-a-local --overwrite \
  nginx.ingress.kubernetes.io/canary-weight=25
```

---

## Header-based canary (za QA tim)

Korisno kad QA tim treba testirati canary verziju bez utjecaja na produkcijske korisnike:

```yaml
# AWS ALB: header-based routing
alb.ingress.kubernetes.io/conditions.canary-header: |
  [
    {
      "field": "http-header",
      "httpHeaderConfig": {
        "httpHeaderName": "X-Canary",
        "values": ["true"]
      }
    }
  ]
```

QA testira slanjem: `curl -H "X-Canary: true" https://app.firma.com/api/v1/test`

---

## Tradeoffi Canary

**Prednosti:**
- Najsigurnija strategija za rizične promjene — izlažeš samo mali postotak korisnika
- Automatski rollback na osnovu metrika (error rate, latencija)
- Idealno za A/B testiranje novih feature-a
- Rollback instant (weight → 0%)

**Nedostaci:**
- Najkompleksnija implementacija
- Zahtijeva dobro podešen monitoring (Prometheus + alerting)
- Duže traje (više koraka × monitoring period = 20-40 minuta za kompletan deploy)
- Stari i novi kod rade istovremeno — isti DB schema zahtjevi kao Rolling Update
- ALB weighted routing anotacije su verbose i podložne greškama u kucanju

**Kada koristiti za ovaj projekt:**
- Nova Vue komponenta s drastično drugačijim API pozivima
- Promjena u go-service koja mijenja algoritam (npr. novi caching pristup)
- Bilo koja promjena za koju ne znaš tačno kako će reagirati pod produkcijskim opterećenjem
