# Environment lifecycle management — pipeline-driven

Kompletan ciklus: **create → deploy → discover URLs → destroy**. Sve radi i kroz GitLab pipeline (UI) i sa lokalne mašine (isti skripti).

## Arhitektura lifecycle-a

```
Manual trigger (GitLab UI)
        │
        ▼
  create:env:dev          ← terraform apply + K8s controllers
        │
        ▼
  migrate:dev             ← golang-migrate up (auto)
        │
        ▼
  deploy:dev              ← helm upgrade --atomic (auto na main)
        │
        ▼
  env:info:dev            ← discover URLs, print status (manual, any time)
        │
        ▼
  destroy:env:dev         ← terraform destroy (manual ili scheduled)
```

---

## .gitlab-ci.yml — kompletan environment lifecycle

```yaml
# Environment lifecycle stages
stages:
  - validate
  - build
  - test
  - env-create    # NEW: create AWS environment
  - migrate
  - deploy
  - verify
  - env-info      # NEW: show all URLs and status
  - env-destroy   # NEW: destroy environment

# ── ENVIRONMENT CREATE ──────────────────────────────────────────────────────

.tf_base:
  image:
    name: hashicorp/terraform:1.7
    entrypoint: [""]
  before_script:
    - apk add --no-cache aws-cli kubectl helm curl bash
    - aws sts assume-role-with-web-identity
        --role-arn "$AWS_ROLE_ARN"
        --role-session-name "gitlab-ci-${CI_PIPELINE_ID}"
        --web-identity-token "$AWS_OIDC_TOKEN"
        --duration-seconds 3600 > /tmp/aws_creds.json
    - export AWS_ACCESS_KEY_ID=$(jq -r '.Credentials.AccessKeyId' /tmp/aws_creds.json)
    - export AWS_SECRET_ACCESS_KEY=$(jq -r '.Credentials.SecretAccessKey' /tmp/aws_creds.json)
    - export AWS_SESSION_TOKEN=$(jq -r '.Credentials.SessionToken' /tmp/aws_creds.json)
  id_tokens:
    AWS_OIDC_TOKEN:
      aud: https://gitlab.com

create:env:dev:
  extends: .tf_base
  stage: env-create
  when: manual
  allow_failure: false
  environment:
    name: development
    url: https://app.dev.firma.com
    on_stop: destroy:env:dev
  variables:
    AWS_ROLE_ARN: $DEV_AWS_ROLE_ARN
    TF_ENV: dev
  script:
    - echo "=== Creating DEV environment ==="

    # Terraform apply
    - cd terraform/envs/dev
    - terraform init -backend-config="bucket=${TF_STATE_BUCKET}" -backend-config="key=dev/terraform.tfstate"
    - terraform plan -var-file=dev.tfvars -out=plan.tfplan
    - terraform apply plan.tfplan

    # Save outputs for next jobs
    - terraform output -json > /tmp/tf_outputs.json
    - echo "EKS_CLUSTER_NAME=$(terraform output -raw cluster_name)" >> create.env
    - echo "AWS_REGION=$(terraform output -raw aws_region)" >> create.env

    # Configure kubectl
    - aws eks update-kubeconfig
        --name "$(terraform output -raw cluster_name)"
        --region "$(terraform output -raw aws_region)"
        --alias dev

    # Install ALB Controller
    - helm upgrade --install aws-load-balancer-controller eks/aws-load-balancer-controller
        --namespace kube-system
        --set clusterName="$(terraform output -raw cluster_name)"
        --set serviceAccount.annotations."eks\.amazonaws\.com/role-arn"="$(terraform output -raw alb_controller_role_arn)"
        --wait --timeout 5m

    # Install cert-manager
    - helm upgrade --install cert-manager jetstack/cert-manager
        --namespace cert-manager --create-namespace
        --set installCRDs=true
        --wait --timeout 5m

    # Install External Secrets Operator
    - helm upgrade --install external-secrets external-secrets/external-secrets
        --namespace external-secrets --create-namespace
        --wait --timeout 5m

    - echo "=== DEV environment created ==="
  artifacts:
    reports:
      dotenv: create.env
    expire_in: 1 day

create:env:staging:
  extends: create:env:dev
  environment:
    name: staging
    url: https://app.staging.firma.com
    on_stop: destroy:env:staging
  variables:
    AWS_ROLE_ARN: $STAGING_AWS_ROLE_ARN
    TF_ENV: staging
  script:
    - cd terraform/envs/staging
    - terraform init -backend-config="bucket=${TF_STATE_BUCKET}" -backend-config="key=staging/terraform.tfstate"
    - terraform apply -var-file=staging.tfvars -auto-approve
    # ... isti pattern

# ── DEPLOY ──────────────────────────────────────────────────────────────────

.deploy_base:
  image: alpine/helm:3.14
  before_script:
    - apk add --no-cache aws-cli curl jq bash
    # AWS auth (isti pattern kao tf_base)
    - echo "$KUBE_CONFIG" | base64 -d > ~/.kube/config

deploy:dev:
  extends: .deploy_base
  stage: deploy
  needs: [build:images, migrate:dev]
  environment:
    name: development
    url: https://app.dev.firma.com
  variables:
    AWS_ROLE_ARN: $DEV_AWS_ROLE_ARN
  script:
    - echo "=== Deploying to DEV ==="

    # Create namespace if not exists
    - kubectl create namespace project-a-dev --dry-run=client -o yaml | kubectl apply -f -

    # Deploy app
    - helm upgrade --install project-a ./helm/project-a
        --namespace project-a-dev
        -f helm/project-a/values/dev.yaml
        --set goService.image.tag=$CI_COMMIT_SHA
        --set phpService.image.tag=$CI_COMMIT_SHA
        --set notificationService.image.tag=$CI_COMMIT_SHA
        --set frontend.image.tag=$CI_COMMIT_SHA
        --wait --timeout 5m --atomic

    # Deploy monitoring
    - helm upgrade --install monitoring prometheus-community/kube-prometheus-stack
        --namespace monitoring --create-namespace
        -f helm/monitoring/values-dev.yaml
        --wait --timeout 10m

    # Seed database (first deploy only)
    - kubectl exec -n project-a-dev deployment/go-service --
        /server seed --if-empty 2>/dev/null || true

    # Discover and print URLs
    - bash scripts/get-urls.sh dev

    - echo "=== Deploy complete ==="

# ── ENV INFO (discover URLs) ─────────────────────────────────────────────────

env:info:dev:
  stage: env-info
  image: alpine:3.19
  needs: []
  when: manual
  allow_failure: true
  environment:
    name: development
  script:
    - apk add --no-cache kubectl aws-cli jq
    - echo "$KUBE_CONFIG_DEV" | base64 -d > ~/.kube/config

    - echo "========================================"
    - echo "=== PROJECT-A DEV ENVIRONMENT INFO ==="
    - echo "========================================"
    - echo ""

    - echo "--- APPLICATION ---"
    - APP_URL=$(kubectl get ingress project-a -n project-a-dev
        -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "Not deployed")
    - echo "App URL:        https://$APP_URL"

    - echo ""
    - echo "--- MONITORING ---"
    - GF_URL=$(kubectl get ingress -n monitoring
        -l app.kubernetes.io/name=grafana
        -o jsonpath='{.items[0].status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "Not installed")
    - echo "Grafana:        https://$GF_URL"

    - echo ""
    - echo "--- MAILPIT (email testing) ---"
    - MAIL_URL=$(kubectl get ingress mailpit -n project-a-dev
        -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "Not installed")
    - echo "Mailpit:        https://$MAIL_URL"

    - echo ""
    - echo "--- KUBERNETES ---"
    - echo "Nodes:"
    - kubectl get nodes --no-headers | awk '{print "  "$1" ("$5")"}'
    - echo ""
    - echo "Pods:"
    - kubectl get pods -n project-a-dev --no-headers |
        awk '{print "  "$1" ["$3"]"}'

    - echo ""
    - echo "--- AWS RESOURCES ---"
    - echo "EKS Cluster:    $(aws eks list-clusters --query 'clusters[?contains(@,`project-a-dev`)]|[0]' --output text)"
    - echo "RDS:            $(aws rds describe-db-instances --query 'DBInstances[?contains(DBInstanceIdentifier,`dev`)].DBInstanceStatus' --output text)"

    - echo ""
    - echo "--- ESTIMATED DAILY COST ---"
    - echo "  (Run: aws ce get-cost-and-usage for exact figures)"
    - echo "  EKS node (t3.medium x1): ~\$1.13/day"
    - echo "  RDS (t3.micro):          ~\$0.82/day"
    - echo "  NAT Gateway:             ~\$1.08/day"
    - echo "  ALB:                     ~\$0.53/day"
    - echo "  Total est.:              ~\$3.56/day"
    - echo "========================================"

# ── ENV DESTROY ──────────────────────────────────────────────────────────────

destroy:env:dev:
  extends: .tf_base
  stage: env-destroy
  when: manual
  allow_failure: false
  environment:
    name: development
    action: stop
  variables:
    AWS_ROLE_ARN: $DEV_AWS_ROLE_ARN
  script:
    - echo "=== Destroying DEV environment ==="

    # Step 1: Uninstall Helm releases (removes ALB)
    - echo "$KUBE_CONFIG_DEV" | base64 -d > ~/.kube/config
    - helm uninstall project-a -n project-a-dev 2>/dev/null || true
    - helm uninstall monitoring -n monitoring 2>/dev/null || true
    - helm uninstall aws-load-balancer-controller -n kube-system 2>/dev/null || true

    # Step 2: Wait for ALB deletion (max 3 min)
    - echo "Waiting for ALB to be deleted..."
    - |
      TIMEOUT=180
      START=$SECONDS
      while aws elbv2 describe-load-balancers \
          --query "LoadBalancers[?contains(LoadBalancerName,'project-a-dev')]" \
          --output text 2>/dev/null | grep -q .; do
        [ $((SECONDS-START)) -gt $TIMEOUT ] && { echo "ALB timeout - continuing"; break; }
        sleep 10
        echo "Still waiting..."
      done
    - echo "ALB removed."

    # Step 3: Terraform destroy
    - cd terraform/envs/dev
    - terraform init -backend-config="bucket=${TF_STATE_BUCKET}" -backend-config="key=dev/terraform.tfstate"
    - terraform destroy -var-file=dev.tfvars -auto-approve

    # Step 4: Verify
    - echo "=== POST-DESTROY VERIFICATION ==="
    - aws eks list-clusters --query "clusters[?contains(@,'project-a-dev')]" --output text | grep -q . && echo "WARNING: EKS still exists!" || echo "✓ EKS deleted"
    - aws rds describe-db-instances --query "DBInstances[?contains(DBInstanceIdentifier,'project-a-dev')].DBInstanceStatus" --output text | grep -q . && echo "WARNING: RDS still exists!" || echo "✓ RDS deleted"
    - echo "========================================"
    - echo "=== DEV ENVIRONMENT DESTROYED ==="
    - echo "Monthly savings: ~\$107 (if running 30 days)"
    - echo "========================================"

# ── SCHEDULED: Auto-destroy dev every Friday 18:00 ──────────────────────────

destroy:env:dev:scheduled:
  extends: destroy:env:dev
  environment:
    name: development
    action: stop
  rules:
    - if: '$CI_PIPELINE_SOURCE == "schedule" && $SCHEDULE_NAME == "weekly-cleanup"'
  after_script:
    - |
      curl -X POST -H 'Content-type: application/json' \
        --data '{"text":"🧹 Dev environment destroyed (weekly cleanup). Recreate: GitLab → Pipeline → create:env:dev"}' \
        $SLACK_WEBHOOK_URL 2>/dev/null || true
```

