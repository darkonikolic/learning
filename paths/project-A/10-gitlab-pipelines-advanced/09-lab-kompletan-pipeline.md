# 09 — LAB: Kompletan pipeline za project-A

## Cilj

Napisati i testirati kompletan `.gitlab-ci.yml` za project-A koji pokriva:
build, test, terraform plan/apply, helm deploy za sve environments,
review apps, destroy jobove i notifikacije.

---

## Stages pregled

```yaml
stages:
  - lint
  - build
  - test
  - tf-plan
  - tf-apply
  - deploy
  - verify
  - destroy
```

Redoslijed je bitan — svaki stage čeka uspjeh prethodnog.
`destroy` stage sadrži samo manuelne jobove koji se ne pokreću automatski.

---

## Kompletan .gitlab-ci.yml

```yaml
# ============================================================
# project-A — GitLab CI/CD Pipeline
# ============================================================

stages:
  - lint
  - build
  - test
  - tf-plan
  - tf-apply
  - deploy
  - verify
  - destroy

variables:
  IMAGE_NAME: $CI_REGISTRY_IMAGE
  IMAGE_TAG: $CI_COMMIT_SHORT_SHA
  TF_STATE_BUCKET: project-a-tf-state

# ============================================================
# SHARED CONFIGURATIONS
# ============================================================

.helm_base:
  image: alpine/helm:3.14
  before_script:
    - mkdir -p ~/.kube
    - echo "$KUBE_CONFIG" | base64 -d > ~/.kube/config
    - chmod 600 ~/.kube/config

.terraform_base:
  image:
    name: hashicorp/terraform:1.7
    entrypoint: [""]
  before_script:
    - cd $TF_DIR
    - terraform init
        -backend-config="bucket=$TF_STATE_BUCKET"
        -backend-config="key=$TF_STATE_KEY"
        -backend-config="region=eu-central-1"

# ============================================================
# LINT STAGE
# ============================================================

lint:dockerfile:
  stage: lint
  image: hadolint/hadolint:latest-alpine
  script:
    - hadolint Dockerfile
  rules:
    - if: $CI_MERGE_REQUEST_IID
    - if: $CI_COMMIT_BRANCH == "main"

lint:yaml:
  stage: lint
  image: cytopia/yamllint:1.26
  script:
    - yamllint .gitlab-ci.yml
    - yamllint helm/
  rules:
    - if: $CI_MERGE_REQUEST_IID
    - if: $CI_COMMIT_BRANCH == "main"

lint:terraform:
  stage: lint
  image:
    name: hashicorp/terraform:1.7
    entrypoint: [""]
  script:
    - terraform fmt -check -recursive terraform/
  rules:
    - if: $CI_MERGE_REQUEST_IID
    - if: $CI_COMMIT_BRANCH == "main"

# ============================================================
# BUILD STAGE
# ============================================================

build:docker-image:
  stage: build
  image: docker:24
  services:
    - docker:24-dind
  script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
    - docker build
        --cache-from $IMAGE_NAME:latest
        --tag $IMAGE_NAME:$IMAGE_TAG
        --tag $IMAGE_NAME:latest
        .
    - docker push $IMAGE_NAME:$IMAGE_TAG
    - docker push $IMAGE_NAME:latest
  rules:
    - if: $CI_MERGE_REQUEST_IID
    - if: $CI_COMMIT_BRANCH == "main"
    - if: $CI_COMMIT_TAG =~ /^v\d+\.\d+\.\d+$/

# ============================================================
# TEST STAGE
# ============================================================

test:security-scan:
  stage: test
  image:
    name: aquasec/trivy:latest
    entrypoint: [""]
  script:
    - trivy image
        --exit-code 1
        --severity HIGH,CRITICAL
        --no-progress
        $IMAGE_NAME:$IMAGE_TAG
  allow_failure: true  # ne blokiraj deploy za security findings u projektu učenja
  rules:
    - if: $CI_MERGE_REQUEST_IID
    - if: $CI_COMMIT_BRANCH == "main"

test:helm-lint:
  stage: test
  image: alpine/helm:3.14
  script:
    - helm lint helm/helloworld/
    - helm template helm/helloworld/ -f helm/helloworld/values/dev.yaml
  rules:
    - if: $CI_MERGE_REQUEST_IID
    - if: $CI_COMMIT_BRANCH == "main"

# ============================================================
# TERRAFORM PLAN STAGE
# ============================================================

tf-plan:dev:
  extends: .terraform_base
  stage: tf-plan
  variables:
    TF_DIR: terraform/environments/dev
    TF_STATE_KEY: dev/terraform.tfstate
    AWS_ROLE_ARN: $DEV_AWS_ROLE_ARN
  script:
    - terraform plan -no-color -out=tfplan | tee plan.txt
    - |
      if [ -n "$CI_MERGE_REQUEST_IID" ]; then
        PLAN=$(cat plan.txt | tail -20)
        curl -s --request POST \
          --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
          --data "body=**Terraform plan (dev):**\n\`\`\`\n${PLAN}\n\`\`\`" \
          "$CI_API_V4_URL/projects/$CI_PROJECT_ID/merge_requests/$CI_MERGE_REQUEST_IID/notes"
      fi
  artifacts:
    paths: [terraform/environments/dev/tfplan]
    expire_in: 1 day
  rules:
    - if: $CI_MERGE_REQUEST_IID
    - if: $CI_COMMIT_BRANCH == "main"

# ============================================================
# TERRAFORM APPLY STAGE
# ============================================================

tf-apply:dev:
  extends: .terraform_base
  stage: tf-apply
  variables:
    TF_DIR: terraform/environments/dev
    TF_STATE_KEY: dev/terraform.tfstate
    AWS_ROLE_ARN: $DEV_AWS_ROLE_ARN
  script:
    - terraform apply -auto-approve
  needs: [tf-plan:dev]
  rules:
    - if: $CI_COMMIT_BRANCH == "main"

# ============================================================
# DEPLOY STAGE
# ============================================================

deploy:review:
  extends: .helm_base
  stage: deploy
  variables:
    KUBE_CONFIG: $KUBE_CONFIG_DEV
  environment:
    name: review/$CI_MERGE_REQUEST_IID
    url: https://mr-$CI_MERGE_REQUEST_IID.dev.firma.com
    on_stop: destroy:review
    auto_stop_in: 3 days
  script:
    - >
      helm upgrade --install helloworld-mr-$CI_MERGE_REQUEST_IID
      ./helm/helloworld
      --namespace helloworld-mr-$CI_MERGE_REQUEST_IID
      --create-namespace
      -f helm/helloworld/values/dev.yaml
      --set image.tag=$IMAGE_TAG
      --set ingress.host=mr-$CI_MERGE_REQUEST_IID.dev.firma.com
      --wait --timeout 5m --atomic
  rules:
    - if: $CI_MERGE_REQUEST_IID

deploy:dev:
  extends: .helm_base
  stage: deploy
  variables:
    KUBE_CONFIG: $KUBE_CONFIG_DEV
  environment:
    name: dev
    url: https://app.dev.firma.com
  script:
    - >
      helm upgrade --install helloworld ./helm/helloworld
      --namespace helloworld-dev --create-namespace
      -f helm/helloworld/values/dev.yaml
      --set image.tag=$IMAGE_TAG
      --wait --timeout 5m --atomic
  rules:
    - if: $CI_COMMIT_BRANCH == "main"

deploy:staging:
  extends: .helm_base
  stage: deploy
  variables:
    KUBE_CONFIG: $KUBE_CONFIG_STAGING
  environment:
    name: staging
    url: https://app.staging.firma.com
  script:
    - >
      helm upgrade --install helloworld ./helm/helloworld
      --namespace helloworld-staging --create-namespace
      -f helm/helloworld/values/staging.yaml
      --set image.tag=$IMAGE_TAG
      --wait --timeout 5m --atomic
  rules:
    - if: $CI_COMMIT_BRANCH == "main"

deploy:prod:
  extends: .helm_base
  stage: deploy
  variables:
    KUBE_CONFIG: $KUBE_CONFIG_PROD
  environment:
    name: prod
    url: https://app.firma.com
  when: manual
  script:
    - >
      helm upgrade --install helloworld ./helm/helloworld
      --namespace helloworld-prod --create-namespace
      -f helm/helloworld/values/prod.yaml
      --set image.tag=$IMAGE_TAG
      --wait --timeout 10m --atomic
  rules:
    - if: $CI_COMMIT_TAG =~ /^v\d+\.\d+\.\d+$/
      when: manual

# ============================================================
# VERIFY STAGE
# ============================================================

verify:dev:
  stage: verify
  image: curlimages/curl:latest
  script:
    - sleep 15
    - curl -f --max-time 30 https://app.dev.firma.com/
  rules:
    - if: $CI_COMMIT_BRANCH == "main"

# ============================================================
# DESTROY STAGE (svi manuelni)
# ============================================================

destroy:review:
  extends: .helm_base
  stage: destroy
  variables:
    KUBE_CONFIG: $KUBE_CONFIG_DEV
    GIT_STRATEGY: none
  environment:
    name: review/$CI_MERGE_REQUEST_IID
    action: stop
  when: manual
  script:
    - helm uninstall helloworld-mr-$CI_MERGE_REQUEST_IID
        --namespace helloworld-mr-$CI_MERGE_REQUEST_IID || true
    - kubectl delete namespace helloworld-mr-$CI_MERGE_REQUEST_IID || true
  rules:
    - if: $CI_MERGE_REQUEST_IID
      when: manual

destroy:dev:
  stage: destroy
  image:
    name: hashicorp/terraform:1.7
    entrypoint: [""]
  when: manual
  environment:
    name: dev
    action: stop
  script:
    - echo "$KUBE_CONFIG_DEV" | base64 -d > /tmp/kubeconfig
    - export KUBECONFIG=/tmp/kubeconfig
    - helm uninstall helloworld --namespace helloworld-dev || true
    - kubectl delete namespace helloworld-dev || true
    - cd terraform/environments/dev
    - terraform init -backend-config="bucket=$TF_STATE_BUCKET"
    - terraform destroy -auto-approve
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
      when: manual

# ============================================================
# NOTIFICATIONS (.post uvijek radi)
# ============================================================

notify:failure:
  stage: .post
  image: curlimages/curl:latest
  when: on_failure
  script:
    - |
      curl -X POST $SLACK_WEBHOOK_URL \
        -H 'Content-type: application/json' \
        --data "{\"text\": \"Pipeline failed: $CI_COMMIT_BRANCH by $GITLAB_USER_NAME — <$CI_PIPELINE_URL|View>\"}"
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
      when: on_failure
```

