# 05 — Backup i Restore Strategija

## RDS Automatski Backups

### Kako funkcionišu

RDS automatski backupi se rade u definisanom `backup_window` i zadržavaju se `backup_retention_period` dana.

- **Mehanizam**: Snapshot storage + transaction logs (binlog) → Point-in-time Recovery (PITR)
- **Granularnost PITR**: Do 5 minuta nazad (transaction logs se čuvaju kontinuirano)
- **Storage**: Backup storage u istom regionu, besplatno do veličine DB instanced (zatim se naplaćuje)

```
backup_retention_period:
  dev:     7 dana   (cost-effective, dovoljno za debugging)
  staging: 14 dana
  prod:    30 dana  (compliance requirement u većini organizacija)
```

### Backup Window konfiguracija

```
backup_window     = "03:00-04:00"   # UTC
maintenance_window = "Sun:04:00-Sun:05:00"  # Ne smije se preklapati s backup_window!
```

**Što se dešava za Multi-AZ tokom backup-a:**
- Backup se uzima sa standby instance — nema I/O impact na primary
- Za single-AZ instancu: kratki I/O suspension na početku snapshotiranja

### Provjera backup statusa

```bash
# Lista dostupnih automated backups
aws rds describe-db-instance-automated-backups \
  --db-instance-identifier project-a-prod-mysql-master \
  --query 'DBInstanceAutomatedBackups[*].{Status:Status,Period:RestorableTime}'

# Provjeri earliest restore time
aws rds describe-db-instances \
  --db-instance-identifier project-a-prod-mysql-master \
  --query 'DBInstances[0].{EarliestRestorableTime:EarliestRestorableTime,LatestRestorableTime:LatestRestorableTime}'
```

---

## Manual Snapshot: Kreiranje Prije Migracija

**Pravilo**: Svaka schema migracija u produkciji = manual snapshot PRIJE migracije.

```bash
# Kreiranje manual snapshot-a
aws rds create-db-snapshot \
  --db-instance-identifier project-a-prod-mysql-master \
  --db-snapshot-identifier project-a-prod-pre-migration-$(date +%Y%m%d-%H%M)

# Provjeri status snapshot-a (čekaj "available")
aws rds describe-db-snapshots \
  --db-snapshot-identifier project-a-prod-pre-migration-20240115-1430 \
  --query 'DBSnapshots[0].Status'

# Čekaj dok snapshot nije dostupan (može trajati 5-30 min za veliku bazu)
aws rds wait db-snapshot-available \
  --db-snapshot-identifier project-a-prod-pre-migration-20240115-1430
echo "Snapshot ready, proceeding with migration"
```

**Manual snapshots ne istječu** — za razliku od automated backups koji se brišu nakon retention periode. Eksplicitno ih obriši kada više nisu potrebni.

```bash
# Brisanje starog manual snapshot-a
aws rds delete-db-snapshot \
  --db-snapshot-identifier project-a-prod-pre-migration-20240101-0900
```

---

## Point-in-Time Restore (PITR)

### Kada koristiti PITR

- Accidental data delete ili UPDATE bez WHERE clause
- Softverski bug koji je korrumpovao podatke (i nije odmah uočen)
- Rollback migracije koja je prošla ali ostavila nekonzistentne podatke

### Kako izvršiti PITR

```bash
# Restore do specifičnog trenutka (5 min granularnost)
aws rds restore-db-instance-to-point-in-time \
  --source-db-instance-identifier project-a-prod-mysql-master \
  --target-db-instance-identifier project-a-prod-mysql-pitr-recovery \
  --restore-time 2024-01-15T14:30:00Z \
  --db-instance-class db.t3.medium \
  --db-subnet-group-name project-a-prod-rds \
  --vpc-security-group-ids sg-0123456789abcdef

# Provjeri status
aws rds describe-db-instances \
  --db-instance-identifier project-a-prod-mysql-pitr-recovery \
  --query 'DBInstances[0].DBInstanceStatus'
```

**Expert gotcha**: PITR kreira NOVU instancu — ne restore na postojeću. Implikacije:
1. Nova instanca dobija novi DNS endpoint
2. Aplikacija mora se rekonfigurirati da koristi novi endpoint
3. Stara (oštećena) instanca ostaje pokrenuta dok je eksplicitno ne obrišeš
4. Cijena: plaćaš obje instance dok traje recovery proces

