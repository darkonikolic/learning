# 02 — Xdebug PHP konfiguracija

## Xdebug 3 vs Xdebug 2: kritična razlika

Ako guglate Xdebug greške, mnogi rezultati su za Xdebug 2. **Konfiguracija je potpuno drugačija:**

| Postavka | Xdebug 2 | Xdebug 3 |
|----------|----------|----------|
| Enable step debug | `xdebug.remote_enable=1` | `xdebug.mode=debug` |
| Client host | `xdebug.remote_host` | `xdebug.client_host` |
| Client port | `xdebug.remote_port=9000` | `xdebug.client_port=9003` |
| Auto start | `xdebug.remote_autostart=1` | `xdebug.start_with_request=yes` |

Port 9000 → 9003 je najčešća greška pri migraciji. PHP-FPM i starije Xdebug instalacije koristile su 9000 koji se sukobljava sa php-fpm masterom.

---

## Dockerfile za PHP debug target

```dockerfile
# docker/php/Dockerfile

FROM php:8.3-fpm-alpine AS base

# Instaliraj sistem dependencies
RUN apk add --no-cache \
    libzip-dev \
    zip \
    unzip \
    curl

# Instaliraj PHP extenzije potrebne aplikaciji
RUN docker-php-ext-install pdo pdo_mysql zip opcache

# Composer
COPY --from=composer:2.7 /usr/bin/composer /usr/bin/composer

WORKDIR /app
COPY composer.json composer.lock ./
RUN composer install --no-dev --optimize-autoloader --no-interaction

COPY src/ /app/src/
COPY docker/php/php-fpm.conf /usr/local/etc/php-fpm.d/www.conf

# ─── Debug target ───────────────────────────────────────────────────────────
FROM base AS debug

# Instaliraj build dependencies, instaliraj Xdebug, ukloni build deps
# Fiksirana verzija: uvijek znamo što je instalirano, nema iznenađenja
RUN apk add --no-cache $PHPIZE_DEPS \
    && pecl install xdebug-3.3.1 \
    && docker-php-ext-enable xdebug \
    && apk del $PHPIZE_DEPS

# Composer install WITH dev dependencies za debug (npr. var-dumper, faker)
RUN composer install --optimize-autoloader --no-interaction

COPY docker/php/xdebug.ini /usr/local/etc/php/conf.d/docker-php-ext-xdebug.ini

# ─── Production target ───────────────────────────────────────────────────────
FROM base AS production
# Nema Xdebug, nema dev dependencies, nema debug konfiguracije
# composer install --no-dev već je pokrenut u base stage-u
```

Napomena o `$PHPIZE_DEPS`: ovo je Docker PHP oficijalna varijabla koja sadrži sve pakete potrebne za kompajliranje PHP ekstenzija (`autoconf`, `g++`, `gcc`, `make` itd.). Instaliramo ih, kompajliramo Xdebug, a zatim brišemo da smanjimo image veličinu.

---

## `docker/php/xdebug.ini` — kompletna konfiguracija

