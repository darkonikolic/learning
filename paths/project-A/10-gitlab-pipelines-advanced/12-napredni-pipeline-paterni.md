# 12 — Napredni pipeline paterni

Stack: Vue.js + PHP + Go + MySQL + Redis na AWS EKS. GitLab CI/CD. Svi alati u Dockeru.

---

## 1. Retry — automatski ponovi failovane jobove

```yaml
# Retry za flaky tests ili network errors
test:integration:
  retry:
    max: 2                          # Max 2 retry (3 ukupno pokušaja)
    when:
      - runner_system_failure       # Runner crashnuo
      - stuck_or_timeout_failure    # Job se zaglavio
      - script_failure              # Script exitcode != 0 (oprezno!)
      # NE koristiti script_failure za testove — maskira stvarne greške

# Za Terraform koji ponekad fail-uje zbog AWS API rate limits:
tf:apply:dev:
  retry:
    max: 1
    when:
      - script_failure              # OK za TF — idempotentno
```

**Kada koristiti `script_failure`:**
- Terraform, Helm, AWS CLI — idempotentne operacije gdje retry nema štetnih efekata
- NE za unit/integration testove — ako test fail-uje, to je informacija, ne greška

**`when` opcije:**
| Vrijednost | Kada se aktivira |
|---|---|
| `runner_system_failure` | Runner infrastructure problem |
| `stuck_or_timeout_failure` | Job prekoračio timeout ili se zaglavio |
| `script_failure` | Script vratio exitcode != 0 |
| `api_failure` | GitLab API problem |
| `missing_dependency_failure` | Artifact iz needs nedostaje |
| `always` | Uvijek (opasno) |

---

## 2. Timeout — nikad neka job čeka beskonačno

```yaml
variables:
  # Globalni default timeout za sve jobove
  CI_DEFAULT_TIMEOUT: "10m"

build:go-service:
  timeout: 10 minutes              # Build ne smije trajati > 10 min

build:vue:
  timeout: 8 minutes               # npm build

tf:apply:dev:
  timeout: 30 minutes              # Terraform može trajati duže

deploy:prod:
  timeout: 15 minutes              # Helm --wait ima interni timeout

e2e:staging:
  timeout: 20 minutes              # Playwright testovi

test:unit:
  timeout: 5 minutes               # Brzi unit testovi — kratki timeout

# NIKAD: bez timeouta na K8s Job-ovima koji čekaju resourcee
# UVEK: timeout manji od GitLab project timeout (default: 1h)
# Postavljanje: Settings → CI/CD → General pipelines → Timeout
```

**Preporuke po tipu joba:**
| Tip | Timeout |
|---|---|
| Unit testovi | 5 min |
| Build (Go/PHP) | 10 min |
| Build Docker image | 15 min |
| Terraform plan | 10 min |
| Terraform apply | 30 min |
| Helm deploy | 15 min |
| E2E testovi | 20 min |

---

## 3. Cleanup jobovi — briši artefakte, privremene resurse

```yaml
# after_script se izvršava UVEK (i na fail i na pass)
deploy:review:
  environment:
    name: review/$CI_MERGE_REQUEST_IID
    on_stop: cleanup:review
  script:
    - helm upgrade --install review-$CI_MERGE_REQUEST_IID ./helm/project-a
        --namespace project-a-dev
        --set image.tag=$CI_COMMIT_SHA
        --wait --timeout 5m
  after_script:
    # Cleanup privremenih fajlova (ne environment-a — to je on_stop job)
    - rm -f /tmp/kubeconfig /tmp/aws_creds.json

# Dedicated cleanup job — pokreće se when: manual ili on_stop
cleanup:review:
  stage: cleanup
  when: manual
  environment:
    name: review/$CI_MERGE_REQUEST_IID
    action: stop
  script:
    - helm uninstall review-$CI_MERGE_REQUEST_IID -n project-a-dev 2>/dev/null || true
    - kubectl delete namespace project-a-mr-$CI_MERGE_REQUEST_IID 2>/dev/null || true

# Scheduled cleanup: briši stare Docker images iz registrija
cleanup:registry:
  stage: cleanup
  rules:
    - if: '$SCHEDULE_NAME == "registry-cleanup"'
  script:
    # Zadrži zadnjih 10 tagova, obriši stare
    - |
      IMAGES=$(curl --header "PRIVATE-TOKEN: $REGISTRY_CLEANUP_TOKEN" \
        "https://gitlab.com/api/v4/projects/$CI_PROJECT_ID/registry/repositories" | \
        jq -r '.[].id')
      for REPO_ID in $IMAGES; do
        curl --request DELETE \
          --header "PRIVATE-TOKEN: $REGISTRY_CLEANUP_TOKEN" \
          "https://gitlab.com/api/v4/projects/$CI_PROJECT_ID/registry/repositories/$REPO_ID/tags?keep_n=10&name_regex_delete=.*"
      done
```

