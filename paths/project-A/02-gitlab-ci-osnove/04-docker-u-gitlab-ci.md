# 04 - Docker u GitLab CI

## Problem: Docker unutar Docker kontejnera

GitLab CI job se izvršava unutar Docker kontejnera. Ali za build Docker imagea trebate Docker daemon. Kako pokrenuti Docker unutar Docker kontejnera?

Dva pristupa: **Docker-in-Docker (DinD)** i **Docker socket binding**.

## Docker-in-Docker (DinD)

DinD pokreće zasebni Docker daemon unutar job kontejnera, kao `service`. Svaki job dobija vlastiti, izolovani daemon.

```yaml
build-image:
  image: docker:24
  services:
    - name: docker:24-dind
      alias: docker
  variables:
    DOCKER_HOST: tcp://docker:2376
    DOCKER_TLS_CERTDIR: "/certs"
    DOCKER_TLS_VERIFY: "1"
    DOCKER_CERT_PATH: "/certs/client"
  script:
    - docker build -t $IMAGE_TAG .
    - docker push $IMAGE_TAG
```

Šta se dešava:
1. Runner pokreće dva kontejnera: `docker:24` (vaš job) i `docker:24-dind` (daemon)
2. `DOCKER_HOST` usmjerava Docker klijent na DinD daemon umjesto na lokalni socket
3. TLS osigurava komunikaciju između klijenta i daemona
4. Job kontejner komunicira s DinD kontejnerom po mreži

**Prednosti DinD:**
- Potpuna izolacija — svaki job ima vlastiti daemon, vlastiti image cache
- Sigurno — job ne može pristupiti host Docker daemonu
- Radi na shared GitLab.com runnerima

**Nedostaci DinD:**
- Sporiji — daemon se pokreće od nule za svaki job, image cache se ne dijeli
- Privilegovani mode — DinD kontejner zahtijeva `--privileged` flag (na shared runnerima je to već podešeno)

> **Podman u GitLab CI:**
> Docker-in-Docker (`docker:dind`) nije potreban s Podmanom. Koristi Podman socket pristup:
> ```yaml
> build:
>   image: quay.io/podman/stable
>   variables:
>     STORAGE_DRIVER: vfs
>   before_script:
>     - podman info
>   script:
>     - podman build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
>     - podman push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
> ```
> Prednost: ne treba `privileged: true` runner — Podman radi rootless.

## Docker socket binding

Alternativno: montirajte host Docker socket unutar job kontejnera. Job direktno komunicira s host daemonom.

```yaml
build-image:
  image: docker:24
  variables:
    DOCKER_HOST: unix:///var/run/docker.sock
  before_script:
    - docker info  # provjera
  script:
    - docker build -t $IMAGE_TAG .
    - docker push $IMAGE_TAG
```

Runner mora biti konfigurisan s volume mountom:
```toml
# config.toml na runneru
[[runners]]
  [runners.docker]
    volumes = ["/var/run/docker.sock:/var/run/docker.sock"]
```

**Prednosti socket binding:**
- Brže — koristi postojeći daemon, image layers su već cached
- Manji overhead — nema pokretanja novog daemona

**Nedostaci socket binding:**
- Sigurnosni rizik — job ima root pristup host Docker daemonu, može pristupiti svim kontejnerima i imagima na hostu
- Ne radi na shared GitLab.com runnerima (ne možete montovati socket)
- Job može "pobjeći" iz kontejner izolacije

**Odluka za project-A:** Koristimo DinD. Radimo sa shared runnerima na GitLab.com, a sigurnost je važnija od brzine u ranim fazama. Za self-hosted runner u pouzdanom okruženju socket binding je prihvatljiv kompromis.

## Ključne varijable

```yaml
variables:
  # Gdje je Docker daemon
  DOCKER_HOST: tcp://docker:2376

  # Direktorij za TLS certifikate (DinD ih kreira ovdje)
  DOCKER_TLS_CERTDIR: "/certs"

  # Storage driver (overlay2 je performansniji)
  DOCKER_DRIVER: overlay2
```

`DOCKER_TLS_CERTDIR` je posebno važan: ako ga postavite na prazan string (`DOCKER_TLS_CERTDIR: ""`), DinD radi bez TLS-a na portu 2375 (nesigurno, ali jednostavnije za debugging).

## Build i push image u pipeline-u

Kompletan job za build i push:

```yaml
build-and-push:
  stage: build
  image: docker:24
  services:
    - docker:24-dind
  variables:
    DOCKER_TLS_CERTDIR: "/certs"
    IMAGE_TAG: $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA
    IMAGE_LATEST: $CI_REGISTRY_IMAGE:latest
  before_script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
  script:
    - |
      docker build \
        --tag $IMAGE_TAG \
        --tag $IMAGE_LATEST \
        --label "git.sha=$CI_COMMIT_SHA" \
        --label "git.branch=$CI_COMMIT_BRANCH" \
        --label "build.date=$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        .
    - docker push $IMAGE_TAG
    - docker push $IMAGE_LATEST
    - echo "IMAGE=$IMAGE_TAG" >> build.env
  artifacts:
    reports:
      dotenv: build.env
    expire_in: 1 day
```

Labels su metapodaci ugrađeni u image — korisni za audit ("koji commit je u ovom imageu?").

## Layer cache strategija u CI

Docker gradi image u layers. Ako se layer nije promijenio, Docker ga reuse-uje iz cache-a. U CI, svaki job je svježi kontejner — nema cache-a po defaultu.

Strategija `--cache-from`:

```yaml
build-with-cache:
  script:
    # Povuci prethodni image da koristis kao cache
    - docker pull $CI_REGISTRY_IMAGE:latest || true
    - |
      docker build \
        --cache-from $CI_REGISTRY_IMAGE:latest \
        --tag $IMAGE_TAG \
        --tag $CI_REGISTRY_IMAGE:latest \
        .
    - docker push $IMAGE_TAG
    - docker push $CI_REGISTRY_IMAGE:latest
```

`|| true` na `docker pull` sprečava fail ako image još ne postoji (npr. prvi run). `--cache-from` koristi `latest` image kao izvor cache-a — ako se `COPY` ili `RUN` sloj nije promijenio u odnosu na prethodni build, Docker preskače taj korak.

Za nginx hello-world projekt ovo je manje kritično (build je brz), ali za projekte s npm install ili pip install može uštedjeti minute po pipelinu.

## Kompletan job primer za project-A

```yaml
build-hello-world:
  stage: build
  image: docker:24
  services:
    - name: docker:24-dind
      alias: docker
  variables:
    DOCKER_TLS_CERTDIR: "/certs"
    IMAGE_TAG: $CI_REGISTRY_IMAGE/hello-world:$CI_COMMIT_SHORT_SHA
    IMAGE_BRANCH: $CI_REGISTRY_IMAGE/hello-world:$CI_COMMIT_REF_SLUG
  before_script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
  script:
    - docker pull $IMAGE_BRANCH || true
    - |
      docker build \
        --cache-from $IMAGE_BRANCH \
        --tag $IMAGE_TAG \
        --tag $IMAGE_BRANCH \
        .
    - docker push $IMAGE_TAG
    - docker push $IMAGE_BRANCH
    - echo "IMAGE_TAG=$IMAGE_TAG" >> build.env
  artifacts:
    reports:
      dotenv: build.env
    expire_in: 1 week
  rules:
    - if: $CI_COMMIT_BRANCH
```

`$CI_COMMIT_REF_SLUG` je branch ime adaptirano za Docker tag (slasha zamjenjuje crtom, lowercase). Npr. `feature/add-button` postaje `feature-add-button`.
