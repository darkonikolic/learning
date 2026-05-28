# 08 — Pipeline best practices

## Teorija

Dobro napisan pipeline je **dokumentacija koja se izvršava**. Čitaš `.gitlab-ci.yml`
i razumiješ: koje korake projekt ima, koji su kritični, gdje može failovati i što se
dešava u svakom scenariju. Loš pipeline je crna kutija iz koje niko ne razumije izlaz.

---

## Pipeline kao dokumentacija

Stage i job nazivi trebaju biti čitljivi, a ne tehničke skracenice:

```yaml
# Loše
stages: [b, t, d]
j1:
  stage: b
  script: docker build .

# Dobro
stages:
  - build
  - test
  - deploy
  - verify

build:docker-image:
  stage: build
  script:
    - docker build -t $IMAGE_NAME:$CI_COMMIT_SHORT_SHA .
```

Kad pipeline faila u "build:docker-image", odmah znaš gdje je problem.
Kad faila u "j1", moraš čitati kod da shvatiš što je to.

---

## Fail fast: linting i statička analiza na početku

Daj programeru feedback u prvih 2 minuta, ne nakon 15 minuta:

```yaml
stages:
  - lint        # 1-2 minute, ne zahteva Docker build
  - build       # 3-5 minuta
  - test        # paralelno, 2-5 minuta
  - deploy
  - verify

lint:yaml:
  stage: lint
  image: cytopia/yamllint:1.26
  script:
    - yamllint .gitlab-ci.yml helm/

lint:dockerfile:
  stage: lint
  image: hadolint/hadolint:latest-alpine
  script:
    - hadolint Dockerfile

lint:terraform:
  stage: lint
  image: hashicorp/terraform:1.7
  script:
    - terraform fmt -check -recursive
    - terraform validate
```

Grješka u Dockerfileu ili Terraformu → feedback za 60 sekundi, ne 15 minuta.

---

## Paralelizacija: neovisni jobovi u istom stage-u

Jobovi u istom stage-u teku **paralelno** (po defaultu, ako ima dostupnih runnera).

```yaml
test:
  stage: test
  script:
    - npm test
    - trivy image $IMAGE_NAME  # security scan — zašto je ovo u istom jobu?

# Bolje: dva neovisna joba koji teku paralelno
test:unit:
  stage: test
  script:
    - npm test

test:security-scan:
  stage: test
  script:
    - trivy image $IMAGE_NAME
```

Ako test:unit traje 2 minute i test:security-scan traje 3 minute, paralelno = 3 minute.
Sekvencijalno = 5 minuta. Na 20 jobova, razlika je ogromna.

---

## Artifacts retention: ne čuvaj sve zauvijek

```yaml
build:docker-image:
  artifacts:
    paths:
      - build/
    expire_in: 1 hour   # samo za sljedeći stage, ne treba duže

terraform:plan:
  artifacts:
    paths:
      - terraform/tfplan
    expire_in: 1 day    # reviewer ima 24h da odobri

test:coverage:
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage/cobertura-coverage.xml
    expire_in: 1 week   # korisno za trending, ali ne zauvijek
```

GitLab storage nije beskonačan. Artifacts koji nikad ne expiraju akumuliraju se.

---

## Runner tags: specijalizirani runneri za heavy jobs

```yaml
build:docker-image:
  tags:
    - docker          # runner s Docker daemon-om

deploy:prod:
  tags:
    - restricted      # runner koji ima pristup prod networkingu
    - kubernetes      # runner unutar K8s clustera

test:gpu:
  tags:
    - gpu             # runner s GPU za ML jobove
```

Bez tagova, job može ići na bilo koji runner. Za sigurnosno-osjetljive jobove
(prod deploy) koristi specijalizirane, izolovane runnere.

---

## DRY: reference, extends, include

**`extends`**: naslijedi konfiguraciju od drugog joba

```yaml
.deploy_base:
  image: alpine/helm:3.14
  before_script:
    - echo "$KUBE_CONFIG" | base64 -d > ~/.kube/config

deploy:dev:
  extends: .deploy_base
  variables:
    KUBE_CONFIG: $KUBE_CONFIG_DEV
  environment:
    name: dev

deploy:staging:
  extends: .deploy_base
  variables:
    KUBE_CONFIG: $KUBE_CONFIG_STAGING
  environment:
    name: staging
```

**`include`**: uvuci `.gitlab-ci.yml` iz drugog fajla ili projekta

```yaml
include:
  - local: '.gitlab/ci/build.yml'
  - local: '.gitlab/ci/deploy.yml'
  - project: 'company/shared-ci'
    file: '/templates/docker-build.yml'
    ref: main
```

Dijeljeni templates u grupi: svi projekti koriste isti build template, centralizovano ažurirani.

---

## Notifikacije: Slack/email na failed pipeline

```yaml
notify:slack:failure:
  stage: .post
  image: curlimages/curl:latest
  when: on_failure
  script:
    - |
      curl -X POST $SLACK_WEBHOOK_URL \
        -H 'Content-type: application/json' \
        --data "{
          \"text\": \"Pipeline failed on branch *$CI_COMMIT_BRANCH* by $GITLAB_USER_NAME\",
          \"attachments\": [{
            \"color\": \"danger\",
            \"text\": \"<$CI_PIPELINE_URL|View Pipeline>\"
          }]
        }"

notify:slack:prod-deployed:
  stage: .post
  when: on_success
  rules:
    - if: $CI_COMMIT_TAG =~ /^v\d+\.\d+\.\d+$/
  script:
    - |
      curl -X POST $SLACK_WEBHOOK_URL \
        --data "{\"text\": \"🚀 $CI_COMMIT_TAG deployovan na produkciju!\"}"
```

`.post` stage se uvijek izvršava zadnji, bez obzira na status prethodnih stageva.

---

## Pipeline duration: target < 10 minuta

Feedback loop od 30 minuta demotiviše programere. Cilj za project-A:

| Stage | Target |
|-------|--------|
| lint | < 2 min |
| build | < 5 min |
| test | < 3 min (paralelno) |
| deploy | < 3 min |
| verify | < 1 min |
| **Ukupno** | **< 14 min** |

Optimizacije:
- Docker layer caching: `--cache-from` u build jobu
- Parallel test execution
- Lightweight lint images (ne pull pun Ubuntu za yamllint)
- `needs:` keyword za prijevremeni start downstream joba

---

## AI workflow

Sporiji pipeline? Daj Claude `.gitlab-ci.yml` za optimizaciju:

> "Ovaj pipeline traje 28 minuta. Priloži .gitlab-ci.yml. Identifikuj bottlenecke
> i predloži optimizacije: paralelizacija, caching, stage reorganizacija.
> Prikaži očekivano trajanje nakon optimizacije."

---

## Veza sa project-A

Za project-A cilj je pipeline koji:
1. Daje lint feedback za 90 sekundi
2. Ima build + test paralelno, ne sekvencijalno
3. Deploy stage koji jasno pokazuje koji environment se ažurira
4. Slack notifikaciju na failed pipeline (da ne propustiš broken main)
5. Ukupno trajanje ispod 10 minuta za push na main branch
