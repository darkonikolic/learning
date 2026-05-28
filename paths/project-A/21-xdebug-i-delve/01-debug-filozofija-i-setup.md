# 01 — Debug filozofija i setup

## Zašto debug alati nikad ne idu u produkciju

Ovo nije preferencija — to je sigurnosni i operativni zahtjev.

### Xdebug u produkciji: šta se dešava

Xdebug step debugger radi tako što pri svakom PHP requestu otvori TCP konekciju prema konfiguriranom `client_host:client_port` i čeka instrukcije od IDE-a. Posljedice u produkciji:

**Performance:**
- Step debug mode: 100–300% overhead na svakom requestu, čak i bez aktivnog debuggera
- Profile mode: zapisuje Cachegrind fajl na disk za svaki request — disk I/O eksplodira
- Xdebug troši memoriju za tracking call stack-a i varijabli

**Sigurnost:**
- Ako je `xdebug.start_with_request=yes` i port 9003 dostupan, bilo ko na mreži može se konektovati kao debugger
- Debugger ima puni pristup PHP procesu: može čitati varijable (lozinke, tokeni), mijenjati ih, i izvršavati kod
- CVE primjeri postoje za misconfigured Xdebug instance izložene na internetu

### Delve u produkciji: šta se dešava

**Veličina binarnog fajla:**
- Normalni Go binary (release build): ~8–12 MB
- Debug build sa `-gcflags="all=-N -l"`: ~25–35 MB (3x veći zbog DWARF debug simbola)
- Simboli se ne mogu strip-ovati naknadno ako ih je Delve koristio za breakpoint mapping

**Optimizacije:**
- `-N` disables compiler optimizations — kod se izvršava sporije, CPU usage raste
- `-l` disables inlining — function calls su skuplje, heap allocations su drugačije
- Benchmark razlike mogu biti 20–40% degradacija throughput-a

**Sigurnost:**
- Delve port (40000) koji sluša u produkciji je direktni remote code execution vektor
- Zahtijeva `SYS_PTRACE` capability i `seccomp:unconfined` — značajno proširuje attack surface kontejnera

---

## Pattern: docker-compose.override.yml

Docker Compose automatski traži dva fajla i merge-uje ih:

```
docker-compose.yml           ← base konfiguracija, produkcijski ekvivalent
docker-compose.override.yml  ← lokalni override, automatski se merge-uje
```

Kako merge funkcioniše:

```bash
# Oba fajla — normalni lokalni razvoj (override se automatski primjenjuje)
docker compose up

# Samo base fajl — simulacija produkcije lokalno, ili CI/CD build
docker compose -f docker-compose.yml up

# Eksplicitni override — ako override fajl ima drugačije ime
docker compose -f docker-compose.yml -f docker-compose.debug.yml up
```

> **Podman:** `podman compose up`
> **Podman:** `podman compose -f docker-compose.yml up`
> **Podman:** `podman compose -f docker-compose.yml -f docker-compose.debug.yml up`

Zašto ovaj pattern:
- `docker-compose.yml` commit-uješ — kolege imaju isti base
- `docker-compose.override.yml` dodaš u `.gitignore` ILI commit-uješ jer sadrži samo bezopasne debug postavke
- CI/CD uvijek koristi samo base fajl: `docker compose -f docker-compose.yml build`

```yaml
# .gitignore
docker-compose.override.yml   # opcija A: svako ima svoj override lokalno
```

Ili:

```yaml
# docker-compose.override.yml se commit-uje jer sadrži samo dev debug config
# Onda CI mora eksplicitno ignorisati: docker compose -f docker-compose.yml ...
```

Za ovaj projekat: commit-ujemo override.yml jer je debug konfiguracija zajednička za tim.

---

## Zasebni Dockerfile target-i (multi-stage build)

```dockerfile
# docker/php/Dockerfile

FROM php:8.3-fpm-alpine AS base
# Zajednička instalacija: PHP extenzije, composer, app kod
RUN apk add --no-cache $PHPIZE_DEPS \
    && pecl install xdebug-3.3.1 \
    && apk del $PHPIZE_DEPS
# Xdebug je instaliran u base ali NIJE ENABLED — nema docker-php-ext-enable

COPY docker/php/php-fpm.conf /usr/local/etc/php-fpm.d/www.conf
COPY src/ /app/src/

FROM base AS debug
# Samo u debug target-u: enable Xdebug i kopiraj konfiguraciju
RUN docker-php-ext-enable xdebug
COPY docker/php/xdebug.ini /usr/local/etc/php/conf.d/xdebug.ini
# debug image: xdebug aktivan, svi debug postavke

FROM base AS production
# Xdebug je instaliran ali NIJE enabled (nema .so u conf.d)
# Verifikacija: docker run <image> php -m | grep xdebug → prazno
```

Alternativni pristup — instaliraj samo u debug:

