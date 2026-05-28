# 08 — Brisanje Starih Backupa

## Pregled svih backup resursa i troškova

```bash
#!/bin/bash
# scripts/list-all-backups.sh
set -euo pipefail

echo "=== RDS MANUAL SNAPSHOTS ==="
aws rds describe-db-snapshots \
  --snapshot-type manual \
  --query 'DBSnapshots[*].[DBSnapshotIdentifier,DBInstanceIdentifier,SnapshotCreateTime,AllocatedStorage]' \
  --output table

echo ""
echo "=== RDS AUTOMATED BACKUPS ==="
aws rds describe-db-instance-automated-backups \
  --query 'DBInstanceAutomatedBackups[*].[DBInstanceIdentifier,RestoreWindow.LatestTime,AllocatedStorage]' \
  --output table

echo ""
echo "=== S3 MYSQLDUMP BACKUPS ==="
aws s3 ls s3://project-a-db-backups/mysqldump/ --recursive --human-readable

echo ""
echo "=== ESTIMATED COSTS ==="
SNAPSHOT_GB=$(aws rds describe-db-snapshots \
  --snapshot-type manual \
  --query 'sum(DBSnapshots[*].AllocatedStorage)' \
  --output text 2>/dev/null || echo 0)
S3_GB=$(aws s3 ls s3://project-a-db-backups/ --recursive 2>/dev/null | \
  awk '{sum+=$3} END {printf "%.2f", sum/1024/1024/1024}')
echo "Manual snapshots: ${SNAPSHOT_GB}GB x \$0.095 = \$$(echo "$SNAPSHOT_GB * 0.095" | bc)/mj"
echo "S3 dumps: ${S3_GB}GB x \$0.023 = \$$(echo "$S3_GB * 0.023" | bc)/mj"
```

---

## Brisanje RDS manual snapshota

```bash
# Lista svih manual snapshota (sortirano po datumu, najstariji prvi)
aws rds describe-db-snapshots \
  --snapshot-type manual \
  --query 'sort_by(DBSnapshots, &SnapshotCreateTime)[*].[DBSnapshotIdentifier,SnapshotCreateTime,AllocatedStorage]' \
  --output table

# Obriši specifičan snapshot
aws rds delete-db-snapshot \
  --db-snapshot-identifier project-a-prod-20240115-1430

# Obriši sve snapshote starije od 30 dana
CUTOFF=$(date -u -d '30 days ago' +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || \
         date -u -v-30d +%Y-%m-%dT%H:%M:%SZ)  # macOS fallback

aws rds describe-db-snapshots \
  --snapshot-type manual \
  --query "DBSnapshots[?SnapshotCreateTime<='$CUTOFF'].DBSnapshotIdentifier" \
  --output text | tr '\t' '\n' | while read -r SNAPSHOT_ID; do
    [ -z "$SNAPSHOT_ID" ] && continue
    echo "Deleting: $SNAPSHOT_ID"
    aws rds delete-db-snapshot --db-snapshot-identifier "$SNAPSHOT_ID"
done

# Prekini snapshot koji je u toku (ako treba prekinuti dug proces)
aws rds describe-db-snapshots \
  --snapshot-type manual \
  --query "DBSnapshots[?Status=='creating'].DBSnapshotIdentifier" \
  --output text | tr '\t' '\n' | while read -r ID; do
    [ -z "$ID" ] && continue
    echo "Cancelling in-progress snapshot: $ID"
    aws rds delete-db-snapshot --db-snapshot-identifier "$ID"
done
```

---

## Brisanje S3 mysqldump backupa

