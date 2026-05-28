# 09 — Backup, Revert i Cost Strategija za project-a

## 1. Backup strategija za project-a

### Tri nivoa backupa

```
Nivo 1: RDS Automated Backups (BESPLATNO)
  - Svakodnevni snapshot + kontinuirani binlog za PITR
  - Retention: 1 dan (dev) / 7 dana (prod)
  - PITR: restore do bilo koje sekunde unutar retention perioda
  - Storage: besplatno do veličine DB instance (20GB DB = 20GB backup besplatno)
  - NAPOMENA: gube se pri terraform destroy!

Nivo 2: Manual Snapshots ($0.095/GB/mj)
  - Kreirati ručno ili automatski (pre-deploy)
  - Postoje čak i nakon brisanja RDS instance
  - 20GB snapshot = $1.90/mj
  - Idealno za: pre-deploy checkpoint, before destroy

Nivo 3: mysqldump → S3 ($0.023/GB/mj compressed)
  - Application-level backup
  - Portabilno: radi na bilo kojoj MySQL instanci
  - 20GB dump, gzip komprimiran ~5GB = $0.115/mj
  - Idealno za: cross-environment copy, audit trail
```

### Ukupni troškovi za project-a

```
Dev (1 dan automated): $0
Prod (7 dana automated): $0 (do 20GB)
1 manual snapshot pred svaki tjedno: $1.90/mj
Weekly mysqldump → S3 (5GB): $0.12/mj
──────────────────────────────
UKUPNO: ~$2/mj za solidan backup
```

---

## 2. Terraform backup konfiguracija

```hcl
# terraform/modules/rds/main.tf

resource "aws_db_instance" "main" {
  identifier        = "project-a-${var.env}"
  engine            = "mysql"
  engine_version    = "8.0"
  instance_class    = var.instance_class
  allocated_storage = var.allocated_storage
  storage_type      = "gp3"

  # Backup konfiguracija
  backup_retention_period = var.backup_retention_days  # dev=1, prod=7
  backup_window           = "02:00-03:00"              # UTC, van peak houra
  maintenance_window      = "sun:03:00-sun:04:00"      # nedjelja ujutro

  # Da li kreirati final snapshot pri brisanju
  skip_final_snapshot       = var.env == "dev" ? true : false
  final_snapshot_identifier = var.env != "dev" ? "project-a-${var.env}-final-${formatdate("YYYYMMDD", timestamp())}" : null

  # Restore from snapshot (prazno = nova baza)
  snapshot_identifier = var.snapshot_identifier != "" ? var.snapshot_identifier : null

  # Point in time recovery (automatski uz backup_retention_period > 0)
  # Nema zasebnog flag-a — aktivan dok je backup_retention_period > 0

  delete_automated_backups = true   # Brisi automated backupe pri brisanju instance

  tags = {
    Environment = var.env
    Backup      = "enabled"
  }
}

# S3 bucket za mysqldump backupe
resource "aws_s3_bucket" "db_backups" {
  bucket = "project-a-db-backups-${var.account_id}"
}

resource "aws_s3_bucket_lifecycle_configuration" "db_backups" {
  bucket = aws_s3_bucket.db_backups.id

  rule {
    id     = "expire-old-backups"
    status = "Enabled"

    filter {
      prefix = "mysqldump/"
    }

    expiration {
      days = 30   # Čuvaj mysqldump backupe 30 dana
    }

    transition {
      days          = 7
      storage_class = "GLACIER_IR"  # Jeftiniji storage nakon 7 dana
    }
  }

  rule {
    id     = "expire-snapshots-exports"
    status = "Enabled"

    filter {
      prefix = "snapshot-exports/"
    }

    expiration {
      days = 90
    }
  }
}
```

**Variables za backup konfiguraciju:**

