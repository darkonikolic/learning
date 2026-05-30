# 05 — Docker Compose: lokalni razvoj

## Kompletan docker-compose.yml

```yaml
# docker-compose.yml
version: "3.9"

networks:
  app-net:
    driver: bridge
    # Eksplicitna subnet mreža nije obavezna lokalno,
    # ali je dobra praksa za konzistentnost sa produkcijom
    ipam:
      config:
        - subnet: 172.20.0.0/16

volumes:
  mysql-master-data:
  mysql-replica-data:
  redis-data:

services:

  # ─── nginx reverse proxy (TLS termination) ───────────────────────
  # nginx je uvijek prvi servis — jedina tačka ulaza iz browsera.
  # Drži TLS certifikat, radi HTTP→HTTPS redirect, i proxy_pass-uje
  # na backende. App kontejneri nemaju portove prema hostu.
  nginx:
    image: nginx:1.25-alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - ./certs:/etc/nginx/certs:ro
    depends_on:
      php-service:
        condition: service_healthy
    networks:
      - app-net
    restart: unless-stopped

  # ─── PHP servis (Slim proxy) ──────────────────────────────────────
  php-service:
    build:
      context: ./php-service
      dockerfile: Dockerfile
    env_file:
      - .env.local
    environment:
      REDIS_HOST: redis
      GO_SERVICE_URL: http://go-service:8080
    depends_on:
      redis:
        condition: service_healthy
      go-service:
        condition: service_healthy
    networks:
      - app-net
    healthcheck:
      test: ["CMD", "php", "-r", "exit(0);"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 15s
    restart: unless-stopped

  # ─── Go servis (business logic) ───────────────────────────────────
  go-service:
    build:
      context: ./go-service
      dockerfile: Dockerfile
    env_file:
      - .env.local
    environment:
      MYSQL_MASTER_DSN: "${MYSQL_USER}:${MYSQL_PASSWORD}@tcp(mysql-master:3306)/${MYSQL_DATABASE}?parseTime=true&tls=false"
      MYSQL_REPLICA_DSN: "${MYSQL_USER}:${MYSQL_PASSWORD}@tcp(mysql-replica:3307)/${MYSQL_DATABASE}?parseTime=true&tls=false"
      REDIS_ADDR: redis:6379
    depends_on:
      mysql-master:
        condition: service_healthy
      mysql-replica:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - app-net
    healthcheck:
      test: ["/app/server", "-health"]
      interval: 15s
      timeout: 5s
      retries: 3
      start_period: 20s
    restart: unless-stopped

  # ─── MySQL master ─────────────────────────────────────────────────
  mysql-master:
    image: mysql:8.0
    env_file:
      - .env.local
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
      MYSQL_DATABASE: ${MYSQL_DATABASE}
      MYSQL_USER: ${MYSQL_USER}
      MYSQL_PASSWORD: ${MYSQL_PASSWORD}
    command:
      - --server-id=1
      - --log-bin=mysql-bin
      - --binlog-format=ROW
      - --gtid-mode=ON
      - --enforce-gtid-consistency=ON
    ports:
      - "3306:3306"  # Expose lokalno za MySQL Workbench/TablePlus
    volumes:
      - mysql-master-data:/var/lib/mysql
      - ./mysql/init:/docker-entrypoint-initdb.d  # SQL init skripte
    networks:
      - app-net
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-u", "root", "-p${MYSQL_ROOT_PASSWORD}"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s
    restart: unless-stopped

  # ─── MySQL replica ────────────────────────────────────────────────
  mysql-replica:
    image: mysql:8.0
    env_file:
      - .env.local
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
      MYSQL_DATABASE: ${MYSQL_DATABASE}
      MYSQL_USER: ${MYSQL_USER}
      MYSQL_PASSWORD: ${MYSQL_PASSWORD}
    command:
      - --server-id=2
      - --log-bin=mysql-bin
      - --binlog-format=ROW
      - --gtid-mode=ON
      - --enforce-gtid-consistency=ON
      - --read-only=ON  # Replica je read-only
    ports:
      - "3307:3306"  # Drugačiji host port da ne kolizuje sa master-om
    volumes:
      - mysql-replica-data:/var/lib/mysql
    networks:
      - app-net
    depends_on:
      mysql-master:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-u", "root", "-p${MYSQL_ROOT_PASSWORD}"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 40s  # Duži start_period jer replikacija treba konfiguraciju
    restart: unless-stopped

  # ─── Redis ────────────────────────────────────────────────────────
  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD} --save 60 1 --loglevel notice
    env_file:
      - .env.local
    ports:
      - "6379:6379"  # Expose za lokalni redis-cli debug
    volumes:
      - redis-data:/data
    networks:
      - app-net
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3
    restart: unless-stopped
```