> **Podman alternativa za `build:docker-image` job:**
> Zamijeni `docker:24-dind` s Podman pristupom koji ne zahtijeva privileged runner:
> ```yaml
> build:podman-image:
>   image: quay.io/podman/stable
>   variables:
>     STORAGE_DRIVER: vfs
>   script:
>     - podman login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
>     - podman build --tag $IMAGE_NAME:$IMAGE_TAG --tag $IMAGE_NAME:latest .
>     - podman push $IMAGE_NAME:$IMAGE_TAG
>     - podman push $IMAGE_NAME:latest
> ```
> Za multi-platform build: `podman manifest create` + `podman build --platform` (vidi modul 01/12).

---

## Testiranje pipeline-a: step by step

**Korak 1: Push na feature branch**
```bash
git checkout -b feature/novi-naslov
# Izmijeni index.html
git add . && git commit -m "feat: promijeni naslov"
git push origin feature/novi-naslov
```
Otvori MR u GitLab UI. Vidi: lint → build → test → deploy:review.
Klikni "View app" link u MR panelu.

**Korak 2: Merge u main**
Merge MR. Prati: deploy:dev → deploy:staging → verify:dev.
Provjeri `https://app.dev.firma.com` — nova verzija.

**Korak 3: Tag za prod**
```bash
git tag v1.0.0
git push origin v1.0.0
```
U GitLab Pipelines vidiš pipeline za tag. `deploy:prod` je manuelni — klikni "Run".

**Korak 4: Destroy dev**
Pipelines → pronađi pipeline na main → `destroy:dev` job → klikni "Run".
Provjeri AWS konzolu — EKS workload gone.

---

## AI workflow

Ceo `.gitlab-ci.yml` daj Claude za review i optimizaciju:

> "Ovo je .gitlab-ci.yml za project-A. Review:
> 1. Postoje li sigurnosni propusti (exposed secrets, previše permisija)?
> 2. Koje jobove možeš paralelizovati?
> 3. Gdje se gubi najviše vremena?
> 4. Nedostaje li nešto što bi trebalo biti u production-grade pipeline-u?"
