# 05 — GitLab CI integracija

## Kompletna pipeline arhitektura

```
┌──────────┐   ┌──────────────────────────────────────┐   ┌──────────┐
│          │   │           STAGE: test                │   │          │
│          │   │  ┌─────────────┐  ┌────────────────┐ │   │          │
│  commit  │──▶│  │  test:go    │  │   test:php     │ │──▶│  build   │
│          │   │  │  test:vue   │  │  (paralelno)   │ │   │          │
│          │   │  └─────────────┘  └────────────────┘ │   │          │
└──────────┘   └──────────────────────────────────────┘   └────┬─────┘
                                                               │
               ┌──────────┐   ┌──────────┐   ┌───────────────▼──────┐
               │          │   │          │   │                       │
               │ tf-apply │◀──│ tf-plan  │◀──│  deploy (review app) │
               │          │   │          │   │                       │
               └──────────┘   └──────────┘   └──────────┬───────────┘
                                                         │
                                           ┌─────────────▼──────────┐
                                           │       STAGE: e2e       │
                                           │  e2e:review            │
                                           │  (against review app)  │
                                           └─────────────┬──────────┘
                                                         │
                                           ┌─────────────▼──────────┐
                                           │  STAGE: destroy        │
                                           │  (cleanup review app)  │
                                           └────────────────────────┘
```

---

## Kompletan `.gitlab-ci.yml`

```yaml
# .gitlab-ci.yml

stages:
  - test
  - build
  - tf-plan
  - tf-apply
  - deploy
  - e2e
  - destroy

# ============================================
# Varijable (globalne)
# ============================================
variables:
  DOCKER_BUILDKIT: "1"
  DOCKER_DRIVER: overlay2
  # Registry
  REGISTRY: $CI_REGISTRY
  IMAGE_TAG: $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA

# ============================================
# STAGE: test
# ============================================

test:go:
  stage: test
  image: golang:1.22-alpine
  services:
    - name: mysql:8.0
      alias: mysql
    - name: redis:7-alpine
      alias: redis
  variables:
    MYSQL_ROOT_PASSWORD: testpass
    MYSQL_DATABASE:      testdb
    MYSQL_USER:          testuser
    MYSQL_PASSWORD:      userpass
    # Ove vrijednosti čita tvoj app u test modu
    DB_HOST:    mysql
    DB_PORT:    "3306"
    DB_NAME:    testdb
    DB_USER:    testuser
    DB_PASS:    userpass
    REDIS_HOST: redis
    REDIS_PORT: "6379"
  before_script:
    - apk add --no-cache git
    - go install github.com/jstemmer/go-junit-report/v2@latest
  script:
    # Unit testovi (brzo, nema services)
    - go test ./internal/... -v -race -count=1 -coverprofile=coverage.out 2>&1 | tee test-output.txt
    # Coverage check
    - go tool cover -func=coverage.out | tail -1
    # Fail ako coverage < 70%
    - |
      COVERAGE=$(go tool cover -func=coverage.out | tail -1 | awk '{print $3}' | tr -d '%')
      echo "Coverage: ${COVERAGE}%"
      if [ $(echo "$COVERAGE < 70" | bc -l) -eq 1 ]; then
        echo "ERROR: Coverage ${COVERAGE}% je ispod minimuma 70%"
        exit 1
      fi
    # JUnit XML
    - cat test-output.txt | go-junit-report -set-exit-code > junit.xml
    # Integration testovi (s MySQL + Redis services)
    - go test ./internal/repository/... -v -race -count=1 -tags=integration 2>&1 | go-junit-report -set-exit-code >> junit.xml
  artifacts:
    when: always  # Sačuvaj čak i ako test padne
    reports:
      junit: junit.xml
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
    paths:
      - coverage.out
    expire_in: 1 week
  coverage: '/total:\s+\(statements\)\s+(\d+\.\d+)%/'
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH

test:php:
  stage: test
  image: php:8.3-fpm-alpine
  before_script:
    - apk add --no-cache $PHPIZE_DEPS linux-headers
    - pecl install pcov && docker-php-ext-enable pcov
    - curl -sS https://getcomposer.org/installer | php -- --install-dir=/usr/local/bin --filename=composer
    - composer install --with-all-dependencies --no-interaction
  script:
    - ./vendor/bin/pest --ci --log-junit=junit.xml --coverage-cobertura=coverage.xml --min=70
  artifacts:
    when: always
    reports:
      junit: junit.xml
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
    expire_in: 1 week
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH

test:vue:
  stage: test
  image: node:20-alpine
  before_script:
    - cd frontend
    - npm ci
  script:
    - npm run test:unit -- --reporter=verbose --reporter=junit --outputFile=junit.xml
    - npm run type-check
  artifacts:
    when: always
    reports:
      junit: frontend/junit.xml
    expire_in: 1 week
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH

# ============================================
# STAGE: build
# ============================================

build:go:
  stage: build
  image: docker:24
  services:
    - docker:24-dind
  before_script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
  script:
    # Dockerfile test stage je uključen u build — ako pane, build pane
    - docker build
        --target production
        --tag $CI_REGISTRY_IMAGE/go-service:$CI_COMMIT_SHA
        --file services/go/Dockerfile
        services/go/
    - docker push $CI_REGISTRY_IMAGE/go-service:$CI_COMMIT_SHA
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == "main"

# ============================================
# STAGE: deploy (review app)
# ============================================

deploy:review:
  stage: deploy
  image: bitnami/kubectl:latest
  environment:
    name: review/$CI_COMMIT_REF_SLUG
    url: https://mr-$CI_MERGE_REQUEST_IID.dev.firma.com
    on_stop: destroy:review
    auto_stop_in: 1 day
  script:
    - kubectl config use-context $KUBE_CONTEXT_DEV
    - envsubst < k8s/review-app.yaml | kubectl apply -f -
    - kubectl rollout status deployment/review-$CI_MERGE_REQUEST_IID -n review --timeout=300s
  rules:
    - if: $CI_MERGE_REQUEST_IID

# ============================================
# STAGE: e2e
# ============================================

e2e:review:
  stage: e2e
  image: mcr.microsoft.com/playwright:v1.42.0-jammy
  needs:
    - job: deploy:review  # ne čeka sve prethodne jobs, samo deploy
  variables:
    APP_URL: "https://mr-$CI_MERGE_REQUEST_IID.dev.firma.com"
  script:
    - cd tests/e2e
    - npm ci
    - npx playwright test --reporter=junit,html
  after_script:
    # Upload Playwright HTML report kao artifact
    - echo "Playwright report dostupan u artifacts"
  artifacts:
    when: always
    reports:
      junit: tests/e2e/junit.xml
    paths:
      - tests/e2e/playwright-report/
    expire_in: 1 week
  rules:
    - if: $CI_MERGE_REQUEST_IID

# ============================================
# STAGE: destroy
# ============================================

destroy:review:
  stage: destroy
  image: bitnami/kubectl:latest
  environment:
    name: review/$CI_COMMIT_REF_SLUG
    action: stop
  script:
    - kubectl config use-context $KUBE_CONTEXT_DEV
    - kubectl delete deployment review-$CI_MERGE_REQUEST_IID -n review --ignore-not-found
    - kubectl delete service review-$CI_MERGE_REQUEST_IID -n review --ignore-not-found
    - kubectl delete ingress review-$CI_MERGE_REQUEST_IID -n review --ignore-not-found
  when: manual
  rules:
    - if: $CI_MERGE_REQUEST_IID
```