**`after_script` vs `on_stop`:**
- `after_script` — cleanup privremenih fajlova, uvijek se izvršava u istom jobu
- `on_stop` — uklanjanje environment-a (Helm uninstall, namespace delete), pokreće se poseban job

---

## 4. Needs i DAG (Directed Acyclic Graph) pipeline

```yaml
# Standardni stages (sekvencijalni):
# build → test → deploy
# Sve u build moraju završiti prije nego što test počne — čak i ako su nezavisni

# DAG sa needs (paralelno izvršavanje zavisnosti):
stages:
  - build
  - test
  - deploy

build:go:
  stage: build
  script:
    - CGO_ENABLED=0 go build -o bin/server ./services/go-service/cmd/...

build:php:
  stage: build                     # Pokreće se PARALELNO sa build:go
  script:
    - composer install --no-dev --optimize-autoloader

test:go:
  needs: [build:go]                # Počinje čim build:go završi
  stage: test                      # NE čeka build:php
  script:
    - go test ./services/go-service/...

test:php:
  needs: [build:php]               # Počinje čim build:php završi
  stage: test                      # NE čeka build:go
  script:
    - php vendor/bin/phpunit

deploy:dev:
  needs:                           # Čeka OBA testa
    - test:go
    - test:php
  stage: deploy
  script:
    - helm upgrade --install project-a ./helm/project-a

# artifacts: false — ne download-uj artefakte od needs joba (brže, manje I/O)
deploy:dev:
  needs:
    - job: test:go
      artifacts: false
    - job: test:php
      artifacts: false
```

**Standardni stages vs DAG:**
```
Standardno (sekvencijalno):
build:go ─┐
           ├─ čeka se ─► test:go ─┐
build:php ─┘             test:php ─┴─ čeka se ─► deploy

DAG (optimalno):
build:go ──► test:go ─┐
                       ├─► deploy
build:php ──► test:php ─┘
```
DAG može biti 30-50% brži na većim projektima.

---

## 5. Rules — precizna kontrola kada se job pokreće

```yaml
# Kompletni rules primjer za projekt

# Deployment na produkciju: samo na version tag, manuelno
deploy:prod:
  rules:
    - if: '$CI_COMMIT_TAG =~ /^v\d+\.\d+\.\d+$/'
      when: manual
      allow_failure: false
    - when: never

# Review app: samo na Merge Request
review:deploy:
  rules:
    - if: '$CI_MERGE_REQUEST_IID'
      when: on_success
    - when: never

# Build: samo ako su relevantni fajlovi promijenjeni (path-based CI)
build:go:
  rules:
    - changes:
        - services/go-service/**/*
        - go.mod
        - go.sum
      when: on_success
    - when: never

build:vue:
  rules:
    - changes:
        - services/frontend/**/*
        - package.json
        - package-lock.json
      when: on_success
    - when: never

# Kombinovanje if + changes
lint:terraform:
  rules:
    - if: '$CI_MERGE_REQUEST_IID'
      changes:
        - terraform/**/*
      when: on_success
    - if: '$CI_COMMIT_BRANCH == "main"'
      changes:
        - terraform/**/*
      when: on_success
    - when: never

# Security scan: na MR i na main, NE na feature branchevima
security:sast:
  rules:
    - if: '$CI_MERGE_REQUEST_IID'
    - if: '$CI_COMMIT_BRANCH == "main"'
    - when: never
```

**Rules prioritet:** Evaluira se od prve ka zadnjoj, izvršava se prva koja match-uje.

**`when` vrijednosti unutar rules:**
| Vrijednost | Ponašanje |
|---|---|
| `on_success` | Pokreni ako prethodni jobovi prošli (default) |
| `on_failure` | Pokreni samo ako neki job fail-ovao |
| `always` | Uvijek pokreni |
| `manual` | Zahtjeva manuelni trigger |
| `never` | Nikad ne pokreći |
| `delayed` | Odgodi pokretanje (`start_in: 10 minutes`) |

---

## 6. Artifacts — dijeljenje između jobova

