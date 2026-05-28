# 10 — Volume tipovi i kada koji koristiti

Volume je jedan od najčešće pogrešno korištenih Docker koncepata. Krivo odabran tip volume-a znači ili spor razvoj (pogrešan tip za dev), ili izgubljen podatak (pogrešan tip za prod), ili sigurnosni propust (bind mount gdje ne treba). Ovaj dokument pokrića svaki tip s konkretnim primjerima za naš stack.

---

## Pregled tipova

| Tip | Kontrolira host | Persists | Performanse | Prod-ready |
|-----|----------------|----------|-------------|------------|
| Bind mount | Da — host path | Da | Mac/Win: sporo | Ne za src kod |
| Named volume | Docker | Da | Brzo | Da |
| tmpfs | Ne | Ne (RAM) | Najbrže | Situaciono |
| Anonymous volume | Docker (random) | Dokle god kontejner | Brzo | Antipattern |

---

## 1. Bind Mount

Direktno mapira direktorijum ili fajl sa hosta u kontejner. Što se promijeni na hostu — odmah je vidljivo u kontejneru, i obrnuto.

```yaml
# docker-compose.override.yml
services:
  php-service:
    volumes:
      # Source kod — read-only u kontejneru, live reload bez rebuild
      - ./services/php-service/src:/app/src:ro
      - ./services/php-service/config:/app/config:ro

  go-service:
    volumes:
      # Go hot reload s Air
      - ./services/go-service:/app:ro

  vue-frontend:
    volumes:
      # Vite HMR — src promjene odmah u browser
      - ./services/vue-frontend/src:/app/src:ro
```

Kada koristiti:
- Lokalni razvoj s live reloadom — jedina situacija gdje ima smisla
- Config fajlovi koje mijenjamo često (nginx.conf, php.ini) tokom razvoja
- Log fajlovi koje hoćemo čitati direktno s hosta (tokom debugiranja)

Kada NE koristiti:
- Produkcija — kontejner mora biti self-contained, nezavisan od host filesystem-a
- CI — sporiji od named volume-a zbog virtualizacione overhead
- Direktorijumi koji trebaju biti prazni pri startu kontejnera (node_modules, vendor)

Performansni problem na Mac i Windows: Docker Desktop koristi virtualiziranu Linux VM. Bind mount zahtijeva sinhronizaciju između macOS APFS/Windows NTFS i Linux filesystema unutar VM-a. Rezultat: read/write operacije mogu biti i do 10x sporije nego na Linux hostu.

Za PHP Composer vendor direktorijum ovo je posebno bolno — ne montiraj `vendor/` kao bind mount. Instaliraj unutar kontejnera u build stageu.

```yaml
# POGREŠNO — vendor/ kao bind mount je spor i problematičan
services:
  php-service:
    volumes:
      - ./services/php-service:/app  # Ovo uključuje vendor/, node_modules/ — sporo!

# ISPRAVNO — samo src/ koji se mijenja
services:
  php-service:
    volumes:
      - ./services/php-service/src:/app/src:ro  # Samo kod, bez dependencies
```

`:ro` vs `:rw` — uvijek eksplicitno:
- `:ro` (read-only): kontejner ne može pisati na host. Koristi za source kod — sprečava scenarij gdje kontejnerski proces slučajno mijenja tvoje fajlove
- `:rw` (default): kontejner može pisati na host. Koristi za logove, uploads, generisane fajlove koje hoćeš vidjeti na hostu

---

## 2. Named Volume

Docker upravlja storage lokacijom. Host ne zna gdje su fajlovi na disku (nalazi se u Docker-ovom storage backend-u, obično `/var/lib/docker/volumes/` na Linux-u).

```yaml
# docker-compose.yml
volumes:
  mysql-data:
    driver: local
  redis-data:
    driver: local

services:
  mysql:
    volumes:
      - mysql-data:/var/lib/mysql

  redis:
    volumes:
      - redis-data:/data
      # Redis persistencija zahtijeva --appendonly yes u command:
    command: redis-server --requirepass ${REDIS_PASSWORD} --appendonly yes
```

