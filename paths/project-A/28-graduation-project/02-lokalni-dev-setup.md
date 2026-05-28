# Lokalni Dev Setup

Cilj: `docker compose up` → login stranica radi na `https://app.local`. Sve 7 kontejnera (nginx, frontend, php-service, go-service, mysql-master, mysql-replica, redis) dižu se zajedno, health checkovi su wired, ne treba ništa lokalno instalirati.

## Korak 1: kind konfiguracija za multi-service

```yaml
# kind-config.yaml — u root projekta
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
    kubeadmConfigPatches:
      - |
        kind: InitConfiguration
        nodeRegistration:
          kubeletExtraArgs:
            node-labels: "ingress-ready=true"
    extraPortMappings:
      - containerPort: 80
        hostPort: 80
        protocol: TCP
      - containerPort: 443
        hostPort: 443
        protocol: TCP
      - containerPort: 30000
        hostPort: 30000
        protocol: TCP   # opciono: NodePort debug
  - role: worker
  - role: worker
```

```bash
kind create cluster --name project-a --config kind-config.yaml

# nginx Ingress Controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/\
controller-v1.10.0/deploy/static/provider/kind/deploy.yaml

kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=120s

# /etc/hosts
echo "127.0.0.1 app.local" | sudo tee -a /etc/hosts
```

Dva worker noda su bitna: go-service i mysql ne mogu na isti node zbog resource contention u lokalnom testu.

## Korak 2: .env.local

`.env.local` **ne ide na git** (`.gitignore` mora sadržavati `.env.local`). Lokalno se ne koristi AWS SM — direktne vrijednosti za brzinu iteracije.

```bash
# .env.local — NIJE za commit, NIJE produkciona lozinka
# Za lokalni dev samo

# MySQL
MYSQL_ROOT_PASSWORD=localrootpass
MYSQL_DATABASE=appdb
MYSQL_USER=appuser
MYSQL_PASSWORD=applocalpass

# Redis
REDIS_PASSWORD=redislocalpass

# Go service
GO_DB_MASTER_DSN=appuser:applocalpass@tcp(mysql-master:3306)/appdb?parseTime=true
GO_DB_REPLICA_DSN=appuser:applocalpass@tcp(mysql-replica:3306)/appdb?parseTime=true
GO_REDIS_ADDR=redis:6379
GO_REDIS_PASSWORD=redislocalpass
GO_JWT_SECRET=localjwtsecret-change-in-prod

# PHP service
PHP_GO_SERVICE_URL=http://go-service:8080
PHP_APP_ENV=local

# Nginx
NGINX_UPSTREAM_PHP=php-service:9000
```

## Korak 3: docker-compose.yml

