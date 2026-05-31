# 11 — Dockerfile targets i Docker Compose profiles

Targets i profiles su dva ortogonalna mehanizma koji zajedno rješavaju isti problem: kako imati jedan codebase koji radi u dev, CI, debug i prod okruženju bez kopiranja konfiguracije. Targets se bave time kako se image builduje. Profiles se bave time koji servisi se pokreću.

---

## Dio 1: Dockerfile multi-stage targets

### Zašto targets, a ne zasebni Dockerfilovi?

Bez targeta, svako okruženje dobija svoj Dockerfile:
```
docker/
├── Dockerfile.dev
├── Dockerfile.test
├── Dockerfile.debug
└── Dockerfile.prod   ← 4 fajla, ista logika ponovljena 4 puta
```

S targetima:
```
services/php-service/
└── Dockerfile        ← jedan fajl, 5 targeta, nula ponavljanja
```

Svaki target se gradi na prethodnom. Promjena u `base` stageu automatski propagira u sve targete koji ga nasljeđuju.

### Standardna target hijerarhija

```
base ────────────────── zajednički runtime dependencies
  │
  ├── development ────── base + dev tools, hot reload
  │     │
  │     └── test ──────── development + test runner, pokrene testove u build fazu
  │
  ├── debug ───────────── base + debugger (Xdebug/Delve)
  │
  └── production ──────── base (ili direktno od scratch), minimalan image
```

---

### PHP 8.3 service — kompletan Dockerfile

```dockerfile
# services/php-service/Dockerfile

# ──────────────────────────────────────────────────────────
# BASE — runtime dependencies, bez dev/test/debug
# ──────────────────────────────────────────────────────────
FROM php:8.3-fpm-alpine AS base

# Sistem dependencies — samo runtime
RUN apk add --no-cache \
    fcgi \                     # php-fpm-healthcheck
    libpng libpng-dev \        # GD za slike
    libzip libzip-dev \        # ZIP arhive
    && docker-php-ext-install \
        pdo_mysql \
        opcache \
        gd \
        zip \
    && apk del libpng-dev libzip-dev \  # Build deps obriši
    && rm -rf /var/cache/apk/*

# PHP config
COPY docker/php/php.ini /usr/local/etc/php/conf.d/app.ini
COPY docker/php/php-fpm.conf /usr/local/etc/php-fpm.d/app.conf

# Composer
COPY --from=composer:2.7 /usr/bin/composer /usr/bin/composer

WORKDIR /app

# Instaliraj production dependencies
COPY composer.json composer.lock ./
RUN --mount=type=cache,target=/root/.composer \
    composer install \
        --no-dev \
        --no-scripts \
        --no-autoloader \
        --prefer-dist

# Kopiraj izvorni kod
COPY src/ ./src/
COPY bootstrap/ ./bootstrap/
COPY config/ ./config/
COPY public/ ./public/

# Generiraj optimizovani autoloader
RUN composer dump-autoload --optimize --no-dev

# Ne radi kao root
RUN chown -R www-data:www-data /app
USER www-data

EXPOSE 9000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD SCRIPT_NAME=/ping SCRIPT_FILENAME=/ping REQUEST_METHOD=GET \
        cgi-fcgi -bind -connect 127.0.0.1:9000 || exit 1


# ──────────────────────────────────────────────────────────
# DEVELOPMENT — base + dev dependencies, hot reload support
# ──────────────────────────────────────────────────────────
FROM base AS development

USER root

# Reinstaliraj Composer sa dev dependencies
RUN --mount=type=cache,target=/root/.composer \
    composer install \
        --no-scripts \
        --prefer-dist
# Note: source kod se montira kao bind mount u docker-compose.override.yml
# COPY ovdje nije ni potreban — override.yml montira ./src:/app/src:ro

ENV APP_ENV=development
ENV APP_DEBUG=true

USER www-data


# ──────────────────────────────────────────────────────────
# TEST — development base + test runner
# Ovo je poseban slučaj: testovi se pokreću TOKOM docker build-a
# Ako testovi padnu, build pada. CI job pada. Image se ne pushuje.
# ──────────────────────────────────────────────────────────
FROM development AS test

USER root

# Kopiraj sve (uključujući tests/) — bind mount nije dostupan u build stageu
COPY . /app/
RUN chown -R www-data:www-data /app

USER www-data

# Postavi test env
ENV APP_ENV=testing
ENV DB_CONNECTION=sqlite
ENV DB_DATABASE=:memory:

# Pokreni testove — build pada ako testovi padnu
RUN ./vendor/bin/pest \
    --ci \
    --log-junit=/app/test-results/junit.xml \
    --coverage-text


# ──────────────────────────────────────────────────────────
# DEBUG — base + Xdebug
# Nikad ne koristiti u produkciji ili CI
# ──────────────────────────────────────────────────────────
FROM base AS debug

USER root

RUN apk add --no-cache $PHPIZE_DEPS linux-headers \
    && pecl install xdebug-3.3.1 \
    && docker-php-ext-enable xdebug \
    && apk del $PHPIZE_DEPS \
    && rm -rf /var/cache/apk/*

COPY docker/php/xdebug.ini /usr/local/etc/php/conf.d/xdebug.ini

USER www-data


# ──────────────────────────────────────────────────────────
# PRODUCTION — base je već production-ready
# Ovaj stage je alias koji eksplicitno označava koji target ide u prod
# Dodaje samo production-specifičnu finalizaciju
# ──────────────────────────────────────────────────────────
FROM base AS production

# OPcache za produkciju — agresivniji od dev defaulta
COPY docker/php/opcache-prod.ini /usr/local/etc/php/conf.d/opcache.ini

# Security: ukloni Composer (ne treba se u kontejneru)
RUN rm /usr/bin/composer

LABEL org.opencontainers.image.source="https://gitlab.example.com/project-a" \
      org.opencontainers.image.description="PHP 8.3 service" \
      org.opencontainers.image.licenses="UNLICENSED"
```