```ini
[xdebug]
; ─── Osnovni mod ─────────────────────────────────────────────────────────────
; Xdebug 3 koristi mode umjesto pojedinačnih enable/disable postavki
; debug     = step debugger (breakpoints, variable inspection)
; develop   = poboljšani var_dump, stack trace prikaz
; profile   = Cachegrind output za performance analizu
; trace     = log svake funkcije (veoma verbose)
; coverage  = code coverage za PHPUnit
; Može se kombinovati zarezom: xdebug.mode=debug,develop
xdebug.mode=debug

; ─── Pokretanje debuga ───────────────────────────────────────────────────────
; yes     = debug svaki request automatski (development convenience)
; no      = nikad ne debuguj (override za privremeno gašenje)
; trigger = debug samo kad je prisutan XDEBUG_TRIGGER cookie/header/GET param
;           trigger je bolji za shared dev okruženja gdje više developera radi
xdebug.start_with_request=yes

; ─── Konekcija prema IDE-u ───────────────────────────────────────────────────
; Xdebug se KONEKTUJE prema IDE-u (ne obrnuto)
; IDE sluša na portu, Xdebug inicira konekciju

; host.docker.internal: Docker Desktop (Mac i Windows) magic hostname
; koji automatski resolv-uje na host machine IP
; Na Linux: host.docker.internal ne postoji po defaultu!
; Linux rješenje 1: koristiti docker-compose extra_hosts: host.docker.internal:host-gateway
; Linux rješenje 2: eksplicitni IP bridge interfejsa: 172.17.0.1
; Linux rješenje 3: environment variable: XDEBUG_CONFIG=client_host=192.168.1.x
xdebug.client_host=host.docker.internal

; Xdebug 3 default port je 9003
; Xdebug 2 koristio je 9000 (konflikt sa php-fpm i nekad supervisord)
; Ako 9003 nije slobodan: lsof -i :9003 da vidiš što ga koristi
xdebug.client_port=9003

; ─── IDE key ─────────────────────────────────────────────────────────────────
; IDE key mora se podudarati sa VS Code konfiguracijim
; VS Code PHP Debug ekstenzija koristi VSCODE kao default key
; PhpStorm koristi PHPSTORM
; Važno za trigger mode: XDEBUG_SESSION_START=VSCODE u URL-u
xdebug.idekey=VSCODE

; ─── Logging ─────────────────────────────────────────────────────────────────
; Log fajl pomaže pri dijagnostici kada debug ne radi
; log_level=0 = samo greške (minimalno)
; log_level=7 = sve (veoma verbose, samo za dijagnostiku)
; Promijeni na 7 kad dijagnostikuješ zašto konekcija ne radi
xdebug.log=/tmp/xdebug.log
xdebug.log_level=0

; ─── Timeout ─────────────────────────────────────────────────────────────────
; Koliko sekundi Xdebug čeka na IDE konekciju
; Default je 20 sekundi — povećaj ako VS Code sporo startuje
xdebug.connect_timeout_ms=2000

; ─── Limiti za varijable ─────────────────────────────────────────────────────
; Koliko duboko prikazivati nested strukture u debuggeru
; Previsoke vrijednosti mogu zamrznuti VS Code za velike objekte
xdebug.var_display_max_depth=5
xdebug.var_display_max_children=256
xdebug.var_display_max_data=1024
```

---

## `docker-compose.override.yml` za PHP

```yaml
# docker-compose.override.yml
# Automatski se merge-uje sa docker-compose.yml pri 'docker compose up'
# Ovaj fajl se commit-uje — sadrži samo dev/debug konfiguraciju

version: "3.9"

services:
  php-service:
    build:
      # Override base target sa debug target-om
      target: debug
    environment:
      # XDEBUG_CONFIG env var override-uje xdebug.ini postavke
      # Korisno za privremenu promjenu bez rebuild-a
      XDEBUG_CONFIG: "client_host=host.docker.internal client_port=9003"
      # APP_ENV mora biti development za debug mode u aplikaciji
      APP_ENV: development
    ports:
      # Xdebug se KONEKTUJE na host, ne prima konekcije
      # Ovaj port nije potreban za Xdebug step debug
      # Ali je potreban ako koristiš reverse tunnel ili non-standard setup
      # Zakomentiraj ako nije potrebno
      # - "9003:9003"
    extra_hosts:
      # Linux fix: dodaj host.docker.internal kao alias za host gateway
      # Na Mac/Windows Docker Desktop ovo postoji automatski
      # Na Linux mora se eksplicitno dodati
      - "host.docker.internal:host-gateway"
    volumes:
      # Mount source koda za live reload — ne treba rebuild za code promjene
      - ./services/php-service/src:/app/src
      # Mount composer vendor za brži razvoj
      - ./services/php-service/vendor:/app/vendor
      # Profile output direktorij (za profiling mode)
      - ./profiles/php:/tmp/xdebug-profiles
```