---

## Lokalna egzekucija — isti skripti, bez pipeline

Svaki pipeline job može se izvršiti lokalno. Nema razlike u logici — samo nema GitLab context varijabli.

```bash
# Kreiraj environment lokalno
export AWS_PROFILE=project-a-dev
cd terraform/envs/dev
terraform apply -var-file=dev.tfvars
aws eks update-kubeconfig --name project-a-dev --region eu-west-1

# Deploy lokalno
helm upgrade --install project-a ./helm/project-a \
  --namespace project-a-dev \
  -f helm/project-a/values/dev.yaml \
  --set goService.image.tag=$(git rev-parse --short HEAD)

# Discover URLs
bash scripts/get-urls.sh dev

# Destroy lokalno
bash scripts/total-destroy.sh dev
```

---

## scripts/get-urls.sh

Skript koji koriste i pipeline i lokalna mašina:

```bash
#!/usr/bin/env bash
# scripts/get-urls.sh <env>
set -euo pipefail

ENV=${1:-dev}
NS="project-a-${ENV}"

echo "========================================"
echo "=== PROJECT-A ${ENV^^} URLS ==="
echo "========================================"

get_ingress_host() {
  local name=$1 ns=$2
  kubectl get ingress "$name" -n "$ns" \
    -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null \
    || echo "pending..."
}

APP=$(get_ingress_host project-a "$NS")
GF=$(kubectl get ingress -n monitoring \
  -l app.kubernetes.io/name=grafana \
  -o jsonpath='{.items[0].status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "not installed")
MAIL=$(get_ingress_host mailpit "$NS")

echo ""
echo "  App:      https://${APP}"
echo "  Grafana:  https://${GF}"
echo "  Mailpit:  https://${MAIL}"
echo ""
echo "========================================"
```

