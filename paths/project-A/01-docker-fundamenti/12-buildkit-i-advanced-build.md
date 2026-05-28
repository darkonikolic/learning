# 12 — BuildKit i advanced build tehnike

BuildKit je novi Docker build engine, aktivan po defaultu od Docker 23.0. Nije samo brži — donosi fundamentalno nove mogućnosti koje bez njega jednostavno ne postoje: paralelni build stagevi, mount cache koji opstaje između build-ova, secrets koji nikad ne ulaze u image, i multi-platform build s jedne mašine.

---

## Zašto BuildKit mijenja stvari

Bez BuildKit-a:
- Dockerfile stagevi se izvršavaju sekvencijalno
- Cache se prekida čim se promijeni bilo koji layer ispred
- Nema načina da proslijediš secret bez da ostane u layer-u
- Svaki `go build` treba preuzeti sve module iznova

S BuildKit-om:
- Nezavisni stagevi se izvršavaju paralelno
- `--mount=type=cache` daje persistentni cache između build-ova na istoj mašini
- `--mount=type=secret` injektuje secret koji nikad ne ulazi u image
- `go build` s 0 promjena traje < 1 sekundu umjesto 30+

---

## Aktivacija

BuildKit je default od Docker Desktop 4.x i Docker Engine 23.0+. Provjeri:

```bash
docker buildx version
# buildx v0.13.0 ...

docker info | grep -i buildkit
# Server: BuildKit enabled
```

Ako nije aktivan, eksplicitno:

```bash
# Per-session (shell varijable)
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Permanentno u daemon.json
# ~/.docker/daemon.json (Docker Desktop) ili /etc/docker/daemon.json (Linux)
{
  "features": {
    "buildkit": true
  }
}
```

> **Podman / Buildah ekvivalent:**
> Podman koristi `buildah` ispod — BuildKit nije potreban:
> ```bash
> # --mount=type=cache ekvivalent (Podman 4.2+)
> podman build --layers .
>
> # Multi-platform build
> podman manifest create myapp:latest
> podman build --platform linux/amd64 --manifest myapp:latest .
> podman build --platform linux/arm64 --manifest myapp:latest .
> podman manifest push myapp:latest
> ```
> `--mount=type=secret` syntax je isti u Podmanu 4.x+.

---

## Cache mount — persistentni build cache

Ovo je najvažnija BuildKit funkcionalnost za svakodnevni rad. `--mount=type=cache` kreira direktorijum koji:
- Nije dio image-a (ne povećava veličinu)
- Opstaje između build-ova na istoj mašini
- Dijeli se između stageva koji imaju isti `target`

### PHP — Composer cache

```dockerfile
FROM php:8.3-fpm-alpine AS base

COPY --from=composer:2.7 /usr/bin/composer /usr/bin/composer

WORKDIR /app
COPY composer.json composer.lock ./

# Bez cache mounta: svaki build preuzima sve packade iznova (~30-60s)
# Sa cache mountom: prvi build 60s, svaki sljedeći 2-5s
RUN --mount=type=cache,target=/root/.composer/cache \
    composer install \
        --no-dev \
        --no-scripts \
        --no-autoloader \
        --prefer-dist

COPY src/ ./src/
RUN composer dump-autoload --optimize --no-dev
```

Za development stage koji instalira dev deps:
```dockerfile
FROM base AS development

RUN --mount=type=cache,target=/root/.composer/cache \
    composer install \
        --no-scripts \
        --prefer-dist
# Isti cache mount — Composer ne preuzima ponovo ono što je već keširano
```

### Go — module i build cache

Go ima dva nivo cacheovnja: module download cache (`/go/pkg/mod`) i build cache (`/root/.cache/go-build`). Oba su važna.

```dockerfile
FROM golang:1.22-alpine AS base

WORKDIR /app
COPY go.mod go.sum ./

RUN --mount=type=cache,target=/go/pkg/mod \
    go mod download

FROM base AS builder

COPY . .

# go/pkg/mod: ne preuzimaj module koje već imamo
# root/.cache/go-build: ne rekompajliraj pakete koji se nisu promijenili
RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    CGO_ENABLED=0 \
    GOOS=linux \
    go build \
        -ldflags="-s -w" \
        -o /server \
        ./cmd/server/
```

Praktičan efekat: Promijeniš jedan `.go` fajl → samo taj paket se rekompajlira. Ostalo je iz cache-a. Build koji je ranije trajao 45 sekundi → 3 sekunde.

### Vue.js — npm cache

