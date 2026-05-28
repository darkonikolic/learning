# 04 — Docker test stage

## Zašto test stage u Dockerfile, a ne samo u CI script

CI script pristup:
```yaml
script:
  - go test ./...
  - docker build .
  - docker push .
```

Dockerfile test stage pristup:
```yaml
script:
  - docker build .   # ovaj korak ne može uspjeti ako testovi padnu
  - docker push .
```

Razlika nije samo stilska:

**1. Image se ne može buildovati ako testovi padnu.**
Nema načina da deployaš image koji nije prošao testove. CI script može imati bug gdje se `docker build` i `docker push` izvrše čak i kad prethodni `go test` padne (exit code ignore, wrong condition). Dockerfile test stage je atomaran — ako test stage padne, `docker build` vraća error, ne može se nastaviti.

**2. Test environment = production environment.**
CI script testira na runner-u. Runner ima određenu verziju Go-a, određene sistemske biblioteke, određene environment varijable. Dockerfile test stage testira unutar `golang:1.22-alpine` — istog base image-a koji se koristi za build. Nema drift između okruženja.

**3. "Works on my machine" je eliminisan.**
Developer lokalno radi `docker build .` — isti test stage se pokreće. CI radi `docker build .` — isti test stage. Ne postoji scenarij gdje testovi prolaze na jednom računalu ali padaju na drugom ako oba imaju Docker.

**4. Reproducibilnost je garantirana.**
`go.mod`, `go.sum`, `composer.lock` — sve je zaključano. `golang:1.22-alpine` je specific tag (ne `latest`). Test environment od 3 godine u budućnosti je reproducibilan ako imaš iste lockfile-ove i image digest.

---

## Go multi-stage sa test stagom

```dockerfile
# ============================================
# Stage 1: Dependencies (cached layer)
# ============================================
FROM golang:1.22-alpine AS deps

# Sistemske dependencije za CGO (ako su potrebne)
# Za CGO_ENABLED=0 build, ovo nije potrebno
RUN apk add --no-cache git ca-certificates tzdata

WORKDIR /app

# VAŽNO: Kopiraj samo go.mod i go.sum PRIJE source koda.
# Docker layer cache — ovaj layer se rebuilda samo kad se go.mod/go.sum promijeni,
# a NE svaki put kad se promijeni source kod.
COPY go.mod go.sum ./
RUN go mod download && go mod verify

# ============================================
# Stage 2: Test
# ============================================
FROM deps AS test

COPY . .

# -race: detektuje data race uslove
# -count=1: onemogući test cache
# ./...: svi paketi
RUN go test ./... -race -count=1

# ============================================
# Stage 3: Build
# ============================================
# NAPOMENA: Build stage ovisi o deps, NE o test stage.
# BuildKit može graditi test i build stage paralelno.
# Final image (production) ovisi o build — BuildKit tada
# garantira da test mora proći (jer je dependecy chain).
# Ali u DefaultDockerfile modu (bez BuildKit), redoslijed
# je sekvencijalan. Koristiti DOCKER_BUILDKIT=1.
FROM deps AS build

COPY . .

# CGO_ENABLED=0: static binary, nema shared library dependencija
# GOOS=linux: cross-compile ako builduješ na macOS
# -ldflags="-w -s": strip debug info i symbol table → manji binary
RUN CGO_ENABLED=0 GOOS=linux go build \
    -ldflags="-w -s" \
    -o /app/server \
    ./cmd/server  # putanja do main paketa

# ============================================
# Stage 4: Production
# ============================================
FROM scratch AS production

# Bez base image-a — nema shell-a, nema package manager-a,
# nema curl-a da exfiltriraš podatke, nema sh da pokrneš komande.
# Attack surface: minimalan.

# Binary
COPY --from=build /app/server /server

# SSL certifikati (bez ovih, HTTPS pozivi prema eksternim API-jima padaju)
COPY --from=build /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/

# Timezone data (ako tvoj kod koristi time.LoadLocation())
COPY --from=build /usr/share/zoneinfo /usr/share/zoneinfo

# Non-root user (za sigurnost, čak i bez OS-a)
# scratch ne podržava USER naredbu direktno, ali:
USER 65534:65534  # nobody:nogroup UID

EXPOSE 8080

ENTRYPOINT ["/server"]
```

### BuildKit cache za Go module download

```dockerfile
FROM golang:1.22-alpine AS deps
WORKDIR /app
COPY go.mod go.sum ./

# --mount=type=cache: persistuje /go/pkg/mod između buildova
# Key: unikatan po projektu da nema kolizija između projekata
RUN --mount=type=cache,target=/go/pkg/mod,id=go-mod-cache \
    --mount=type=cache,target=/root/.cache/go-build,id=go-build-cache \
    go mod download
```

> **Podman:** `--mount=type=cache` zahtijeva Podman 4.2+ ili buildah. Alternativa: `podman build --layers` za layer caching.

Bez cache mountova: svaki `docker build` preuzima sve Go module. Za projekat s 30 dependencija — 2-3 minute. S cache mountovima — sekunde.

Cache mountovi su host-local. Na GitLab runner-u sa shared cache volume, sve pipelines dijele isti cache. Konfiguracija u `.gitlab-ci.yml`:

```yaml
variables:
  DOCKER_BUILDKIT: "1"

build:
  script:
    - docker build --build-arg BUILDKIT_INLINE_CACHE=1 .
```

