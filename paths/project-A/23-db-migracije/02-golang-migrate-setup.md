# 02 — golang-migrate: Setup i Upravljanje

## Instalacija kroz Docker (preporučeno — bez lokalne instalacije)

```bash
# Pokretanje kroz Docker
docker run --rm -v $(pwd)/migrations:/migrations \
  migrate/migrate:v4.17.0 \
  -path /migrations \
  -database "mysql://root:pass@tcp(localhost:3306)/project_a" \
  up

# Convenience alias za lokalni razvoj
alias migrate='docker run --rm -v $(pwd)/migrations:/migrations migrate/migrate:v4.17.0'

# Provjera verzije
docker run --rm migrate/migrate:v4.17.0 --version
```

---

## Struktura migrations direktorijuma

```
migrations/
├── 000001_create_users_table.up.sql
├── 000001_create_users_table.down.sql
├── 000002_add_email_verified.up.sql
├── 000002_add_email_verified.down.sql
├── 000003_create_sessions_table.up.sql
└── 000003_create_sessions_table.down.sql
```

**Pravilo imenovanja:** `{version}_{opis}.{up|down}.sql`
- `version` — 6-cifreni broj: `000001`, `000002`, ... (vodeće nule za ispravno sortiranje)
- `opis` — snake_case, kratko ali jasno (šta migracija radi)
- Svaka migracija: **par fajlova** (up + down), uvijek oba

---

## Primjeri SQL migracija

### 000001_create_users_table.up.sql
```sql
CREATE TABLE users (
    id            BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    email         VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### 000001_create_users_table.down.sql
```sql
DROP TABLE IF EXISTS users;
```

### 000002_add_email_verified.up.sql
```sql
ALTER TABLE users
    ADD COLUMN email_verified_at   TIMESTAMP    NULL DEFAULT NULL AFTER email,
    ADD COLUMN verification_token  VARCHAR(255) NULL             AFTER email_verified_at;
```

### 000002_add_email_verified.down.sql
```sql
ALTER TABLE users
    DROP COLUMN verification_token,
    DROP COLUMN email_verified_at;
```

> **Napomena:** DOWN migracija briše kolone u obrnutom redoslijedu od UP-a.
> MySQL ne dozvoljava `DROP COLUMN` i `ADD COLUMN` na istoj koloni u jednoj izjavi.

---

## Upravljanje migracijama — sve komande

```bash
# Apply SVE pending migracije (uobičajeno u CI/CD)
migrate -path ./migrations \
  -database "mysql://admin:pass@tcp(rds-endpoint:3306)/project_a" \
  up

# Apply samo N migracija naprijed
migrate -path ./migrations -database "..." up 2

# Rollback JEDNE migracije (koristiti SAMO u razvoju)
migrate -path ./migrations -database "..." down 1

# Rollback SVIH migracija (koristiti SAMO lokalno/staging za reset)
migrate -path ./migrations -database "..." down

# Provjeri trenutni nivo (koja je zadnja primijenjena verzija)
migrate -path ./migrations -database "..." version
# Output: 3

# Force na specifičnu verziju — EMERGENCY ONLY, za dirty state
# Ne pokreće SQL, samo mijenja version u schema_migrations
migrate -path ./migrations -database "..." force 3

# Status svih migracija (da li su pending ili applied)
migrate -path ./migrations -database "..." status
```

---

## schema_migrations tracking u bazi

```sql
-- golang-migrate automatski kreira ovu tablicu pri prvom pokretanju
SELECT * FROM schema_migrations;
```

```
version | dirty
--------|------
1       | false
2       | false
3       | false
```

**dirty = true** znači da je migracija pala na pola:
```bash
# Simptom: migrate version prikazuje "3 (dirty)"
# FIX workflow:
# 1. Nađi šta je migracija 3 trebala uraditi
cat migrations/000003_problematic_migration.up.sql

# 2. Ručno provjeri stanje baze
mysql -h $DB_HOST -u $DB_USER -p$DB_PASS $DB_NAME \
  -e "SHOW TABLES; DESCRIBE users;"

# 3. Ručno ispravi bazu (dodaj što nedostaje ili obriši što je na pola)
mysql -h $DB_HOST -u $DB_USER -p$DB_PASS $DB_NAME < manual_fix.sql

# 4. Resetuj dirty flag na čisto stanje NAKON što je baza ispravna
migrate -path ./migrations -database "..." force 3
```

---

## Database URL formati

```bash
# MySQL / MariaDB
mysql://user:password@tcp(host:3306)/dbname
mysql://user:password@tcp(host:3306)/dbname?multiStatements=true

# S AWS RDS IAM auth (bez lozinke u URL-u)
# Bolje rješenje: koristiti env varijable, ne hardcode u URL
DB_URL="mysql://${DB_USER}:${DB_PASS}@tcp(${DB_HOST}:3306)/${DB_NAME}"
migrate -path ./migrations -database "$DB_URL" up
```

---

## Lokalni razvoj: docker-compose integracija

```yaml
# docker-compose.yml
services:
  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: rootpass
      MYSQL_DATABASE: project_a
      MYSQL_USER: appuser
      MYSQL_PASSWORD: apppass
    ports:
      - "3306:3306"
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 5s
      timeout: 3s
      retries: 10

  migrate:
    image: migrate/migrate:v4.17.0
    depends_on:
      mysql:
        condition: service_healthy
    volumes:
      - ./migrations:/migrations
    command:
      - -path=/migrations
      - -database=mysql://appuser:apppass@tcp(mysql:3306)/project_a
      - up
    profiles:
      - tools   # Pokreni eksplicitno: docker-compose --profile tools run migrate
```

```bash
# Pokreni migracije lokalno
docker-compose --profile tools run --rm migrate

# Ili direktno s aliasom
migrate -path ./migrations \
  -database "mysql://appuser:apppass@tcp(localhost:3306)/project_a" \
  up
```