```yaml
# Binary za deployment — kratko trajanje
build:go:
  script:
    - CGO_ENABLED=0 go build -o bin/server ./services/go-service/cmd/...
  artifacts:
    paths:
      - bin/server
    expire_in: 1 hour              # Kratko — samo za ovaj pipeline

# Test rezultati — duže trajanje za analizu
test:go:
  script:
    - go test ./... -v 2>&1 | go-junit-report > test-results.xml
    - go test -coverprofile=coverage.out ./...
    - go tool cover -html=coverage.out -o coverage.html
    - gocov convert coverage.out | gocov-xml > coverage.xml
  artifacts:
    when: always                   # Upload I na fail — da vidimo koji testovi su pali
    reports:
      junit: test-results.xml      # GitLab UI prikazuje test rezultate u MR
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
    paths:
      - coverage.html
    expire_in: 1 week

# Terraform plan — GitLab MR widget
terraform:plan:
  script:
    - cd terraform/envs/dev
    - terraform plan -var-file=dev.tfvars -out=plan.tfplan
    - terraform show -json plan.tfplan > plan.json
  artifacts:
    paths:
      - terraform/envs/dev/plan.tfplan
    reports:
      terraform: terraform/envs/dev/plan.json   # GitLab Terraform MR widget
    expire_in: 1 day

# Prenos varijabli između jobova via dotenv artifact
create:env:dev:
  script:
    - |
      EKS_CLUSTER=$(aws eks list-clusters --region eu-west-1 --query 'clusters[0]' --output text)
      echo "EKS_CLUSTER_NAME=$EKS_CLUSTER" >> deploy.env
      echo "K8S_NAMESPACE=project-a-dev" >> deploy.env
  artifacts:
    reports:
      dotenv: deploy.env           # Varijable automatski dostupne u downstream jobovima
    expire_in: 1 day

deploy:dev:
  needs:
    - job: create:env:dev
      artifacts: true              # Preuzmi dotenv varijable
    - job: build:go
      artifacts: true              # Preuzmi binary
  script:
    - echo "Deploying to $EKS_CLUSTER_NAME namespace $K8S_NAMESPACE"
    - helm upgrade --install project-a ./helm/project-a
        --set image.tag=$CI_COMMIT_SHA
```

---

## 7. Notifications — Slack, email, MR komentari

```yaml
# Reusable Slack notification kao hidden job
.notify_slack:
  after_script:
    - |
      if [ "$CI_JOB_STATUS" = "failed" ]; then
        EMOJI=":red_circle:"
        COLOR="danger"
        STATUS="FAILED"
      else
        EMOJI=":white_check_mark:"
        COLOR="good"
        STATUS="SUCCESS"
      fi
      curl -s -X POST -H 'Content-type: application/json' \
        --data "{
          \"text\": \"$EMOJI Pipeline $STATUS — $CI_PROJECT_NAME\",
          \"attachments\": [{
            \"color\": \"$COLOR\",
            \"fields\": [
              {\"title\": \"Branch\", \"value\": \"$CI_COMMIT_REF_NAME\", \"short\": true},
              {\"title\": \"Commit\", \"value\": \"$CI_COMMIT_SHORT_SHA\", \"short\": true},
              {\"title\": \"Author\", \"value\": \"$CI_COMMIT_AUTHOR\", \"short\": true},
              {\"title\": \"Job\", \"value\": \"$CI_JOB_NAME\", \"short\": true},
              {\"title\": \"Pipeline URL\", \"value\": \"$CI_PIPELINE_URL\", \"short\": false}
            ]
          }]
        }" \
        "$SLACK_WEBHOOK_URL" || true

deploy:prod:
  extends: .notify_slack            # Naslijedi after_script
  script:
    - helm upgrade --install project-a ./helm/project-a
        --namespace project-a-prod
        -f helm/project-a/values/prod.yaml
        --set image.tag=$CI_COMMIT_SHA
        --wait --timeout 10m --atomic

# Terraform plan kao MR komentar
tf:plan:dev:
  script:
    - cd terraform/envs/dev
    - terraform plan -var-file=dev.tfvars 2>&1 | tee plan.txt
    - |
      PLAN=$(cat plan.txt | tail -50)    # Zadnjih 50 linija (GitLab limit komentara)
      curl --request POST \
        --header "PRIVATE-TOKEN: $GITLAB_API_TOKEN" \
        --data-urlencode "body=## Terraform Plan — dev

      \`\`\`hcl
      $PLAN
      \`\`\`
      
      Commit: \`$CI_COMMIT_SHORT_SHA\` | Pipeline: $CI_PIPELINE_URL" \
        "https://gitlab.com/api/v4/projects/$CI_PROJECT_ID/merge_requests/$CI_MERGE_REQUEST_IID/notes"
  rules:
    - if: '$CI_MERGE_REQUEST_IID'
      changes:
        - terraform/**/*

# Deploy summary komentar na MR
deploy:review:
  script:
    - helm upgrade --install review-$CI_MERGE_REQUEST_IID ./helm/project-a
        --namespace project-a-dev
        --set image.tag=$CI_COMMIT_SHA
        --wait --timeout 5m
    - |
      REVIEW_URL="https://review-$CI_MERGE_REQUEST_IID.dev.example.com"
      curl --request POST \
        --header "PRIVATE-TOKEN: $GITLAB_API_TOKEN" \
        --data-urlencode "body=:rocket: Review app deployed: $REVIEW_URL" \
        "https://gitlab.com/api/v4/projects/$CI_PROJECT_ID/merge_requests/$CI_MERGE_REQUEST_IID/notes"
```