Lifecycle — ovo je ključna razlika od bind mounta:

```bash
# Volume postoji nezavisno od kontejnera
docker compose down           # Kontejneri obrisani, volume OSTAJE
docker compose down --volumes # Kontejneri I volume obrisani

# Ručno upravljanje
docker volume ls              # Prikaz svih named volume-a
docker volume inspect mysql-data  # Detalji i stvarna lokacija na hostu
docker volume rm mysql-data   # Brisanje (mora biti odmontiran)
```

Backup named volume-a — jedina pouzdana metoda:

```bash
# Backup mysql-data volume-a u tar arhivu na hostu
docker run --rm \
  -v mysql-data:/data \
  -v $(pwd)/backups:/backup \
  alpine \
  tar czf /backup/mysql-$(date +%Y%m%d).tar.gz -C /data .

# Restore
docker run --rm \
  -v mysql-data:/data \
  -v $(pwd)/backups:/backup \
  alpine \
  tar xzf /backup/mysql-20240115.tar.gz -C /data
```

Kada koristiti:
- MySQL podaci — obavezno named volume, ne bind mount
- Redis persistentni podaci (AOF/RDB fajlovi)
- Upload fajlovi koje treba čuvati između restartova kontejnera
- CI build cache (npm cache, composer cache, go module cache) — named volume je brži od bind mounta u CI

Kada NE koristiti:
- Source kod — bind mount je boiji za dev
- Privremeni podaci — tmpfs je bolji
- Produkcija s više instanci (Swarm, K8s) — tu trebaju external volume driveri ili S3

---

## 3. tmpfs Mount

Montira RAM direktorijum u kontejner. Podaci postoje samo dok kontejner radi — gube se pri stopu ili restartu. Nema disk I/O.

```yaml
services:
  php-service:
    # Kratka forma
    tmpfs:
      - /tmp
      - /run/php

    # Duga forma s opcijama
    volumes:
      - type: tmpfs
        target: /app/cache/opcache
        tmpfs:
          size: 134217728  # 128MB u bajtima

  mysql-test:
    # Test baza u memoriji — brža za testove, gubi se pri stopu
    tmpfs:
      - /var/lib/mysql
    environment:
      MYSQL_DATABASE: test_db
      MYSQL_ROOT_PASSWORD: testpass
```

Specifični use casevi za naš stack:

PHP Opcache scratch:
```yaml
services:
  php-service:
    tmpfs:
      - /tmp:mode=1777   # mode=1777 = sticky bit, kao pravi /tmp
    volumes:
      - type: tmpfs
        target: /app/storage/framework/cache
        tmpfs:
          size: 67108864  # 64MB dovoljno za framework cache
```

Xdebug profili tokom debug sessiona (akumuliraju se brzo):
```yaml
services:
  php-service-debug:
    tmpfs:
      - /tmp/xdebug-profiles  # Profili se gube pri stopu, ali to je OK
```

CI test baza:
```yaml
services:
  mysql-test:
    image: mysql:8.0
    tmpfs:
      - /var/lib/mysql   # Bez disk I/O, testovi su brži 2-3x
```

Ograničenja:
- Radi samo na Linux. Docker Desktop (Mac, Windows) ne podržava pravi tmpfs — podatak se i dalje zapisuje na virtualni disk unutar VM-a, ali ne na host disk
- Bez persistencije — svjesna odluka
- Limit veličine moraš postaviti eksplicitno ili defaultno koristi 50% RAM-a

---

## 4. Anonymous Volume

Docker kreira volume s random imenom. Teško upravljati, teško backupovati. U pravilu: antipattern za novi kod.

```dockerfile
# Dockerfile koji kreira anonymous volume
VOLUME /app/node_modules
```

```yaml
# docker-compose.yml koji kreira anonymous volume
services:
  php-service:
    volumes:
      - /app/vendor  # Bez imena = anonymous volume
```

Problem: nakon `docker compose down`, volume ostaje s random UUID imenom. `docker volume ls` prikazuje desetine bezimenih volumea. Ne znaš što je što.

Postoji jedan legitiman use case: spriječiti da bind mount "prekrije" direktorijum koji postoji u image-u ali ne na hostu.