Xdebug konfiguracija:
```ini
; docker/php/xdebug.ini
[xdebug]
xdebug.mode=debug,profile
xdebug.start_with_request=yes
xdebug.client_host=${XDEBUG_CLIENT_HOST}
xdebug.client_port=9003
xdebug.log=/tmp/xdebug.log
xdebug.profiler_output_dir=/tmp/xdebug-profiles
```

---

### Go 1.22 service — kompletan Dockerfile

```dockerfile
# services/go-service/Dockerfile

# ──────────────────────────────────────────────────────────
# BASE — dependency download, zajednička osnova
# ──────────────────────────────────────────────────────────
FROM golang:1.22-alpine AS base

WORKDIR /app

# Kopiraj mod fajlove i preuzmi dependencies
# Ovaj layer se cacheuje dok se go.mod/go.sum ne promijene
COPY go.mod go.sum ./
RUN --mount=type=cache,target=/go/pkg/mod \
    go mod download


# ──────────────────────────────────────────────────────────
# DEVELOPMENT — base + Air (hot reload)
# ──────────────────────────────────────────────────────────
FROM base AS development

# Air za hot reload
RUN go install github.com/cosmtrek/air@v1.51.0

# Source se montira kao bind mount iz docker-compose.override.yml
# ./services/go-service:/app:ro

ENV APP_ENV=development
EXPOSE 8080

CMD ["air", "-c", ".air.toml"]


# ──────────────────────────────────────────────────────────
# TEST — pokreni testove u build stageu
# ──────────────────────────────────────────────────────────
FROM base AS test

COPY . .

RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    go test \
        ./... \
        -race \
        -count=1 \
        -coverprofile=/app/coverage.out \
        -v 2>&1 | tee /app/test-output.txt


# ──────────────────────────────────────────────────────────
# BUILDER — kompajlira binarni fajl za produkciju
# ──────────────────────────────────────────────────────────
FROM base AS builder

COPY . .

RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    CGO_ENABLED=0 \
    GOOS=linux \
    go build \
        -ldflags="-s -w -X main.version=${BUILD_VERSION} -X main.buildTime=${BUILD_TIME}" \
        -o /server \
        ./cmd/server/


# ──────────────────────────────────────────────────────────
# PRODUCTION — scratch image, samo binarni fajl
# Rezultat: ~10-15MB image umjesto ~300MB golang:alpine
# ──────────────────────────────────────────────────────────
FROM scratch AS production

# SSL certifikati za HTTPS pozive ka externim API-ima
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/

# Timezone data
COPY --from=builder /usr/share/zoneinfo /usr/share/zoneinfo

# Binarni fajl
COPY --from=builder /server /server

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD ["/server", "healthcheck"]

ENTRYPOINT ["/server"]


# ──────────────────────────────────────────────────────────
# DEBUG — Delve remote debugger
# Zahtijeva security_opt i cap_add u docker-compose.debug.yml
# ──────────────────────────────────────────────────────────
FROM golang:1.22-alpine AS debug

RUN go install github.com/go-delve/delve/cmd/dlv@latest

WORKDIR /app
COPY . .

RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    CGO_ENABLED=0 \
    go build \
        -gcflags="all=-N -l" \  # Isključi optimizacije — debugger treba ovo
        -o /server \
        ./cmd/server/

EXPOSE 8080 40000

CMD ["/go/bin/dlv", \
     "exec", "/server", \
     "--headless", \
     "--listen=:40000", \
     "--api-version=2", \
     "--continue", \
     "--accept-multiclient"]
```