```hcl
# terraform/modules/rds/variables.tf

variable "backup_retention_days" {
  description = "Broj dana čuvanja automated backupa. 0 = isključeno."
  type        = number
  default     = 7

  validation {
    condition     = var.backup_retention_days >= 0 && var.backup_retention_days <= 35
    error_message = "backup_retention_days mora biti između 0 i 35."
  }
}

variable "snapshot_identifier" {
  description = "Snapshot ID za restore. Prazno = nova baza."
  type        = string
  default     = ""
}

variable "account_id" {
  description = "AWS Account ID za jedinstveni S3 bucket naziv."
  type        = string
}
```

**Environment-specific vrijednosti:**

```hcl
# terraform/environments/dev/terraform.tfvars
backup_retention_days = 1
snapshot_identifier   = ""

# terraform/environments/prod/terraform.tfvars
backup_retention_days = 7
snapshot_identifier   = ""   # popuni pri restore scenariju
```

---

## 3. Automatski pre-deploy snapshot

```bash
#!/bin/bash
# scripts/pre-deploy-snapshot.sh ENV
# Kreirati snapshot prije svakog prod deploy-a

set -e
ENV=${1:-prod}
DB_ID="project-a-$ENV"
SNAPSHOT_ID="project-a-$ENV-pre-deploy-$(date +%Y%m%d-%H%M)"

echo "Creating pre-deploy snapshot: $SNAPSHOT_ID"

aws rds create-db-snapshot \
  --db-instance-identifier "$DB_ID" \
  --db-snapshot-identifier "$SNAPSHOT_ID" \
  --tags Key=Type,Value=pre-deploy Key=Environment,Value="$ENV"

echo "Waiting for snapshot (5-10 min)..."
aws rds wait db-snapshot-completed \
  --db-snapshot-identifier "$SNAPSHOT_ID"

echo "✓ Snapshot ready: $SNAPSHOT_ID"

# Spremi u fajl za potencijalni rollback
echo "$SNAPSHOT_ID" > ".last-${ENV}-snapshot"
echo "Rollback command:"
echo "  aws rds restore-db-instance-from-db-snapshot \\"
echo "    --db-instance-identifier ${DB_ID}-restore \\"
echo "    --db-snapshot-identifier $SNAPSHOT_ID"
```

**Integracija u CI/CD pipeline:**

```yaml
# .github/workflows/deploy-prod.yml (relevantan dio)

jobs:
  pre-deploy-snapshot:
    runs-on: ubuntu-latest
    steps:
      - name: Create pre-deploy snapshot
        run: |
          chmod +x scripts/pre-deploy-snapshot.sh
          ./scripts/pre-deploy-snapshot.sh prod
        env:
          AWS_REGION: eu-west-1
          # Credentials via OIDC / assumed role

  deploy:
    needs: pre-deploy-snapshot
    runs-on: ubuntu-latest
    steps:
      - name: Deploy application
        run: |
          # ... deploy koraci
```

---

## 4. Point-in-Time Recovery (PITR)

### Šta je PITR

- AWS RDS neprekidno sprema binlog na S3
- Možeš restore-ovati do bilo koje sekunde unutar retention perioda
- Precision: 5 minuta (AWS ažurira binlog svakih 5 min)

### Kada koristiti PITR

- "Ooops, obrisali smo production tablicu u 14:32"
- "Deployali smo bug koji je pisao pogrešne podatke od 10:15 do 11:47"
- Data corruption incident

### PITR komande

```bash
# Restore do specifičnog vremena
# NAPOMENA: Kreira NOVU RDS instancu (ne overwrite-uje staru)
aws rds restore-db-instance-to-point-in-time \
  --source-db-instance-identifier "project-a-prod" \
  --target-db-instance-identifier "project-a-prod-pitr-restore" \
  --restore-time "2024-01-15T14:30:00Z" \
  --db-instance-class db.t3.micro \
  --publicly-accessible false \
  --tags Key=Purpose,Value=pitr-restore

# Čekaj restore (~15-30 minuta)
aws rds wait db-instance-available \
  --db-instance-identifier "project-a-prod-pitr-restore"

# Dobij novi endpoint
aws rds describe-db-instances \
  --db-instance-identifier "project-a-prod-pitr-restore" \
  --query 'DBInstances[0].Endpoint.Address' \
  --output text

# Sada: connect na restore, pronađi podatke, kopiraj natrag na prod
```