---

## 8. Cache — ubrzaj ponavljajuće operacije

```yaml
# Go module cache — key je hash go.sum fajla
build:go:
  cache:
    key:
      files:
        - services/go-service/go.sum    # Cache key = hash ovog fajla
    paths:
      - services/go-service/.cache/go
    policy: pull-push                   # Download na početku, upload na kraju
  script:
    - export GOPATH=$CI_PROJECT_DIR/services/go-service/.cache/go
    - go build -o bin/server ./services/go-service/cmd/...

# npm cache — key je hash package-lock.json
build:vue:
  cache:
    key:
      files:
        - services/frontend/package-lock.json
    paths:
      - services/frontend/node_modules
    policy: pull-push
  script:
    - cd services/frontend && npm ci && npm run build

# PHP Composer cache
build:php:
  cache:
    key:
      files:
        - composer.lock
    paths:
      - vendor
    policy: pull-push
  script:
    - composer install --no-dev --optimize-autoloader

# Terraform provider cache
tf:plan:dev:
  cache:
    key: terraform-providers-v1
    paths:
      - terraform/.terraform
    policy: pull-push
  script:
    - cd terraform/envs/dev
    - terraform init -backend-config=backend-dev.hcl
    - terraform plan -var-file=dev.tfvars

# Read-only cache za testove (ne upload-uj — deps se ne mijenjaju)
test:go:
  cache:
    key:
      files:
        - services/go-service/go.sum
    paths:
      - services/go-service/.cache/go
    policy: pull                    # Samo download, bez upload

# Docker layer cache via GitLab Container Registry
build:go-image:
  script:
    - docker buildx build
        --cache-from $CI_REGISTRY_IMAGE/go-service:cache
        --cache-to type=registry,ref=$CI_REGISTRY_IMAGE/go-service:cache,mode=max
        --tag $CI_REGISTRY_IMAGE/go-service:$CI_COMMIT_SHA
        --push
        services/go-service/
```

**Cache policy:**
| Policy | Ponašanje | Koristiti za |
|---|---|---|
| `pull-push` | Download + upload | Build jobovi koji mijenjaju dependencies |
| `pull` | Samo download | Test/deploy jobovi koji koriste deps ali ih ne mijenjaju |
| `push` | Samo upload | Rijetko |

---

## 9. Interruptible i resource_group

```yaml
# Interruptible: cancel stari pipeline kada novi push dođe na isti branch
build:go:
  interruptible: true              # Brzi jobovi — OK za cancel

build:php:
  interruptible: true

test:go:
  interruptible: true

# NE cancel deploya koji je u toku!
deploy:dev:
  interruptible: false             # Helm --atomic bi ostavio polu-deployovan sistem

deploy:prod:
  interruptible: false

# Resource group: osiguraj da samo jedan deploy istovremeno radi na istom environmentu
deploy:dev:
  resource_group: deploy-dev      # Sljedeći deploy čeka dok ovaj ne završi
  script:
    - helm upgrade --install project-a ./helm/project-a
        --namespace project-a-dev
        --set image.tag=$CI_COMMIT_SHA
        --wait --atomic

deploy:prod:
  resource_group: deploy-prod     # Zasebna grupa za prod
  # deploy:dev i deploy:prod mogu biti istovremeni
  # ali dva deploy:prod nikad ne mogu biti istovremeni

# Terraform state locking + resource_group = dvostruka zaštita
tf:apply:dev:
  resource_group: terraform-dev   # Sprječava concurrent apply i na GitLab nivou
  script:
    - terraform apply -auto-approve plan.tfplan
```

**Zašto `interruptible: false` za deploy?**
Helm `--atomic` rollback funkcioniše samo ako deploy job normalno završi ili fail-uje. Cancel na sredini ostavlja K8s u nekonzistentnom stanju.

---

## 10. Include i template reuse

