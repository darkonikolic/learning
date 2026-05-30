# 09 — Config fajlovi kompletno

Svaki Docker projekat ima isti problem: previše fajlova, nejasno koji se primjenjuje kada, i zašto build radi lokalno ali ne i u CI. Ovaj dokument pokriva svaki config fajl koji postoji u projektu, precizno objašnjava merge logiku i daje konkretne primjere za naš stack.

---

## Pregled svih fajlova

```
project-root/
├── docker-compose.yml             ← base, production-equivalent
├── docker-compose.override.yml    ← dev (automatski merge)
├── docker-compose.debug.yml       ← debug (eksplicitno)
├── docker-compose.test.yml        ← CI testovi (eksplicitno)
├── .env                           ← default vrijednosti, u git-u
├── .env.local                     ← lokalni override, NIKAD u git
├── .dockerignore                  ← što ne ići u build context
└── ~/.docker/daemon.json          ← Docker daemon konfiguracija
```

---

## docker-compose.yml — base fajl

Ovaj fajl opisuje production-equivalent servis konfiguraciju. Ne sadrži ništa dev-specifično: nema `build:`, nema eksponiranih portova ka hostu (osim onih koji su i u produkciji), nema bind mountova za source kod.

Pravilo: sve što piše ovdje mora biti smisleno i u produkciji.

```yaml
# docker-compose.yml
services:
  nginx:
    image: ${CI_REGISTRY_IMAGE}/nginx:${IMAGE_TAG}
    networks: [app-network]
    ports: ["80:80", "443:443"]
    depends_on:
      php-service:
        condition: service_healthy
    restart: unless-stopped

  php-service:
    image: ${CI_REGISTRY_IMAGE}/php-service:${IMAGE_TAG}
    networks: [app-network]
    depends_on:
      mysql:
        condition: service_healthy
      redis:
        condition: service_healthy
    environment:
      APP_ENV: ${APP_ENV}
      DB_HOST: mysql
      DB_NAME: ${MYSQL_DATABASE}
      REDIS_HOST: redis
    healthcheck:
      test: ["CMD", "php-fpm-healthcheck"]
      interval: 30s
      timeout: 3s
      retries: 3
      start_period: 10s
    restart: unless-stopped

  go-service:
    image: ${CI_REGISTRY_IMAGE}/go-service:${IMAGE_TAG}
    networks: [app-network]
    depends_on:
      mysql:
        condition: service_healthy
      redis:
        condition: service_healthy
    environment:
      APP_ENV: ${APP_ENV}
      DB_HOST: mysql
      DB_NAME: ${MYSQL_DATABASE}
      REDIS_HOST: redis
    healthcheck:
      test: ["CMD", "wget", "-qO-", "http://localhost:8080/health"]
      interval: 30s
      timeout: 3s
      retries: 3
    restart: unless-stopped

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
    restart: unless-stopped

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
    restart: unless-stopped

networks:
  app-network:
    driver: bridge

volumes:
  mysql-data:
    driver: local
  redis-data:
    driver: local
```

Zašto nema `ports:` za MySQL i Redis: u produkciji ti servisi nisu dostupni direktno sa hosta. Samo nginx je eksponiran. Ostali komunikiraju interno unutar `app-network`.

---

## docker-compose.override.yml — automatski merge

Docker Compose automatski učitava i merge-uje ovaj fajl kada pokreneš `docker compose up` bez eksplicitnog `-f`. Ne moraš ga navoditi — to je njegova svrha.

Sadrži isključivo dev-specifične izmjene: `build:` direktive (jer lokalno buildujemo image, ne povlačimo iz registra), bind mountove za live reload, i eksponirane portove za lokalne alate.