---

## `.vscode/launch.json` za PHP

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Listen for Xdebug (PHP)",
      "type": "php",
      "request": "launch",
      "port": 9003,
      "hostname": "0.0.0.0",
      "pathMappings": {
        "/app/src": "${workspaceFolder}/services/php-service/src",
        "/app/vendor": "${workspaceFolder}/services/php-service/vendor"
      },
      "log": true,
      "ignore": [
        "**/vendor/**/*.php"
      ]
    }
  ]
}
```

`pathMappings` detalji:
- Ključ je **putanja unutar kontejnera** (kako Xdebug vidi fajl)
- Vrijednost je **lokalna putanja** (kako VS Code vidi fajl)
- `${workspaceFolder}` je root direktorij koji si otvorio u VS Code-u
- Ako imaš monorepo sa više servisa, svaki servis treba sopstveni mapping
- Vendor direktori: dodaj mapping samo ako debuguješ Composer pakete

`ignore`: preskače breakpoint-e u vendor direktoriju — bez ovoga debugger staje u Composer pakete pri step-in što je rijetko korisno.

---

## Korak po korak verifikacija

### Korak 1: Pokreni servise

```bash
# Rebuild + pokretanje (override.yml se automatski uključuje)
docker compose up --build php-service

# Provjeri da je Xdebug učitan
docker exec <php-container-name> php -m | grep xdebug
# Očekivani output: xdebug
```

> **Podman:** `podman compose up --build php-service`
> **Podman:** `podman exec <php-container-name> php -m | grep xdebug`

### Korak 2: Provjeri Xdebug konfiguraciju unutar kontejnera

```bash
docker exec <php-container-name> php -i | grep xdebug.client_host
# Mora biti: xdebug.client_host => host.docker.internal => host.docker.internal

docker exec <php-container-name> php -i | grep xdebug.mode
# Mora biti: xdebug.mode => debug => debug
```

> **Podman:** `podman exec <php-container-name> php -i | grep xdebug.client_host`
> **Podman:** `podman exec <php-container-name> php -i | grep xdebug.mode`

### Korak 3: Pokreni VS Code listener

1. Otvori VS Code u root direktoriju projekta
2. Pritisni `F5` ili idi na Run → Start Debugging
3. Odaberi "Listen for Xdebug (PHP)"
4. Status bar postaje narandžast/crvenkast, pojavljuje se debug toolbar
5. Provjeri Output → PHP Debug za eventualene greške

### Korak 4: Postavi breakpoint i pošalji request

```bash
# Postavi breakpoint u VS Code na npr. liniju u auth controller-u
# Zatim pošalji request:
curl -X POST http://localhost/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"testpass"}'
```

VS Code mora se fokusirati i pokazati žutu liniju na breakpointu. U lijevom panelu vidiš:
- **Variables**: lokalne i globalne varijable
- **Watch**: izrazi koje pratiš
- **Call Stack**: stack trace do ovog trenutka
- **Breakpoints**: lista svih breakpoint-a

### Korak 5: Debug Xdebug log ako ne radi

```bash
# Privremeno povećaj log level
docker exec <php-container-name> bash -c "echo 'xdebug.log_level=7' >> /usr/local/etc/php/conf.d/docker-php-ext-xdebug.ini"

# Restart PHP-FPM
docker exec <php-container-name> kill -USR2 1

# Pošalji request i čitaj log
docker exec <php-container-name> tail -f /tmp/xdebug.log
```

> **Podman:** `podman exec <php-container-name> bash -c "echo 'xdebug.log_level=7' >> /usr/local/etc/php/conf.d/docker-php-ext-xdebug.ini"`
> **Podman:** `podman exec <php-container-name> kill -USR2 1`
> **Podman:** `podman exec <php-container-name> tail -f /tmp/xdebug.log`

---

## Česte greške i rješenja

### Greška 1: "Xdebug: [Step Debug] Could not connect to debugging client"

```
Xdebug: [Step Debug] Could not connect to debugging client. Tried: host.docker.internal:9003
```

**Uzroci:**
- VS Code PHP Debug listener nije pokrenut
- Pogrešan `client_host` — na Linuxu `host.docker.internal` ne resolv-uje
- Firewall blokira port 9003

**Rješenja:**
```bash
# Provjeri da VS Code sluša
lsof -i :9003
# Mora pokazati VS Code process

