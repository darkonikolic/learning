# 03 - Stages, Jobs i Artifacts

## Stages: sekvencijalni tok

Stages definišu redosled izvršavanja. GitLab ih izvršava jedan po jedan — sljedeći stage počinje tek kada svi jobovi prethodnog završe uspješno.

```yaml
stages:
  - build      # 1. gradi image
  - test       # 2. testira image (samo ako build prošao)
  - release    # 3. taguje image kao stable
  - deploy     # 4. deplouje na okruženje
```

Ako `build` stage fail-uje, `test` se nikad ne pokreće. Ovo je željeno ponašanje — nema smisla testirati image koji nije ni napravljen.

**Paralelizacija unutar stage-a**: svi jobovi istog stage-a pokreću se istovremeno (ako ima slobodnih runnera). Ovo je ključno za ubrzanje pipeline-a:

```yaml
test:
  stage: test

lint:
  stage: test   # pokreće se paralelno s test jobom!

security-scan:
  stage: test   # i ovaj — sva tri idu istovremeno
```

## Job dependencies: needs keyword

Podrazumijevano, job u stage-u čeka da **svi jobovi prethodnog stage-a** završe. `needs` mijenja to — job počinje čim završe specificirani jobovi, bez obzira na stage.

```yaml
stages:
  - build
  - test
  - deploy

build-image:
  stage: build
  script:
    - docker build -t $IMAGE_TAG .
    - docker push $IMAGE_TAG

# Ovaj job NE čeka lint job — počinje čim build-image završi
integration-test:
  stage: test
  needs:
    - build-image
  script:
    - docker run --rm $IMAGE_TAG curl -f http://localhost

# Ovaj job čeka oba testa
deploy-dev:
  stage: deploy
  needs:
    - integration-test
    - lint           # mora završiti i lint
  script:
    - kubectl apply -f k8s/
```

Ovo je **DAG pipeline** (Directed Acyclic Graph). Korisno kada imate dugotrajne jobove koji ne zavise jedan od drugog — ne čekaju nepotrebno.

## Artifacts: dijeljenje između jobova

Artifacts su fajlovi ili direktoriji koje job kreira i koje GitLab čuva. Sljedeći jobovi (po defaultu u istom pipeline-u) ih automatski dobijaju.

```yaml
build-image:
  stage: build
  script:
    - docker build -t $IMAGE_TAG .
    - docker push $IMAGE_TAG
    # Spremi image digest za sljedeće jobove
    - docker inspect --format='{{index .RepoDigests 0}}' $IMAGE_TAG > image-digest.txt
    - echo "IMAGE_DIGEST=$(cat image-digest.txt)" >> build.env
  artifacts:
    paths:
      - image-digest.txt      # fajl dostupan za preuzimanje iz UI
    reports:
      dotenv: build.env       # varijable automatski ubačene u okruženje sljedećih jobova
    expire_in: 1 week         # automatski briše se nakon 7 dana
```

U sljedećem jobu:

```yaml
deploy:
  stage: deploy
  script:
    - echo "Deploying $IMAGE_DIGEST"  # varijabla automatski dostupna iz dotenv
```

`reports.dotenv` je posebno moćan — sve što zapišete u `build.env` (format `KLJUČ=VRIJEDNOST`) postaje environment varijabla u svim sljedećim jobovima.

**expire_in** je obavezan da se ne bi nakupljali gigabajti artifacts. Tipične vrijednosti: `1 hour` za privremene fajlove, `1 week` za build output, `never` za release artifacts.

## Cache: dependency cache vs artifact

Razlika je konceptualna:

| Cache | Artifact |
|-------|----------|
| Ubrzava ponavljajuće operacije | Prenosi rezultate između jobova |
| Dijeli se između pipeline-a | Samo unutar jednog pipeline-a |
| Može biti outdated (nije garantovano) | Uvijek tačan za taj pipeline |
| npm, pip, go modules | Docker image digest, compiled binary |

```yaml
# Cache za npm dependencies
build-frontend:
  cache:
    key: "$CI_COMMIT_REF_SLUG-npm"
    paths:
      - node_modules/
    policy: pull-push   # pull na početku, push na kraju
  script:
    - npm install       # brže jer node_modules iz cache-a
    - npm run build
  artifacts:
    paths:
      - dist/           # kompajlirani fajlovi idu kao artifact
    expire_in: 1 day
```

Za Docker images: ne koristite artifact za cijeli image (prevelik). Pushujte u registry i koristite tag ili digest kao identifikator.

## Environments i deployments

GitLab prati deploymente po environments. Kada job deploya na okruženje, GitLab bilježi to u Environments UI.

```yaml
deploy-staging:
  stage: deploy
  script:
    - kubectl set image deployment/hello-world nginx=$IMAGE_TAG -n helloworld-staging
  environment:
    name: staging
    url: https://staging.project-a.com
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
```

U GitLab UI → Operate → Environments vidite:
- Koja verzija je trenutno na svakom okruženju
- Historiju deploya (ko je deploovao, kada, koji commit)
- Rollback dugme (deploya prethodnu verziju)

## Primer: build → artifact → deploy

```yaml
stages:
  - build
  - test
  - deploy

variables:
  IMAGE_TAG: $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA

build-image:
  stage: build
  image: docker:24
  services:
    - docker:24-dind
  variables:
    DOCKER_TLS_CERTDIR: "/certs"
  before_script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
  script:
    - docker build -t $IMAGE_TAG .
    - docker push $IMAGE_TAG
    - echo "BUILT_IMAGE=$IMAGE_TAG" >> build.env
  artifacts:
    reports:
      dotenv: build.env
    expire_in: 1 day

test-image:
  stage: test
  needs:
    - build-image   # ne čeka ostatak build stage-a (ako ga ima)
  image: docker:24
  services:
    - docker:24-dind
  variables:
    DOCKER_TLS_CERTDIR: "/certs"
  script:
    - docker run --rm -d --name app -p 8080:80 $BUILT_IMAGE
    - sleep 2
    - curl -sf http://localhost:8080 | grep "Hello World"
    - docker stop app

deploy-dev:
  stage: deploy
  image: bitnami/kubectl:latest
  script:
    - kubectl set image deployment/hello-world nginx=$BUILT_IMAGE -n helloworld-dev
  environment:
    name: dev
    url: https://dev.project-a.local
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
```

`$BUILT_IMAGE` dolazi iz `build.env` — `deploy-dev` job nikad direktno ne gradi image, samo koristi tag koji je `build-image` zabilježio.
