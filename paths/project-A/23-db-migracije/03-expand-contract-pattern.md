# 03 — Expand-Contract Pattern

## Zašto expand-contract

Zero-downtime deploy na Kubernetesu znači da **stara i nova verzija aplikacije rade ISTOVREMENO** tokom rolling update. Migracija se primjenjuje PRIJE deploymenta, ali stari podovi su još uvijek živi. Ako je migracija breaking change → crash starih podova.

```
Bez expand-contract:
  T=0:  K8s Job → migrate up (ALTER TABLE RENAME COLUMN name → full_name)
  T=1:  Rolling update počinje
  T=2:  Pod s novim kodom startuje → OK (čita full_name)
  T=3:  Stari pod prima request → ERROR: "Unknown column 'name'" → crash
  T=4:  DOWNTIME dok se svi stari podovi ne ugase
```

**Pravilo:** Svaka migracija mora biti **backward-compatible** s prethodnom verzijom aplikacije.

---

## Primjer 1: Preimenuj kolonu (LOŠE vs DOBRO)

### Loše (breaking migration)
```sql
-- 000005_rename_name_column.up.sql
-- NIKAD ovako u produkciji s rolling deploymentom!
ALTER TABLE users RENAME COLUMN name TO full_name;
-- Stara app verzija pada odmah: "Unknown column 'name'"
```

### Dobro (expand-contract u 4 koraka kroz 2-3 deploye)

**Deploy 1 — EXPAND: Dodaj novu kolonu, stara kolona ostaje**
```sql
-- 000005_add_full_name_column.up.sql
ALTER TABLE users ADD COLUMN full_name VARCHAR(255) NULL AFTER name;
-- Stara app ignoriše novu kolonu → radi normalno
-- DOWN:
-- ALTER TABLE users DROP COLUMN full_name;
```

**Deploy 2 — Nova app verzija piše u OBE kolone**
```go
// Go kod u tranzicijskom periodu (piše u obje kolone)
func (r *UserRepository) Update(ctx context.Context, u *User) error {
    _, err := r.db.ExecContext(ctx,
        `UPDATE users SET name = ?, full_name = ?, updated_at = NOW() WHERE id = ?`,
        u.FullName, u.FullName, u.ID,  // ista vrijednost u obje kolone
    )
    return err
}

// Čita iz nove kolone, fallback na staru
func (r *UserRepository) Get(ctx context.Context, id int64) (*User, error) {
    var u User
    err := r.db.QueryRowContext(ctx,
        `SELECT id, COALESCE(NULLIF(full_name, ''), name) as full_name FROM users WHERE id = ?`,
        id,
    ).Scan(&u.ID, &u.FullName)
    return &u, err
}
```

**Deploy 3 — BACKFILL + NOT NULL constraint**
```sql
-- 000006_backfill_and_constrain_full_name.up.sql
-- Backfill sve null vrijednosti iz stare kolone
UPDATE users SET full_name = name WHERE full_name IS NULL OR full_name = '';

-- Sada možemo dodati NOT NULL (sve vrijednosti su popunjene)
ALTER TABLE users MODIFY full_name VARCHAR(255) NOT NULL;

-- DOWN (pazi: ovo gubi podatke ako se ikad rollbackuje):
-- ALTER TABLE users MODIFY full_name VARCHAR(255) NULL;
-- UPDATE users SET full_name = NULL;
```

**Deploy 4 — CONTRACT: App čita SAMO full_name, briše staru kolonu**
```sql
-- 000007_drop_name_column.up.sql
ALTER TABLE users DROP COLUMN name;
-- DOWN:
-- ALTER TABLE users ADD COLUMN name VARCHAR(255) NULL;
-- UPDATE users SET name = full_name;
```

---

## Primjer 2: Dodaj foreign key na velikoj tablici

### Naivno (može blokirati tablicu minutama)
```sql
-- OPASNO na tablici s milijunima redova:
ALTER TABLE orders ADD CONSTRAINT fk_user
  FOREIGN KEY (user_id) REFERENCES users(id);
-- MySQL uzima metadata lock → novi upiti čekaju → efektivni downtime
```

### Produkcijski (minimalni lock kroz korake)
```sql
-- Korak 1: Dodaj kolonu bez FK (brzo, mali lock)
-- 000008_add_user_id_new_to_orders.up.sql
ALTER TABLE orders ADD COLUMN user_id_new BIGINT UNSIGNED NULL;
```