```yaml
# .gitlab-ci.yml — uključi module

include:
  # GitLab managed SAST/security templates
  - template: Security/SAST.gitlab-ci.yml
  - template: Security/Dependency-Scanning.gitlab-ci.yml
  - template: Security/Secret-Detection.gitlab-ci.yml

  # Vlastiti moduli iz istog repoa
  - local: '.gitlab/ci/build.yml'
  - local: '.gitlab/ci/test.yml'
  - local: '.gitlab/ci/deploy.yml'
  - local: '.gitlab/ci/terraform.yml'

  # Shared templates iz drugog projekta (verzionisano)
  - project: 'yourgroup/ci-templates'
    ref: 'v2.1.0'                  # Pinuj na tag, ne na main
    file:
      - '/templates/helm-deploy.yml'
      - '/templates/notify-slack.yml'

# Primjer rules na .gitlab-ci.yml nivou
workflow:
  rules:
    - if: '$CI_COMMIT_MESSAGE =~ /\[skip ci\]/'
      when: never
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
    - if: '$CI_COMMIT_BRANCH == "main"'
    - if: '$CI_COMMIT_BRANCH == "develop"'
    - if: '$CI_COMMIT_TAG'
    - when: never
```

```yaml
# .gitlab/ci/deploy.yml — reusable deploy template

.helm_deploy:
  image: alpine/helm:3.14
  before_script:
    - echo "$KUBE_CONFIG" | base64 -d > /tmp/kubeconfig
    - export KUBECONFIG=/tmp/kubeconfig
    - kubectl config use-context $KUBE_CONTEXT
  script:
    - helm upgrade --install $HELM_RELEASE_NAME ./helm/project-a
        --namespace $K8S_NAMESPACE
        -f helm/project-a/values/$DEPLOY_ENV.yaml
        --set image.tag=$CI_COMMIT_SHA
        --set image.repository=$CI_REGISTRY_IMAGE/go-service
        --wait --timeout 5m --atomic
  after_script:
    - rm -f /tmp/kubeconfig

deploy:dev:
  extends: .helm_deploy
  variables:
    HELM_RELEASE_NAME: project-a
    K8S_NAMESPACE: project-a-dev
    DEPLOY_ENV: dev
    KUBE_CONTEXT: eks-cluster-dev
  environment:
    name: development
    url: https://dev.project-a.example.com
  rules:
    - if: '$CI_COMMIT_BRANCH == "develop"'

deploy:staging:
  extends: .helm_deploy
  variables:
    HELM_RELEASE_NAME: project-a
    K8S_NAMESPACE: project-a-staging
    DEPLOY_ENV: staging
    KUBE_CONTEXT: eks-cluster-staging
  environment:
    name: staging
    url: https://staging.project-a.example.com
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'

deploy:prod:
  extends: .helm_deploy
  variables:
    HELM_RELEASE_NAME: project-a
    K8S_NAMESPACE: project-a-prod
    DEPLOY_ENV: prod
    KUBE_CONTEXT: eks-cluster-prod
  timeout: 20 minutes              # Override .helm_deploy timeout
  environment:
    name: production
    url: https://project-a.example.com
  rules:
    - if: '$CI_COMMIT_TAG =~ /^v\d+\.\d+\.\d+$/'
      when: manual
```

---

## 11. Protected variables i environments

```yaml
# Protected environment setup (GitLab UI):
# Settings → Environments → production → Protect
# Allowed to deploy: Maintainer role (ili specifični korisnici)
# Ova zaštita sprječava da developer greškom deploy-uje na prod

deploy:prod:
  environment:
    name: production
    url: https://project-a.example.com
  # Ovaj job se NE može pokrenuti osim ako je user Maintainer+
  # i branch/tag je protected

# Variable scoping po environmentu:
# Settings → CI/CD → Variables → Add variable
#
# Varijabla        Environment      Protected  Masked
# DB_HOST          development      No         No
# DB_HOST          staging          No         No
# DB_HOST          production       Yes        No
# DB_PASSWORD      development      No         Yes
# DB_PASSWORD      production       Yes        Yes
# AWS_ROLE_ARN     development      No         No
# AWS_ROLE_ARN     production       Yes        No
#
# Unutar joba: $DB_HOST automatski dobija pravu vrijednost
# ovisno o environment: name vrijednosti

# OIDC za AWS — bez long-lived credentials
deploy:prod:
  environment:
    name: production
  id_tokens:
    AWS_OIDC_TOKEN:
      aud: https://gitlab.com
  script:
    - |
      # Preuzmi privremene AWS credentials via OIDC
      CREDS=$(aws sts assume-role-with-web-identity \
        --role-arn "$AWS_ROLE_ARN" \
        --role-session-name "gitlab-$CI_JOB_ID" \
        --web-identity-token "$AWS_OIDC_TOKEN" \
        --duration-seconds 3600 \
        --query 'Credentials' --output json)
      export AWS_ACCESS_KEY_ID=$(echo $CREDS | jq -r '.AccessKeyId')
      export AWS_SECRET_ACCESS_KEY=$(echo $CREDS | jq -r '.SecretAccessKey')
      export AWS_SESSION_TOKEN=$(echo $CREDS | jq -r '.SessionToken')
    - aws eks update-kubeconfig --name $EKS_CLUSTER_NAME --region $AWS_REGION
    - helm upgrade --install project-a ./helm/project-a ...
```

