# 03 — Restore workflow

## Restore na Docker MySQL (lokalni dev)

Dev radi lokalno sa Docker Compose MySQL instancom. Restore koristi `docker compose exec`:

```bash
# Download dump iz S3
aws s3 cp s3://$STATE_BUCKET/db-dumps/latest.sql.gz /tmp/latest.sql.gz

# Restore (gunzip na licu mjesta, pipe u mysql)
gunzip -c /tmp/latest.sql.gz | docker compose exec -T mysql mysql \
  -u root \
  -p$MYSQL_ROOT_PASSWORD \
  project_a
```
> **Podman:** `gunzip -c /tmp/latest.sql.gz | podman compose exec -T mysql mysql -u root -p$MYSQL_ROOT_PASSWORD project_a`

Flag `-T` za `docker compose exec` je obavezan u non-interactive kontekstu (skripte, pipeline) — disabluje pseudo-TTY alokaciju. Bez njega, stdin pipe ne radi ispravno i restore puca.

### Alternativa: docker run za restore (bez docker compose)

Ako lokalni workflow ne koristi docker compose ili se radi u CI kontekstu:

```bash
gunzip -c /tmp/latest.sql.gz | docker run --rm -i \
  --network host \
  mysql:8.0 mysql \
  -h 127.0.0.1 \
  -u root \
  -p$MYSQL_ROOT_PASSWORD \
  project_a
```
> **Podman:** `gunzip -c /tmp/latest.sql.gz | podman run --rm -i --network host mysql:8.0 mysql -h 127.0.0.1 -u root -p$MYSQL_ROOT_PASSWORD project_a`

`--network host` je potrebno da container može dosegnuti localhost MySQL instancu.

---

## Restore na RDS MySQL (AWS env)

Za AWS envove (dev, staging, review apps), restore ide direktno na RDS endpoint:

```bash
# Download iz S3 i restore na RDS (pipe bez privremenog fajla)
aws s3 cp s3://$STATE_BUCKET/db-dumps/latest.sql.gz - \
  | gunzip \
  | docker run --rm -i mysql:8.0 mysql \
      -h $RDS_DEV_ENDPOINT \
      -u admin \
      -p$DB_PASSWORD \
      project_a
```
> **Podman:** `aws s3 cp s3://$STATE_BUCKET/db-dumps/latest.sql.gz - | gunzip | podman run --rm -i mysql:8.0 mysql -h $RDS_DEV_ENDPOINT -u admin -p$DB_PASSWORD project_a`

Opet: streaming pipeline bez privremenog fajla na disku. Posebno važno za veliku bazu — nema potrebe za diskom dovoljno velikim za cijeli dump.

### Network connectivity

CI runner mora biti u VPC koji može dosegnuti RDS endpoint (ili koristiti VPC peering/PrivateLink). RDS security group mora dopustiti inbound 3306 od CI runner security group-e. Ovo je Terraform konfiguracija iz modula 07/08.

---

## Idempotent restore

Restore mora biti idempotent — ponovljeno pokretanje mora dati isti rezultat, bez grešaka zbog "tabela već postoji".

### Opcija A: `--add-drop-table` u dump-u (preporučeno)

Najčišće rješenje: dodaj flag pri kreiranju dump-a:

```bash
mysqldump \
  --add-drop-table \        # DROP TABLE IF EXISTS prije svake CREATE TABLE
  --single-transaction \
  ...
```

Dump tada izgleda:

```sql
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` ( ... );
INSERT INTO `users` VALUES ( ... );
```

Ponovljeni restore je siguran jer DROP TABLE IF EXISTS ne puca ako tabela ne postoji.

### Opcija B: DROP + CREATE database prije restore-a

Agresivniji pristup koji garantira čisto stanje:

```bash
# Pripremi čistu bazu
docker run --rm mysql:8.0 mysql \
  -h $RDS_DEV_ENDPOINT \
  -u admin \
  -p$DB_PASSWORD \
  -e "DROP DATABASE IF EXISTS project_a; CREATE DATABASE project_a CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# Restore
gunzip -c latest.sql.gz | docker run --rm -i mysql:8.0 mysql \
  -h $RDS_DEV_ENDPOINT \
  -u admin \
  -p$DB_PASSWORD \
  project_a