```yaml
# docker-compose.override.yml
# NAPOMENA: Ovaj fajl je AUTOMATSKI aktivan pri `docker compose up`.
# Ne commitovati build-specific secretsili lozinke ovdje.

services:
  php-service:
    # Lokalno buildujemo, ne koristimo registry image
    image: ""  # Poništi image iz base fajla
    build:
      context: ./services/php-service
      target: development
      cache_from:
        - ${CI_REGISTRY_IMAGE}/php-service:cache
    volumes:
      # Live reload — promjene u src/ vidljive odmah, bez rebuild
      - ./services/php-service/src:/app/src:ro
      - ./services/php-service/config:/app/config:ro
    environment:
      APP_ENV: development
      APP_DEBUG: "true"
      # Xdebug client host — Docker Desktop (Mac/Win) vs Linux
      XDEBUG_CLIENT_HOST: host.docker.internal

  go-service:
    image: ""
    build:
      context: ./services/go-service
      target: development
    volumes:
      - ./services/go-service:/app:ro
    environment:
      APP_ENV: development

  vue-frontend:
    image: ""
    build:
      context: ./services/vue-frontend
      target: development
    volumes:
      - ./services/vue-frontend/src:/app/src:ro
    ports:
      - "5173:5173"  # Vite dev server
    environment:
      NODE_ENV: development

  # Eksponiraj DB portove lokalno — za DBeaver, TablePlus, DataGrip
  mysql:
    ports:
      - "3306:3306"

  redis:
    ports:
      - "6379:6379"
```

Merge logika: vrijednosti iz override-a se spajaju sa base fajlom. Arrays (kao `ports`, `volumes`, `environment`) se konkateniraju. Skalarne vrijednosti (kao `image`) se prepisuju.

---

## docker-compose.debug.yml — eksplicitni debug

Ovaj fajl se ne učitava automatski. Mora se eksplicitno navesti uz `-f`.

```bash
# PHP debug session
docker compose \
  -f docker-compose.yml \
  -f docker-compose.override.yml \
  -f docker-compose.debug.yml \
  up php-service

# Go debug session
docker compose \
  -f docker-compose.yml \
  -f docker-compose.override.yml \
  -f docker-compose.debug.yml \
  up go-service
```

> **Podman:**
> ```bash
> podman compose \
>   -f docker-compose.yml \
>   -f docker-compose.override.yml \
>   -f docker-compose.debug.yml \
>   up php-service
> ```

```yaml
# docker-compose.debug.yml
services:
  php-service:
    build:
      target: debug        # Xdebug instaliran u ovom targetu
    ports:
      - "9003:9003"        # Xdebug port — PhpStorm sluša ovdje

  go-service:
    build:
      context: ./services/go-service
      dockerfile: docker/go/Dockerfile
      target: debug
    ports:
      - "40000:40000"      # Delve remote debugger
    security_opt:
      - "seccomp:unconfined"  # Potrebno za Delve
    cap_add:
      - SYS_PTRACE          # Potrebno za Delve attach
```

Zašto odvojeno: Xdebug značajno usporava PHP (i do 10x). Delve zahtijeva opasne kernel capabilities. Ništa od ovoga ne smije biti uvijek aktivno.

---

## docker-compose.test.yml — CI testovi

Koristi se u CI pipeline-u za pokretanje integracijskog testiranja sa test-specifičnom bazom.

```yaml
# docker-compose.test.yml
services:
  mysql-test:
    image: mysql:8.0
    environment:
      MYSQL_DATABASE: test_db
      MYSQL_ROOT_PASSWORD: testpass
      MYSQL_USER: testuser
      MYSQL_PASSWORD: testpass
    tmpfs:
      - /var/lib/mysql     # U memoriji — brže, nema persistencije

  php-test:
    build:
      context: ./services/php-service
      target: test
    depends_on:
      mysql-test:
        condition: service_healthy
    environment:
      DB_HOST: mysql-test
      DB_NAME: test_db
      APP_ENV: testing
    volumes:
      - ./test-results:/app/test-results  # Izvuci JUnit XML za CI

  go-service-test:
    build:
      context: ./services/go-service
      target: test
    depends_on:
      mysql-test:
        condition: service_healthy
    environment:
      DB_HOST: mysql-test
      DB_NAME: test_db
```