---

## 12. Pipeline triggers i webhooks

```yaml
# Trigger downstream pipeline (multi-repo setup)
trigger:infra:
  stage: deploy
  trigger:
    project: yourgroup/infra-repo
    branch: main
    strategy: depend               # Čekaj da downstream pipeline završi
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'
      changes:
        - terraform/**/*

# Trigger API — za eksterne sisteme (npr. Jenkins, custom webhook)
# curl --request POST \
#   --form "token=$CI_JOB_TOKEN" \
#   --form "ref=main" \
#   --form "variables[DEPLOY_ENV]=staging" \
#   "https://gitlab.com/api/v4/projects/$PROJECT_ID/trigger/pipeline"

# Parent-child pipeline — dinamički generisan pipeline
stages:
  - generate
  - trigger

generate:service-pipelines:
  stage: generate
  script:
    - |
      # Generiši pipeline samo za servise koji su promijenjeni
      python3 scripts/generate-pipeline.py \
        --changed-files $(git diff --name-only $CI_MERGE_REQUEST_DIFF_BASE_SHA) \
        --output generated-pipeline.yml
  artifacts:
    paths:
      - generated-pipeline.yml
    expire_in: 1 hour

trigger:services:
  stage: trigger
  needs:
    - job: generate:service-pipelines
      artifacts: true
  trigger:
    include:
      - artifact: generated-pipeline.yml
        job: generate:service-pipelines
    strategy: depend

# Scheduled pipeline trigger (Settings → CI/CD → Schedules)
cleanup:old-deployments:
  rules:
    - if: '$SCHEDULE_NAME == "weekly-cleanup"'
  script:
    - |
      # Obriši review app deploymente koji su stariji od 7 dana
      CUTOFF_DATE=$(date -d '7 days ago' +%s)
      for RELEASE in $(helm list -n project-a-dev -q | grep review-); do
        DEPLOY_DATE=$(helm status $RELEASE -n project-a-dev -o json | \
          jq -r '.info.first_deployed' | xargs -I{} date -d {} +%s)
        if [ "$DEPLOY_DATE" -lt "$CUTOFF_DATE" ]; then
          helm uninstall $RELEASE -n project-a-dev
          echo "Deleted: $RELEASE"
        fi
      done
```

---

## 13. Debugging failing pipelines

```yaml
# Debug varijable — verbose output
variables:
  CI_DEBUG_TRACE: "false"          # "true" = VERY verbose (sadrži secrets — oprezno!)
  TF_LOG: "WARN"                   # TRACE/DEBUG/INFO/WARN/ERROR za Terraform
  HELM_DEBUG: "false"              # "true" za Helm verbose output

# Debug runner environment (manuelni trigger)
debug:runner:
  when: manual
  script:
    - cat /etc/os-release
    - docker info 2>/dev/null || echo "Docker not available"
    - kubectl version --client 2>/dev/null || echo "kubectl not available"
    - helm version 2>/dev/null || echo "Helm not available"
    - terraform version 2>/dev/null || echo "Terraform not available"
    - aws --version 2>/dev/null || echo "AWS CLI not available"
    - echo "CPU: $(nproc) cores"
    - echo "Memory: $(free -h | grep Mem | awk '{print $2}')"
    - echo "Disk: $(df -h / | tail -1 | awk '{print $4}') free"

# Print environment varijable — NIKAD u prod, NIKAD bez filtera
debug:env:
  when: manual
  environment: development         # Samo development env
  script:
    - env | sort | grep -v -E "(PASSWORD|TOKEN|SECRET|KEY|CERT)" | head -100

# K8s debug — šta se dešava sa deploymentom
debug:k8s:
  when: manual
  environment: development
  script:
    - kubectl get pods -n project-a-dev
    - kubectl get events -n project-a-dev --sort-by='.lastTimestamp' | tail -20
    - kubectl describe deployment project-a -n project-a-dev || true
    - |
      FAILED_POD=$(kubectl get pods -n project-a-dev | grep -v Running | grep -v Completed | tail -1 | awk '{print $1}')
      if [ -n "$FAILED_POD" ]; then
        kubectl logs $FAILED_POD -n project-a-dev --previous 2>/dev/null || \
        kubectl logs $FAILED_POD -n project-a-dev || true
      fi

# Dry run — provjeri šta bi pipeline uradio bez stvarnog izvršavanja
lint:ci-config:
  stage: .pre
  script:
    - |
      curl --silent --header "PRIVATE-TOKEN: $GITLAB_API_TOKEN" \
        --request POST \
        --header "Content-Type: application/json" \
        --data "{\"content\": \"$(cat .gitlab-ci.yml | base64 -w 0)\"}" \
        "https://gitlab.com/api/v4/projects/$CI_PROJECT_ID/ci/lint" | \
        jq -e '.valid == true' || (echo "CI config invalid!" && exit 1)
  rules:
    - changes:
        - .gitlab-ci.yml
        - .gitlab/ci/**/*
```

