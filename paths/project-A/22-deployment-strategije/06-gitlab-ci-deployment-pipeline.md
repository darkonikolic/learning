# 06 — GitLab CI deployment pipeline

## Kompletna pipeline integracija za sve tri strategije

Jedna `.gitlab-ci.yml` konfiguracija koja podržava rolling, blue-green i canary — odabir strategije se radi kroz `DEPLOY_STRATEGY` varijablu.

```yaml
# .gitlab-ci.yml — deployment stages

stages:
  - build
  - test
  - deploy
  - verify

# ─── GLOBALNE VARIJABLE ──────────────────────────────────────────────────────
variables:
  # Promijeni strategiju ovdje ili kroz GitLab UI (Settings → CI/CD → Variables)
  DEPLOY_STRATEGY: rolling          # rolling | blue-green | canary
  NAMESPACE: project-a-prod
  HELM_CHART: ./helm/project-a
  APP_HOST: app.firma.com
  KUBECONFIG_SECRET: KUBECONFIG_PROD   # Naziv GitLab CI/CD varijable s kubeconfig

# ─── BEFORE SCRIPT ────────────────────────────────────────────────────────────
.deploy_defaults: &deploy_defaults
  before_script:
    - echo "$KUBECONFIG_PROD" | base64 -d > /tmp/kubeconfig
    - export KUBECONFIG=/tmp/kubeconfig
    - kubectl config current-context
    - helm version --short
  tags:
    - docker
    - eks-runner    # Runner koji ima pristup EKS clusteru

# ─── ROLLING UPDATE ───────────────────────────────────────────────────────────
deploy:rolling:prod:
  stage: deploy
  <<: *deploy_defaults
  rules:
    - if: '$CI_COMMIT_TAG && $DEPLOY_STRATEGY == "rolling"'
      when: manual
  environment:
    name: production
    url: https://app.firma.com
  script:
    - |
      echo "=== ROLLING UPDATE: $CI_COMMIT_TAG ==="
      helm upgrade --install project-a $HELM_CHART \
        -n $NAMESPACE \
        -f $HELM_CHART/values/prod.yaml \
        --set image.tag=$CI_COMMIT_TAG \
        --atomic \
        --wait \
        --timeout 5m \
        --history-max 5

    # Anotacija za rollout history
    - |
      kubectl annotate deployment/go-service -n $NAMESPACE \
        kubernetes.io/change-cause="$CI_COMMIT_TAG — $CI_COMMIT_TITLE" \
        --overwrite || true
      kubectl annotate deployment/php-service -n $NAMESPACE \
        kubernetes.io/change-cause="$CI_COMMIT_TAG — $CI_COMMIT_TITLE" \
        --overwrite || true

    - kubectl rollout status deployment/go-service -n $NAMESPACE --timeout=3m
    - kubectl rollout status deployment/php-service -n $NAMESPACE --timeout=3m

# ─── BLUE-GREEN ───────────────────────────────────────────────────────────────
deploy:blue-green:prod:
  stage: deploy
  <<: *deploy_defaults
  rules:
    - if: '$CI_COMMIT_TAG && $DEPLOY_STRATEGY == "blue-green"'
      when: manual
  environment:
    name: production
    url: https://app.firma.com
  script:
    - |
      # Odredi koji je trenutno aktivan
      CURRENT=$(kubectl get ingress project-a -n $NAMESPACE \
        -o jsonpath='{.metadata.annotations.current-color}' 2>/dev/null || echo "blue")
      NEW=$([ "$CURRENT" = "blue" ] && echo "green" || echo "blue")
      echo "CURRENT=$CURRENT, NEW=$NEW"

      # Deploy na neaktivni slot
      helm upgrade --install project-a-$NEW $HELM_CHART \
        -n $NAMESPACE \
        -f $HELM_CHART/values/prod.yaml \
        --set deployment.color=$NEW \
        --set image.tag=$CI_COMMIT_TAG \
        --set ingress.enabled=false \
        --wait --timeout 5m

      # Smoke test direktno na novi slot
      kubectl port-forward deployment/project-a-$NEW 18080:80 -n $NAMESPACE &
      PF_PID=$!
      sleep 3

      HTTP_STATUS=$(curl -so /dev/null -w "%{http_code}" http://localhost:18080/health/ready || echo "000")
      kill $PF_PID || true

      if [ "$HTTP_STATUS" != "200" ]; then
        echo "FAIL: Smoke test HTTP $HTTP_STATUS — aborting, deleting $NEW"
        helm uninstall project-a-$NEW -n $NAMESPACE
        exit 1
      fi

      echo "Smoke test passed. Switching ALB to $NEW..."

      # Switch ALB weight
      kubectl annotate ingress project-a -n $NAMESPACE --overwrite \
        "alb.ingress.kubernetes.io/actions.weighted-routing={\"type\":\"forward\",\"forwardConfig\":{\"targetGroups\":[{\"serviceName\":\"project-a-$CURRENT\",\"servicePort\":\"80\",\"weight\":0},{\"serviceName\":\"project-a-$NEW\",\"servicePort\":\"80\",\"weight\":100}]}}"

      kubectl annotate ingress project-a -n $NAMESPACE --overwrite \
        current-color=$NEW

      echo "ALB switched. Sleeping 5 min for in-flight requests on $CURRENT..."
      sleep 300

      helm uninstall project-a-$CURRENT -n $NAMESPACE
      echo "=== BLUE-GREEN DEPLOY COMPLETE: $CI_COMMIT_TAG on $NEW ==="

rollback:blue-green:prod:
  stage: deploy
  <<: *deploy_defaults
  when: manual
  needs: []
  environment:
    name: production
  script:
    - bash scripts/blue-green-rollback.sh $NAMESPACE

# ─── CANARY ───────────────────────────────────────────────────────────────────
deploy:canary:prod:
  stage: deploy
  <<: *deploy_defaults
  rules:
    - if: '$CI_COMMIT_TAG && $DEPLOY_STRATEGY == "canary"'
      when: manual
  environment:
    name: production
    url: https://app.firma.com
  timeout: 60m   # Canary deploy traje duže zbog monitoring perioda
  script:
    - bash scripts/canary-deploy.sh $CI_COMMIT_TAG

rollback:canary:prod:
  stage: deploy
  <<: *deploy_defaults
  when: manual
  needs: []
  environment:
    name: production
  script:
    - bash scripts/canary-rollback.sh $NAMESPACE

# ─── VERIFIKACIJA DEPLOYA ─────────────────────────────────────────────────────
verify:deployment:
  stage: verify
  <<: *deploy_defaults
  needs:
    - job: deploy:rolling:prod
      optional: true
    - job: deploy:blue-green:prod
      optional: true
    - job: deploy:canary:prod
      optional: true
  rules:
    - if: '$CI_COMMIT_TAG'
      when: on_success
  script:
    - |
      echo "=== POST-DEPLOY VERIFICATION ==="
      echo "Monitoring error rate for 5 minutes..."

      FAIL_COUNT=0
      MAX_ERRORS=10   # Tolerancija: max 10 error logova u 30s

      for i in $(seq 1 10); do
        echo "--- Check $i/10 ($(date +%H:%M:%S)) ---"

        # HTTP health check
        HTTP_STATUS=$(curl -so /dev/null -w "%{http_code}" \
          https://$APP_HOST/health/ready || echo "000")

        echo "  Health endpoint: HTTP $HTTP_STATUS"

        if [ "$HTTP_STATUS" != "200" ]; then
          FAIL_COUNT=$((FAIL_COUNT + 1))
          echo "  WARN: Health check failed ($FAIL_COUNT consecutive)"

          if [ "$FAIL_COUNT" -ge 3 ]; then
            echo "  ERROR: 3 consecutive health failures — triggering rollback"
            helm rollback project-a -n $NAMESPACE || true
            exit 1
          fi
        else
          FAIL_COUNT=0
        fi

        # Error log check
        ERROR_COUNT=$(kubectl logs -l app=project-a -n $NAMESPACE \
          --since=30s --all-containers=true 2>/dev/null \
          | grep -c '"level":"error"' || true)

        echo "  Error logs in last 30s: $ERROR_COUNT"

        if [ "$ERROR_COUNT" -gt "$MAX_ERRORS" ]; then
          echo "  ERROR: $ERROR_COUNT errors > threshold $MAX_ERRORS — triggering rollback"
          helm rollback project-a -n $NAMESPACE || true
          exit 1
        fi

        sleep 30
      done

      echo "=== VERIFICATION PASSED: Deployment stable after 5 minutes ==="

# ─── CLEANUP STALE RELEASES ──────────────────────────────────────────────────
cleanup:stale:
  stage: verify
  <<: *deploy_defaults
  when: manual
  needs: []
  script:
    - |
      echo "=== CLEANUP STALE HELM RELEASES ==="
      
      # Prikaži sve release-ove koji nisu u deployed statusu
      helm list -n $NAMESPACE --failed --pending
      
      # Obrisi canary i non-active blue/green ako postoje
      for RELEASE in project-a-canary; do
        if helm status $RELEASE -n $NAMESPACE &>/dev/null; then
          echo "Deleting stale release: $RELEASE"
          helm uninstall $RELEASE -n $NAMESPACE
        fi
      done
      
      echo "Cleanup complete."
```

