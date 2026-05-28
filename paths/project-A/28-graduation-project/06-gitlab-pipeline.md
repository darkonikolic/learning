# GitLab Pipeline

## Kompletni .gitlab-ci.yml

```yaml
# .gitlab-ci.yml
include:
  - local: '.gitlab/ci/lint.yml'
  - local: '.gitlab/ci/build.yml'
  - local: '.gitlab/ci/terraform.yml'
  - local: '.gitlab/ci/deploy.yml'

variables:
  DOCKER_DRIVER: overlay2
  DOCKER_BUILDKIT: "1"
  IMAGE_TAG: $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA
  HELM_CHART: ./helm/helloworld

stages:
  - lint
  - build
  - tf-plan
  - tf-apply
  - deploy
  - verify
  - destroy
```

## .gitlab/ci/lint.yml

```yaml
# Svi lint jobovi rade paralelno — nisu međusobno zavisni
hadolint:
  stage: lint
  image: hadolint/hadolint:latest-debian
  script:
    - hadolint app/Dockerfile

helm-lint:
  stage: lint
  image:
    name: alpine/helm:3.14.0
    entrypoint: [""]
  script:
    - helm lint $HELM_CHART
    - helm lint $HELM_CHART -f $HELM_CHART/values/prod.yaml

terraform-lint:
  stage: lint
  image:
    name: hashicorp/terraform:1.7
    entrypoint: [""]
  script:
    - find terraform -name "*.tf" -exec dirname {} \; | sort -u | while read dir; do
        cd $CI_PROJECT_DIR/$dir && terraform fmt -check && terraform validate || true;
      done
```

Sva tri lint joba rade u paraleli — `helm-lint` ne čeka `hadolint`. Štedi
2-3 minute po pipeline runu.

## .gitlab/ci/build.yml

```yaml
docker-build:
  stage: build
  image: docker:24
  services:
    - docker:24-dind
  needs: ["hadolint"]   # Čeka samo hadolint, ne sve lint
  before_script:
    - docker login -u $CI_REGISTRY_USER -p $CI_JOB_TOKEN $CI_REGISTRY
  script:
    - docker build
        --cache-from $CI_REGISTRY_IMAGE:latest
        --build-arg BUILDKIT_INLINE_CACHE=1
        -f app/Dockerfile
        -t $IMAGE_TAG
        -t $CI_REGISTRY_IMAGE:latest
        .
    - docker push $IMAGE_TAG
    - docker push $CI_REGISTRY_IMAGE:latest

> **Podman multi-platform u GitLab CI:**
> ```yaml
> build:
>   image: quay.io/podman/stable
>   variables:
>     STORAGE_DRIVER: vfs
>   script:
>     - podman manifest create $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
>     - podman build --platform linux/amd64 --manifest $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
>     - podman build --platform linux/arm64 --manifest $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
>     - podman manifest push --all $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
> ```
> Nema potrebe za `buildx` ili BuildKit — Podman manifest nativno podržava multi-platform.

trivy-scan:
  stage: build
  image:
    name: aquasec/trivy:latest
    entrypoint: [""]
  needs: ["docker-build"]
  script:
    - trivy image
        --exit-code 1
        --severity HIGH,CRITICAL
        --no-progress
        $IMAGE_TAG
  allow_failure: false   # Pipeline se stopa na HIGH/CRITICAL
```

`--cache-from $CI_REGISTRY_IMAGE:latest` je docker layer cache. Svaki push
povuče prethodni `latest` image kao cache — slojevi koji se nisu promijenili
se ne rebuilduju. Štedi 3-5 minuta za nginx image.

## .gitlab/ci/terraform.yml

```yaml
.tf-base: &tf-base
  image:
    name: hashicorp/terraform:1.7
    entrypoint: [""]
  before_script:
    - &aws-auth >
      export $(printf "AWS_ACCESS_KEY_ID=%s AWS_SECRET_ACCESS_KEY=%s
      AWS_SESSION_TOKEN=%s" $(aws sts assume-role-with-web-identity
      --role-arn $AWS_ROLE_ARN_DEV
      --role-session-name "gitlab-ci-$CI_PIPELINE_ID"
      --web-identity-token $CI_JOB_JWT_V2
      --duration-seconds 3600
      --query 'Credentials.[AccessKeyId,SecretAccessKey,SessionToken]'
      --output text))
    - cd terraform/envs/dev
    - terraform init

tf-plan-dev:
  <<: *tf-base
  stage: tf-plan
  script:
    - terraform plan -var-file=dev.tfvars -out=tfplan -no-color 2>&1 | tee plan.txt
    - |
      if [ -n "$CI_MERGE_REQUEST_IID" ]; then
        BODY="## Terraform Plan (dev)\n\`\`\`\n$(cat plan.txt)\n\`\`\`"
        curl --silent --request POST \
          --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
          --data-urlencode "body=$BODY" \
          "$CI_API_V4_URL/projects/$CI_PROJECT_ID/merge_requests/$CI_MERGE_REQUEST_IID/notes"
      fi
  artifacts:
    paths: [terraform/envs/dev/tfplan]
    expire_in: 1 hour
  rules:
    - if: $CI_MERGE_REQUEST_IID

tf-apply-dev:
  <<: *tf-base
  stage: tf-apply
  script:
    - terraform apply -auto-approve tfplan
  dependencies: ["tf-plan-dev"]
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
      when: on_success
```