**Tipičan recovery workflow nakon PITR:**

```bash
# 1. Restore do trenutka prije incidenta
RESTORE_INSTANCE="project-a-prod-pitr-$(date +%Y%m%d-%H%M)"

aws rds restore-db-instance-to-point-in-time \
  --source-db-instance-identifier "project-a-prod" \
  --target-db-instance-identifier "$RESTORE_INSTANCE" \
  --restore-time "2024-01-15T14:29:00Z"   # 1 min prije incidenta

aws rds wait db-instance-available \
  --db-instance-identifier "$RESTORE_INSTANCE"

RESTORE_HOST=$(aws rds describe-db-instances \
  --db-instance-identifier "$RESTORE_INSTANCE" \
  --query 'DBInstances[0].Endpoint.Address' --output text)

# 2. Izvuci podatke koji su oštećeni/obrisani
mysql -h "$RESTORE_HOST" -u admin -p project_a \
  -e "SELECT * FROM orders WHERE created_at BETWEEN '2024-01-14' AND '2024-01-15'" \
  > recovered_orders.sql

# 3. Importuj nazad na prod (uz provjeru!)
mysql -h "$PROD_HOST" -u admin -p project_a < recovered_orders.sql

# 4. Obriši restore instancu (košta dok postoji!)
aws rds delete-db-instance \
  --db-instance-identifier "$RESTORE_INSTANCE" \
  --skip-final-snapshot
```

### PITR Terraform

```hcl
# terraform/modules/rds/pitr-restore.tf

resource "aws_db_instance" "pitr_restore" {
  count      = var.pitr_restore_time != "" ? 1 : 0
  identifier = "project-a-${var.env}-pitr"

  restore_to_point_in_time {
    source_db_instance_identifier = "project-a-${var.env}"
    restore_time                  = var.pitr_restore_time  # "2024-01-15T14:30:00Z"
  }

  instance_class      = "db.t3.micro"
  skip_final_snapshot = true

  tags = {
    Environment = var.env
    Purpose     = "pitr-restore"
    AutoDelete  = "true"  # Tag za cleanup automation
  }
}

variable "pitr_restore_time" {
  description = "ISO 8601 timestamp za PITR restore. Prazno = ne kreira restore instancu."
  type        = string
  default     = ""
}

output "pitr_restore_endpoint" {
  value = var.pitr_restore_time != "" ? aws_db_instance.pitr_restore[0].address : ""
}
```

---

## 5. mysqldump → S3 workflow

### K8s CronJob za scheduled backup

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: mysql-backup
  namespace: project-a-prod
spec:
  schedule: "0 3 * * 0"   # Svake nedjelje u 03:00 UTC
  concurrencyPolicy: Forbid
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 3
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: OnFailure
          serviceAccountName: backup-job-sa   # IRSA: S3 write permission
          containers:
            - name: mysql-backup
              image: mysql:8.0
              env:
                - name: DB_HOST
                  valueFrom:
                    secretKeyRef:
                      name: db-credentials
                      key: host
                - name: DB_PASSWORD
                  valueFrom:
                    secretKeyRef:
                      name: db-credentials
                      key: password
                - name: S3_BUCKET
                  value: "project-a-db-backups-123456789"
                - name: AWS_REGION
                  value: "eu-west-1"
              command:
                - /bin/sh
                - -c
                - |
                  set -e
                  FILENAME="mysqldump/project_a_$(date +%Y%m%d_%H%M).sql.gz"
                  echo "Starting backup: $FILENAME"

                  # Dump sa replike (ne mastera!) za čitanje bez lock-a
                  mysqldump \
                    -h "$DB_HOST" \
                    -u backup_user \
                    -p"$DB_PASSWORD" \
                    --single-transaction \
                    --set-gtid-purged=OFF \
                    --column-statistics=0 \
                    project_a \
                    | gzip -9 \
                    | aws s3 cp - "s3://$S3_BUCKET/$FILENAME" \
                      --region "$AWS_REGION" \
                      --expected-size 1000000

                  echo "Backup completed: s3://$S3_BUCKET/$FILENAME"

                  # Provjeri veličinu
                  SIZE=$(aws s3 ls "s3://$S3_BUCKET/$FILENAME" | awk '{print $3}')
                  [ "$SIZE" -lt 1000 ] && { echo "ERROR: Backup too small ($SIZE bytes)!"; exit 1; }
                  echo "Backup size: $SIZE bytes"