```dockerfile
FROM node:20-alpine AS base

WORKDIR /app
COPY package.json package-lock.json ./

# npm cache između build-ova
RUN --mount=type=cache,target=/root/.npm \
    npm ci --only=production

COPY . .

FROM base AS development

RUN --mount=type=cache,target=/root/.npm \
    npm ci  # Uključi dev dependencies

FROM base AS builder

RUN --mount=type=cache,target=/root/.npm \
    npm ci \
    && npm run build

FROM nginx:1.25-alpine AS production
COPY --from=builder /app/dist /usr/share/nginx/html
COPY docker/nginx/nginx.conf /etc/nginx/conf.d/default.conf
```

---

## Secrets u build stageu — jedini ispravan način

Problem: kako proslijediti API token ili SSH ključ u build bez da ostane u image layeru?

Pogrešan pristup koji se često viđa:
```dockerfile
# POGREŠNO — secret je vidljiv u docker history i u layer-u
ARG GITHUB_TOKEN
RUN git clone https://${GITHUB_TOKEN}@github.com/private/repo.git
```

Čak i `RUN rm /secret` ne pomaže — Docker layer je snimak filesystem-a prije i poslije RUN naredbe. Secret ostaje u prethodnom layer-u.

BuildKit secrets rješavaju ovo fundamentalno drugačije: secret se montira kao in-memory fajl koji je dostupan samo tokom izvršavanja te `RUN` naredbe i nikad ne ulazi u image.

### Composer private repository

```dockerfile
FROM php:8.3-fpm-alpine AS base

COPY --from=composer:2.7 /usr/bin/composer /usr/bin/composer
WORKDIR /app
COPY composer.json composer.lock ./

# Secret je dostupan samo za trajanje ove RUN naredbe
# Nikad se ne zapisuje u image layer
RUN --mount=type=secret,id=composer_auth \
    --mount=type=cache,target=/root/.composer/cache \
    COMPOSER_AUTH=$(cat /run/secrets/composer_auth) \
    composer install \
        --no-dev \
        --no-scripts \
        --prefer-dist
```

Build komanda:
```bash
# Proslijedi lokalni auth.json kao secret
docker build \
    --secret id=composer_auth,src=${HOME}/.composer/auth.json \
    --target production \
    ./services/php-service
```

Sadržaj `~/.composer/auth.json`:
```json
{
  "github-oauth": {
    "github.com": "ghp_xxxxxxxxxxxxxxxxxxxx"
  },
  "http-basic": {
    "repo.packagist.com": {
      "username": "token",
      "password": "your-packagist-token"
    }
  }
}
```

### SSH ključ za private Go modul

```dockerfile
FROM golang:1.22-alpine AS base

RUN apk add --no-cache git openssh-client

# Konfiguracija da git koristi SSH umjesto HTTPS za private modul
RUN git config --global url."git@gitlab.example.com:".insteadOf "https://gitlab.example.com/"

WORKDIR /app
COPY go.mod go.sum ./

RUN --mount=type=ssh \
    --mount=type=cache,target=/go/pkg/mod \
    go mod download
```

Build komanda:
```bash
# Proslijedi SSH agent
docker build \
    --ssh default=$SSH_AUTH_SOCK \
    ./services/go-service
```

Ili eksplicitno specificiran ključ:
```bash
docker build \
    --ssh default=/path/to/private/key \
    ./services/go-service
```

### GitLab CI — secrets u build-u

```yaml
# .gitlab-ci.yml
build:php:
  stage: build
  before_script:
    - echo "$COMPOSER_AUTH_JSON" > /tmp/composer-auth.json
  script:
    - docker build
        --secret id=composer_auth,src=/tmp/composer-auth.json
        --target production
        --tag ${CI_REGISTRY_IMAGE}/php-service:${CI_COMMIT_SHA}
        ./services/php-service
  after_script:
    - rm -f /tmp/composer-auth.json
```

`COMPOSER_AUTH_JSON` je GitLab CI/CD variable (masked, protected).

---

## Multi-platform build

Zašto to bitno: M1/M2/M3 Mac builduje ARM64 image nativno. AWS EC2 c5/m5 instancee su AMD64. Ako ne specificiraš `--platform`, GitLab CI runner na AMD64 builduje AMD64 image, ali tvoj lokalni Mac builduje ARM64 image — a možda ih pushujete u isti tag.

Emulacija je rješenje: buildx može buildovati za drugu arhitekturu koristeći QEMU emulaciju, ili nativno ako imaš oba tipa runnera.

### Setup

```bash
# Provjeri dostupne platforme
docker buildx ls

# Kreiraj builder koji podržava multi-platform
docker buildx create \
    --name multiplatform \
    --driver docker-container \
    --use

# Inicijalizuj (preuzima QEMU emulatore)
docker buildx inspect --bootstrap
```

### Build za obe platforme

