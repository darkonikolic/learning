# Graduation — Kompletan pipeline reference

## Pipeline overview

Kompletan `.gitlab-ci.yml` ima sljedeće stage-ove:

```
validate      → lint, fmt, hadolint, terraform validate
build         → docker build + push (sve 4 services)
test          → go test, pest, playwright (review app)
env-create    → terraform apply + K8s controllers (manual)
migrate       → golang-migrate up (auto, needs env-create)
deploy        → helm upgrade (auto na main)
verify        → smoke test, health check
env-info      → discover URLs (manual, any time)
env-destroy   → terraform destroy (manual ili scheduled)
```

---

## Job reference po environmentu

### DEV environment

| Job | Trigger | Šta radi |
|-----|---------|----------|
| `create:env:dev` | Manual (UI) | TF apply + ALB controller + cert-manager |
| `deploy:dev` | Auto na main | Helm upgrade --atomic |
| `migrate:dev` | Auto (needs create) | golang-migrate up |
| `env:info:dev` | Manual (any time) | Prints all URLs + costs |
| `destroy:env:dev` | Manual ili scheduled | TF destroy + verify |

### STAGING

| Job | Trigger | Šta radi |
|-----|---------|----------|
| `create:env:staging` | Manual | TF apply staging |
| `deploy:staging` | Manual (after dev OK) | Helm deploy |
| `env:info:staging` | Manual | URLs + status |
| `destroy:env:staging` | Manual | TF destroy |

### PROD

| Job | Trigger | Šta radi |
|-----|---------|----------|
| `create:env:prod` | Manual + approval | TF apply prod |
| `deploy:prod` | Manual + approval | Helm deploy |
| `snapshot:prod` | Manual (pre-deploy) | RDS snapshot |
| `env:info:prod` | Manual | URLs + status |
| `destroy:env:prod` | Manual + double approval | TF destroy (never scheduled!) |

### Review apps (dynamic per MR)

| Job | Trigger | Šta radi |
|-----|---------|----------|
| `deploy:review` | Auto na svaki MR | Helm deploy u mr-{N} namespace |
| `env:info:review` | Auto (link u MR) | URL na review app |
| `destroy:review` | Auto na MR close | Helm uninstall + cleanup |

---

## Upravljanje environmentima iz lokalne mašine

```bash
# Sve što može pipeline može i lokalno

# Create
./scripts/create-env.sh dev

# Deploy
./scripts/deploy.sh dev $(git rev-parse --short HEAD)

# Discover URLs
./scripts/get-urls.sh dev

# Destroy
./scripts/total-destroy.sh dev
```

---

## GitLab CI Variables (setup u Settings → CI/CD)

| Variable | Env | Type | Opis |
|----------|-----|------|------|
| `DEV_AWS_ROLE_ARN` | dev | Variable | OIDC IAM role za dev |
| `STAGING_AWS_ROLE_ARN` | staging | Variable | OIDC IAM role za staging |
| `PROD_AWS_ROLE_ARN` | prod | Variable (Protected) | OIDC IAM role za prod |
| `TF_STATE_BUCKET` | All | Variable | S3 bucket za TF state |
| `KUBE_CONFIG_DEV` | dev | File | base64 kubeconfig za dev |
| `KUBE_CONFIG_STAGING` | staging | File | base64 kubeconfig za staging |
| `KUBE_CONFIG_PROD` | prod | File (Protected) | base64 kubeconfig za prod |
| `SLACK_WEBHOOK_URL` | All | Variable (Masked) | Slack notifikacije |

---

## Schedulirani pipelines

Settings → CI/CD → Pipeline schedules:

| Naziv | Cron | Branch | Variable |
|-------|------|--------|----------|
| Weekly dev cleanup | `0 18 * * 5` | main | `SCHEDULE_NAME=weekly-cleanup` |
| Daily dev pause | `0 19 * * 1-4` | main | `SCHEDULE_NAME=daily-pause` |
| Nightly DB backup | `0 3 * * *` | main | `SCHEDULE_NAME=db-backup` |
| Synthetic monitoring | `*/15 * * * *` | main | `SCHEDULE_NAME=synthetic-monitor` |

---

## Pipeline DAG — dependency graph

```
validate ──────────────────────────────────────────────────────────┐
                                                                    ▼
build:images ──────────────────────────────────────────────────────┐
                                                                    ▼
test:go ──────┐                                                     │
test:php ─────┤──────────────────────────────────────────────────►  │
test:e2e ─────┘                                                     │
                                                                    ▼
create:env:dev (manual) ──────────────────────────────────────────►  │
       │                                                            │
       ▼                                                            │
migrate:dev (auto, needs create) ──────────────────────────────────┤
       │                                                            │
       ▼                                                            │
deploy:dev (auto na main, needs build + migrate) ──────────────────┤
       │                                                            │
       ▼                                                            │
verify:dev (smoke test) ────────────────────────────────────────────┤
                                                                    │
env:info:dev (manual, needs: []) ───────────────────────────────────┤
                                                                    │
destroy:env:dev (manual) ───────────────────────────────────────────┘
```

Ključno: `env:info:dev` ima `needs: []` — može se pokrenuti u bilo kom trenutku, ne čeka ništa.

---

## Approval gates za prod

```yaml
deploy:prod:
  stage: deploy
  when: manual
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'
  environment:
    name: production
    url: https://app.firma.com
  # Protected environment (Settings → CI/CD → Protected Environments)
  # zahtijeva approval od: @lead-devops, @tech-lead
  # min. 1 od 2 approvera mora odobriti
```

Destroy prod ima dvostruku zaštitu:
```yaml
destroy:env:prod:
  when: manual
  allow_failure: false
  rules:
    - if: '$CI_COMMIT_BRANCH == "main" && $FORCE_PROD_DESTROY == "true"'
  # FORCE_PROD_DESTROY mora biti explicitno postavljen
  # Protected environment approval i dalje važi
```

---

## Monitoring pipeline health-a

Svaki failed job šalje Slack notifikaciju:

```yaml
.notify_on_failure:
  after_script:
    - |
      if [ "$CI_JOB_STATUS" = "failed" ]; then
        curl -X POST -H 'Content-type: application/json' \
          --data "{
            \"text\": \"❌ Pipeline failed: ${CI_JOB_NAME} na ${CI_COMMIT_BRANCH}\",
            \"attachments\": [{
              \"text\": \"<${CI_PIPELINE_URL}|View pipeline>\",
              \"color\": \"danger\"
            }]
          }" \
          "$SLACK_WEBHOOK_URL" 2>/dev/null || true
      fi
```

---

## Checklist: novi environment setup

- [ ] IAM OIDC provider za GitLab dodan u AWS account
- [ ] IAM role sa Trust Policy za GitLab project path kreiran
- [ ] S3 bucket za TF state postoji (`terraform-state-project-a-{env}`)
- [ ] GitLab CI variables postavljene (ARN, bucket, webhook)
- [ ] Protected environment konfigurisan u GitLab (za staging i prod)
- [ ] Pipeline schedule kreiran za weekly-cleanup (dev)
- [ ] `terraform/envs/{env}/` direktorijum sa `{env}.tfvars` postoji
- [ ] `helm/project-a/values/{env}.yaml` postoji
- [ ] DNS CNAME za `app.{env}.firma.com` usmjeren na ALB (nakon create)