```

### IRSA ServiceAccount za S3 write

```hcl
# terraform/modules/k8s-backup/main.tf

resource "aws_iam_role" "backup_job" {
  name = "project-a-${var.env}-backup-job"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Federated = var.oidc_provider_arn
      }
      Action = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "${var.oidc_provider}:sub" = "system:serviceaccount:project-a-${var.env}:backup-job-sa"
        }
      }
    }]
  })
}

resource "aws_iam_role_policy" "backup_job_s3" {
  name = "s3-backup-write"
  role = aws_iam_role.backup_job.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["s3:PutObject", "s3:GetObject", "s3:ListBucket"]
      Resource = [
        "arn:aws:s3:::project-a-db-backups-${var.account_id}",
        "arn:aws:s3:::project-a-db-backups-${var.account_id}/mysqldump/*"
      ]
    }]
  })
}
```

---

## 6. Restore iz S3 mysqldump

```bash
#!/bin/bash
# scripts/restore-from-s3.sh TARGET_ENV [S3_KEY]
# Restore mysqldump sa S3 na specificni environment

set -e
TARGET_ENV=$1
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
S3_BUCKET="project-a-db-backups-$ACCOUNT_ID"

# Ako S3 ključ nije proslijeđen, uzmi najnoviji dump
S3_KEY=${2:-$(aws s3 ls "s3://$S3_BUCKET/mysqldump/" \
  | sort -k1,2 \
  | tail -1 \
  | awk '{print "mysqldump/"$4}')}

echo "=== RESTORE FROM S3 ==="
echo "Target:    $TARGET_ENV"
echo "Dump:      s3://$S3_BUCKET/$S3_KEY"
echo ""

# Potvrda (za prod!)
if [ "$TARGET_ENV" = "prod" ]; then
  read -rp "WARNING: Restoring to PRODUCTION. Type 'yes' to confirm: " CONFIRM
  [ "$CONFIRM" != "yes" ] && { echo "Aborted."; exit 1; }
fi

DB_HOST=$(aws rds describe-db-instances \
  --db-instance-identifier "project-a-$TARGET_ENV" \
  --query 'DBInstances[0].Endpoint.Address' \
  --output text)

DB_PASS=$(aws secretsmanager get-secret-value \
  --secret-id "/project-a/$TARGET_ENV/db-password" \
  --query 'SecretString' \
  --output text)

echo "Target host: $DB_HOST"
echo "Downloading and restoring..."

aws s3 cp "s3://$S3_BUCKET/$S3_KEY" - \
  | gunzip \
  | docker run --rm -i mysql:8.0 mysql \
      -h "$DB_HOST" -u admin -p"$DB_PASS" project_a

echo "✓ Restore complete"
```

**Provjera integriteta dumpа prije restora:**

```bash
# Provjeri da dump nije prazan i da sadrži CREATE TABLE statement
aws s3 cp "s3://$S3_BUCKET/$S3_KEY" - \
  | gunzip \
  | head -100 \
  | grep -c "CREATE TABLE" \
  | xargs -I{} sh -c '[ {} -gt 0 ] && echo "✓ Dump valid: {} tables found" || { echo "ERROR: No tables in dump!"; exit 1; }'