---

## scripts/total-destroy.sh

```bash
#!/usr/bin/env bash
# scripts/total-destroy.sh <env>
# Siguran destroy: Helm prvo (uklanja ALB), čeka ALB brisanje, Terraform destroy
set -euo pipefail

ENV=${1:?Usage: total-destroy.sh <env>}
NS="project-a-${ENV}"
TF_DIR="terraform/envs/${ENV}"

echo "=== DESTROYING ${ENV^^} ENVIRONMENT ==="
echo "This will remove ALL AWS resources. Press Ctrl+C to cancel."
read -t 10 -p "Nastavljam za 10 sekundi... " || true

# 1. Helm uninstall
echo "--- Removing Helm releases ---"
kubectl config use-context "${ENV}" 2>/dev/null || true
helm uninstall project-a -n "${NS}" 2>/dev/null && echo "project-a removed" || echo "project-a not found"
helm uninstall monitoring -n monitoring 2>/dev/null && echo "monitoring removed" || echo "monitoring not found"
helm uninstall aws-load-balancer-controller -n kube-system 2>/dev/null && echo "alb-controller removed" || echo "alb-controller not found"

# 2. Wait for ALB
echo "--- Waiting for ALB deletion (max 3min) ---"
TIMEOUT=180
START=$SECONDS
while aws elbv2 describe-load-balancers \
    --query "LoadBalancers[?contains(LoadBalancerName,'project-a-${ENV}')]" \
    --output text 2>/dev/null | grep -q .; do
  if [ $((SECONDS - START)) -gt $TIMEOUT ]; then
    echo "WARNING: ALB timeout, continuing anyway"
    break
  fi
  sleep 10
  echo "  Still waiting for ALB... ($((SECONDS - START))s)"
done
echo "ALB clear."

# 3. Terraform destroy
echo "--- Terraform destroy ---"
cd "${TF_DIR}"
terraform init -reconfigure \
  -backend-config="bucket=${TF_STATE_BUCKET}" \
  -backend-config="key=${ENV}/terraform.tfstate"
terraform destroy -var-file="${ENV}.tfvars" -auto-approve

# 4. Verify
echo ""
echo "=== POST-DESTROY CHECK ==="
aws eks list-clusters \
  --query "clusters[?contains(@,'project-a-${ENV}')]" \
  --output text | grep -q . \
  && echo "  WARNING: EKS still exists!" \
  || echo "  ✓ EKS deleted"

aws rds describe-db-instances \
  --query "DBInstances[?contains(DBInstanceIdentifier,'project-a-${ENV}')].DBInstanceIdentifier" \
  --output text | grep -q . \
  && echo "  WARNING: RDS still exists!" \
  || echo "  ✓ RDS deleted"

echo ""
echo "=== ${ENV^^} ENVIRONMENT DESTROYED ==="
```