```bash
# Prikaži sve s veličinom, datumom i ukupnim sumarijem
aws s3 ls s3://project-a-db-backups/mysqldump/ \
  --recursive --human-readable --summarize

# Obriši specifičan fajl
aws s3 rm s3://project-a-db-backups/mysqldump/project_a_20240101_030000.sql.gz

# Obriši sve osim najnovijeg (zaštiti zadnji backup)
LATEST=$(aws s3 ls s3://project-a-db-backups/mysqldump/ | \
  sort -k1,2 | tail -1 | awk '{print $4}')

if [ -z "$LATEST" ]; then
  echo "No backups found."
  exit 0
fi

echo "Keeping latest: $LATEST"
aws s3 ls s3://project-a-db-backups/mysqldump/ | \
  awk '{print $4}' | grep -v "^$" | grep -v "^$LATEST$" | \
  while read -r FILE; do
    echo "Deleting: $FILE"
    aws s3 rm "s3://project-a-db-backups/mysqldump/$FILE"
  done

# Obriši SVE mysqldump backupe (total cleanup)
aws s3 rm s3://project-a-db-backups/mysqldump/ --recursive

# Provjeri da je prazan
aws s3 ls s3://project-a-db-backups/mysqldump/ && echo "Files remain!" || echo "Empty — OK"
```

---

## Brisanje automated backupa pri terraform destroy

Automated backupovi se brišu automatski samo ako je `delete_automated_backups = true` postavljeno UNAPRIJED na RDS instanci.

```hcl
# terraform/modules/rds/main.tf
resource "aws_db_instance" "main" {
  identifier = "project-a-${var.env}"
  # ...

  # MORA biti postavljeno unaprijed — ne može se retroaktivno primijeniti na destroy
  delete_automated_backups = true

  # dev: skip final snapshot (nema smisla čuvati dev snapshots)
  # prod: napravi final snapshot prije destroy-a
  skip_final_snapshot       = var.env == "dev" ? true : false
  final_snapshot_identifier = var.env != "dev" ? "project-a-${var.env}-final-${formatdate("YYYYMMDD", timestamp())}" : null
}
```

```bash
# Ako je instanca već uništena a automated backupi ostali:
# Lista orphaned automated backupova
aws rds describe-db-instance-automated-backups \
  --query 'DBInstanceAutomatedBackups[?Status==`retained`].[DBInstanceIdentifier,DBInstanceAutomatedBackupsArn]' \
  --output table

# Obriši specifičan retained automated backup
aws rds delete-db-instance-automated-backup \
  --dbi-resource-id "db-ABCDEFGHIJKLMNOPQRST"
```

---

## Potpuna cleanup skripta (za total reset)

```bash
#!/bin/bash
# scripts/cleanup-all-backups.sh
# Koristi: ./cleanup-all-backups.sh dev
set -euo pipefail

ENV=${1:-}
if [ -z "$ENV" ]; then
  echo "ERROR: Navedi environment: ./cleanup-all-backups.sh dev|staging|prod"
  exit 1
fi

if [ "$ENV" = "prod" ]; then
  echo "UPOZORENJE: Tražiš brisanje produkcijskih backupa!"
  echo "Ovo je NEPOVRATNA operacija."
fi

echo "=== CLEANUP ALL BACKUPS: $ENV ==="
read -rp "Ovo ce obrisati SVE backupe za '$ENV'. Nastavi? (yes/no): " CONFIRM
[ "$CONFIRM" != "yes" ] && { echo "Aborted."; exit 0; }

ERRORS=0

# 1. RDS manual snapshots
echo ""
echo "[1/3] Deleting RDS manual snapshots za $ENV..."
SNAPSHOT_IDS=$(aws rds describe-db-snapshots \
  --snapshot-type manual \
  --query "DBSnapshots[?contains(DBSnapshotIdentifier,'project-a-$ENV')].DBSnapshotIdentifier" \
  --output text | tr '\t' '\n' | grep -v '^$' || true)

if [ -z "$SNAPSHOT_IDS" ]; then
  echo "  Nema manual snapshota za $ENV."
else
  echo "$SNAPSHOT_IDS" | while read -r ID; do
    echo "  Deleting: $ID"
    if ! aws rds delete-db-snapshot --db-snapshot-identifier "$ID" > /dev/null; then
      echo "  GRESKA: Nije moguce obrisati $ID" >&2
      ERRORS=$((ERRORS + 1))
    fi
  done
fi

# 2. S3 mysqldump backups
echo ""
echo "[2/3] Deleting S3 mysqldump backups za $ENV..."
# Sigurnosna mjera: ako brisuš dev, ne diraj prod fajlove
S3_EXCLUDE=""
if [ "$ENV" = "dev" ]; then
  S3_EXCLUDE="--exclude '*prod*'"
fi

# shellcheck disable=SC2086
aws s3 rm "s3://project-a-db-backups/mysqldump/" \
  --recursive \
  --include "*${ENV}*" \
  $S3_EXCLUDE \
  2>&1 | tee /tmp/s3-cleanup-$ENV.log || {
    echo "  GRESKA tokom S3 brisanja — provjeri /tmp/s3-cleanup-$ENV.log" >&2
    ERRORS=$((ERRORS + 1))
  }

# 3. Verifikacija
echo ""
echo "[3/3] Verifying cleanup..."

REMAINING_SNAPSHOTS=$(aws rds describe-db-snapshots \
  --snapshot-type manual \
  --query "length(DBSnapshots[?contains(DBSnapshotIdentifier,'project-a-$ENV')])" \
  --output text 2>/dev/null || echo "?")

REMAINING_S3=$(aws s3 ls "s3://project-a-db-backups/mysqldump/" 2>/dev/null | \
  grep "$ENV" | wc -l | tr -d ' ' || echo "?")

echo "Preostali manual snapshots: $REMAINING_SNAPSHOTS"
echo "Preostali S3 fajlovi: $REMAINING_S3"

echo ""
if [ "$ERRORS" -eq 0 ]; then
  echo "=== CLEANUP COMPLETE (bez gresaka) ==="
else
  echo "=== CLEANUP ZAVRSENO S $ERRORS GRESK(A) — provjeri output iznad ===" >&2
  exit 1
fi
```

