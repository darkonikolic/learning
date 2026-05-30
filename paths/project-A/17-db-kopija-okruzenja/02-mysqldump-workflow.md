# 02 — mysqldump workflow

## mysqldump iz Docker kontejnera

Nikad ne instaliramo MySQL klijent direktno na CI runner ili dev mašinu. Koristimo Docker image — verzija alata je uvijek eksplicitna i konzistentna sa serverom:

```bash
docker run --rm mysql:8.0 mysqldump \
  -h $RDS_MASTER_ENDPOINT \
  -u admin \
  -p$DB_PASSWORD \
  --single-transaction \
  --routines \
  --triggers \
  --set-gtid-purged=OFF \
  --column-statistics=0 \
  project_a > dump_$(date +%Y%m%d_%H%M).sql
```
> **Podman:** `podman run --rm mysql:8.0 mysqldump -h $RDS_MASTER_ENDPOINT -u admin -p$DB_PASSWORD --single-transaction --routines --triggers --set-gtid-purged=OFF --column-statistics=0 project_a > dump_$(date +%Y%m%d_%H%M).sql`

Svaki flag ima razlog za postojanje. Slijedi detaljna analiza.

---

## `--single-transaction` — MVCC konzistentnost bez table lock-ova

Ovo je najvažniji flag. Bez njega, mysqldump zaključava svaku tabelu dok je dumpuje — što znači da pisanje u prod bazu staje dok dump traje.

### Kako radi internally

Kad mysqldump primijeni `--single-transaction`, izvršava:

```sql
SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ;
START TRANSACTION WITH CONSISTENT SNAPSHOT;
```

`WITH CONSISTENT SNAPSHOT` je MySQL-specific ekstenzija koja atomično kreira MVCC (Multi-Version Concurrency Control) read view u trenutku izvršavanja naredbe. Taj read view je "zamrznuti pogled" na cijelu bazu u jednom trenutku.

**MVCC semantika:** InnoDB čuva više verzija svakog reda u undo log-u. Transakcija koja koristi REPEATABLE READ vidi isključivo verzije redova koje su bile committed **prije** nego što je read view kreiran. Sve naknadne izmjene su nevidljive toj transakciji, bez obzira koliko dugo dump traje.

Rezultat: mysqldump može čitati 50 tabela tokom 10 minuta, a aplikacija može pisati slobodno — dump će uvijek biti konzistentna slika stanja iz trenutka kad je `START TRANSACTION WITH CONSISTENT SNAPSHOT` bio izvršen.

### Ograničenje: samo InnoDB

`--single-transaction` radi **jedino** za InnoDB tabele. Ako baza sadrži MyISAM tabele, mysqldump će ih i dalje zaključati (`LOCK TABLES`). Za project-A: sve tabele su InnoDB (jedino razumno za produkcijsku MySQL 8.0 bazu).

### Provjera da su sve tabele InnoDB

```sql
SELECT table_name, engine
FROM information_schema.tables
WHERE table_schema = 'project_a'
  AND engine != 'InnoDB';
```

Ako ovaj upit vrati redove — imaš problem. Migracija MyISAM → InnoDB je preduvjet za `--single-transaction` konzistentnost.

---

## `--set-gtid-purged=OFF` — GTID i cross-instance restore

### Što su GTID-ovi

GTID (Global Transaction Identifier) je jedinstveni identifikator koji MySQL 8.0 dodjeljuje svakoj transakciji. Format: `source_uuid:transaction_id`, npr. `3E11FA47-71CA-11E1-9E33-C80AA9429562:1-23`.

RDS MySQL instance imaju GTID mode uključen po defaultu. Svaki dump koji se napravi bez `--set-gtid-purged=OFF` sadrži naredbu:

```sql
SET @@GLOBAL.gtid_purged='3E11FA47-71CA-11E1-9E33-C80AA9429562:1-23456';
```

### Problem pri restore-u

Kad restore-uješ ovaj dump na **drugu** RDS instancu (npr. dev), ta instanca već ima vlastiti `gtid_executed` set sa vlastitim UUID-om. Pokušaj postavljanja `gtid_purged` koji se preklapa sa `gtid_executed` rezultira greškom:

```
ERROR 1840 (HY000): @@GLOBAL.gtid_purged can only be set when @@GLOBAL.gtid_executed is empty.
```

Ili još gore — tiho preskakanje transakcija ako se GTID setovi parcijalno preklapaju u replikacijskom kontekstu.

### Rješenje: `--set-gtid-purged=OFF`

Flag kaže mysqldump-u da **ne uključuje** `SET @@GLOBAL.gtid_purged` naredbu u dump. Dump postaje "GTID-agnostičan" — može se restore-ovati na bilo koju instancu bez konflikta.

Jedini slučaj kada **ne** koristiš `--set-gtid-purged=OFF` je ako restore-uješ dump u replikacijsku hijerarhiju i trebaš da slave zna koje transakcije su već primijenjene. Za naš use case (kopija podataka u izolirani env), uvijek OFF.

---

## `--column-statistics=0` — MySQL 8.0 gotcha

mysqldump 8.0 je uveo automatsko prikupljanje column statistics (`ANALYZE TABLE`) pri dumpovanju, koje koristi information_schema tablicu `COLUMN_STATISTICS`. Problem: ova tablica ne postoji u MySQL 5.7, niti u nekim cloud-managed verzijama.

Čak i ako source i target su oba MySQL 8.0, `--column-statistics=0` ubrzava dump jer preskače nepotreban overhead. Uvijek ga uključi.