```
> **Podman:** `podman run --rm mysql:8.0 mysql -h $RDS_DEV_ENDPOINT -u admin -p$DB_PASSWORD -e "DROP DATABASE IF EXISTS project_a; CREATE DATABASE project_a CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"` i `gunzip -c latest.sql.gz | podman run --rm -i mysql:8.0 mysql -h $RDS_DEV_ENDPOINT -u admin -p$DB_PASSWORD project_a`

Prednost: garantirano čisto stanje — nema ostataka od prethodnih restore-a ili migracija.
Mana: kratak downtime database-a (sekunde) dok je baza droppana i recreirana.

Za review apps koji se kreiraju iz scratch-a: Opcija B je prirodan izbor jer baza ionako ne postoji još.

---

## Schema migracije nakon restore-a

Ovo je kritična tačka gdje mnogi griješe.

### Problem

Prod dump sadrži **prod shemu** — onakvu kakva je u produkciji u tom trenutku. Ali dev ili staging branch koji primaš dump može imati **pending migracije** koje još nisu deployane u prod.

Primjer:
- Prod je na migraciji #45
- Dev branch dodaje migraciju #46 (nova kolona `users.subscription_tier`)
- Dump iz prod-a sadrži shemu do migracije #45

Ako restore-uješ dump bez aplikacije migracije #46, aplikacija na dev env-u će pucati jer pokušava pisati u kolonu koja ne postoji.

### Ispravni redosled

```
1. Restore dump (sadrži prod shemu + prod podatke)
2. Pokreni pending migracije za ovaj branch/env
3. Aplikacija startuje
```

Nikad ne mijenj ovaj redosled. Migracije koje dodaju kolone moraju biti primijenjene **na podatke koji već postoje** — to je upravo svrha `UP` migracija.

### Implementacija u pipeline-u

```yaml
db:restore-and-migrate:
  stage: post-deploy
  script:
    # 1. Restore
    - aws s3 cp s3://$STATE_BUCKET/db-dumps/latest.sql.gz - | gunzip | mysql ...
    # 2. Pending migracije
    - php artisan migrate --force
    # ili: go run ./cmd/migrate up
    # ili: flyway migrate
```

Što "pending" znači ovisi o migration tooling-u projekta. Za Laravel: `migrate` bez `--fresh`. Za custom Go migration tool: `up` command koji aplicira sve not-yet-applied migracije.

---

## Restore timing — planiranje pipeline timeouts

Ovo je nešto što se zaboravi do prvog puta kad pipeline timeoutuje u produkciji.

| Dump veličina | Restore na Docker (lokalno) | Restore na RDS | Download iz S3 |
|---|---|---|---|
| 50 MB | ~30 sec | ~45 sec | ~5 sec |
| 100 MB | ~1-2 min | ~2-3 min | ~10 sec |
| 500 MB | ~5-10 min | ~8-15 min | ~30 sec |
| 1 GB | ~15-25 min | ~20-35 min | ~60 sec |
| 5 GB | ~60-90 min | ~80-120 min | ~5 min |

Faktori koji utječu na brzinu restore-a:
- **RDS instance class:** db.t3.micro (1 vCPU, 1GB RAM) vs db.r6g.large (2 vCPU, 16GB RAM) — ogromna razlika
- **Storage IOPS:** gp2 vs gp3 vs io1 — InnoDB je I/O bound pri bulk inserts
- **`innodb_buffer_pool_size`:** ako je malen u odnosu na veličinu podataka, restore ide sporo
- **Network bandwidth:** CI runner do RDS
- **Broj indeksa:** svaki INSERT mora ažurirati sve indekse — tablica sa 10 indeksa restore-uje se ~3x sporije nego bez

### Optimizacija restore-a za veliku bazu

Ako restore postane predugo, postoji set optimizacija za mysqldump restore:

```sql
-- Privremeno za brži bulk restore (poništi nakon!)
SET foreign_key_checks = 0;
SET unique_checks = 0;
SET sql_log_bin = 0;        -- samo ako nisi na replikaciji
```

Ili u dump fajlu dodaj na početak (kroz dump opcije ili ručno):

```bash
mysqldump \
  --disable-keys \          # DROP+CREATE keys nakon bulk insert
  --extended-insert \       # multi-row INSERT (manji SQL, brži parse)
  ...
```

`--extended-insert` grupira redove u jedan INSERT:
```sql
-- Bez --extended-insert (sporo):
INSERT INTO users VALUES (1,'alice',...);
INSERT INTO users VALUES (2,'bob',...);

-- Sa --extended-insert (brzo):
INSERT INTO users VALUES (1,'alice',...),(2,'bob',...),(3,'charlie',...);
```

Za dev workflow: restore > 10 minuta je signal da treba pregledati arhitekturu (subset podataka? RDS snapshot? veći instance type za dev RDS?).

---

## Restore provjera (smoke test)

Nakon restore-a, pokreni brzi sanity check:

```bash
docker run --rm mysql:8.0 mysql \
  -h $RDS_DEV_ENDPOINT \
  -u admin \
  -p$DB_PASSWORD \
  -e "
    SELECT table_name, table_rows
    FROM information_schema.tables
    WHERE table_schema = 'project_a'
    ORDER BY table_rows DESC
    LIMIT 10;
  "
```
> **Podman:** `podman run --rm mysql:8.0 mysql -h $RDS_DEV_ENDPOINT -u admin -p$DB_PASSWORD -e "SELECT table_name, table_rows FROM information_schema.tables WHERE table_schema = 'project_a' ORDER BY table_rows DESC LIMIT 10;"`

`table_rows` u information_schema je aproksimacija (ne exact count), ali dovoljno za provjeru da restore nije rezultirao praznim tabelama.