**Recovery workflow:**

```
1. PITR → nova instanca (project-a-prod-mysql-pitr-recovery)
2. Provjeri podatke na novoj instanci (je li vraćeno ispravno stanje?)
3. Opcija A: Rename/swap endpointove (aplikacija restart)
4. Opcija B: mysqldump specifičnih tabela iz PITR instance → import u originalnu
5. Obriši PITR instancu kada recovery završi
```

Opcija B je češća za "surgical recovery" (vraćanje jedne tabele ili skupa podataka, a ne cijele baze).

---

## mysqldump: Aplikativni Backup

### Zašto mysqldump pored RDS snapshot-a

RDS snapshot je S3 binary format — ne možeš ga koristiti za:
- Import na non-RDS MySQL (lokalni dev, drugačiji cloud provider)
- Selektivni restore jedne tabele
- Schema comparison između okruženja
- Verzionisanje schema promjena u git-u

```bash
# Kompletni dump za portabilnost
mysqldump \
  -h $RDS_MASTER_ENDPOINT \
  -u admin \
  -p"$DB_PASS" \
  --single-transaction \        # InnoDB: consistent snapshot bez lock-a
  --routines \                  # Uključi stored procedures i functions
  --triggers \                  # Uključi triggere
  --events \                    # Uključi scheduled events
  --hex-blob \                  # BLOB kolone kao hex (safe za transport)
  --set-gtid-purged=OFF \        # Izbjegni GTID probleme pri importu na drugi server
  project_a \
  > backup_$(date +%Y%m%d_%H%M).sql

# Komprimirani dump (preporučeno za veće baze)
mysqldump \
  -h $RDS_MASTER_ENDPOINT \
  -u admin \
  -p"$DB_PASS" \
  --single-transaction \
  --routines --triggers \
  project_a | gzip > backup_$(date +%Y%m%d_%H%M).sql.gz
```

**Zašto `--single-transaction`?**
- Bez ove opcije: mysqldump radi `LOCK TABLES` što blokira write operacije za cijelo trajanje dump-a
- S `--single-transaction`: otvara jednu InnoDB transakciju → consistent snapshot bez lock-a
- Radi SAMO za InnoDB tabele. Za MyISAM (rijetko): lock je neizbježan

### Automatizovani backup Job u K8s

```yaml
# k8s/base/jobs/mysql-backup.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: mysql-backup
  namespace: project-a
spec:
  schedule: "0 2 * * *"   # Svaki dan u 02:00 UTC
  concurrencyPolicy: Forbid
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 1
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: OnFailure
          containers:
            - name: mysql-backup
              image: mysql:8.0
              command:
                - /bin/sh
                - -c
                - |
                  mysqldump \
                    -h $DB_MASTER_HOST \
                    -u $DB_USER \
                    -p"$DB_PASSWORD" \
                    --single-transaction \
                    --routines --triggers \
                    $DB_NAME | gzip > /backup/backup_$(date +%Y%m%d_%H%M).sql.gz
                  
                  # Upload na S3
                  aws s3 cp /backup/backup_$(date +%Y%m%d_%H%M).sql.gz \
                    s3://project-a-backups/mysql/$(date +%Y/%m)/
                  
                  echo "Backup completed"
              envFrom:
                - secretRef:
                    name: rds-credentials
              volumeMounts:
                - name: backup-storage
                  mountPath: /backup
          volumes:
            - name: backup-storage
              emptyDir: {}
```

---

## Cross-Environment Restore: Prod Snapshot → Staging

Korisno za: reprodukcija prod bug-a u staging-u, load testing s realnim podacima (uz obfuskaciju PII).

### Terraform: Kreiranje Instance iz Snapshot-a