---

## `--routines` i `--triggers`

mysqldump **ne uključuje** stored procedures, functions i triggers po defaultu. Ako ih imaš u prod bazi i zaboraviš ove flagove, restore okruženje neće biti funkcionalno ekvivalentno.

Za project-A koji još nema stored procedures: ove flagove svejedno uključi. Dump s njima je kompatibilan s bazom koja nema routines (unit output je prazan), a ako ih dodaš u budućnosti, dump workflow ostaje ispravan bez izmjene.

---

## Dump veličina i kompresija

SQL dump je izrazito kompresibilan (repetitivne INSERT naredbe). Faktor kompresije za tipičan MySQL dump je 5-10x.

### Pipeline za kompresiju na licu mjesta

```bash
docker run --rm mysql:8.0 mysqldump \
  -h $RDS_MASTER_ENDPOINT \
  -u admin \
  -p$DB_PASSWORD \
  --single-transaction \
  --routines \
  --triggers \
  --set-gtid-purged=OFF \
  --column-statistics=0 \
  project_a \
  | gzip -9 \
  | aws s3 cp - s3://$STATE_BUCKET/db-dumps/latest.sql.gz \
    --storage-class STANDARD_IA
```
> **Podman:** `podman run --rm mysql:8.0 mysqldump -h $RDS_MASTER_ENDPOINT -u admin -p$DB_PASSWORD --single-transaction --routines --triggers --set-gtid-purged=OFF --column-statistics=0 project_a | gzip -9 | aws s3 cp - s3://$STATE_BUCKET/db-dumps/latest.sql.gz --storage-class STANDARD_IA`

Prednosti pipe pristupa:
- Nema privremenog fajla na disku — dump direktno teče u gzip → S3
- Manja memorijska potrošnja nego buffer cijelog dump-a
- `STANDARD_IA` S3 storage class je ~40% jeftiniji od STANDARD za podatke koji se čitaju rjeđe od jednom mjesečno

### Naming konvencija u S3

```
s3://project-a-state-bucket/db-dumps/
  latest.sql.gz          ← uvijek najnoviji, symlink pattern
  2024-01-15_0200.sql.gz ← datum-stamped backup za retenciju
```

`latest.sql.gz` se svaki dan overwrite-uje novim dumpom. Datumski stamp fajlovi se čuvaju 30 dana (S3 lifecycle policy).

---

## Pokretanje na read replica, ne masteru

Expert pravilo: **nikad ne pokreći dump na RDS master instanci u produkcijskom okruženju**.

Razlog: `--single-transaction` sprječava table lock-ove, ali dump i dalje:
- Čita ogromne količine podataka → povećava read I/O na instanci
- Otvara long-running transakciju → može blokirati vacuum i purge operacije u InnoDB
- Povećava CPU load na instanci koja služi produkcijski traffic

RDS read replica postoji upravo za ovakve read-heavy operacije. Konfiguriraj dump job da koristi read replica endpoint:

```bash
-h $RDS_READ_REPLICA_ENDPOINT  # ne master
```

Jedino upozorenje: read replica može imati **replication lag** — podaci mogu biti stari nekoliko sekundi do minuta. Za naš use case (daily backup za lower envs), lag od par minuta je apsolutno prihvatljiv. Za point-in-time recovery ili kritičan backup — koristi master ili RDS automated backup.

---

## Provjera integriteta dump-a

Nikad ne restore-uj dump bez provjere da nije koruptiran:

```bash
# Provjeri da dump završava sa COMMIT ili Dump completed
tail -5 dump_latest.sql

# Provjeri da gzip nije korumpiran
gzip -t dump_latest.sql.gz && echo "OK" || echo "CORRUPTED"

# Provjeri veličinu — drastično manji dump od prethodnog je alarm
aws s3 ls s3://$STATE_BUCKET/db-dumps/ --human-readable
```

U pipeline-u, dodaj checksum provjeru:

```bash
sha256sum dump_latest.sql.gz > dump_latest.sql.gz.sha256
aws s3 cp dump_latest.sql.gz.sha256 s3://$STATE_BUCKET/db-dumps/latest.sql.gz.sha256
```

---

## Makefile — dodaj u ovom poglavlju

Ovo poglavlje uvodi mysqldump workflow. Dodaj u `Makefile` u korenu projekta:

```makefile
# === OBLAST 17: DB kopija okruženja ===

db-dump: ## Dump MySQL baze iz produkcije (DB=mydb HOST=rds.endpoint make db-dump)
	docker run --rm \
	  -v $(PWD):/dump \
	  mysql:8 mysqldump -h $(HOST) -u root -p$(MYSQL_PASSWORD) \
	  --single-transaction --quick $(DB) > ./dump/$(DB)-$$(date +%Y%m%d).sql

db-restore: ## Restore MySQL dump u ciljno okruženje (FILE=dump.sql DB=mydb HOST=localhost make db-restore)
	docker run --rm \
	  -v $(PWD):/dump \
	  mysql:8 mysql -h $(HOST) -u root -p$(MYSQL_PASSWORD) $(DB) < /dump/$(FILE)
```

Centralni Makefile već sadrži ove targete — ovo je referenca šta si dodao u ovoj oblasti.

Provjeri da targeti rade:
```bash
DB=myapp HOST=prod-rds.example.com make db-dump
FILE=myapp-20240101.sql DB=myapp HOST=localhost make db-restore
make help | grep "^db-"
```