---

## nginx kao standard — zašto svaki docker-compose ima nginx ispred

Svaki `docker-compose.yml` u project-A pathu ima nginx kao prvi servis i jedinu tačku ulaza. App kontejneri (PHP, Go, Vue) koriste `expose`, ne `ports` — direktno nisu dostupni iz browsera.

**Razlog 1 — TLS na jednom mjestu.** nginx drži certifikat i radi TLS termination. Aplikacioni servisi komuniciraju plain HTTP kroz interni Docker network — ne moraju znati ništa o certifikatima.

**Razlog 2 — Isti pattern lokalno i u produkciji.** Lokalno: nginx kontejner sa mkcert certifikatom. Na AWS-u: ALB preuzima ulogu nginx-a (TLS, redirect, routing). Aplikacioni kod i konfiguracija su nepromijenjeni.

**Razlog 3 — Security headers na jednom mjestu.** HSTS, X-Frame-Options, X-Content-Type-Options — jednom u nginx.conf, važe za sve backend servise.

**Razlog 4 — HTTP → HTTPS redirect.** Jedan `return 301` u nginx bloku za port 80. Nema potrebe implementirati u svakoj aplikaciji zasebno.

**Lokalni certifikati** se generišu s `make cert-local-mkcert` ili `make cert-local-openssl` i stavljaju u `certs/` (koji je u `.gitignore`). Detalji u `01-docker-fundamenti/14-nginx-reverse-proxy-i-https.md`.

---

## .env.local — sve credentials na jednom mjestu

```bash
# .env.local — NIKAD ne commitovati u git
# .gitignore mora sadržati: .env.local

# MySQL
MYSQL_ROOT_PASSWORD=local_root_secret
MYSQL_DATABASE=project_a
MYSQL_USER=app_user
MYSQL_PASSWORD=local_app_secret

# Redis
REDIS_PASSWORD=local_redis_secret
```

`docker-compose.yml` koristi `env_file: .env.local` — svaki servis dobija sve varijable iz fajla. Servisi koje ne trebaju sve varijable (npr. nginx ne treba MySQL password) to ignorišu. Alternativa je eksplicitno navoditi `environment` za svaki servis što je verbozno ali precizno.

---

## MySQL master/replica replikacija lokalno

Lokalna replikacija zahtijeva inicijalni setup koji nije automatski. Init skripta:

```sql
-- mysql/init/01-replication-user.sql
-- Izvršava se na master-u pri prvom startu

CREATE USER IF NOT EXISTS 'replicator'@'%' IDENTIFIED BY 'replication_secret';
GRANT REPLICATION SLAVE ON *.* TO 'replicator'@'%';
FLUSH PRIVILEGES;
```

Replikacija se konfiguriše ručno nakon što oba kontejnera startaju:

```bash
# Skripta za setup replikacije (pokrenuti jednom)
#!/bin/bash

# Dobij master poziciju
MASTER_STATUS=$(docker compose exec mysql-master \
    mysql -uroot -p${MYSQL_ROOT_PASSWORD} -e "SHOW MASTER STATUS\G")

# Konfiguriši repliku
docker compose exec mysql-replica \
    mysql -uroot -p${MYSQL_ROOT_PASSWORD} -e "
    STOP SLAVE;
    CHANGE REPLICATION SOURCE TO
        SOURCE_HOST='mysql-master',
        SOURCE_USER='replicator',
        SOURCE_PASSWORD='replication_secret',
        SOURCE_AUTO_POSITION=1;
    START SLAVE;
    SHOW SLAVE STATUS\G;
"
```