---

## 14. Pipeline efficiency — smanjiti trajanje

```yaml
# 1. Shallow clone — za velike repoe (ne treba cijela historija)
variables:
  GIT_DEPTH: 10                    # Fetch zadnjih 10 commitova
  GIT_CLONE_PATH: $CI_BUILDS_DIR/project-a   # Konzistentna putanja za cache

# 2. Path-based CI — ne buildaj ono što nije promijenjeno
build:go:
  rules:
    - changes:
        - services/go-service/**/*
        - go.mod
        - go.sum

build:php:
  rules:
    - changes:
        - services/php-api/**/*
        - composer.lock

build:vue:
  rules:
    - changes:
        - services/frontend/**/*
        - package-lock.json

# 3. Paralelizacija unutar joba
test:go:
  script:
    - go test ./... -parallel 8 -count=1   # 8 parallel test suites

test:php:
  parallel: 3                      # GitLab pokretanje 3 instance joba paralelno
  script:
    - php vendor/bin/phpunit --testsuite "group-$CI_NODE_INDEX"

# 4. Skip pipeline za trivijalne promjene
workflow:
  rules:
    - if: '$CI_COMMIT_MESSAGE =~ /\[skip ci\]/'
      when: never
    - if: '$CI_COMMIT_MESSAGE =~ /^(docs|chore|style):'  # Conventional commits
      when: never
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
    - if: '$CI_COMMIT_BRANCH == "main"'
    - if: '$CI_COMMIT_TAG'

# 5. Pre-built base images — ne instaluj tools svaki put
# Umjesto:
#   before_script:
#     - apt-get install -y terraform helm kubectl awscli jq
# Napravi custom image jednom:
build:tools-image:
  rules:
    - changes:
        - docker/ci-tools/Dockerfile
      when: manual
  script:
    - docker build -t $CI_REGISTRY_IMAGE/ci-tools:latest docker/ci-tools/
    - docker push $CI_REGISTRY_IMAGE/ci-tools:latest

# Koristiti pre-built image:
deploy:dev:
  image: $CI_REGISTRY_IMAGE/ci-tools:latest   # Svi alati su već tu
  script:
    - helm upgrade --install ...

# 6. Fail fast — najbrže provjere prve
stages:
  - validate    # Lint, format check, config validation (< 2 min)
  - test        # Unit testovi (< 5 min)
  - build       # Docker build (< 10 min)
  - integration # Integration testovi (< 10 min)
  - deploy      # Deployment

lint:all:
  stage: validate
  needs: []                        # Odmah, bez čekanja
  script:
    - golangci-lint run ./...
    - phpcs services/php-api/
    - eslint services/frontend/src/

# 7. Mjerenje i optimizacija
# GitLab → CI/CD → Analytics → Pipeline charts
# Identifikuj najsporije jobove i fokusiraj optimizaciju tamo

# 8. Executor specific optimizacija (za self-hosted runners)
# gitlab-runner config.toml:
# [[runners.kubernetes.volumes.empty_dir]]
#   name = "docker-certs"
#   mount_path = "/certs/client"
# concurrent = 10   # Paralelni jobovi po runneru
```

---

## Kombinovani primjer — kompletan .gitlab-ci.yml