---

## Skripte (moraju biti u repozitoriju)

### scripts/blue-green-deploy.sh

```bash
#!/bin/bash
# Upotreba: bash scripts/blue-green-deploy.sh <current_color> <new_color> <namespace>
set -euo pipefail

CURRENT=${1:?"Nedostaje current color (blue|green)"}
NEW=${2:?"Nedostaje new color (blue|green)"}
NAMESPACE=${3:-project-a-prod}

echo "Switching ALB: $CURRENT → $NEW"

kubectl annotate ingress project-a -n "$NAMESPACE" --overwrite \
  "alb.ingress.kubernetes.io/actions.weighted-routing={\"type\":\"forward\",\"forwardConfig\":{\"targetGroups\":[{\"serviceName\":\"project-a-$CURRENT\",\"servicePort\":\"80\",\"weight\":0},{\"serviceName\":\"project-a-$NEW\",\"servicePort\":\"80\",\"weight\":100}]}}"

kubectl annotate ingress project-a -n "$NAMESPACE" --overwrite \
  current-color="$NEW"

echo "Done. 100% traffic on project-a-$NEW"
```

### scripts/blue-green-rollback.sh

```bash
#!/bin/bash
# Upotreba: bash scripts/blue-green-rollback.sh <namespace>
set -euo pipefail

NAMESPACE=${1:-project-a-prod}

CURRENT=$(kubectl get ingress project-a -n "$NAMESPACE" \
  -o jsonpath='{.metadata.annotations.current-color}' 2>/dev/null || echo "green")
PREVIOUS=$([ "$CURRENT" = "green" ] && echo "blue" || echo "green")

echo "=== ROLLBACK: $CURRENT → $PREVIOUS ==="

# Provjeri da previous release postoji
if ! helm status project-a-$PREVIOUS -n "$NAMESPACE" &>/dev/null; then
  echo "ERROR: project-a-$PREVIOUS release ne postoji — ne mogu rollbackati"
  echo "Dostupni release-ovi:"
  helm list -n "$NAMESPACE"
  exit 1
fi

kubectl annotate ingress project-a -n "$NAMESPACE" --overwrite \
  "alb.ingress.kubernetes.io/actions.weighted-routing={\"type\":\"forward\",\"forwardConfig\":{\"targetGroups\":[{\"serviceName\":\"project-a-$PREVIOUS\",\"servicePort\":\"80\",\"weight\":100},{\"serviceName\":\"project-a-$CURRENT\",\"servicePort\":\"80\",\"weight\":0}]}}"

kubectl annotate ingress project-a -n "$NAMESPACE" --overwrite \
  current-color="$PREVIOUS"

echo "Rollback complete. 100% traffic on project-a-$PREVIOUS"
```