> **Podman:** `podman compose exec mysql-master ...` / `podman compose exec mysql-replica ...` — isti syntax.
>
> **Podman Compose instalacija:**
> - macOS: `brew install podman-compose`
> - Linux: `pip3 install podman-compose`
> - Podman 4.x+ uključuje `podman compose` koji interno poziva podman-compose
> - Sintaksa je identična: `docker compose up -d` → `podman compose up -d`

Za lokalni razvoj, GTID-based replikacija (`SOURCE_AUTO_POSITION=1`) je jednostavnija od file/position based — nema potrebe ručno pratiti binlog pozicije.

---

## Zašto Redis single (ne Sentinel) lokalno

Redis Sentinel omogućava automatski failover — kada master padne, Sentinel promoviše repliku. U produkciji je obavezno.

Lokalno: jedan Redis kontejner je potpuno prihvatljivo iz konkretnih razloga:
- Lokalni razvoj nema SLA zahtjeve
- Sentinel setup zahtijeva minimum 3 Sentinel instance + master + replica = 5 kontejnera za ovu svrhu
- Razvojni ciklus ne zavisi od Redis HA

Jedino što treba: Redis koji se ponaša isto kao produkcijski Redis (iste komande, isti TTL behavior). Single Redis node to pruža.

---

## depends_on sa service_healthy — zašto je ovo kritično

`depends_on: service: condition: service_healthy` znači da Docker Compose neće startati zavisni servis dok HEALTHCHECK ne vrati success.

Bez `condition: service_healthy` (samo `depends_on: mysql-master`): Docker Compose čeka da kontejner *startuje*, ne da MySQL *bude spreman za konekcije*. MySQL inicijalizacija traje 15-30 sekundi. Go servis koji pokuša konekciju prerano dobija "Connection refused" i puca.

Pattern za aplikacije koje se startuju brzo (Go binary): koristiti `start_period` na healthcheck-u da se daju servisu sekunde za inicijalizaciju bez da se healthcheck failures broje.

---

## Pokretanje i troubleshooting

```bash
# Prvi start (build svih image-a i start)
docker compose up --build

# Rebuild samo jednog servisa (brže od rebuild svega)
docker compose up --build go-service

# Provjeri logove svih servisa u realnom vremenu
docker compose logs -f

# Exec u kontejner za debug (PHP ima shell, Go scratch nema)
docker compose exec php-service sh
docker compose exec mysql-master mysql -uroot -p

# Provjeri koji servisi su healthy
docker compose ps

# Potpuno čišćenje (volumes se brišu — gubi se DB sadržaj)
docker compose down -v

# Restart samo jednog servisa
docker compose restart go-service
```

> **Podman:** Sve gore navedene komande rade identično s `podman compose` umjesto `docker compose`.
> Primjeri: `podman compose up --build`, `podman compose logs -f`, `podman compose down -v`
>
> **Podman Compose instalacija:**
> - macOS: `brew install podman-compose`
> - Linux: `pip3 install podman-compose`
> - Podman 4.x+ uključuje `podman compose` koji interno poziva podman-compose
> - Sintaksa je identična: `docker compose up -d` → `podman compose up -d`

Kada `docker compose up` završi bez grešaka, `http://localhost` treba otvoriti Vue.js login stranicu. Ako nginx javlja 502, PHP-FPM nije dostupan. Ako API pozivi vraćaju 503, Go servis ili MySQL nije spreman.

---

## Makefile — dodaj u ovom poglavlju

Ovo poglavlje uvodi docker-compose za lokalni razvoj. Dodaj u `Makefile` u korenu projekta:

```makefile
# === LOKALNI RAZVOJ ===

up: ## Pokreni sve servise lokalno (docker-compose)
	docker compose up -d

down: ## Zaustavi i ukloni lokalne kontejnere
	docker compose down

logs: ## Prikaži logove lokalnih servisa (live)
	docker compose logs -f

ps: ## Prikaži status lokalnih servisa
	docker compose ps

restart: ## Restart specifičnog servisa (SVC=php make restart)
	docker compose restart $(SVC)
```

Centralni Makefile već sadrži ove targete — ovo je referenca šta si dodao u ovoj oblasti.

Provjeri da targeti rade:
```bash
make up
make ps
make logs
SVC=go-service make restart
make down
make help | grep -E "^(up|down|logs|ps|restart)"
```
