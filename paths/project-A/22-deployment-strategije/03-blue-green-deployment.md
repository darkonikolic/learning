# 03 — Blue-Green Deployment

## Koncept

```
Blue  = trenutno u produkciji, prima 100% saobraćaja
Green = nova verzija, deployovana ali ne prima saobraćaj

ALB: 100% → Blue

Korak 1: Deploy green, testiraj direktno (port-forward)
Korak 2: ALB: 100% → Green (instant switch, < 1 sekunda)
Korak 3: Monitoruj 5 minuta
Korak 4a: Sve OK → obrisi blue
Korak 4b: Problem → ALB: 100% → Blue (instant rollback)
```

Ključna prednost: rollback je promjena jedne anotacije na Ingress resursu. Nema čekanja na pod startup, nema Rolling Update — instant.

---

## Implementacija: Helm + AWS ALB

### Korak 1: Deploy green (ne prima saobraćaj)

```bash
# Green se deploya bez Ingress-a — ALB ga ne vidi
helm upgrade --install project-a-green ./helm/project-a \
  -n project-a-prod \
  -f helm/project-a/values/prod.yaml \
  --set deployment.color=green \
  --set image.tag=v1.2.0 \
  --set ingress.enabled=false \
  --wait --timeout 5m

# Provjeri da su svi podovi Running i Ready
kubectl get pods -l app=project-a,color=green -n project-a-prod
# NAME                              READY   STATUS    RESTARTS
# project-a-green-6d8f9b7c4-abc12   1/1     Running   0
# project-a-green-6d8f9b7c4-def34   1/1     Running   0
# project-a-green-6d8f9b7c4-ghi56   1/1     Running   0
```

### Korak 2: Smoke test na green direktno

```bash
# Port-forward direktno na green deployment — zaobiđe ALB
kubectl port-forward deployment/project-a-green 8080:80 -n project-a-prod &
PF_PID=$!

sleep 2  # Čekaj da se port-forward uspostavi

# Zdravstvena provjera
curl -sf http://localhost:8080/health/ready || {
  echo "FAIL: Green health check failed — ne prebacujem saobraćaj"
  kill $PF_PID
  helm uninstall project-a-green -n project-a-prod
  exit 1
}

# API smoke test
curl -sf http://localhost:8080/api/v1/status | python3 -m json.tool || {
  echo "FAIL: API smoke test failed"
  kill $PF_PID
  exit 1
}

kill $PF_PID
echo "Green smoke tests passed."
```

---

## ALB Weighted Routing Ingress

AWS ALB Ingress Controller podržava weighted target groups direktno kroz anotacije.

```yaml
# helm/project-a/templates/ingress-blue-green.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: project-a
  namespace: project-a-prod
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/certificate-arn: {{ .Values.ingress.certificateArn }}
    alb.ingress.kubernetes.io/ssl-redirect: "443"
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTP": 80}, {"HTTPS": 443}]'
    alb.ingress.kubernetes.io/healthcheck-path: /health/ready
    alb.ingress.kubernetes.io/healthcheck-interval-seconds: "10"
    alb.ingress.kubernetes.io/healthy-threshold-count: "2"
    # Weighted routing action — blue 100%, green 0%
    alb.ingress.kubernetes.io/actions.weighted-routing: |
      {
        "type": "forward",
        "forwardConfig": {
          "targetGroups": [
            {
              "serviceName": "project-a-blue",
              "servicePort": "80",
              "weight": 100
            },
            {
              "serviceName": "project-a-green",
              "servicePort": "80",
              "weight": 0
            }
          ],
          "targetGroupStickinessConfig": {
            "enabled": false
          }
        }
      }
    # Pratimo koji je trenutno aktivan (za CI/CD skripte)
    current-color: blue
spec:
  rules:
    - host: app.firma.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: weighted-routing
                port:
                  name: use-annotation
```

Napomena: `name: weighted-routing` mora odgovarati imenu anotacije `alb.ingress.kubernetes.io/actions.weighted-routing`. Ovo je ALB Ingress Controller konvencija — ne referencira se stvarni Service tog imena.

---

## Korak 3: Switch saobraćaja na green

```bash
# Prebaci 100% saobraćaja na green
kubectl annotate ingress project-a -n project-a-prod --overwrite \
  'alb.ingress.kubernetes.io/actions.weighted-routing={"type":"forward","forwardConfig":{"targetGroups":[{"serviceName":"project-a-blue","servicePort":"80","weight":0},{"serviceName":"project-a-green","servicePort":"80","weight":100}]}}'

# Ažuriraj tracker
kubectl annotate ingress project-a -n project-a-prod --overwrite \
  current-color=green

echo "Traffic switched to green. Monitoring for 5 minutes..."
```

---

## Korak 4a: Verifikacija i cleanup

```bash
# Provjeri HTTP status s produkcijskog URL-a
for i in $(seq 1 6); do
  STATUS=$(curl -so /dev/null -w "%{http_code}" https://app.firma.com/health/ready)
  echo "$(date +%H:%M:%S) — HTTP $STATUS"
  [ "$STATUS" != "200" ] && {
    echo "ERROR: Health check failed — pokretanje rollbacka"
    bash scripts/blue-green-rollback.sh project-a-prod
    exit 1
  }
  sleep 30
done

# Ako je sve OK, obrisi blue
# Čekaj 5 minuta za in-flight zahtjeve koji su eventualno još na podu
sleep 300
helm uninstall project-a-blue -n project-a-prod
echo "Blue environment deleted. Green is now stable."
```