```bash
# Korak 2: Backfill asinkrono u batchevima (NE u jednom UPDATE)
# scripts/backfill_user_id.sh
set -e
BATCH=10000
OFFSET=0
while true; do
    AFFECTED=$(mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" -sN -e \
        "UPDATE orders SET user_id_new = user_id
         WHERE user_id_new IS NULL
         LIMIT $BATCH;
         SELECT ROW_COUNT();")
    echo "Updated $AFFECTED rows (offset $OFFSET)"
    [ "$AFFECTED" -eq 0 ] && break
    OFFSET=$((OFFSET + BATCH))
    sleep 0.1  # Daj breathing room za produkcijski promet
done
echo "Backfill complete."
```

```sql
-- Korak 3: Indeks + FK (brže jer je kolona indeksirana)
-- 000009_add_fk_user_id_new.up.sql
ALTER TABLE orders ADD INDEX idx_user_id_new (user_id_new);
ALTER TABLE orders ADD CONSTRAINT fk_orders_user
    FOREIGN KEY (user_id_new) REFERENCES users(id) ON DELETE RESTRICT;
ALTER TABLE orders MODIFY user_id_new BIGINT UNSIGNED NOT NULL;

-- Korak 4: Ukloni staru kolonu, preimenuj novu
-- 000010_drop_old_user_id.up.sql
ALTER TABLE orders DROP FOREIGN KEY fk_orders_user_old;  -- ako postoji
ALTER TABLE orders DROP COLUMN user_id;
ALTER TABLE orders RENAME COLUMN user_id_new TO user_id;
ALTER TABLE orders RENAME INDEX idx_user_id_new TO idx_user_id;
```

---

## Primjer 3: Dodaj NOT NULL kolonu bez DEFAULT

### Loše
```sql
-- Pada ako tablice ima podataka: "Column 'status' cannot be null"
ALTER TABLE orders ADD COLUMN status VARCHAR(50) NOT NULL;
```

### Dobro
```sql
-- Korak 1: NULL s DEFAULT (backward-compatible)
-- 000011_add_status_nullable.up.sql
ALTER TABLE orders ADD COLUMN status VARCHAR(50) NULL DEFAULT 'pending';

-- Korak 2: Backfill (ako je potrebno drugačije od DEFAULT)
-- (u ovom slučaju DEFAULT je dovoljan)

-- Korak 3: NOT NULL constraint (pošto su sve vrijednosti popunjene)
-- 000012_status_not_null.up.sql
ALTER TABLE orders MODIFY status VARCHAR(50) NOT NULL DEFAULT 'pending';
```

---

## Provjera lock time-a na staging

```bash
# Procijeni trajanje ALTER TABLE (ne izvršava promjenu)
mysql -h "$STAGING_DB" -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" -e \
  "EXPLAIN FORMAT=JSON ALTER TABLE orders ADD INDEX idx_status (status);" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(json.dumps(d, indent=2))"

# Provjeri veličinu tablice (bitno za procjenu lock trajanja)
mysql -h "$STAGING_DB" -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" -e \
  "SELECT table_name,
          ROUND(data_length/1024/1024, 2) AS data_mb,
          ROUND(index_length/1024/1024, 2) AS index_mb,
          table_rows
   FROM information_schema.tables
   WHERE table_schema = 'project_a'
   ORDER BY data_length DESC;"
```

```bash
# pt-online-schema-change (Percona Toolkit) za ALTER bez locka na produkciji
# Radi kopiju tablice, migrira row po row, zatim swap
docker run --rm percona/percona-toolkit:latest \
  pt-online-schema-change \
  --alter "ADD COLUMN new_col VARCHAR(255) NULL" \
  --host="$DB_HOST" \
  --user="$DB_USER" \
  --password="$DB_PASS" \
  D="$DB_NAME",t=orders \
  --execute \
  --progress=time,5 \
  --print
# UPOZORENJE: pt-osc kreira triggere → nije kompatibilno sa svim verzijama MySQL replikacije
```

---

## Non-breaking migration checklist

Provjeri svaku migraciju prije commitanja:

- [ ] Nema `RENAME COLUMN` direktno — koristiti expand-contract
- [ ] Nema `DROP COLUMN` dok stara app verzija koristi tu kolonu
- [ ] Nema `NOT NULL` bez `DEFAULT` ili prethodnog backfilla
- [ ] Nema promjena koje mijenjaju ponašanje stare app verzije
- [ ] Svaki `ALTER TABLE` na tablici s >100k redova testiran na staging (izmjeri lock time!)
- [ ] `DOWN` migracija je ispravna i testirana lokalno
- [ ] Migracija je testirana na kopiji produkcijske baze na stagingu
- [ ] Nema `SELECT *` u SQL — eksplicitne kolone (robusnost na schema promjene)