```yaml
services:
  vue-frontend:
    volumes:
      - ./services/vue-frontend/src:/app/src:ro
      - /app/node_modules  # Anonymous volume — node_modules ostaje iz image-a
                           # Bind mount src/ ne prekrije ga
```

Preporuka: koristi named volume umjesto anonymous volumea. Budi eksplicitan.

```yaml
# Bolje: eksplicitno imenovan
volumes:
  vue-node-modules:

services:
  vue-frontend:
    volumes:
      - ./services/vue-frontend/src:/app/src:ro
      - vue-node-modules:/app/node_modules
```

---

## 5. Read-only filesystem pattern

Za security-hardened deployment — cijeli container filesystem je read-only, eksplicitno se definiše što smije biti writeable.

```yaml
services:
  go-service:
    read_only: true         # Cijeli filesystem read-only
    tmpfs:
      - /tmp               # Jedini writeable RAM direktorijum
    volumes:
      - ./logs:/app/logs   # Eksplicitni write za logove (samo u devu)
```

PHP zahtijeva više paznje jer framework treba pisati na disk:

```yaml
services:
  php-service:
    read_only: true
    tmpfs:
      - /tmp:mode=1777
      - /run/php-fpm
    volumes:
      # Sve što PHP framework mora pisati — eksplicitno
      - type: tmpfs
        target: /app/storage/framework/sessions
      - type: tmpfs
        target: /app/storage/framework/views
      - type: tmpfs
        target: /app/storage/framework/cache
      - type: tmpfs
        target: /app/storage/logs
```

Zašto ovo u produkciji: kompromitovan kontejner ne može modificirati binarne fajlove ili ubaciti malware u filesystem kontejnera.

---

## Decision matrix za naš projekat

| Use case | Volume tip | Konfiguracija |
|----------|-----------|---------------|
| PHP source kod (dev) | Bind mount `:ro` | `./services/php-service/src:/app/src:ro` |
| Go source kod (dev) | Bind mount `:ro` | `./services/go-service:/app:ro` |
| Vue source kod (dev) | Bind mount `:ro` | `./services/vue-frontend/src:/app/src:ro` |
| MySQL podaci | Named volume | `mysql-data:/var/lib/mysql` |
| Redis podaci | Named volume | `redis-data:/data` |
| PHP sessions | Redis (ne volume) | `SESSION_DRIVER=redis` u APP config |
| Xdebug profili | tmpfs | `/tmp/xdebug-profiles` |
| Opcache scratch | tmpfs | `/app/storage/framework/cache` |
| CI test MySQL | tmpfs | `/var/lib/mysql` na mysql-test servisu |
| CI build cache (composer) | Named volume | `composer-cache:/root/.composer` |
| CI build cache (go modules) | Named volume | `go-modules:/go/pkg/mod` |
| Upload fajlovi (dev) | Named volume | `uploads:/app/storage/uploads` |
| Upload fajlovi (prod) | S3 (ne Docker volume) | AWS SDK, ne volume |
| nginx config (dev) | Bind mount `:ro` | `./docker/nginx/nginx.conf:/etc/nginx/nginx.conf:ro` |
| Logovi (dev) | Bind mount `:rw` | `./logs:/app/logs` |
| Logovi (prod) | Docker log driver | `logging:` konfiguracija u compose |

---

## Čišćenje volume-a

Tokom razvoja akumuliraju se stari volume-i. Periodično čistiti:

```bash
# Prikaz svih volume-a s veličinom
docker system df -v

# Obriši sve nekorištene volume-e (nije montiran ni u jednom kontejneru)
docker volume prune

# Obriši sve nekorištene resurse (volume-i, image-i, mreže, build cache)
docker system prune --volumes

# Nuclear opcija — sve obriši (pazi, briše i mysql-data!)
docker system prune -af --volumes
```

Sigurna rutina za reset lokalnog okruženja:
```bash
# Zaustavi sve, obriši kontejnere i named volume-e za ovaj projekt
docker compose down --volumes

# Ponovo pokreni s čistim stanjem
docker compose up --build
```