---

## Paralelno izvršavanje u test stage-u

`test:go`, `test:php`, i `test:vue` su u istom `test` stage-u. GitLab pokreće sve jobs u istom stage-u paralelno. Ukupno trajanje test stage-a = trajanje najsporijeg job-a, ne suma svih.

Tipično:
- `test:go`: 3-4 minute (uključuje integration testove s MySQL/Redis startup)
- `test:php`: 1-2 minute
- `test:vue`: 30 sekundi

Bez paralelizacije: 5-7 minuta. S paralelizacijom: 3-4 minute.

---

## `needs:` vs stage dependency

Defaultno, svaki stage čeka da svi jobs u prethodnom stage-u završe. `needs:` mijenja ovo:

```yaml
e2e:review:
  needs:
    - job: deploy:review
    # NE čeka build:php ili bilo šta drugo
```

`deploy:review` je ready čim Docker build završi. E2E može početi čim deploy prođe, ne čekajući sve ostale jobs u `deploy` stage-u (ako ih ima više).

---

## JUnit u MR UI

Kada `artifacts: reports: junit:` je konfigurisan, GitLab prikazuje:
- Broj prošlih/palih testova u MR overview
- Lista specifičnih testova koji su pali
- Diff od prethodnog run-a: "3 new failures, 1 fixed"
- Klik na failed test → stack trace

Ovo drastično smanjuje debugging cycle. Umjesto da otvoriš CI log i tražiš FAIL pattern, odmah vidiš koji test pada.

---

## Coverage u GitLab

```yaml
coverage: '/total:\s+\(statements\)\s+(\d+\.\d+)%/'
```

Ovaj regex GitLab primjenjuje na job log da izvuče coverage broj. Prikazuje se:
- U MR-u: coverage% za ovu granu
- Diff prema main grani: "Coverage changed from 73% to 71%"
- Badge na projektu: `[![coverage](https://gitlab.com/.../badges/main/coverage.svg)](...)` 

Cobertura format (`coverage_report: coverage_format: cobertura`) omogućuje line-level coverage diff direktno u MR — vidiš koje linije koda nisu pokrivene testovima.

---

## Rules: kada se pokreće koji job

```yaml
rules:
  - if: $CI_PIPELINE_SOURCE == "merge_request_event"  # MR pipeline
  - if: $CI_COMMIT_BRANCH                              # svaki push na bilo koji branch
```

Bez `rules:` — job se pokreće uvijek. S ovim `rules:` — pokreće se na svaki commit i na svaki MR. Ovo je željeno ponašanje: testovi se nikad ne preskakuju.

Za jobs koji trebaju ići samo na `main`:
```yaml
rules:
  - if: $CI_COMMIT_BRANCH == "main"
```

Za jobs koji trebaju ići samo na MR:
```yaml
rules:
  - if: $CI_MERGE_REQUEST_IID
```

---

## Protected branch + merge requirements

U GitLab Settings → Repository → Protected branches:

| Branch | Allowed to push | Allowed to merge |
|--------|-----------------|------------------|
| `main` | No one | Maintainers |
| `staging` | No one | Developers + Maintainers |

U GitLab Settings → Merge Requests:

- **"Pipelines must succeed"** — merge button je greyed out dok pipeline nije zelena
- **"All discussions must be resolved"** — nema merge dok postoje otvoreni komentari
- **Required approvals: 1** — bar jedan reviewer mora approvati

Ove tri kontrole zajedno garantiraju: nema koda u `main` koji nije prošao testove, nije review-an, ili ima otvorenih pitanja.