---

## Terraform: S3 lifecycle za automatsko brisanje

Postavi jednom, brisanje se dešava automatski bez ručne intervencije:

```hcl
# terraform/modules/s3-backups/main.tf
resource "aws_s3_bucket_lifecycle_configuration" "db_backups" {
  bucket = aws_s3_bucket.db_backups.id

  rule {
    id     = "auto-delete-old-mysqldumps"
    status = "Enabled"

    filter {
      prefix = "mysqldump/"
    }

    expiration {
      days = 30    # Auto-briše mysqldump fajlove starije od 30 dana
    }

    noncurrent_version_expiration {
      noncurrent_days = 7    # Briše stare verzije fajlova nakon 7 dana
    }
  }

  rule {
    id     = "auto-delete-snapshot-exports"
    status = "Enabled"

    filter {
      prefix = "snapshot-exports/"
    }

    expiration {
      days = 14    # Snapshot exporti: kraći retention
    }
  }

  rule {
    id     = "abort-incomplete-multipart-uploads"
    status = "Enabled"

    filter {}    # Primijeni na sve

    abort_incomplete_multipart_upload {
      days_after_initiation = 3    # Briše nedovršene uploade
    }
  }
}
```

```bash
# Provjeri da je lifecycle policy primijenjena
aws s3api get-bucket-lifecycle-configuration \
  --bucket project-a-db-backups \
  --output json | python3 -m json.tool

# Ručno triggeruj lifecycle provjeru (korisno za testiranje)
aws s3api put-bucket-lifecycle-configuration \
  --bucket project-a-db-backups \
  --lifecycle-configuration file://lifecycle.json
```

---

## Kada što brisati

| Tip | Preporučeni retention | Automatsko brisanje |
|-----|----------------------|---------------------|
| RDS manual snapshots | 30 dana (dev), 90 dana (prod) | Ne (ručno ili kroz CLI skriptu) |
| RDS automated backups | Kontroliše `backup_retention_period` u Terraform | Da, automatski |
| S3 mysqldump | 30 dana | Da, S3 lifecycle |
| S3 snapshot exports | 14 dana | Da, S3 lifecycle |
| Prod final snapshot | Trajno (ili dok ne potvrdiš da nije potreban) | Ne |