> **Podman:** `--mount=type=cache` zahtijeva Podman 4.2+ ili buildah. Alternativa: `podman build --layers` za layer caching.

---

## PHP multi-stage sa test stagom

```dockerfile
# ============================================
# Stage 1: Composer vendor (production only)
# ============================================
FROM composer:2.7 AS composer-prod
WORKDIR /app
COPY composer.json composer.lock ./
RUN composer install \
    --no-dev \
    --no-scripts \
    --no-autoloader \
    --prefer-dist

COPY . .
RUN composer dump-autoload --optimize --no-dev

# ============================================
# Stage 2: Composer vendor (dev + test)
# ============================================
FROM composer:2.7 AS composer-dev
WORKDIR /app
COPY composer.json composer.lock ./
RUN composer install \
    --with-all-dependencies \
    --no-scripts \
    --prefer-dist

COPY . .
RUN composer dump-autoload

# ============================================
# Stage 3: Test
# ============================================
FROM php:8.3-fpm-alpine AS test

# PCOV je brži od Xdebug za coverage (ne podržava debugging, samo coverage)
RUN apk add --no-cache $PHPIZE_DEPS linux-headers \
    && pecl install pcov \
    && docker-php-ext-enable pcov

WORKDIR /app
COPY --from=composer-dev /app/vendor /app/vendor
COPY . .

# --ci: non-interactive
# --log-junit: JUnit XML za GitLab
# --coverage-cobertura: coverage format koji GitLab razumije
# --min=70: fail ako coverage ispod 70%
RUN ./vendor/bin/pest \
    --ci \
    --log-junit=junit.xml \
    --coverage-cobertura=coverage.xml \
    --min=70

# ============================================
# Stage 4: Production
# ============================================
FROM php:8.3-fpm-alpine AS production

# Samo runtime extensions, nema PCOV, nema Xdebug
RUN docker-php-ext-install pdo pdo_mysql opcache

WORKDIR /app

# Kopiraj optimizovani autoloader iz production composer stage
COPY --from=composer-prod /app/vendor /app/vendor
COPY --from=composer-prod /app/composer.json .

# Source code (bez test fajlova)
COPY src/ src/
COPY public/ public/

# OPcache konfiguracija za produkciju
COPY docker/php/opcache.ini /usr/local/etc/php/conf.d/

EXPOSE 9000
CMD ["php-fpm"]
```

---

## `docker build --target` u CI-ju

```bash
# Samo pokreni test stage — ne gradi final image
# Korisno u CI pipelinu koji samo treba test output
docker build --target test --tag myapp:test .

# Izvuci junit.xml iz container-a koji je buildovan do test stage-a
docker create --name test-container myapp:test
docker cp test-container:/app/junit.xml ./junit.xml
docker rm test-container
```

Alternativno s bind mountom (BuildKit):
```bash
docker build --target test \
    --output type=local,dest=./test-output \
    .
```

Ili direktno u CI job bez izvlačenja fajlova — samo pass/fail:
```bash
docker build --target test .
# Exit code 0 = svi testovi prošli
# Exit code != 0 = neki test pao, ne nastavlja se
```

---

## Integration testovi: CI job services umjesto Dockerfile

Testcontainers ne radi unutar `docker build` jer nema Docker daemon-a u build contextu. Za integration testove koji trebaju pravu bazu koristiš GitLab CI `services:`.

```yaml
test:go-integration:
  stage: test
  image: golang:1.22-alpine
  services:
    - name: mysql:8.0
      alias: mysql  # hostname unutar job-a
    - name: redis:7-alpine
      alias: redis
  variables:
    MYSQL_ROOT_PASSWORD: testpass
    MYSQL_DATABASE: testdb
    MYSQL_USER: testuser
    MYSQL_PASSWORD: userpass
    DB_HOST: mysql        # tvoj app čita ovaj env var
    DB_PORT: "3306"
    REDIS_HOST: redis
    REDIS_PORT: "6379"
  script:
    - go test ./internal/repository/... -v -race -count=1 -tags=integration
```

`-tags=integration` — build tag za separiranje integration testova od unit testova:

```go
//go:build integration
// +build integration

package repository_test

// Ovaj fajl se kompajlira samo kad je -tags=integration proslijeđen
func TestUserRepositoryIntegration(t *testing.T) {
    db := connectToDBFromEnv(t)  // čita DB_HOST, DB_PORT iz env
    // ...
}
```

Unit testovi se pokreću brzo bez services. Integration testovi se pokreću zasebno s database services. Oboje su u istom `test` stage-u, ali u zasebnim jobs koji idu paralelno.

---

## Usporedba pristupa

| Aspekt | CI script | Dockerfile test stage |
|--------|-----------|----------------------|
| Image buildability | Može buildovati čak i ako test job padne (greška u pipeline konfiguraciji) | Nije moguće buildovati ako test stage padne |
| Env paritet | Ovisi o runner konfiguraciji | Identičan base image kao production |
| Lokalno pokretanje | `go test ./...` direktno | `docker build --target test .` |
| Reproducibilnost | Ovisna o runner setup-u | Determinirana iz Dockerfila |
| Testcontainers | Radi (ima Docker socket) | Ne radi (nema Docker daemon) |
| Coverage artifact | Mora se eksplicitno kopirati | `docker cp` iz builtovanog image-a |

Preporuka: unit testovi u Dockerfile test stage, integration testovi u CI job s services.