## .gitlab/ci/deploy.yml

```yaml
.helm-base: &helm-base
  image: alpine/helm:3.14.0
  before_script:
    - *aws-auth
    - aws eks update-kubeconfig --name project-a-dev --region $AWS_REGION

deploy-dev:
  <<: *helm-base
  stage: deploy
  script:
    - helm upgrade --install helloworld $HELM_CHART
        --namespace helloworld-dev
        --create-namespace
        --set image.tag=$CI_COMMIT_SHORT_SHA
        -f $HELM_CHART/values/dev.yaml
        --wait --timeout 5m
  environment:
    name: dev
    url: https://app.$DOMAIN_DEV
  rules:
    - if: $CI_COMMIT_BRANCH == "main"

# Review app za svaki MR
deploy-review:
  <<: *helm-base
  stage: deploy
  variables:
    REVIEW_NS: mr-$CI_MERGE_REQUEST_IID
    REVIEW_HOST: mr-$CI_MERGE_REQUEST_IID.$DOMAIN_DEV
  script:
    - helm upgrade --install helloworld-$REVIEW_NS $HELM_CHART
        --namespace $REVIEW_NS
        --create-namespace
        --set image.tag=$CI_COMMIT_SHORT_SHA
        --set ingress.host=$REVIEW_HOST
        -f $HELM_CHART/values/dev.yaml
        --wait --timeout 5m
  environment:
    name: review/$CI_MERGE_REQUEST_IID
    url: https://mr-$CI_MERGE_REQUEST_IID.$DOMAIN_DEV
    on_stop: destroy-review
  rules:
    - if: $CI_MERGE_REQUEST_IID

destroy-review:
  <<: *helm-base
  stage: destroy
  variables:
    REVIEW_NS: mr-$CI_MERGE_REQUEST_IID
  script:
    - helm uninstall helloworld-$REVIEW_NS --namespace $REVIEW_NS --wait
    - kubectl delete namespace $REVIEW_NS
  environment:
    name: review/$CI_MERGE_REQUEST_IID
    action: stop
  rules:
    - if: $CI_MERGE_REQUEST_IID
      when: manual

deploy-prod:
  <<: *helm-base
  stage: deploy
  before_script:
    - *aws-auth  # Isti pattern ali sa PROD role
    - aws eks update-kubeconfig --name project-a-prod --region $AWS_REGION
  script:
    - helm upgrade --install helloworld $HELM_CHART
        --namespace helloworld-prod
        --create-namespace
        --set image.tag=$CI_COMMIT_SHORT_SHA
        -f $HELM_CHART/values/prod.yaml
        --wait --timeout 10m
  environment:
    name: production
    url: https://app.$DOMAIN_PROD
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
      when: manual
```

## Pregled svih jobova

| Job | Trigger | Trajanje | Šta radi |
|-----|---------|---------|---------|
| `hadolint` | Svaki push | ~30s | Lint Dockerfile |
| `helm-lint` | Svaki push | ~20s | Lint Helm chart |
| `terraform-lint` | Svaki push | ~30s | fmt + validate |
| `docker-build` | Nakon hadolint | ~3m | Build + push image |
| `trivy-scan` | Nakon build | ~2m | CVE scan, fail na HIGH |
| `tf-plan-dev` | Samo MR | ~2m | Plan + komentar na MR |
| `tf-apply-dev` | Push na main | ~4m | Apply Terraform |
| `deploy-dev` | Push na main | ~2m | Helm deploy na dev |
| `deploy-review` | Svaki MR | ~2m | Review app kreiranje |
| `destroy-review` | Manual (MR zatvoren) | ~1m | Brisanje review app-a |
| `deploy-prod` | Manual na main | ~3m | Prod deploy |

## AWS OIDC auth u pipeline-u

```yaml
# OIDC token dobijamo iz $CI_JOB_JWT_V2 (GitLab 15.7+)
# AWS STS konvertuje JWT u privremene credentials
# Credentials traju 3600 sekundi (1 sat)
# Svaki job radi zasebno assume-role — nema dijeljenja credentials između jobova

# Provjera da OIDC radi (dodaj u before_script za debug):
- aws sts get-caller-identity
```

## AI prompt za pipeline optimizaciju

```
Ovaj GitLab CI pipeline traje 15 minuta. Evo .gitlab-ci.yml:
[prijepi cijeli sadržaj]

Analiziraj:
1. Koji jobovi mogu raditi paralelno (nisu međusobno zavisni)?
2. Gdje je docker build spor — kako optimizovati layer caching?
3. Da li terraform apply mora raditi na svakom push na main ili samo
   kada se .tf fajlovi promijene?
4. Predloži konkretne promjene sa procijenjenom uštedom vremena.
```