```yaml
# docker-compose.yml
version: "3.9"

x-logging: &default-logging
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"

services:

  mysql-master:
    image: mysql:8.0
    container_name: project-a-mysql-master
    env_file: .env.local
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
      MYSQL_DATABASE: ${MYSQL_DATABASE}
      MYSQL_USER: ${MYSQL_USER}
      MYSQL_PASSWORD: ${MYSQL_PASSWORD}
    command: >
      --server-id=1
      --log-bin=mysql-bin
      --binlog-format=ROW
      --gtid-mode=ON
      --enforce-gtid-consistency=ON
    volumes:
      - mysql-master-data:/var/lib/mysql
      - ./services/go-service/db/migrations:/docker-entrypoint-initdb.d:ro
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-u", "root", "-p${MYSQL_ROOT_PASSWORD}"]
      interval: 10s
      timeout: 5s
      retries: 10
      start_period: 30s
    networks:
      - backend
    logging: *default-logging

  mysql-replica:
    image: mysql:8.0
    container_name: project-a-mysql-replica
    env_file: .env.local
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
      MYSQL_DATABASE: ${MYSQL_DATABASE}
      MYSQL_USER: ${MYSQL_USER}
      MYSQL_PASSWORD: ${MYSQL_PASSWORD}
    command: >
      --server-id=2
      --log-bin=mysql-bin
      --binlog-format=ROW
      --gtid-mode=ON
      --enforce-gtid-consistency=ON
      --read-only=ON
    volumes:
      - mysql-replica-data:/var/lib/mysql
    depends_on:
      mysql-master:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-u", "root", "-p${MYSQL_ROOT_PASSWORD}"]
      interval: 10s
      timeout: 5s
      retries: 10
      start_period: 30s
    networks:
      - backend
    logging: *default-logging

  redis:
    image: redis:7-alpine
    container_name: project-a-redis
    command: redis-server --requirepass ${REDIS_PASSWORD} --appendonly yes
    volumes:
      - redis-data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5
    networks:
      - backend
    logging: *default-logging

  go-service:
    build:
      context: ./services/go-service
      dockerfile: Dockerfile
    container_name: project-a-go-service
    env_file: .env.local
    environment:
      DB_MASTER_DSN: ${GO_DB_MASTER_DSN}
      DB_REPLICA_DSN: ${GO_DB_REPLICA_DSN}
      REDIS_ADDR: ${GO_REDIS_ADDR}
      REDIS_PASSWORD: ${GO_REDIS_PASSWORD}
      JWT_SECRET: ${GO_JWT_SECRET}
      PORT: "8080"
    depends_on:
      mysql-master:
        condition: service_healthy
      mysql-replica:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost:8080/health"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 10s
    networks:
      - backend
    logging: *default-logging

  php-service:
    build:
      context: ./services/php-service
      dockerfile: Dockerfile
    container_name: project-a-php-service
    env_file: .env.local
    environment:
      GO_SERVICE_URL: ${PHP_GO_SERVICE_URL}
      APP_ENV: ${PHP_APP_ENV}
    depends_on:
      go-service:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost:8000/health"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 10s
    networks:
      - backend
      - frontend
    logging: *default-logging

  frontend:
    build:
      context: ./services/frontend
      dockerfile: Dockerfile
      target: build          # multi-stage: samo build artefakt, ne serve
    container_name: project-a-frontend-build
    volumes:
      - frontend-dist:/app/dist
    # Kontejner završi build i stane — nginx čita iz volumea

  nginx:
    build:
      context: ./services/nginx
      dockerfile: Dockerfile
    container_name: project-a-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - frontend-dist:/usr/share/nginx/html:ro
    depends_on:
      php-service:
        condition: service_healthy
      frontend:
        condition: service_completed_successfully
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost/health"]
      interval: 10s
      timeout: 5s
      retries: 3
    networks:
      - frontend
    logging: *default-logging

networks:
  backend:
    driver: bridge
  frontend:
    driver: bridge

volumes:
  mysql-master-data:
  mysql-replica-data:
  redis-data:
  frontend-dist:
```

## Korak 4: health check endpointi

Svaki servis mora imati `GET /health` koji odgovara `200 OK` sa JSON-om. Ovo je i liveness probe u K8s.

**Go service** (`GET :8080/health`):
```json
{"status":"ok","service":"go","db_master":"ok","db_replica":"ok","redis":"ok"}
```

**PHP service** (`GET :8000/health`):
```json
{"status":"ok","service":"php","go_service":"ok"}
```

**nginx** (`GET :80/health`):
```
200 OK
```

nginx `/health` se servira direktno, bez proxy-a — za ALB target group health check.

```nginx
# u nginx.conf
location /health {
    access_log off;
    return 200 "ok\n";
    add_header Content-Type text/plain;
}

location /api/ {
    proxy_pass http://php-service:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 30s;
    proxy_connect_timeout 5s;
}

location / {
    root /usr/share/nginx/html;
    try_files $uri $uri/ /index.html;   # SPA fallback
    expires 1h;
    add_header Cache-Control "public, no-transform";
}
```

## Korak 5: od docker compose up do login stranice