---

## Ključni koncepti

### OIDC auth umjesto long-lived credentials

Pipeline ne koristi `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` varijable. Koristi OIDC federation:

```
GitLab CI job
    │ id_tokens: AWS_OIDC_TOKEN (JWT sa claim: sub=project:env:ref)
    ▼
AWS STS AssumeRoleWithWebIdentity
    │ verifikuje JWT potpis (GitLab OIDC provider)
    ▼
Temporary credentials (1h TTL)
    │ automatski expire — nema leakage
    ▼
Terraform / kubectl / helm operacije
```

IAM Trust Policy na svakom env roleu:
```json
{
  "Condition": {
    "StringLike": {
      "gitlab.com:sub": "project_path:myorg/project-a:ref_type:branch:ref:main"
    }
  }
}
```

### on_stop — veza između create i destroy

```yaml
create:env:dev:
  environment:
    name: development
    on_stop: destroy:env:dev   ← GitLab zna koji job je "stop" akcija

destroy:env:dev:
  environment:
    action: stop               ← mora biti deklarisano
```

GitLab UI prikazuje "Stop" dugme na Environments stranici. Kada se pritisne — triggera `destroy:env:dev` job direktno.

### artifacts: dotenv — dijeljenje outputa između jobova

```yaml
# create job
artifacts:
  reports:
    dotenv: create.env    ← KEY=VALUE format, GitLab čita automatski

# deploy job (downstream)
needs:
  - job: create:env:dev
    artifacts: true       ← EKS_CLUSTER_NAME i AWS_REGION dostupni kao env vars
```

### --atomic u helm upgrade

```bash
helm upgrade --install project-a ./helm/project-a \
  --wait --timeout 5m \
  --atomic    ← ako deploy ne uspije u timeout-u, automatski rollback
```

Bez `--atomic`: failed deploy ostavlja polu-deployan stanje. Sa `--atomic`: ili 100% uspješan novi release ili vraćanje na prethodni.
