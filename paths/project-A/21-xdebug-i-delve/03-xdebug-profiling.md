# 03 — Xdebug profiling i tracing

## Razlika između debug, profile i trace moda

| Mode | Šta radi | Kad koristiti |
|------|----------|---------------|
| `debug` | Step debugger, breakpoints | Nepoznati bug, logičke greške |
| `profile` | Cachegrind fajl sa timing podacima | Spori endpoint, memory problem |
| `trace` | Log svake pozvane funkcije | Praćenje toka izvršavanja |
| `develop` | Poboljšani var_dump, stack trace | Svakodnevni razvoj bez debuggera |

Mode-ovi se mogu kombinovati zarezom: `xdebug.mode=debug,develop`

---

## Profile mode — pronalaženje performance bottleneck-a

### Konfiguracija za profilisanje svih requestova

```ini
; docker/php/xdebug-profile.ini
[xdebug]
xdebug.mode=profile

; Direktorij gdje se čuvaju Cachegrind fajlovi
; Mora biti writable od PHP-FPM procesa
xdebug.output_dir=/tmp/xdebug-profiles

; Naming pattern za output fajlove:
; %p = PHP process ID
; %t = timestamp
; %R = request URI (zamjenjuje / sa _)
; %H = HTTP host
; Rezultat: cachegrind.out.1234.1710432000
xdebug.profiler_output_name=cachegrind.out.%p.%t

; Generiši profil za svaki request
xdebug.start_with_request=yes
```

### Volume mount za profile output

```yaml
# docker-compose.override.yml
services:
  php-service:
    build:
      target: debug
    environment:
      # Override da koristiš profile xdebug.ini umjesto debug
      PHP_INI_SCAN_DIR: "/usr/local/etc/php/conf.d:/usr/local/etc/php/conf.debug"
    volumes:
      - ./docker/php/xdebug-profile.ini:/usr/local/etc/php/conf.d/docker-php-ext-xdebug.ini
      - ./profiles/php:/tmp/xdebug-profiles
```

Ili jednostavnije — swap xdebug.ini za profile verziju pri potrebi:

```bash
# Privremeno aktiviraj profile mode
docker cp docker/php/xdebug-profile.ini php-service:/usr/local/etc/php/conf.d/docker-php-ext-xdebug.ini
docker exec php-service kill -USR2 1  # graceful PHP-FPM reload

# Pošalji nekoliko requestova
curl http://localhost/api/slow-endpoint

# Vrati nazad debug mode
docker cp docker/php/xdebug.ini php-service:/usr/local/etc/php/conf.d/docker-php-ext-xdebug.ini
docker exec php-service kill -USR2 1
```

> **Podman:** `podman cp docker/php/xdebug-profile.ini php-service:/usr/local/etc/php/conf.d/docker-php-ext-xdebug.ini`
> **Podman:** `podman exec php-service kill -USR2 1`
> **Podman:** `podman cp docker/php/xdebug.ini php-service:/usr/local/etc/php/conf.d/docker-php-ext-xdebug.ini`
> **Podman:** `podman exec php-service kill -USR2 1`

---

## Trigger mode — profiliraj samo određeni request

Profiling svih requestova generiše gomilu fajlova i usporava sve. Trigger mode aktivira profilisanje samo za specifičan request.

```ini
; docker/php/xdebug-profile-trigger.ini
[xdebug]
xdebug.mode=profile
xdebug.output_dir=/tmp/xdebug-profiles
xdebug.profiler_output_name=cachegrind.out.%p.%t.%R
xdebug.start_with_request=trigger
```

Pokretanje profila via GET parametar:

```bash
# Profiliraj login endpoint
curl "http://localhost/api/auth/login?XDEBUG_PROFILE=1" \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"pass"}'

# Pronađi generirani Cachegrind fajl
ls -lh ./profiles/php/
```

Via HTTP header (korisno za JSON POST requestove gdje GET params ne odgovaraju):

```bash
curl -X POST http://localhost/api/auth/login \
  -H "X-Xdebug-Profile: 1" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"pass"}'
```

Via cookie (za browser testiranje):

```
# U browser developer tools → Application → Cookies:
# Name: XDEBUG_SESSION
# Value: VSCODE
# Sve while naredni requests će biti profilirani
```

---

## Analiza Cachegrind fajlova

### PHPStorm (ugrađeni viewer)

Tools → Analyze Xdebug Profiler Snapshot → odaberi `.cachegrind` fajl

Prikazuje:
- **Inclusive time**: ukupno vrijeme uključujući sve pozvane funkcije
- **Exclusive time**: samo vlastito vrijeme funkcije (bez callees)
- **Call count**: broj poziva
- **Memory usage**: alocirana memorija

### VS Code — php-profile-viewer ekstenzija

1. Instaliraj: `ms-php.php-profiler` ili `hbenl.vscode-php-profiler`
2. Command Palette (`Ctrl+Shift+P`): "Open PHP Profiler"
3. Odaberi Cachegrind fajl

### CLI — qcachegrind / kcachegrind

```bash
# MacOS
brew install qcachegrind
qcachegrind ./profiles/php/cachegrind.out.1234.1710432000

# Linux (KDE)
apt-get install kcachegrind
kcachegrind ./profiles/php/cachegrind.out.1234.1710432000
```

### Ručna analiza Cachegrind fajla

Cachegrind format je tekstualni. Možeš pretražiti najskuplje pozive:

```bash
# Pokaz svaku liniju sa eventima (IR = instruction reads)
grep "^fn=" cachegrind.out.* | sort | uniq -c | sort -rn | head -20

# Gornji tool: php-callgrind-analyzer (npm)
npx callgrind-to-json ./profiles/php/cachegrind.out.* | jq '.[] | select(.totalTime > 10)' 
```

---

## Trace mode — detaljan log izvršavanja

Trace mode zapisuje svaki poziv funkcije, argumente, i povratne vrijednosti. Fajl raste brzo (megabyte po requestu za kompleksne aplikacije).

```ini
; docker/php/xdebug-trace.ini
[xdebug]
xdebug.mode=trace

; Direktorij za trace fajlove
xdebug.output_dir=/tmp/xdebug-trace

; Format: 0 = human readable, 1 = computer readable (parseable)
xdebug.trace_format=0

; Uključi argumente funkcija u trace
; Oprez: može expose-ovati lozinke i sensitive data u log fajl!
xdebug.collect_params=4

; Uključi povratne vrijednosti
xdebug.collect_return=1

; Trigger ili auto
xdebug.start_with_request=trigger
```

Čitanje trace fajla:

```
TRACE START [2024-03-15 14:22:01.123456]
    0.0001      382480   -> {main}() /app/src/public/index.php:0
    0.0023      412680     -> App\Bootstrap::create() /app/src/public/index.php:8
    0.0045      534200       -> Slim\App::__construct() ...
    ...
TRACE END   [2024-03-15 14:22:01.245678]
```

Svaka linija: `[time] [memory] [indent]->[function call] [file:line]`

Trace je koristan kad:
- Ne znaš u kojoj funkciji bug nastaje (step debug je prepolagani pristup)
- Reprodukuješ race condition ili timing-sensitive bug
- Analiziraš third-party library pozive

---

## Develop mode — svakodnevni razvoj

Develop mode ne zahtijeva VS Code listener. Poboljšava prikaz grešaka direktno u browseru/responsu.

```ini
[xdebug]
xdebug.mode=develop

; Maximum dubina za var_dump prikaz
xdebug.var_display_max_depth=5
```

Sa develop modom aktivan, PHP `var_dump()` postaje:

```php
// Normalni PHP var_dump:
// array(2) { ["email"]=> string(16) "test@example.com" ...}

// Xdebug develop var_dump (HTML, formatiran, sa tipovima):
// array (size=2)
//   'email' => string 'test@example.com' (length=16)
//   'roles' => array (size=3) ...  [klick za expand]
```

Stack trace na grešci prikazuje argumente i kontekst koji standardni PHP ne pokazuje.

---

## Kombinirani modes

```ini
; Debug i develop zajedno — korisno za svakodnevni rad
xdebug.mode=debug,develop

; Profile i develop — profiliraj sa boljim error prikazom
xdebug.mode=profile,develop
```

---

## Automatsko čišćenje profile/trace fajlova

Profiling generiše fajlove koji brzo popune disk. Dodaj cron ili cleanup script:

```bash
# Čisti fajlove starije od 1 dana
find ./profiles/php -name "cachegrind.out.*" -mtime +1 -delete
find ./profiles/php -name "trace.*" -mtime +1 -delete
```

Ili u `docker-compose.override.yml` kao health check / lifecycle hook:

```yaml
services:
  php-service:
    # tmpfs za profile direktorij — podaci nestaju pri restart-u kontejnera
    tmpfs:
      - /tmp/xdebug-profiles:size=512m
    # Ako hoćeš trajni, koristiti named volume sa size limitom
```

---

## `.gitignore` za debug artefakte

```gitignore
# Xdebug profile i trace output
/profiles/
/tmp/xdebug*
*.cachegrind
cachegrind.out.*
xdebug.log
xdebug_*.log

# PHP debug pomocni fajlovi
*.php.bak
```

---

## Praktičan workflow: profiliraj spori endpoint

```bash
# 1. Aktiviraj profile mode (trigger)
docker cp docker/php/xdebug-profile-trigger.ini \
  php-service:/usr/local/etc/php/conf.d/docker-php-ext-xdebug.ini
docker exec php-service kill -USR2 1

# 2. Pošalji request sa XDEBUG_PROFILE trigger-om
curl "http://localhost/api/products?XDEBUG_PROFILE=1&category=electronics"

# 3. Pronađi novi Cachegrind fajl
ls -lt ./profiles/php/ | head -5

# 4. Otvori u qcachegrind ili PHPStorm
qcachegrind ./profiles/php/cachegrind.out.latest

# 5. U qcachegrind: sortaj po "Incl." (inclusive time) — vidi Top 10 funkcija
# Obično ćeš naći: N+1 query problem, redundantni API pozivi, ili O(n²) loop

# 6. Vrati debug mode
docker cp docker/php/xdebug.ini \
  php-service:/usr/local/etc/php/conf.d/docker-php-ext-xdebug.ini
docker exec php-service kill -USR2 1
```

> **Podman:** `podman cp docker/php/xdebug-profile-trigger.ini php-service:/usr/local/etc/php/conf.d/docker-php-ext-xdebug.ini`
> **Podman:** `podman exec php-service kill -USR2 1`
> **Podman:** `podman cp docker/php/xdebug.ini php-service:/usr/local/etc/php/conf.d/docker-php-ext-xdebug.ini`
> **Podman:** `podman exec php-service kill -USR2 1`
