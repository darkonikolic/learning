# 06 — Rollback i Emergency Procedure

## Rollback migracije (samo lokalno/staging)

```bash
# Provjeri trenutni nivo
migrate -path ./migrations \
  -database "mysql://admin:pass@tcp(rds:3306)/project_a" \
  version
# Output: 3

# Rollback JEDNE migracije (executa DOWN sql za verziju 3)
migrate -path ./migrations \
  -database "mysql://admin:pass@tcp(rds:3306)/project_a" \
  down 1
# version je sada 2

# Rollback N migracija
migrate -path ./migrations -database "..." down 2

# Rollback SVIH (za totalni reset lokalno)
migrate -path ./migrations -database "..." down
```

---

## NIKAD ne rollbackuj produkcijsku migraciju s realnim podacima

```
DOWN migracija koja briše kolonu → TRAJNI GUBITAK PODATAKA u produkciji!

Ispravno rješenje: Nova FORWARD migracija koja ispravlja problem.

Primjer:
  Migracija 000005 dodala pogrešan indeks koji usporava bazu?
  NE: rollback 000005 na produkciji
  DA: Kreiraj 000006_fix_wrong_index.up.sql koji ispravlja problem

  000006_fix_wrong_index.up.sql:
    DROP INDEX idx_wrong ON orders;
    ALTER TABLE orders ADD INDEX idx_correct (user_id, created_at);
```

---

## Dirty state: migracija pala na pola

```
Simptom: migrate version → "3 (dirty)"
Uzrok: Migracija 000003 počela, SQL statement pao na pola,
       golang-migrate postavio dirty=true, izašao s greškom
```

```bash
# 1. Provjeri koji je problem
mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" \
  -e "SELECT version, dirty FROM schema_migrations;"
# version: 3, dirty: 1

# 2. Pročitaj šta je migracija 3 trebala uraditi
cat migrations/000003_problematic_migration.up.sql

# 3. Provjeri stvarno stanje baze (šta je urađeno, šta nije)
mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" \
  -e "SHOW TABLES; DESCRIBE users; SHOW INDEX FROM users;"

# 4. Pripremi manual fix SQL (popuni što nedostaje ili obriši što je na pola)
cat > /tmp/manual_fix.sql << 'EOF'
-- Primjer: migracija je dodala kolonu ali pala na ADD INDEX
ALTER TABLE users ADD INDEX idx_verification_token (verification_token);
EOF

# 5. Testiraj fix na STAGING prvо
mysql -h "$STAGING_DB" -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" < /tmp/manual_fix.sql
migrate -path ./migrations \
  -database "mysql://$DB_USER:$DB_PASS@tcp($STAGING_DB:3306)/$DB_NAME" \
  version
# Treba da vrati: 3 (dirty) — fix SQL nije promijenio version

# 6. Nakon što je baza u ispravnom stanju, resetuj dirty flag
# force NE izvršava SQL — samo mijenja version u schema_migrations
migrate -path ./migrations \
  -database "mysql://$DB_USER:$DB_PASS@tcp($STAGING_DB:3306)/$DB_NAME" \
  force 3
# Sada: version=3, dirty=false

# 7. Provjeri da migrate status izgleda ispravno
migrate -path ./migrations \
  -database "mysql://$DB_USER:$DB_PASS@tcp($STAGING_DB:3306)/$DB_NAME" \
  version
# Output: 3 (bez "dirty")

# 8. Primijeni isti postupak na PROD
mysql -h "$PROD_DB" -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" < /tmp/manual_fix.sql
migrate -path ./migrations \
  -database "mysql://$DB_USER:$DB_PASS@tcp($PROD_DB:3306)/$DB_NAME" \
  force 3
```

---

## Rollback app verzije bez rollback-a migracije

```bash
# Helm rollback app verzije (ne dira bazu):
helm rollback project-a 2 -n project-a-prod
# app se vraća na staru verziju
# Baza OSTAJE na novijoj schema verziji!

# Zato expand-contract pravilo postoji:
# Stara app verzija mora biti kompatibilna s novijim schema-om.
# Nova kolona → stara app je ignoriše → OK
# Obrisana kolona → stara app je traži → CRASH
```

```bash
# Provjeri Helm historiju
helm history project-a -n project-a-prod
# REVISION  STATUS     CHART
# 1         superseded project-a-1.0.0
# 2         superseded project-a-1.1.0
# 3         deployed   project-a-1.2.0

# Rollback na reviziju 2
helm rollback project-a 2 -n project-a-prod --wait
```

---

## Emergency checklist

```
[ ] Provjeri schema_migrations status (dirty?)
[ ] Provjeri K8s Job status (Failed? Complete?)
[ ] Provjeri app Pod logove (error poruke)
[ ] Provjeri RDS CloudWatch metrike (CPU, connections, deadlocks)
[ ] Provjeri da li je problem u migraciji ili u app kodu
[ ] Ako migration dirty: manual fix → force → verify
[ ] Ako app crash (ne migracija): helm rollback app
[ ] Nikad ne rollbackuj produkcionu migraciju s podacima
[ ] Dokumentiraj incident i korake u GitLab issue
```

---

## Korisne dijagnostičke komande

```bash
# Provjeri schema_migrations direktno u bazi
mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" \
  -e "SELECT * FROM schema_migrations;"

# Provjeri koji K8s Job-ovi postoje
kubectl get jobs -n project-a-prod --sort-by=.metadata.creationTimestamp

# Provjeri log Migration Job-a
kubectl logs -n project-a-prod \
  -l component=db-migrate \
  -c migrate \
  --previous  # --previous za crashed container

# RDS: aktivne konekcije i lock-ovi
mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASS" -e "
  SHOW PROCESSLIST;
  SHOW ENGINE INNODB STATUS\G
  SELECT * FROM information_schema.INNODB_TRX\G
"

# Provjeri da li je neka ALTER TABLE blokirana
mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASS" -e "
  SELECT waiting_trx_id, blocking_trx_id, wait_started, locked_table
  FROM sys.innodb_lock_waits;
"

# Kill blokirajuću konekciju (emergency)
mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASS" -e "KILL <process_id>;"
```

---

## Prevencija: Testiranje migracija u CI-u

```yaml
# .gitlab-ci.yml — test migration na fresh bazi
test:migrations:
  stage: test
  image: docker:24
  services:
    - mysql:8.0
  variables:
    MYSQL_ROOT_PASSWORD: testpass
    MYSQL_DATABASE: project_a_test
    DB_URL: "mysql://root:testpass@tcp(mysql:3306)/project_a_test"
  script:
    # Apply sve migracije
    - docker run --rm --network host
        -v $CI_PROJECT_DIR/migrations:/migrations
        migrate/migrate:v4.17.0
        -path /migrations -database "$DB_URL" up
    # Provjeri verziju
    - docker run --rm --network host
        -v $CI_PROJECT_DIR/migrations:/migrations
        migrate/migrate:v4.17.0
        -path /migrations -database "$DB_URL" version
    # Test rollback (sve down, pa sve up ponovo)
    - docker run --rm --network host
        -v $CI_PROJECT_DIR/migrations:/migrations
        migrate/migrate:v4.17.0
        -path /migrations -database "$DB_URL" down
    - docker run --rm --network host
        -v $CI_PROJECT_DIR/migrations:/migrations
        migrate/migrate:v4.17.0
        -path /migrations -database "$DB_URL" up
    - echo "Migration up/down/up cycle: OK"
```
