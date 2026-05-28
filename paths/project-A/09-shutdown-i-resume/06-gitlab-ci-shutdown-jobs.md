# 06 — GitLab CI: Shutdown i Resume Jobovi

Pipeline integracija za sve shutdown/startup operacije.
Ručni jobovi za kontrolu, scheduled jobovi za automatizaciju.

---

## Kompletni `.gitlab-ci.yml` Dodatak

Dodaj ove jobove u postojeći pipeline. Pretpostavljamo da imaš:
- `variables.tf` sa AWS OIDC autentifikacijom
- `before_script` helper u `.gitlab-ci.yml` koji postavlja `aws` i `kubectl`
- Stages: `build`, `test`, `deploy`, `verify`, `destroy`

```yaml
# ─── STAGES (dodaj destroy ako ga nemaš) ──────────────────────────────────
stages:
  - build
  - test
  - deploy
  - verify
  - destroy        # ← dodaj ovo

# ─── SHARED: Terraform auth ───────────────────────────────────────────────
.terraform_auth: &terraform_auth
  image:
    name: hashicorp/terraform:1.7
    entrypoint: [""]
  id_tokens:
    AWS_OIDC_TOKEN:
      aud: https://gitlab.com
  before_script:
    - apk add --no-cache aws-cli helm kubectl curl bash bc
    - |
      # Preuzmi credentials via OIDC
      CREDS=$(aws sts assume-role-with-web-identity \
        --role-arn "$AWS_ROLE_ARN" \
        --role-session-name "gitlab-ci-${CI_JOB_ID}" \
        --web-identity-token "$AWS_OIDC_TOKEN" \
        --query "Credentials" \
        --output json)
      export AWS_ACCESS_KEY_ID=$(echo "$CREDS" | grep -o '"AccessKeyId": "[^"]*"' | cut -d'"' -f4)
      export AWS_SECRET_ACCESS_KEY=$(echo "$CREDS" | grep -o '"SecretAccessKey": "[^"]*"' | cut -d'"' -f4)
      export AWS_SESSION_TOKEN=$(echo "$CREDS" | grep -o '"SessionToken": "[^"]*"' | cut -d'"' -f4)
    - aws eks update-kubeconfig --name "project-a-${ENV}" --region eu-west-1 --alias "${ENV}" 2>/dev/null || true

# ─── TOTAL DESTROY: Learning Mode ─────────────────────────────────────────
destroy:dev:manual:
  <<: *terraform_auth
  stage: destroy
  variables:
    ENV: dev
    AWS_ROLE_ARN: $DEV_AWS_ROLE_ARN
  when: manual
  allow_failure: false
  environment:
    name: development
    action: stop
  script:
    - echo "=== DESTROY DEV (manual trigger) ==="
    # Helm uninstall
    - helm uninstall project-a -n project-a-dev 2>/dev/null || true
    - helm uninstall monitoring -n monitoring 2>/dev/null || true
    - helm uninstall aws-load-balancer-controller -n kube-system 2>/dev/null || true
    # Čekaj ALB
    - |
      echo "Waiting for ALB..."
      for i in $(seq 1 12); do
        COUNT=$(aws elbv2 describe-load-balancers \
          --query "length(LoadBalancers[?contains(LoadBalancerName,'dev')])" \
          --output text 2>/dev/null || echo "0")
        [ "$COUNT" = "0" ] && echo "ALB deleted" && break
        [ "$i" = "12" ] && echo "WARNING: ALB still active"
        sleep 15
      done
    # Terraform destroy
    - cd terraform/envs/dev
    - terraform init -input=false
    - terraform destroy -var-file=dev.tfvars -auto-approve
    - echo "Dev environment destroyed. Cost: \$0/h"
  after_script:
    - |
      [ -n "$SLACK_WEBHOOK_URL" ] && curl -s -X POST \
        -H 'Content-type: application/json' \
        --data "{\"text\":\"Dev environment destroyed by ${GITLAB_USER_NAME}. Cost: \$0/h\"}" \
        "$SLACK_WEBHOOK_URL" || true
  rules:
    - if: '$CI_PIPELINE_SOURCE != "schedule"'
      when: manual

# ─── TOTAL DESTROY: Scheduled (Weekly Cleanup) ────────────────────────────
destroy:dev:scheduled:
  <<: *terraform_auth
  stage: destroy
  variables:
    ENV: dev
    AWS_ROLE_ARN: $DEV_AWS_ROLE_ARN
  environment:
    name: development
    action: stop
  script:
    - bash scripts/total-destroy.sh dev
  after_script:
    - |
      [ -n "$SLACK_WEBHOOK_URL" ] && curl -s -X POST \
        -H 'Content-type: application/json' \
        --data "{\"text\":\"Dev environment destroyed (scheduled weekly cleanup). Weekend savings: ~\$14\"}" \
        "$SLACK_WEBHOOK_URL" || true
  rules:
    - if: '$CI_PIPELINE_SOURCE == "schedule" && $SCHEDULE_TYPE == "weekly-cleanup"'

# ─── PROD: Snapshot + Destroy ─────────────────────────────────────────────
snapshot-and-pause:prod:
  <<: *terraform_auth
  stage: destroy
  variables:
    ENV: prod
    AWS_ROLE_ARN: $PROD_AWS_ROLE_ARN
  when: manual
  allow_failure: false
  environment:
    name: production
    action: stop
  script:
    - SNAPSHOT_ID="project-a-prod-$(date +%Y%m%d-%H%M)"
    - echo "Creating snapshot: $SNAPSHOT_ID"
    # Snapshot
    - |
      aws rds create-db-snapshot \
        --db-instance-identifier project-a-prod \
        --db-snapshot-identifier "$SNAPSHOT_ID"
      echo "Waiting for snapshot (up to 15 min)..."
      aws rds wait db-snapshot-completed \
        --db-snapshot-identifier "$SNAPSHOT_ID"
      echo "SNAPSHOT_ID=$SNAPSHOT_ID" >> snapshot.env
      echo "Snapshot complete: $SNAPSHOT_ID"
    # Spremi snapshot ID u git
    - |
      echo "$SNAPSHOT_ID" > .last-prod-snapshot
      git config user.email "ci@project-a.com"
      git config user.name "GitLab CI"
      git add .last-prod-snapshot
      git commit -m "ops: save prod snapshot $SNAPSHOT_ID [skip ci]"
      git push "https://gitlab-ci-token:${CI_JOB_TOKEN}@${CI_SERVER_HOST}/${CI_PROJECT_PATH}.git" HEAD:$CI_DEFAULT_BRANCH
    # Helm uninstall
    - helm uninstall project-a -n project-a-prod 2>/dev/null || true
    - helm uninstall aws-load-balancer-controller -n kube-system 2>/dev/null || true
    - sleep 90
    # Terraform destroy
    - cd terraform/envs/prod
    - terraform init -input=false
    - terraform destroy -var-file=prod.tfvars -auto-approve
    - echo "Production paused. Monthly cost: ~\$0.46 (snapshot storage)"
  artifacts:
    reports:
      dotenv: snapshot.env
    expire_in: 30 days
  after_script:
    - |
      SNAP=$(cat .last-prod-snapshot 2>/dev/null || echo "unknown")
      [ -n "$SLACK_WEBHOOK_URL" ] && curl -s -X POST \
        -H 'Content-type: application/json' \
        --data "{\"text\":\"Production PAUSED by ${GITLAB_USER_NAME}. Snapshot: ${SNAP}. To resume: trigger resume:prod job.\"}" \
        "$SLACK_WEBHOOK_URL" || true

# ─── PROD: Resume od Snapshota ────────────────────────────────────────────
resume:prod:
  <<: *terraform_auth
  stage: deploy
  variables:
    ENV: prod
    AWS_ROLE_ARN: $PROD_AWS_ROLE_ARN
    SNAPSHOT_IDENTIFIER: ""   # Override: set u CI/CD variable ili pri ručnom triggeru
  when: manual
  allow_failure: false
  needs: []
  environment:
    name: production
    action: start
  script:
    - |
      # Odredi snapshot ID
      SNAPSHOT=${SNAPSHOT_IDENTIFIER:-$(cat .last-prod-snapshot 2>/dev/null || echo "")}
      if [ -z "$SNAPSHOT" ]; then
        echo "ERROR: Set SNAPSHOT_IDENTIFIER variable or ensure .last-prod-snapshot exists"
        exit 1
      fi
      echo "Resuming from snapshot: $SNAPSHOT"
      # Postavi snapshot_identifier u tfvars
      sed -i "s|snapshot_identifier.*=.*|snapshot_identifier = \"$SNAPSHOT\"|" terraform/envs/prod/prod.tfvars
    # Terraform apply
    - cd terraform/envs/prod
    - terraform init -input=false
    - terraform apply -var-file=prod.tfvars -auto-approve
    # Kubeconfig
    - aws eks update-kubeconfig --name project-a-prod --region eu-west-1 --alias prod
    # ALB Controller
    - |
      ALB_ROLE=$(terraform output -raw alb_controller_role_arn)
      helm repo add eks https://aws.github.io/eks-charts 2>/dev/null || true
      helm repo update eks
      helm upgrade --install aws-load-balancer-controller eks/aws-load-balancer-controller \
        -n kube-system \
        --set clusterName=project-a-prod \
        --set serviceAccount.create=true \
        --set "serviceAccount.annotations.eks\.amazonaws\.com/role-arn=$ALB_ROLE" \
        --wait --timeout=5m
    # Deploy posljednjim production tag-om
    - |
      LAST_TAG=$(aws ecr describe-images \
        --repository-name project-a/go-service \
        --query 'sort_by(imageDetails,&imagePushedAt)[-1].imageTags[0]' \
        --output text)
      echo "Deploying tag: $LAST_TAG"
      helm upgrade --install project-a ./helm/project-a \
        -n project-a-prod --create-namespace \
        -f helm/project-a/values/prod.yaml \
        --set image.tag="$LAST_TAG" \
        --wait --timeout=10m
    # Health check
    - kubectl rollout status deployment/go-service -n project-a-prod --timeout=5m
    - kubectl rollout status deployment/php-service -n project-a-prod --timeout=5m
    # Obrisi snapshot_identifier iz tfvars
    - sed -i 's|snapshot_identifier.*=.*|snapshot_identifier = ""|' terraform/envs/prod/prod.tfvars
    - echo "=== RESUME COMPLETE ==="
    - bash scripts/get-urls.sh prod
  after_script:
    - |
      [ -n "$SLACK_WEBHOOK_URL" ] && curl -s -X POST \
        -H 'Content-type: application/json' \
        --data "{\"text\":\"Production RESUMED by ${GITLAB_USER_NAME}. All data intact from snapshot.\"}" \
        "$SLACK_WEBHOOK_URL" || true

# ─── EOD PAUSE ────────────────────────────────────────────────────────────
eod-pause:dev:
  <<: *terraform_auth
  stage: destroy
  variables:
    ENV: dev
    AWS_ROLE_ARN: $DEV_AWS_ROLE_ARN
  when: manual
  script:
    - bash scripts/eod-pause.sh dev
  after_script:
    - |
      [ -n "$SLACK_WEBHOOK_URL" ] && curl -s -X POST \
        -H 'Content-type: application/json' \
        --data "{\"text\":\"Dev PAUSED for the night by ${GITLAB_USER_NAME}. Overnight savings: ~\$4\"}" \
        "$SLACK_WEBHOOK_URL" || true
  rules:
    - if: '$CI_PIPELINE_SOURCE != "schedule"'
      when: manual

# ─── MORNING START ────────────────────────────────────────────────────────
morning-start:dev:
  <<: *terraform_auth
  stage: deploy
  variables:
    ENV: dev
    AWS_ROLE_ARN: $DEV_AWS_ROLE_ARN
  when: manual
  needs: []
  environment:
    name: development
    action: start
  script:
    - bash scripts/morning-start.sh dev
    - bash scripts/get-urls.sh dev
  after_script:
    - |
      APP_URL=$(kubectl get ingress project-a -n project-a-dev \
        -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "pending")
      [ -n "$SLACK_WEBHOOK_URL" ] && curl -s -X POST \
        -H 'Content-type: application/json' \
        --data "{\"text\":\"Dev environment STARTED. App URL: http://${APP_URL}\"}" \
        "$SLACK_WEBHOOK_URL" || true
  rules:
    - if: '$CI_PIPELINE_SOURCE != "schedule"'
      when: manual

# ─── COST CHECK ───────────────────────────────────────────────────────────
cost-check:
  <<: *terraform_auth
  stage: verify
  variables:
    ENV: dev
    AWS_ROLE_ARN: $DEV_AWS_ROLE_ARN
  when: manual
  needs: []
  script:
    - bash scripts/cost-check.sh dev
    - bash scripts/cost-check.sh prod
  rules:
    - when: manual
```