```hcl
# terraform/environments/staging/rds_from_snapshot.tf
# Koristi se jednokratno kada treba restore prod snapshot u staging

variable "snapshot_identifier" {
  description = "Prod RDS snapshot ID za restore u staging"
  type        = string
  default     = ""
  # Primjer: "rds:project-a-prod-mysql-master-2024-01-15-14-30"
}

resource "aws_db_instance" "staging_from_snapshot" {
  count = var.snapshot_identifier != "" ? 1 : 0

  identifier            = "project-a-staging-mysql-master"
  snapshot_identifier   = var.snapshot_identifier
  # Terraform kreira novu instancu iz ovog snapshot-a

  instance_class        = "db.t3.medium"
  db_subnet_group_name  = aws_db_subnet_group.staging.name
  vpc_security_group_ids = [aws_security_group.rds_staging.id]
  parameter_group_name  = aws_db_parameter_group.mysql8_staging.name

  skip_final_snapshot = true
  apply_immediately   = true

  # VAŽNO: Password se mijenja nakon restore-a (ne koristimo prod password u staging!)
  password = random_password.staging_master.result

  tags = {
    Environment = "staging"
    RestoredFrom = var.snapshot_identifier
  }
}
```

```bash
# Workflow za prod → staging restore
# 1. Nađi dostupne prod snapshots
aws rds describe-db-snapshots \
  --db-instance-identifier project-a-prod-mysql-master \
  --query 'DBSnapshots[*].{ID:DBSnapshotIdentifier,Time:SnapshotCreateTime,Status:Status}' \
  --output table

# 2. Apply Terraform s snapshot ID-em
terraform apply \
  -var="snapshot_identifier=rds:project-a-prod-mysql-master-2024-01-15-14-30" \
  -target=aws_db_instance.staging_from_snapshot
```

**Post-restore obavezni koraci:**

```sql
-- Na staging instanci (nakon restore-a s prod snapshot-a):

-- 1. Promijeni lozinke (staging ne smije koristiti prod credentials)
ALTER USER 'admin'@'%' IDENTIFIED BY 'new_staging_password';

-- 2. Obfuskacija PII podataka (OBAVEZNO ako staging koriste developeri)
UPDATE users SET 
  email = CONCAT('user_', id, '@test.example.com'),
  phone = '0000000000',
  full_name = CONCAT('Test User ', id)
WHERE created_at > '2020-01-01';

-- 3. Provjeri da nema prod API ključeva, payment tokena, itd.
-- (specifično za aplikaciju)

-- 4. Reset sequences/auto_increment ako je potrebno
```

---

## Expert Gotcha: Snapshot Restore Kreira Novu Instancu

Ovo je fundamentalna razlika od tradicionalnih backup/restore sistema:

**Tradicionalni backup**: backup.sql → `mysql restore` → **ista** MySQL instanca, isti endpoint

**RDS snapshot restore**: snapshot → **nova** RDS instanca → **novi** DNS endpoint

```
STARA INSTANCA:
  project-a-prod-mysql-master.abc123.eu-west-1.rds.amazonaws.com  ← ostaje

NOVA INSTANCA (iz snapshot-a):
  project-a-prod-mysql-master-restored.xyz789.eu-west-1.rds.amazonaws.com  ← različit!
```

**Implikacije:**

1. **DNS/connection string** — aplikacija mora se rekonfigurirati (External Secrets update, pod restart)

2. **Secrets Manager** — treba ažurirati `host` vrijednost u secretu koji koristi External Secrets Operator

3. **Parameter Group** — nova instanca dobija default parameter group, ne custom. Mora se ručno promijeniti.

4. **Security Group** — nova instanca dobija default SG, ne naš custom SG. Mora se promijeniti.

5. **Subnet Group** — ako ne specificiraš, uzima default. Može završiti u public subnet!

6. **Multi-AZ** — restore iz snapshot-a je Single-AZ. Multi-AZ se mora ručno omogućiti.

**Checklist za svaki restore:**

```bash
# Nakon restore, provjeri konfiguraciju nove instance
aws rds describe-db-instances \
  --db-instance-identifier project-a-prod-mysql-master-restored \
  --query 'DBInstances[0].{
    MultiAZ:MultiAZ,
    ParameterGroup:DBParameterGroups[0].DBParameterGroupName,
    SecurityGroups:VpcSecurityGroups[*].VpcSecurityGroupId,
    SubnetGroup:DBSubnetGroup.DBSubnetGroupName,
    PubliclyAccessible:PubliclyAccessible
  }'
```

Svako od ovih polja mora biti ispravno prije nego što preusmjeriš aplikacijski traffic.