```dockerfile
FROM php:8.3-fpm-alpine AS base
# Base nema Xdebug uopće
COPY src/ /app/src/

FROM base AS debug
RUN apk add --no-cache $PHPIZE_DEPS \
    && pecl install xdebug-3.3.1 \
    && docker-php-ext-enable xdebug \
    && apk del $PHPIZE_DEPS
COPY docker/php/xdebug.ini /usr/local/etc/php/conf.d/xdebug.ini

FROM base AS production
# Xdebug nije ni instaliran
```

Razlika: prvi pristup (instaliraj u base, enable samo u debug) znači da debug i production imaju isti layer cache za instalaciju, ali production image je malo veći (xdebug.so postoji, samo nije enabled). Drugi pristup je čišći ali debug build je sporiji zbog ponovne instalacije.

**Preporuka**: drugi pristup za produkciju gdje image veličina i čistoća su bitni.

Build naredbe:

```bash
# Debug build (lokalni razvoj)
docker compose up --build

# Production build (CI/CD)
docker build --target production -t myapp/php:latest docker/php/

# Verifikacija: Xdebug nije u produkcijskom image-u
docker run --rm myapp/php:latest php -m | grep xdebug
# Mora biti prazno
```

> **Podman:** `podman compose up --build`
> **Podman:** `podman build --target production -t myapp/php:latest docker/php/`
> **Podman:** `podman run --rm myapp/php:latest php -m | grep xdebug`

---

## VS Code workspace setup

### `.vscode/extensions.json`

Dijeli se u repozitoriju — VS Code predlaže instalaciju kolegama:

```json
{
  "recommendations": [
    "xdebug.php-debug",
    "golang.go",
    "ms-vscode-remote.remote-containers",
    "ms-azuretools.vscode-docker"
  ]
}
```

- `xdebug.php-debug`: PHP debugger za VS Code, sluša na 9003
- `golang.go`: Go support, uključuje Delve integraciju
- `remote-containers`: razvoj unutar kontejnera (opciona alternativa)
- `vscode-docker`: Docker Compose management iz VS Code-a

### `.vscode/launch.json`

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Listen for Xdebug (PHP)",
      "type": "php",
      "request": "launch",
      "port": 9003,
      "pathMappings": {
        "/app/src": "${workspaceFolder}/services/php-service/src"
      },
      "log": true
    },
    {
      "name": "Attach to Go service (Delve)",
      "type": "go",
      "request": "attach",
      "mode": "remote",
      "host": "127.0.0.1",
      "port": 40000,
      "dlvLoadConfig": {
        "followPointers": true,
        "maxVariableRecurse": 3,
        "maxStringLen": 512,
        "maxArrayValues": 64,
        "maxStructFields": -1
      }
    }
  ]
}
```

`pathMappings` je kritičan: Xdebug izvještava o putanjama unutar kontejnera (`/app/src/...`), VS Code mora znati koji lokalni fajl tome odgovara. Neispravni mappings = breakpoint nikad ne puca.

---

## Provjera da debug nije u produkciji (CI)

### GitLab CI job

```yaml
verify:no-debug-in-prod:
  stage: verify
  script:
    # PHP: Xdebug ne smije biti učitan
    - |
      XDEBUG_CHECK=$(docker run --rm $CI_REGISTRY_IMAGE/php-service:$CI_COMMIT_SHA php -m | grep -c xdebug || true)
      if [ "$XDEBUG_CHECK" -gt "0" ]; then
        echo "ERROR: Xdebug is enabled in production image!"
        exit 1
      fi
    # Go: binary ne smije imati Delve ili debug simbole
    - |
      docker run --rm $CI_REGISTRY_IMAGE/go-service:$CI_COMMIT_SHA \
        file /app/server | grep -q "not stripped" && \
        echo "WARNING: Go binary is not stripped (has debug symbols)"
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
```

### Trivy security scan (detektuje debug alate)

```yaml
trivy:scan-prod-image:
  stage: security
  script:
    - trivy image --exit-code 1 --severity HIGH,CRITICAL $CI_REGISTRY_IMAGE/php-service:$CI_COMMIT_SHA
    # Trivy detektuje poznate debug tool vulnerability-e ako su prisutni
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
```

### Lokalna provjera prije pusha

```bash
# Brza provjera: buildi production target i provjeri
docker build --target production -t test-php-prod ./docker/php/
docker run --rm test-php-prod php -m | grep xdebug && echo "FAIL: xdebug found" || echo "OK: no xdebug"
```

> **Podman:** `podman build --target production -t test-php-prod ./docker/php/`
> **Podman:** `podman run --rm test-php-prod php -m | grep xdebug && echo "FAIL: xdebug found" || echo "OK: no xdebug"`

---

## Sažetak: šta gdje ide

| Stavka | `docker-compose.yml` | `docker-compose.override.yml` | Produkcija |
|--------|---------------------|-------------------------------|------------|
| PHP service base | ✓ | — | ✓ |
| Xdebug config | — | ✓ (`target: debug`) | — |
| Go service base | ✓ | — | ✓ |
| Delve ports | — | ✓ | — |
| SYS_PTRACE cap | — | ✓ | — |
| `launch.json` | — | `.vscode/` (commit) | — |