---

### Koji target u kojoj situaciji

| Situacija | PHP target | Go target | Komanda |
|-----------|-----------|-----------|---------|
| Lokalni razvoj | `development` | `development` | `docker compose up` (override.yml) |
| Debug session | `debug` | `debug` | `docker compose -f ... debug.yml up` |
| Lokalni testovi | `test` | `test` | `docker build --target test ...` |
| CI test job | `test` | `test` | Build pada ako testovi padnu |
| CI build job | `production` | `production` | Image ide u registry |
| Staging | `production` | `production` | Identičan prod image |
| Produkcija | `production` | `production` | Jedino prihvatljivo |

CI primjer (.gitlab-ci.yml):
```yaml
variables:
  DOCKER_BUILDKIT: "1"

test:php:
  stage: test
  script:
    # Build test targeta — padne ako padnu testovi
    - docker build --target test --tag php-test:${CI_COMMIT_SHA} ./services/php-service
    # Izvuci test rezultate
    - docker run --rm -v ${CI_PROJECT_DIR}/test-results:/app/test-results php-test:${CI_COMMIT_SHA} true

> **Podman:** `podman build --target test --tag php-test:${CI_COMMIT_SHA} ./services/php-service` / `podman run --rm -v ${CI_PROJECT_DIR}/test-results:/app/test-results php-test:${CI_COMMIT_SHA} true`
  artifacts:
    reports:
      junit: test-results/junit.xml

build:php:
  stage: build
  needs: [test:php]
  script:
    - docker build
        --target production
        --cache-from ${CI_REGISTRY_IMAGE}/php-service:cache
        --tag ${CI_REGISTRY_IMAGE}/php-service:${CI_COMMIT_SHA}
        --tag ${CI_REGISTRY_IMAGE}/php-service:latest
        ./services/php-service
    - docker push ${CI_REGISTRY_IMAGE}/php-service:${CI_COMMIT_SHA}
    - docker push ${CI_REGISTRY_IMAGE}/php-service:latest

> **Podman:** `podman build --target production --cache-from ... --tag ... ./services/php-service` / `podman push ${CI_REGISTRY_IMAGE}/php-service:${CI_COMMIT_SHA}`
```

---

## Dio 2: Docker Compose profiles

### Zašto profiles?

Bez profila, `docker compose up` pokreće SVE servise definirane u compose fajlu. To uključuje adminer, redis-commander, prometheus, grafana — sve što si definisao. U razvoju to je nepotrebno. U CI to troši resurse. U debugiranju hoćeš točno određene servise.

Profiles ti daju grupe servisa koje pokrećeš eksplicitno.

### Kompletna konfiguracija za naš projekt