CI pokretanje:
```bash
# Pokreni testove, izlaz = exit code go-service-test procesa
docker compose \
  -f docker-compose.yml \
  -f docker-compose.test.yml \
  run --rm go-service-test

# Čišćenje nakon CI joba
docker compose \
  -f docker-compose.yml \
  -f docker-compose.test.yml \
  down --volumes --remove-orphans
```

> **Podman:**
> ```bash
> podman compose \
>   -f docker-compose.yml \
>   -f docker-compose.test.yml \
>   run --rm go-service-test
>
> podman compose \
>   -f docker-compose.yml \
>   -f docker-compose.test.yml \
>   down --volumes --remove-orphans
> ```

---

## .env fajl — default vrijednosti

Ovo je jedini `.env` fajl koji smije biti u git-u. Sadrži default vrijednosti koje su sigurne za javnost — bez pravih lozinki, bez production secrets.

```bash
# .env
# Default vrijednosti za lokalni razvoj.
# Ove vrijednosti se koriste ako nisu overridovane u .env.local ili shell env.

# Docker registry
CI_REGISTRY_IMAGE=registry.example.com/project-a
IMAGE_TAG=latest

# App
APP_ENV=development

# Database
MYSQL_DATABASE=project_a
# MYSQL_ROOT_PASSWORD nije ovdje — to je secret, ide u .env.local

# Redis
# REDIS_PASSWORD nije ovdje — ide u .env.local
```

---

## .env.local — lokalni override

Nikad ne idi u git. Dodaj u `.gitignore`:

```bash
# .gitignore
.env.local
.env.*.local
```

```bash
# .env.local — lokalni override sa pravim lozinkama
MYSQL_ROOT_PASSWORD=localdevpass123
REDIS_PASSWORD=localredispass

# Možeš overridovati i ostalo
IMAGE_TAG=my-feature-branch
```

Prioritet env varijabli (od najvišeg prema najnižem):
1. Shell environment varijable (export FOO=bar prije docker compose up)
2. `environment:` direktiva unutar compose fajla
3. `env_file:` direktiva unutar compose fajla
4. `.env` fajl u istom direktorijumu gdje se pokreće docker compose

Ova hijerarhija znači: CI može setovati `MYSQL_ROOT_PASSWORD` kao shell varijablu i ona će pregaziti sve što piše u `.env`.

---

## .dockerignore — kritičan za sigurnost i performanse

Ovo nije samo optimizacija. Bez `.dockerignore`, sve što šalješ u build context može završiti u image-u ako Dockerfile ima `COPY . .`.

```
# .dockerignore

# Version control
.git/
.gitignore

# Secrets — NIKAD ne smiju ući u image
.env.local
.env.*.local
*.pem
*.key
secrets/

# Dependency direktorijumi — instaliraju se u build stageu
node_modules/
vendor/            # PHP — composer install radi u Dockerfileu

# Go build artefakti
*.test             # go test binary
coverage.out
coverage.html
profiles/          # pprof profili

# Debug artefakti
__debug_bin*       # Delve debug binary
*.prof             # Xdebug profili

# OS i editor fajlovi
.DS_Store
Thumbs.db
.idea/
.vscode/
*.swp

# Logovi — ne trebaju biti u image-u
*.log
logs/

# Testovi — ne trebaju biti u production image-u
# (ali mogu biti potrebni u test targetu — vidi Dockerfile)
# tests/            # Komentiraj ako test target treba pristup testovima

# CI/CD
.gitlab-ci.yml
.github/
Jenkinsfile
```

Praktična provjera: `docker build --no-cache .` i zatim `docker history <image>` da vidiš veličinu svakog layer-a. Ako `COPY` layer ima stotine MB, nešto nije dobro.