```bash
# Builduj i pushuj manifest koji podržava obe arhitekture
docker buildx build \
    --platform linux/amd64,linux/arm64 \
    --target production \
    --tag ${CI_REGISTRY_IMAGE}/go-service:${CI_COMMIT_SHA} \
    --tag ${CI_REGISTRY_IMAGE}/go-service:latest \
    --push \
    ./services/go-service
```

`--push` je obavezan za multi-platform — lokalni Docker daemon ne može čuvati manifest list s više arhitektura.

> **Podman / Buildah ekvivalent:**
> Podman koristi `buildah` ispod — BuildKit nije potreban:
> ```bash
> # --mount=type=cache ekvivalent (Podman 4.2+)
> podman build --layers .
>
> # Multi-platform build
> podman manifest create myapp:latest
> podman build --platform linux/amd64 --manifest myapp:latest .
> podman build --platform linux/arm64 --manifest myapp:latest .
> podman manifest push myapp:latest
> ```
> `--mount=type=secret` syntax je isti u Podmanu 4.x+.

Provjeri rezultat:
```bash
docker buildx imagetools inspect ${CI_REGISTRY_IMAGE}/go-service:latest
# Name: ...
# MediaType: application/vnd.docker.distribution.manifest.list.v2+json
# Digest: sha256:...
#
# Manifests:
#   Name: .../go-service:latest@sha256:... (linux/amd64)
#   Name: .../go-service:latest@sha256:... (linux/arm64)
```

### Multi-platform u GitLab CI

```yaml
# .gitlab-ci.yml
build:go-service:
  stage: build
  image: docker:24
  services:
    - docker:24-dind
  variables:
    DOCKER_BUILDKIT: "1"
  before_script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
    - docker buildx create --use --driver docker-container
    - docker buildx inspect --bootstrap
  script:
    - docker buildx build
        --platform linux/amd64,linux/arm64
        --target production
        --cache-from type=registry,ref=${CI_REGISTRY_IMAGE}/go-service:cache
        --cache-to type=registry,ref=${CI_REGISTRY_IMAGE}/go-service:cache,mode=max
        --tag ${CI_REGISTRY_IMAGE}/go-service:${CI_COMMIT_SHA}
        --push
        ./services/go-service
```

Go specijalno: Go kompajlira nativno za target arhitekturu — nema QEMU emulacije za kompajliranje, samo za pokretanje. Rezultat: multi-platform Go build je brz čak i za ARM64 na AMD64 runneru.

> **Podman / Buildah ekvivalent:**
> Podman koristi `buildah` ispod — BuildKit nije potreban:
> ```bash
> # --mount=type=cache ekvivalent (Podman 4.2+)
> podman build --layers .
>
> # Multi-platform build
> podman manifest create myapp:latest
> podman build --platform linux/amd64 --manifest myapp:latest .
> podman build --platform linux/arm64 --manifest myapp:latest .
> podman manifest push myapp:latest
> ```
> `--mount=type=secret` syntax je isti u Podmanu 4.x+.

---

## Registry cache — speedup CI bez lokalnog cache-a

Lokalni `--mount=type=cache` radi samo na istoj mašini. CI runneri su obično ephemeral — svaki job dobija svježi kontejner bez prethodnog cache-a.

Rješenje: spremi BuildKit cache u container registry.

```bash
# Build s cache iz registry-ja
docker buildx build \
    --cache-from type=registry,ref=${CI_REGISTRY_IMAGE}/php-service:cache \
    --cache-to type=registry,ref=${CI_REGISTRY_IMAGE}/php-service:cache,mode=max \
    --target production \
    --tag ${CI_REGISTRY_IMAGE}/php-service:${CI_COMMIT_SHA} \
    --push \
    ./services/php-service
```

`mode=max` znači: snimi cache za sve stageve (uključujući intermediate), ne samo za finalni stage. Ovo je sporije za pushovanje, ali daje bolje cache hit rate za sljedeći build.

`mode=min` (default) — snimi cache samo za finalni stage koji se exportuje.

Za naš projekt:
- `php-service:cache` — cache za PHP image
- `go-service:cache` — cache za Go image  
- `nginx:cache` — cache za nginx image

Efekat na CI: prvi build traje puno (nema cache-a). Svaki sljedeći build koji ne mijenja `go.mod` ili `composer.lock` preskače dependency download fazu — ušteda 30-90 sekundi po jobu.

---

## Parallel stage build — vizualizacija

Bez BuildKit-a, Dockerfile stagevi se izvršavaju sekvencijalno:
```
base → development → (čeka)
base → test        → (čeka)
base → builder     → (čeka)
builder → production
```

S BuildKit-om, nezavisni stagevi se izvršavaju paralelno:
```
base ──┬── development ─── (done)
       ├── test ──────────── (done)
       └── builder ──────┬── production
                         └── (done)
```

`development`, `test` i `builder` se builduju paralelno jer su sve nezavisni children od `base`. Samo `production` čeka `builder`.