---

## GitLab CI varijable koje treba podesiti

| Varijabla | Tip | Opis |
|-----------|-----|------|
| `KUBECONFIG_PROD` | File / base64 string | Kubeconfig za pristup EKS clusteru |
| `DEPLOY_STRATEGY` | Variable | `rolling`, `blue-green`, ili `canary` |
| `ACM_ARN` | Variable | AWS Certificate Manager ARN za HTTPS |
| `REGISTRY_USER` | Variable | Container registry korisničko ime |
| `REGISTRY_PASSWORD` | Masked variable | Container registry lozinka |

Postavljanje u GitLab UI: `Settings → CI/CD → Variables → Add variable`

`KUBECONFIG_PROD` kao base64:
```bash
cat ~/.kube/config | base64 -w 0
# Kopiraj output i spremi kao GitLab varijablu
```

---

## Monitoring integracija

Tokom deployment pipelina, korisno je imati Grafana annotations:

```bash
# Dodaj Grafana anotaciju na početku deploya
curl -s -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $GRAFANA_TOKEN" \
  -d "{
    \"tags\": [\"deploy\", \"$DEPLOY_STRATEGY\", \"$CI_COMMIT_TAG\"],
    \"text\": \"Deploy: $CI_COMMIT_TAG ($DEPLOY_STRATEGY) — $CI_COMMIT_TITLE\",
    \"time\": $(date +%s)000
  }" \
  "https://grafana.firma.com/api/annotations"
```

Ovo ti daje vertikalnu liniju na Grafana grafovima na momentu deploya — odmah vidiš korelaciju između deploya i promjena u metrikama (error rate, latencija, throughput).