# Na Linuxu: provjeri extra_hosts u compose override
docker exec <php-container-name> cat /etc/hosts | grep host.docker.internal
# Mora biti: 172.17.0.1 host.docker.internal

# Ako extra_hosts nije dodao: ručno provjeri host IP
docker inspect bridge | grep Gateway
# Koristi taj IP direktno u xdebug.ini: xdebug.client_host=172.17.0.1
```

> **Podman:** `podman exec <php-container-name> cat /etc/hosts | grep host.docker.internal`
> **Podman:** `podman inspect bridge | grep Gateway`

### Greška 2: Port 9003 već zauzet

```bash
lsof -i :9003
# Vidiš koji proces koristi port

# Promijeni port u xdebug.ini:
# xdebug.client_port=9004

# I u launch.json:
# "port": 9004
```

### Greška 3: Breakpoint nije pogođen (crveni krug bez tačke)

VS Code pokazuje prazan krug umjesto ispunjene crvene tačke — znači da fajl nije mapiran.

**Uzroci:**
- `pathMappings` u `launch.json` su pogrešni
- Lokalni fajl koji editiraš nije isti koji se izvršava u kontejneru

**Dijagnoza:**
```bash
# Provjeri stvarnu putanju unutar kontejnera
docker exec <php-container-name> find /app -name "AuthController.php"
# Output: /app/src/Controllers/AuthController.php

# U launch.json mapping mora biti:
# "/app/src": "${workspaceFolder}/services/php-service/src"
# Ne: "/app": "${workspaceFolder}/services/php-service"
```

> **Podman:** `podman exec <php-container-name> find /app -name "AuthController.php"`

Uobičajena greška: mapping ide previše visoko. Ako mapiraš `/app` na `./services/php-service`, kontejnerski put `/app/src/Controllers/...` postaje `./services/php-service/src/Controllers/...` — ali VS Code treba da pronađe fajl na tom putu. Provjeri da lokalna putanja zaista postoji.

### Greška 4: Xdebug nije učitan

```bash
docker exec <php-container-name> php -m | grep xdebug
# Prazno — Xdebug nije učitan

# Provjeri da li je build koristio debug target
docker inspect <php-container-name> | grep -A5 "Config"
# Ili:
docker compose ps
# Provjeri koji image se koristi
```

> **Podman:** `podman exec <php-container-name> php -m | grep xdebug`
> **Podman:** `podman inspect <php-container-name> | grep -A5 "Config"`
> **Podman:** `podman compose ps`

Uzrok je najčešće da `docker-compose.override.yml` nije primjenjen ili `target: debug` nije u override fajlu.

```bash
# Provjeri koja konfiguracija se primjenjuje
docker compose config | grep target
# Mora pokazati: target: debug
```

> **Podman:** `podman compose config | grep target`

### Greška 5: Debugger se konektuje ali odmah prekida

Simptom: VS Code dostigne breakpoint, ali odmah nastavi bez pauziranja.

**Uzrok**: Multiple PHP-FPM worker procesi — svaki worker pokušava konekciju. VS Code Connected na prvog, ostali prave novu konekciju koja se odbija i PHP-FPM worker završava request bez čekanja.

**Rješenje**: U development, smanji PHP-FPM worker pool na 1:

```ini
; docker/php/php-fpm.conf
[www]
pm = static
pm.max_children = 1
```

Ovo znači samo jedan simultani request — savršeno za debugging, neprihvatljivo za produkciju.
