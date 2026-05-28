# 04 — dbmate: Alternativa za Jednostavnije Projekte

## Šta je dbmate

`dbmate` je Go tool sličan `golang-migrate`, ali s drugačijim formatom fajlova: **jedan fajl po migraciji** koji sadrži i UP i DOWN sekciju. Nema zasebnih `.up.sql` i `.down.sql` fajlova.

---

## Pokretanje kroz Docker

```bash
# Apply sve pending migracije
docker run --rm \
  -v $(pwd)/db/migrations:/db/migrations \
  ghcr.io/amacneil/dbmate:v2 \
  --url "mysql://admin:pass@tcp(localhost:3306)/project_a" \
  up

# Kreiraj novu migraciju (automatski kreira fajl s timestamp-om)
docker run --rm \
  -v $(pwd)/db/migrations:/db/migrations \
  ghcr.io/amacneil/dbmate:v2 \
  new create_sessions_table
# Kreira: db/migrations/20240115141523_create_sessions_table.sql

# Convenience alias
alias dbmate='docker run --rm -v $(pwd)/db/migrations:/db/migrations ghcr.io/amacneil/dbmate:v2'
```

---

## Format fajla (jedan fajl, dvije sekcije)

**20240115141523_create_sessions_table.sql:**
```sql
-- migrate:up
CREATE TABLE sessions (
    id         VARCHAR(255) PRIMARY KEY,
    user_id    BIGINT UNSIGNED NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    data       JSON NULL,

    INDEX idx_user_id (user_id),
    INDEX idx_expires_at (expires_at),

    CONSTRAINT fk_sessions_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- migrate:down
DROP TABLE IF EXISTS sessions;
```

**Poređenje formata:**

| | golang-migrate | dbmate |
|--|---------------|--------|
| Fajl struktura | `000001_name.up.sql` + `000001_name.down.sql` | `20240115_name.sql` (jedan fajl) |
| Verzionisanje | Sekvencionalni broj | Timestamp |
| UP i DOWN | Zasebni fajlovi | Sekcije u jednom fajlu |

---

## Sve komande

```bash
# Apply sve pending migracije
dbmate --url "$DB_URL" up

# Rollback zadnje migracije
dbmate --url "$DB_URL" down

# Rollback i odmah apply (korisno u razvoju)
dbmate --url "$DB_URL" rollback

# Provjeri status (koje su applied, koje pending)
dbmate --url "$DB_URL" status
# Output:
# [x] 20240101000000_create_users_table.sql
# [x] 20240102000000_add_email_verified.sql
# [ ] 20240115141523_create_sessions_table.sql  ← pending

# Dump schema u fajl (korisno za git tracking trenutnog stanja)
dbmate --url "$DB_URL" dump
# Kreira: db/schema.sql

# Kreiraj novu praznu migraciju
dbmate new migration_name
```

---

## Primjer: Kompletna sessions migracija

**Kreiraj:**
```bash
dbmate new create_sessions_table
# Otvori fajl i popuni:
```

```sql
-- migrate:up
CREATE TABLE sessions (
    id         VARCHAR(255) PRIMARY KEY,
    user_id    BIGINT UNSIGNED NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    data       JSON NULL,

    INDEX idx_user_id (user_id),
    INDEX idx_expires_at (expires_at),

    CONSTRAINT fk_sessions_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- migrate:down
DROP TABLE IF EXISTS sessions;
```

**Primijeni:**
```bash
dbmate --url "mysql://admin:pass@tcp(rds:3306)/project_a" up
```

---

## schema_migrations tabela u dbmate

```sql
-- dbmate kreira svoju vlastitu tracking tablicu
SELECT * FROM schema_migrations;
```

```
version
---------------------
20240101000000
20240102000000
20240115141523
```

Samo `version` kolona (bez `dirty` flag-a). Dbmate nema ekvivalent za golang-migrate `dirty` state handling.

---

## Kada dbmate, kada golang-migrate

| Kriterij | dbmate | golang-migrate |
|----------|--------|---------------|
| Jedan fajl po migraciji | Da (up+down zajedno) | Ne (zasebni fajlovi) |
| Docker image veličina | ~15MB | ~25MB |
| Go programmatic API | Slabiji | Odličan |
| Schema dump komanda | Ugrađena | Nema |
| Dirty state handling | Nema | Ima (`force` komanda) |
| Timestamp vs. broj verzija | Timestamp | Broj (000001...) |
| CI/CD integracija | Jednostavna | Jednostavna |
| Preporuka | Manji projekti, manje timova | **Ovaj projekat** |

**Za ovaj projekat koristiti `golang-migrate`** jer:
- Bolja integracija s Go ekosistemom (programmatic API za testove)
- Eksplicitan dirty state handling (kritično za produkciju)
- Zasebni up/down fajlovi = jasniji code review

---

## dbmate u CI/CD (ako bi se koristio)

```yaml
# GitLab CI
migrate:dev:
  stage: migrate
  image: ghcr.io/amacneil/dbmate:v2
  script:
    - dbmate
        --url "mysql://$DEV_DB_USER:$DEV_DB_PASS@tcp($DEV_DB_HOST:3306)/project_a"
        --migrations-dir /builds/$CI_PROJECT_PATH/db/migrations
        up
  environment: development
```