---

## GitLab CI/CD Variables

Postavi ove varijable u `Settings → CI/CD → Variables`:

```
DEV_AWS_ROLE_ARN        = arn:aws:iam::123456789:role/gitlab-ci-dev
PROD_AWS_ROLE_ARN       = arn:aws:iam::123456789:role/gitlab-ci-prod
SLACK_WEBHOOK_URL       = https://hooks.slack.com/services/...  (Protected, Masked)
SNAPSHOT_IDENTIFIER     = ""  (prazno — override ručno pri resume-u)
```

**Variable flags:**
- `DEV_AWS_ROLE_ARN` — Protected (samo protected branches), ne Masked (nije secret)
- `PROD_AWS_ROLE_ARN` — Protected, ne Masked
- `SLACK_WEBHOOK_URL` — Protected + Masked (URL je secret)

---

## GitLab Scheduled Pipelines

Konfiguracija u `Settings → CI/CD → Pipeline schedules`:

```
Schedule 1: Weekly Dev Cleanup
  Description: "Destroy dev environment every Friday evening"
  Interval:    0 18 * * 5         (Petak, 18:00 UTC)
  Branch:      main
  Variable:    SCHEDULE_TYPE = "weekly-cleanup"
  Active:      ✓

Schedule 2: Daily EOD Pause (opcionalno)
  Description: "Pause dev every weekday evening"
  Interval:    0 17 * * 1-5       (Pon-Pet, 17:00 UTC)
  Branch:      main
  Variable:    SCHEDULE_TYPE = "eod-pause"
  Active:      ✓ (aktiviraj tek kada si siguran da morning-start radi)

Schedule 3: Cost Audit
  Description: "Daily cost check"
  Interval:    0 8 * * *          (Svaki dan, 08:00 UTC)
  Branch:      main
  Variable:    SCHEDULE_TYPE = "cost-check"
  Active:      ✓
```

---

## Pipeline Stages Vizualizacija

```
Commit push:
  build → test → deploy:dev → verify → (end)

Ručni destroy:
  (manual) destroy:dev:manual

Ručni pause/resume:
  (manual) snapshot-and-pause:prod
  (manual) resume:prod
  (manual) eod-pause:dev
  (manual) morning-start:dev

Scheduled (Petak 18:00):
  destroy:dev:scheduled
```

---

## Notifikacije u Slacku

Svaki shutdown/startup job šalje poruku u Slack.
Format:

```
Dev environment DESTROYED by darko.nikolic. Cost: $0/h
Production PAUSED by darko.nikolic. Snapshot: project-a-prod-20240315-1800
Production RESUMED by darko.nikolic. All data intact from snapshot.
Dev PAUSED for the night. Overnight savings: ~$4
Dev environment STARTED. App URL: http://k8s-projecta-abc123.eu-west-1.elb.amazonaws.com
```

**Zašto je ovo važno:** Tim odmah zna kad je environment active ili ne.
Smanjuje situacije gdje neko čeka na environment koji je destroyed.