> **Podman:** `podman build --no-cache .` / `podman history <image>`

---

## daemon.json — Docker daemon konfiguracija

Ovo je konfiguracija za sam Docker daemon, ne za kontejnere. Mijenja se rijetko, ali kada treba — mora se znati gdje je i šta mijenjati.

Lokacija:
- macOS Docker Desktop: `~/.docker/daemon.json` (ili kroz Docker Desktop GUI > Settings > Docker Engine)
- Linux: `/etc/docker/daemon.json` (zahtijeva `systemctl restart docker`)

> **Podman:** Nema daemon.json. Podman konfiguracija je u `~/.config/containers/containers.conf` (rootless) ili `/etc/containers/containers.conf` (sistem). Log driver i ulimiti se postavljaju tamo. Podman nema centralnog daemona koji bi se restartovao — konfiguracija se primjenjuje pri svakom pozivu.

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "default-ulimits": {
    "nofile": {
      "Hard": 64000,
      "Soft": 64000
    }
  },
  "features": {
    "buildkit": true
  },
  "registry-mirrors": [],
  "insecure-registries": []
}
```

Zašto `log-driver` i `log-opts`: Docker zadano nema limit na veličinu logova. Kontejner koji puno loguje može popuniti disk za dan-dva. `max-size: 10m` i `max-file: 3` daje maksimalno 30MB po kontejneru, s rotacijom.

Zašto `nofile` ulimit: MySQL, Redis i Go HTTP server otvaraju mnogo file descriptora pri velikom broju konekcija. Default Linux limit je 1024, što je premalo. 64000 je sigurna vrijednost za development.

Zašto `buildkit: true` u daemon.json: BuildKit je brži build engine s parallelizacijom stagea, boljim cache mehanizmom i podrškom za `--secret` i `--mount=type=cache`. Na novijim verzijama Dockera je already default, ali eksplicitno postavljanje garantuje ponašanje.

---

## BuildKit env varijable

Ako iz nekog razloga ne možeš mijenjati daemon.json (dijeljeni Linux server, CI runner), možeš aktivirati BuildKit per-session:

```bash
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

docker compose up --build
```

Ili inline za jedan build:
```bash
DOCKER_BUILDKIT=1 docker build --target production -t myapp:latest .
```

> **Podman:** Podman koristi buildah ispod haube i nema BuildKit. `DOCKER_BUILDKIT` varijabla se ignoriše. `--mount=type=cache` i `--mount=type=secret` rade nativno bez ikakve konfiguracije (Podman 4.2+).
> ```bash
> podman compose up --build
> podman build --target production -t myapp:latest .
> ```

U GitLab CI, postavi ove varijable kao project-level CI/CD variables ili direktno u `.gitlab-ci.yml`:

```yaml
variables:
  DOCKER_BUILDKIT: "1"
  COMPOSE_DOCKER_CLI_BUILD: "1"
```

---

## Merge vizualizacija

Kada pokreneš `docker compose up` lokalno:

```
docker-compose.yml         (base — uvijek)
       +
docker-compose.override.yml (automatski — ako postoji)
       =
Efektivna konfiguracija
```

Kada pokreneš debug:
```
docker-compose.yml
       +
docker-compose.override.yml
       +
docker-compose.debug.yml   (eksplicitno s -f)
       =
Efektivna konfiguracija s debuggerom
```

U CI:
```
docker-compose.yml
       +
docker-compose.test.yml    (eksplicitno s -f, nema override.yml)
       =
Test konfiguracija bez dev alata
```

Ovo je ključna razlika: CI ne smije automatski povući `override.yml` (koji sadrži `build:` sa `target: development`). Ako ne navedeš `-f docker-compose.override.yml` eksplicitno u CI, on se neće ni učitati — što je tačno ono što hoćeš.