---

## Inlining build args — reproducibilnost

```dockerfile
FROM php:8.3-fpm-alpine AS production

# Build args za traceability — koji commit je u ovom image-u?
ARG BUILD_VERSION=unknown
ARG BUILD_DATE=unknown
ARG GIT_COMMIT=unknown

LABEL org.opencontainers.image.version="${BUILD_VERSION}" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.revision="${GIT_COMMIT}" \
      org.opencontainers.image.source="https://gitlab.example.com/project-a"
```

```bash
docker build \
    --build-arg BUILD_VERSION=$(git describe --tags --always) \
    --build-arg BUILD_DATE=$(date -u +%Y-%m-%dT%H:%M:%SZ) \
    --build-arg GIT_COMMIT=${CI_COMMIT_SHA} \
    --target production \
    .
```

Ovo ti omogućava da iz deployed image-a odmah vidiš koji commit je u produkciji:
```bash
docker inspect --format='{{json .Config.Labels}}' myapp:latest | jq .
```

---

## Kompletna CI pipeline sekvenca

```yaml
# .gitlab-ci.yml — kompletna referentna implementacija

variables:
  DOCKER_BUILDKIT: "1"
  COMPOSE_DOCKER_CLI_BUILD: "1"
  PHP_CACHE_IMAGE: "${CI_REGISTRY_IMAGE}/php-service:cache"
  GO_CACHE_IMAGE: "${CI_REGISTRY_IMAGE}/go-service:cache"

stages:
  - test
  - build
  - deploy

# ─── TEST ──────────────────────────────────────────────────
test:php:
  stage: test
  script:
    - docker build
        --target test
        --cache-from type=registry,ref=${PHP_CACHE_IMAGE}
        --tag php-test:${CI_COMMIT_SHA}
        ./services/php-service
  # Ako pest padne → build stage padne → deploy se ne desi

test:go:
  stage: test
  script:
    - docker build
        --target test
        --cache-from type=registry,ref=${GO_CACHE_IMAGE}
        --tag go-test:${CI_COMMIT_SHA}
        ./services/go-service


# ─── BUILD ─────────────────────────────────────────────────
build:php:
  stage: build
  needs: [test:php]
  before_script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
    - echo "$COMPOSER_AUTH_JSON" > /tmp/composer-auth.json
  script:
    - docker buildx build
        --platform linux/amd64,linux/arm64
        --target production
        --secret id=composer_auth,src=/tmp/composer-auth.json
        --cache-from type=registry,ref=${PHP_CACHE_IMAGE}
        --cache-to type=registry,ref=${PHP_CACHE_IMAGE},mode=max
        --build-arg BUILD_VERSION=${CI_COMMIT_TAG:-${CI_COMMIT_SHORT_SHA}}
        --build-arg BUILD_DATE=$(date -u +%Y-%m-%dT%H:%M:%SZ)
        --build-arg GIT_COMMIT=${CI_COMMIT_SHA}
        --tag ${CI_REGISTRY_IMAGE}/php-service:${CI_COMMIT_SHA}
        --tag ${CI_REGISTRY_IMAGE}/php-service:latest
        --push
        ./services/php-service
  after_script:
    - rm -f /tmp/composer-auth.json

build:go:
  stage: build
  needs: [test:go]
  before_script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
    - docker buildx create --use --driver docker-container
    - docker buildx inspect --bootstrap
  script:
    - docker buildx build
        --platform linux/amd64,linux/arm64
        --target production
        --cache-from type=registry,ref=${GO_CACHE_IMAGE}
        --cache-to type=registry,ref=${GO_CACHE_IMAGE},mode=max
        --build-arg BUILD_VERSION=${CI_COMMIT_TAG:-${CI_COMMIT_SHORT_SHA}}
        --build-arg BUILD_DATE=$(date -u +%Y-%m-%dT%H:%M:%SZ)
        --build-arg GIT_COMMIT=${CI_COMMIT_SHA}
        --tag ${CI_REGISTRY_IMAGE}/go-service:${CI_COMMIT_SHA}
        --tag ${CI_REGISTRY_IMAGE}/go-service:latest
        --push
        ./services/go-service
```

---

## Debugging build problema

```bash
# Pogledaj što je u cache-u
docker buildx du

# Isprazni BuildKit cache
docker buildx prune

# Build s verbose outputom — vidiš svaki step
docker buildx build --progress=plain --target production .

# Ispitaj intermediary stage — otvori shell u "zaglavljeni" build
docker build --target base --tag debug-base . \
    && docker run --rm -it debug-base sh

# Provjeri veličinu svakog layer-a u finalnom image-u
docker history --no-trunc ${CI_REGISTRY_IMAGE}/php-service:latest
```