```yaml
include:
  - local: '.gitlab/ci/build.yml'
  - local: '.gitlab/ci/test.yml'
  - local: '.gitlab/ci/deploy.yml'
  - template: Security/SAST.gitlab-ci.yml
  - template: Security/Secret-Detection.gitlab-ci.yml

variables:
  GIT_DEPTH: 10
  DOCKER_BUILDKIT: "1"

workflow:
  rules:
    - if: '$CI_COMMIT_MESSAGE =~ /\[skip ci\]/'
      when: never
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
    - if: '$CI_COMMIT_BRANCH =~ /^(main|develop)$/'
    - if: '$CI_COMMIT_TAG =~ /^v\d+\.\d+\.\d+$/'

stages:
  - validate
  - build
  - test
  - security
  - deploy
  - cleanup

# Lint: odmah, paralelno, ne čeka ništa
lint:go:
  stage: validate
  needs: []
  interruptible: true
  timeout: 5 minutes
  rules:
    - changes: [services/go-service/**/*]
  cache:
    key: golangci-lint
    paths: [.golangci-cache]
    policy: pull-push
  script:
    - golangci-lint run ./services/go-service/...

# Build Go binary
build:go:
  stage: build
  needs: [lint:go]
  interruptible: true
  timeout: 10 minutes
  rules:
    - changes: [services/go-service/**/*]
  cache:
    key:
      files: [go.sum]
    paths: [.cache/go]
    policy: pull-push
  artifacts:
    paths: [bin/server]
    expire_in: 2 hours
  script:
    - export GOPATH=$CI_PROJECT_DIR/.cache/go
    - CGO_ENABLED=0 go build -ldflags="-X main.version=$CI_COMMIT_TAG" -o bin/server ./services/go-service/cmd/...

# Unit testovi
test:go:
  stage: test
  needs:
    - job: build:go
      artifacts: false
  interruptible: true
  timeout: 8 minutes
  retry:
    max: 1
    when: [runner_system_failure]
  rules:
    - changes: [services/go-service/**/*]
  cache:
    key:
      files: [go.sum]
    paths: [.cache/go]
    policy: pull
  artifacts:
    when: always
    reports:
      junit: test-results.xml
    expire_in: 1 week
  script:
    - export GOPATH=$CI_PROJECT_DIR/.cache/go
    - go test ./... -parallel 8 -v 2>&1 | go-junit-report > test-results.xml

# Build Docker image
build:go-image:
  stage: build
  needs:
    - job: test:go
      artifacts: false
  interruptible: true
  timeout: 15 minutes
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'
      changes: [services/go-service/**/*]
    - if: '$CI_COMMIT_TAG =~ /^v\d+\.\d+\.\d+$/'
  script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
    - docker buildx build
        --cache-from $CI_REGISTRY_IMAGE/go-service:cache
        --cache-to type=registry,ref=$CI_REGISTRY_IMAGE/go-service:cache,mode=max
        --tag $CI_REGISTRY_IMAGE/go-service:$CI_COMMIT_SHA
        --push
        services/go-service/

# Deploy dev — automatski na develop branch
deploy:dev:
  stage: deploy
  needs:
    - job: build:go-image
      artifacts: false
  interruptible: false
  timeout: 15 minutes
  resource_group: deploy-dev
  retry:
    max: 1
    when: [runner_system_failure]
  environment:
    name: development
    url: https://dev.project-a.example.com
  rules:
    - if: '$CI_COMMIT_BRANCH == "develop"'
  script:
    - aws eks update-kubeconfig --name $EKS_CLUSTER_DEV --region $AWS_REGION
    - helm upgrade --install project-a ./helm/project-a
        --namespace project-a-dev
        -f helm/project-a/values/dev.yaml
        --set image.tag=$CI_COMMIT_SHA
        --wait --timeout 10m --atomic

# Deploy prod — manualni, samo na version tag
deploy:prod:
  stage: deploy
  needs:
    - job: build:go-image
      artifacts: false
  interruptible: false
  timeout: 20 minutes
  resource_group: deploy-prod
  when: manual
  allow_failure: false
  environment:
    name: production
    url: https://project-a.example.com
  rules:
    - if: '$CI_COMMIT_TAG =~ /^v\d+\.\d+\.\d+$/'
  script:
    - aws eks update-kubeconfig --name $EKS_CLUSTER_PROD --region $AWS_REGION
    - helm upgrade --install project-a ./helm/project-a
        --namespace project-a-prod
        -f helm/project-a/values/prod.yaml
        --set image.tag=$CI_COMMIT_SHA
        --wait --timeout 15m --atomic
```

---

## Cheat sheet

| Pattern | Konfiguracija | Svrha |
|---|---|---|
| Retry | `retry.max: 2` | Flaky runners, network greške |
| Timeout | `timeout: 10 minutes` | Spriječi beskonačno čekanje |
| DAG | `needs: [job-name]` | Paralelno izvršavanje zavisnosti |
| Path CI | `rules.changes` | Ne buildaj neizmijenjene servise |
| Fail fast | Validate stage prvi | Najbrže provjere odmah |
| Cancel stale | `interruptible: true` | Ne troši runner resourcee |
| Serialni deploy | `resource_group` | Spriječi concurrent deployment |
| Dotenv artifact | `reports.dotenv` | Prenos varijabli između jobova |
| Read-only cache | `policy: pull` | Brže nego pull-push za test jobove |
| OIDC auth | `id_tokens` | Bez long-lived AWS credentials |