```bash
# 1. Build i start svih servisa
docker compose --env-file .env.local up --build -d

# 2. Prati logove za startup (MySQL je najsporiji — 20-40s)
docker compose logs -f mysql-master mysql-replica go-service

# 3. Čekaj da su svi healthy
docker compose ps
# Svi servisi trebaju biti: healthy ili running

# 4. Provjera health checkova
curl http://localhost/health
curl http://localhost/api/health
# Oba trebaju vratiti 200

# 5. Login test
curl -X POST http://localhost/api/auth \
  -H "Content-Type: application/json" \
  -d '{"email":"test@firma.com","password":"testpass"}'
# Očekivano: {"token":"eyJ...","user":{"email":"test@firma.com"}}
# Ili: 401 Unauthorized ako user ne postoji u bazi

# 6. Browser
open http://localhost
# Vidiš login formu, loguješ se, vidiš "Hello World, test@firma.com"
```

Seed data za test user — migration fajl koji MySQL učita pri prvom startu:

```sql
-- services/go-service/db/migrations/001_seed.sql
CREATE TABLE IF NOT EXISTS users (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  email VARCHAR(255) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT IGNORE INTO users (email, password_hash) VALUES
  ('test@firma.com', '$2y$10$...bcrypt-hash-of-testpass...');
```

## Česti failure modovi

**PHP ne može dosegnuti Go service (`Connection refused` na go-service:8080)**

Problem: PHP startuje pre nego što je Go service _healthy_. `depends_on: condition: service_healthy` to rješava, ali samo ako je Go service healthcheck ispravno konfigurisan. Provjeri:
```bash
docker inspect project-a-go-service | grep -A 10 '"Health"'
# Status mora biti "healthy", ne "starting"
```
Ako Go service ostaje u `starting` stanju, problem je u health check komandi ili start_period-u (predugo za Dockerovu procjenu).

**MySQL nije spreman kad Go pokušava konekciju (povremeni `dial tcp: connection refused`)**

MySQL image mora inicijalizovati data directory pri prvom startu — to traje. `depends_on: condition: service_healthy` sa `retries: 10` i `start_period: 30s` pokriva ovo. Ako i dalje failuje, dodaj retry logiku u Go DSN connection pool:
```go
// db/mysql.go — connection retry s exponential backoff
for attempts := 0; attempts < 10; attempts++ {
    db, err = sql.Open("mysql", dsn)
    if err == nil {
        if pingErr := db.Ping(); pingErr == nil {
            break
        }
    }
    time.Sleep(time.Duration(attempts+1) * 2 * time.Second)
}
```

**Vue build cache — stari JS u browseru**

Vite output fajlovi imaju content hash u imenu (`app.Bx9kL3mN.js`), ali nginx može cache-ovati `index.html` koji referencira stari hash. Lokalno: `Ctrl+Shift+R` (hard reload). U produkciji: `index.html` mora imati `Cache-Control: no-cache, no-store`.

```nginx
location = /index.html {
    add_header Cache-Control "no-cache, no-store, must-revalidate";
    add_header Pragma "no-cache";
    expires 0;
}
```

**mysql-replica ne replicira od mastera**

Lokalni setup koristi dva odvojena MySQL kontejnera bez automatski konfigurisane replikacije. Za simulaciju master/replica u docker-compose, dodaj init skriptu koja konfiguriše `CHANGE MASTER TO` posle startup-a. Alternativno — koristi isti MySQL kontejner lokalno, samo s različitim variablama (`GO_DB_MASTER_DSN` i `GO_DB_REPLICA_DSN` ukazuju na isti host). Realna replikacija testira se na AWS RDS-u gdje je automatska.

**nginx vraća 502 Bad Gateway na `/api/`**

php-service nije spreman ili nije dosežan. Provjeri:
```bash
docker compose logs php-service --tail 50
docker exec project-a-nginx wget -q -O- http://php-service:8000/health
# Ako ovo ne radi — problem je network (provjeri da su oba na frontend mrežu)
```

**Port 80 zauzet na hostu**

```bash
sudo lsof -i :80 | grep LISTEN
# Ako radi Apache/nginx lokalno: sudo systemctl stop apache2 nginx
# Ili promijeni ports u docker-compose: "8080:80"
```