```

---

## 7. Backup monitoring

```hcl
# terraform/modules/monitoring/backup-alarms.tf

# CloudWatch alarm: RDS automated backup nije uspio
resource "aws_cloudwatch_metric_alarm" "backup_failed" {
  alarm_name          = "project-a-${var.env}-backup-failed"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "FailedBackupJobsCount"
  namespace           = "AWS/Backup"
  period              = 86400  # 24 sata
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "RDS backup failed"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    BackupVaultName = "project-a-${var.env}"
  }
}

# CloudWatch alarm: slobodan storage < 5GB
resource "aws_cloudwatch_metric_alarm" "rds_storage_low" {
  alarm_name          = "project-a-${var.env}-rds-storage-low"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 1
  metric_name         = "FreeStorageSpace"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 5368709120  # 5GB u bajtovima
  alarm_description   = "RDS free storage < 5GB"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    DBInstanceIdentifier = "project-a-${var.env}"
  }
}

# CloudWatch alarm: backup storage troškovi rastu (>25GB)
resource "aws_cloudwatch_metric_alarm" "backup_storage_high" {
  alarm_name          = "project-a-${var.env}-backup-storage-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "TotalBackupStorageBilled"
  namespace           = "AWS/RDS"
  period              = 86400
  statistic           = "Average"
  threshold           = 26843545600  # 25GB u bajtovima (iznad besplatnog limita)
  alarm_description   = "RDS backup storage prekoračio besplatni limit (25GB)"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    DBInstanceIdentifier = "project-a-${var.env}"
  }
}
```

**Provjera statusa backup-a putem CLI:**

```bash
# Zadnjih 5 automated backup-a
aws rds describe-db-instance-automated-backups \
  --db-instance-identifier "project-a-prod" \
  --query 'DBInstanceAutomatedBackups[*].{Status:Status,From:RestoreWindow.EarliestTime,To:RestoreWindow.LatestTime}' \
  --output table

# Lista manual snapshot-a
aws rds describe-db-snapshots \
  --db-instance-identifier "project-a-prod" \
  --snapshot-type manual \
  --query 'DBSnapshots[*].{ID:DBSnapshotIdentifier,Status:Status,Created:SnapshotCreateTime,Size:AllocatedStorage}' \
  --output table

# S3 mysqldump backupi (sortiran po datumu)
aws s3 ls "s3://project-a-db-backups-$(aws sts get-caller-identity --query Account --output text)/mysqldump/" \
  | sort -k1,2 \
  | tail -10
```

---

## 8. Backup checklist po environmentu

| Backup tip | Dev | Staging | Prod |
|---|---|---|---|
| Automated backup retention | 1 dan | 3 dana | 7 dana |
| Pre-deploy manual snapshot | Ne | Da | Da (obavezno) |
| mysqldump → S3 | Ne | Tjedni | Tjedni |
| PITR dostupan | Da (1 dan) | Da (3 dana) | Da (7 dana) |
| Final snapshot pri destroy | Ne (skip) | Da | Da |
| Backup monitoring alarm | Ne | Da | Da (kritično) |

### Procijenjeni trošak po environmentu

| Backup tip | Dev | Staging | Prod |
|---|---|---|---|
| Automated backup (≤20GB) | $0 | $0 | $0 |
| Manual snapshot (20GB, 1x/tjedan) | $0 | $1.90/mj | $1.90/mj |
| mysqldump S3 Standard (7 dana) | $0 | $0.16/mj | $0.16/mj |
| mysqldump S3 Glacier IR (dan 7-30) | $0 | $0.05/mj | $0.05/mj |
| **Ukupno backup** | **$0** | **~$2.11/mj** | **~$2.11/mj** |

> Cijene za `eu-west-1`, Maj 2025. Manual snapshot: $0.095/GB/mj. S3 Standard: $0.023/GB/mj. S3 Glacier IR: $0.0100/GB/mj.