---

## Korak 4b: Instant rollback

```bash
# scripts/blue-green-rollback.sh
#!/bin/bash
NAMESPACE=${1:-project-a-prod}

echo "=== BLUE-GREEN ROLLBACK ==="
echo "Switching 100% traffic back to blue..."

kubectl annotate ingress project-a -n $NAMESPACE --overwrite \
  'alb.ingress.kubernetes.io/actions.weighted-routing={"type":"forward","forwardConfig":{"targetGroups":[{"serviceName":"project-a-blue","servicePort":"80","weight":100},{"serviceName":"project-a-green","servicePort":"80","weight":0}]}}'

kubectl annotate ingress project-a -n $NAMESPACE --overwrite \
  current-color=blue

echo "Rollback complete. All traffic on blue."
echo "Check: https://app.firma.com/health/ready"
```

---

## Helm chart template za blue/green

Deployment template mora koristiti color label da bi blue i green bili neovisni:

```yaml
# helm/project-a/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: project-a-{{ .Values.deployment.color | default "blue" }}
  namespace: {{ .Release.Namespace }}
  labels:
    app: project-a
    color: {{ .Values.deployment.color | default "blue" }}
    version: {{ .Values.image.tag }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      app: project-a
      color: {{ .Values.deployment.color | default "blue" }}
  template:
    metadata:
      labels:
        app: project-a
        color: {{ .Values.deployment.color | default "blue" }}
        version: {{ .Values.image.tag }}
    spec:
      containers:
        - name: app
          image: registry.firma.com/project-a/app:{{ .Values.image.tag }}
          # ...
```

```yaml
# helm/project-a/templates/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: project-a-{{ .Values.deployment.color | default "blue" }}
  namespace: {{ .Release.Namespace }}
spec:
  selector:
    app: project-a
    color: {{ .Values.deployment.color | default "blue" }}
  ports:
    - name: http
      port: 80
      targetPort: 8080
```

---

## GitLab CI blue-green pipeline

```yaml
# .gitlab-ci.yml — blue-green deploy job

deploy:blue-green:prod:
  stage: deploy
  rules:
    - if: '$CI_COMMIT_TAG && $DEPLOY_STRATEGY == "blue-green"'
      when: manual
  environment:
    name: production
    url: https://app.firma.com
  script:
    # Odredi koji je trenutno aktivan
    - |
      CURRENT=$(kubectl get ingress project-a -n project-a-prod \
        -o jsonpath='{.metadata.annotations.current-color}' 2>/dev/null || echo "blue")
      NEW=$([ "$CURRENT" = "blue" ] && echo "green" || echo "blue")
      echo "CURRENT=$CURRENT" >> deploy.env
      echo "NEW=$NEW" >> deploy.env
      echo "Deploying $CI_COMMIT_TAG to $NEW (current: $CURRENT)"

    # Deploy nova verzija na neaktivni slot
    - |
      source deploy.env
      helm upgrade --install project-a-$NEW ./helm/project-a \
        -n project-a-prod \
        -f helm/project-a/values/prod.yaml \
        --set deployment.color=$NEW \
        --set image.tag=$CI_COMMIT_TAG \
        --set ingress.enabled=false \
        --wait --timeout 5m

    # Smoke test
    - |
      source deploy.env
      kubectl port-forward deployment/project-a-$NEW 18080:80 -n project-a-prod &
      sleep 3
      curl -sf http://localhost:18080/health/ready || {
        helm uninstall project-a-$NEW -n project-a-prod
        echo "Smoke test failed — aborting deploy"
        exit 1
      }
      kill %1

    # Switch ALB
    - |
      source deploy.env
      bash scripts/blue-green-deploy.sh $CURRENT $NEW project-a-prod

    # Cleanup starog slota nakon stabilizacije (async — ne blokira pipeline)
    - |
      source deploy.env
      echo "Old slot ($CURRENT) will be cleaned up in 5 minutes..."
      (sleep 300 && helm uninstall project-a-$CURRENT -n project-a-prod) &

  artifacts:
    reports:
      dotenv: deploy.env

rollback:blue-green:prod:
  stage: deploy
  when: manual
  needs: []
  environment:
    name: production
  script:
    - bash scripts/blue-green-rollback.sh project-a-prod
```

---

## Tradeoffi Blue-Green

**Prednosti:**
- Rollback instant (< 1s) — promjena ALB weight anotacije
- Nema mixed-version perioda — korisnici uvijek dobijaju jednu verziju
- Testiraš zeleno okruženje u cijelosti prije nego puštaš saobraćaj

**Nedostaci:**
- 2x resursi tokom deploya (kratko, ali postoji)
- Kompleksniji Helm setup (dvije release instance)
- Stateful servisi (DB konekcije) trebaju pažnju pri switchu — connection pool se ne resetuje
- DB schema mora biti backward-compatible (ili koristiš Recreate za stateful sloj)