```yaml
# docker-compose.yml
services:

  # ────────────────────────────────────────────────────────
  # CORE servisi — bez profila = uvijek pokrenuti
  # ────────────────────────────────────────────────────────
  nginx:
    image: ${CI_REGISTRY_IMAGE}/nginx:${IMAGE_TAG}
    networks: [app-network]
    ports: ["80:80"]
    depends_on:
      php-service:
        condition: service_healthy
      go-service:
        condition: service_healthy

  php-service:
    image: ${CI_REGISTRY_IMAGE}/php-service:${IMAGE_TAG}
    networks: [app-network]
    depends_on:
      mysql:
        condition: service_healthy
      redis:
        condition: service_healthy

  go-service:
    image: ${CI_REGISTRY_IMAGE}/go-service:${IMAGE_TAG}
    networks: [app-network]
    depends_on:
      mysql:
        condition: service_healthy
      redis:
        condition: service_healthy

  mysql:
    image: mysql:8.0
    networks: [app-network]
    volumes:
      - mysql-data:/var/lib/mysql
    environment:
      MYSQL_DATABASE: ${MYSQL_DATABASE}
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    networks: [app-network]
    volumes:
      - redis-data:/data
    command: redis-server --requirepass ${REDIS_PASSWORD} --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3


  # ────────────────────────────────────────────────────────
  # DEBUG profil — debuggeri za PHP i Go
  # ────────────────────────────────────────────────────────
  php-service-debug:
    profiles: [debug]
    build:
      context: ./services/php-service
      target: debug
    networks: [app-network]
    ports:
      - "9003:9003"
    volumes:
      - ./services/php-service/src:/app/src:ro
    environment:
      APP_ENV: development
      XDEBUG_CLIENT_HOST: host.docker.internal
    depends_on:
      mysql:
        condition: service_healthy
      redis:
        condition: service_healthy

  go-service-debug:
    profiles: [debug]
    build:
      context: ./services/go-service
      target: debug
    networks: [app-network]
    ports:
      - "8080:8080"
      - "40000:40000"
    security_opt:
      - "seccomp:unconfined"
    cap_add:
      - SYS_PTRACE
    depends_on:
      mysql:
        condition: service_healthy


  # ────────────────────────────────────────────────────────
  # TOOLS profil — DB GUI, mail catcher, itd.
  # ────────────────────────────────────────────────────────
  adminer:
    profiles: [tools]
    image: adminer:4.8
    networks: [app-network]
    ports:
      - "8081:8080"
    environment:
      ADMINER_DEFAULT_SERVER: mysql
      ADMINER_DESIGN: dracula

  redis-commander:
    profiles: [tools]
    image: rediscommander/redis-commander:latest
    networks: [app-network]
    ports:
      - "8082:8081"
    environment:
      REDIS_HOSTS: "local:redis:6379:0:${REDIS_PASSWORD}"

  mailhog:
    profiles: [tools]
    image: mailhog/mailhog:latest
    networks: [app-network]
    ports:
      - "1025:1025"   # SMTP
      - "8025:8025"   # Web UI


  # ────────────────────────────────────────────────────────
  # MONITORING profil — Prometheus, Grafana
  # ────────────────────────────────────────────────────────
  prometheus:
    profiles: [monitoring]
    image: prom/prometheus:v2.50.0
    networks: [app-network]
    ports:
      - "9090:9090"
    volumes:
      - ./docker/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.retention.time=7d'

  grafana:
    profiles: [monitoring]
    image: grafana/grafana:10.2.0
    networks: [app-network]
    ports:
      - "3000:3000"
    volumes:
      - grafana-data:/var/lib/grafana
      - ./docker/grafana/dashboards:/etc/grafana/provisioning/dashboards:ro
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD:-admin}
    depends_on:
      - prometheus


  # ────────────────────────────────────────────────────────
  # TEST profil — za integracijsko testiranje
  # ────────────────────────────────────────────────────────
  mysql-test:
    profiles: [test]
    image: mysql:8.0
    networks: [app-network]
    tmpfs:
      - /var/lib/mysql
    environment:
      MYSQL_DATABASE: test_db
      MYSQL_ROOT_PASSWORD: testpass
      MYSQL_USER: testuser
      MYSQL_PASSWORD: testpass
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 5s
      timeout: 3s
      retries: 10


networks:
  app-network:
    driver: bridge

volumes:
  mysql-data:
  redis-data:
  prometheus-data:
  grafana-data:
```

### Pokretanje po profilu

```bash
# Samo core servisi (nginx, php, go, mysql, redis)
docker compose up

# Samo core, detached
docker compose up -d

# Core + debug alati za PHP
docker compose --profile debug up php-service-debug

# Core + tools (adminer, redis-commander, mailhog)
docker compose --profile tools up

# Core + monitoring stack
docker compose --profile monitoring up

# Core + tools + monitoring zajedno
docker compose --profile tools --profile monitoring up

# CI: core + test servisi (bez override.yml!)
docker compose \
    -f docker-compose.yml \
    -f docker-compose.test.yml \
    --profile test \
    up mysql-test

# Shutdown samo debug profila
docker compose --profile debug down

# Shutdown svih profila
docker compose --profile debug --profile tools --profile monitoring down
```

> **Podman:** `podman compose up` / `podman compose up -d` / `podman compose --profile debug up php-service-debug` / `podman compose --profile tools up` / `podman compose --profile monitoring up` / `podman compose --profile debug down`

### COMPOSE_PROFILES env varijabla

Umjesto da pišeš `--profile` svaki put, možeš postaviti u `.env.local`:

```bash
# .env.local
COMPOSE_PROFILES=tools,monitoring
```

Tada je `docker compose up` ekvivalentno `docker compose --profile tools --profile monitoring up`.

Korisno za developerske workstacje gdje uvijek hoćeš iste alate. Ne postavljati u `.env` (koji je u git-u) — svako bira svoje profile.

### Profile naming konvencija

Preporuka: profile po namjeni, ne po servisu:

```
debug       → debuggeri (Xdebug, Delve)
tools       → GUI alati (adminer, redis-commander, mailhog)
monitoring  → observability stack (prometheus, grafana, jaeger)
test        → test infrastruktura (test DB, mock servisi)
```

Ne ovako:
```
php         → LOŠE — profile po servisu, nejasna namjena
database    → LOŠE — zbunjujuće, core DB je uvijek aktivan
```

### Mrežna izolacija po environmentu

Compose automatski kreira mrežu po projektu. Ako koristiš jedan `compose.yml` za sve profile, svi servisi završe na istoj `project_default` mreži — `app-test` kontejner može "vidjeti" `db-dev` ako ga netko pokrene paralelno.

Idealan mentalni model:

```
dev environment
  ├── app-dev, db-dev, redis-dev
  └── dev_network          ← samo dev servisi

test environment
  ├── app-test, db-test, redis-test
  └── test_network         ← samo test servisi
```

Servisi iz dev profila ne smiju vidjeti test. Servisi iz test profila ne smiju vidjeti dev. Ovo je posebno važno u CI gdje se profili mogu pokretati paralelno na istom agentu.

Eksplicitno definiraj mreže po profilu:

```yaml
services:
  # ─── DEV profil ───────────────────────────────────────────
  app-dev:
    build:
      context: .
      target: development
    profiles: [dev]
    networks: [dev_network]

  db-dev:
    image: mysql:8.0
    profiles: [dev]
    networks: [dev_network]

  redis-dev:
    image: redis:7-alpine
    profiles: [dev]
    networks: [dev_network]

  # ─── TEST profil ──────────────────────────────────────────
  app-test:
    build:
      context: .
      target: test
    profiles: [test]
    networks: [test_network]

  db-test:
    image: mysql:8.0
    profiles: [test]
    tmpfs:
      - /var/lib/mysql
    networks: [test_network]

  redis-test:
    image: redis:7-alpine
    profiles: [test]
    networks: [test_network]

networks:
  dev_network:
  test_network:
```

Rezultat:
- `app-dev` vidi `db-dev` i `redis-dev`
- `app-test` vidi `db-test` i `redis-test`
- `app-dev` ne vidi `db-test`, i obratno

**Napomena o produkciji:** prod se ne pokreće lokalnim `docker compose --profile prod up` osim za malu aplikaciju ili VPS. Za ozbiljnije okruženje:

```
dev/test lokalno  → Docker Compose s eksplicitnim mrežama
prod              → Kubernetes (izolacija ide preko namespace, NetworkPolicy, ServiceAccount)
```

Minimum u CI/CD za provjeru da prod image nije "mrtav":

```bash
# Build prod image-a
docker build --target production -t myapp:prod .

# Smoke test — potvrdi da se pokreće
docker run --rm myapp:prod php -v
docker run -d -p 8080:80 --name smoke myapp:prod
curl --fail http://localhost:8080/health
docker rm -f smoke
```

> **Podman:** `podman build --target production -t myapp:prod .` / `podman run --rm myapp:prod php -v`

---

## Kombinovanje targeta i profila

Ovo je prava moć — target kontrolira šta je u image-u, profil kontrolira koji servisi se pokreću:

```
docker compose --profile debug up php-service-debug
                    │                      │
                    └─ Koji servis         └─ php-service-debug koristi
                       se pokreće            build.target: debug
```

Za CI pipeline, kombinacija izgleda ovako:

```yaml
# .gitlab-ci.yml
test:integration:
  stage: test
  script:
    # Pokreni test infrastrukturu (mysql-test iz test profila)
    - docker compose
        -f docker-compose.yml
        -f docker-compose.test.yml
        --profile test
        up -d mysql-test

    # Builduj test target za go-service (pokreće go test u build fazi)
    - docker build
        --target test
        --tag go-service-test:${CI_COMMIT_SHA}
        ./services/go-service

    # Pokreni integracijske testove (test kontejner komunicira s mysql-test)
    - docker run
        --network project-a_app-network
        --env DB_HOST=mysql-test
        go-service-test:${CI_COMMIT_SHA}
        go test ./tests/integration/...

> **Podman:** `podman compose -f docker-compose.yml -f docker-compose.test.yml --profile test up -d mysql-test` / `podman build --target test --tag go-service-test:${CI_COMMIT_SHA} ./services/go-service` / `podman run --network project-a_app-network --env DB_HOST=mysql-test go-service-test:${CI_COMMIT_SHA} go test ./tests/integration/...`

  after_script:
    - docker compose
        -f docker-compose.yml
        -f docker-compose.test.yml
        --profile test
        down --volumes

> **Podman:** `podman compose -f docker-compose.yml -f docker-compose.test.yml --profile test down --volumes`
```
