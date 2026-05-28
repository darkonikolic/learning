# 05 — RDS Snapshot alternativa

## Kada mysqldump nije dovoljan

mysqldump je logički dump — eksportira podatke kao SQL naredbe. Performanse ne skaliraju linearno s veličinom baze: svaki red mora biti serijaliziran u tekst, svaki INSERT parsiran i izvršen na target strani.

Pragmatični prag za project-A: kada jedna od ovih situacija postane istinita:

| Situacija | Prag | Akcija |
|---|---|---|
| Dump + upload traje | > 10 min | Razmotriti snapshot |
| Restore traje | > 20 min | Razmotriti snapshot |
| Review app kreiranje | > 15 min ukupno | Snapshot ili subset podataka |
| Baza veličina | > 5 GB | Snapshot + subset za lokalni dev |

---

## RDS Snapshot: kako radi internally

Za razliku od mysqldump (logički dump), RDS snapshot je **fizički snapshot** AWS EBS volumena na kojem se nalazi RDS instanca.

AWS implementacija:
1. Pauses I/O na kratko (milisekunde) da dobije konzistentnu točku
2. Kreira EBS snapshot — to je Copy-on-Write kopija storage blokova
3. I/O se nastavlja odmah; snapshot se dovršava asinkrono u pozadini

Rezultat: snapshot od 100GB instanca se "kreira" za < 1 minutu (AWS API kaže completed brzo), ali restore iz tog snapshot-a traje duže jer mora materijalizirati sve blokove.

### Restore performanse

RDS restore iz snapshot-a ima jedan specifičan AWS optimizacijski mehanizam: **lazy loading**. Nova instanca može biti available za pristup dok se podaci još prenose u pozadini. Pristup blokovima koji još nisu preneseni triggerira njihovo hitno učitavanje.

Praktično: nova RDS instanca iz 50GB snapshot-a može biti u stanju `available` za ~10-15 minuta, ali performanse su degradirane prvih sat-dva dok se podaci lazy-load-aju. Za CI pipeline koji odmah pokušava restore-ovati, ovo može izgledati kao spor restore ali je zapravo normalan initial warmup.

Rješenje: **koristiti `--no-restore-to-point-in-time`** i, ako je moguće, "pogrijati" instancu read operacijom prije nego aplikacija starta.

---

## RDS Snapshot workflow: korak po korak

### Korak 1: Kreiraj snapshot iz prod

```bash
# Atomično imenovanje — datum u nazivu
SNAPSHOT_ID="prod-pre-deploy-$(date +%Y%m%d-%H%M)"

aws rds create-db-snapshot \
  --db-instance-identifier project-a-prod \
  --db-snapshot-identifier "$SNAPSHOT_ID" \
  --tags Key=Environment,Value=prod Key=CreatedBy,Value=pipeline

echo "Snapshot ID: $SNAPSHOT_ID"
```

### Korak 2: Čekaj completion

```bash
# AWS CLI wait command — polling dok snapshot ne bude available
aws rds wait db-snapshot-completed \
  --db-snapshot-identifier "$SNAPSHOT_ID"

# Timeout: wait commands imaju default timeout od 30 minuta (15 pokušaja, 2 min interval)
# Za veliku bazu, povećaj:
aws rds wait db-snapshot-completed \
  --db-snapshot-identifier "$SNAPSHOT_ID" \
  --waiter-config MaxAttempts=60,Delay=60  # 60 minuta
```

### Korak 3: Restore u novi env

```bash
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier "project-a-dev" \
  --db-snapshot-identifier "$SNAPSHOT_ID" \
  --db-instance-class db.t3.medium \
  --db-subnet-group-name project-a-subnet-group \
  --vpc-security-group-ids sg-xxxxxxxxxx \
  --no-multi-az \
  --no-publicly-accessible \
  --tags Key=Environment,Value=dev

# Čekaj da instanca bude available
aws rds wait db-instance-available \
  --db-instance-identifier "project-a-dev"

# Dohvati novi endpoint
NEW_ENDPOINT=$(aws rds describe-db-instances \
  --db-instance-identifier "project-a-dev" \
  --query 'DBInstances[0].Endpoint.Address' \
  --output text)

echo "New dev RDS endpoint: $NEW_ENDPOINT"
```

---

## Problem: nova instanca = novi endpoint

Ovo je najveći operacijski izazov sa snapshot workflow-om. Svaki put kada restore-uješ iz snapshot-a, AWS kreira **novu RDS instancu** s **novim DNS endpointom**. Aplikacija i Terraform moraju biti svjesni novog endpoint-a.

### Rješenje A: Terraform `snapshot_identifier` parametar

Elegantan pristup — Terraform sam upravljava restore-om:

```hcl
resource "aws_db_instance" "dev" {
  identifier             = "project-a-dev"
  instance_class         = "db.t3.medium"
  engine                 = "mysql"
  engine_version         = "8.0"

  # Ako je ova varijabla postavljena, Terraform restore-uje iz snapshot-a
  # Ako je null/empty, kreira praznu instancu
  snapshot_identifier    = var.restore_from_snapshot

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  # IMPORTANT: skip final snapshot pri destroy-u review app-a
  skip_final_snapshot    = var.environment != "prod"

  tags = {
    Environment = var.environment
  }
}
```

```hcl
# variables.tf
variable "restore_from_snapshot" {
  description = "RDS snapshot identifier to restore from. Leave null for fresh instance."
  type        = string
  default     = null
}
```

Pipeline postavi varijablu pri kreiranju novog env-a:

```bash
terraform apply \
  -var="restore_from_snapshot=prod-pre-deploy-20240115-0200" \
  -var="environment=dev"
```

**Ponašanje:** Terraform kreira novu RDS instancu iz snapshot-a. Endpoint je deterministan jer je `identifier` fiksan (`project-a-dev`) — DNS `project-a-dev.xxxxxxxxxx.eu-west-1.rds.amazonaws.com` je uvijek isti sve dok instanca postoji.

### Rješenje B: Data source za postojeći snapshot

Ako nema hardcoded snapshot ID-a, koristi Terraform data source da pronađe najnoviji:

```hcl
data "aws_db_snapshot" "latest_prod" {
  db_instance_identifier = "project-a-prod"
  most_recent            = true
  snapshot_type          = "manual"  # ili "automated"
}

resource "aws_db_instance" "dev" {
  snapshot_identifier = data.aws_db_snapshot.latest_prod.id
  ...
}
```

Ovo automatski uzima najnoviji manual snapshot prod instance — bez hardcoded ID-a u pipeline-u.

---

## Cross-region snapshot: DR scenario

Za disaster recovery, snapshot treba biti u drugoj AWS regiji:

```bash
# Kopiraj snapshot u DR regiju
aws rds copy-db-snapshot \
  --source-db-snapshot-identifier "arn:aws:rds:eu-west-1:123456789:snapshot:prod-20240115" \
  --target-db-snapshot-identifier "prod-20240115-dr" \
  --region eu-central-1 \
  --source-region eu-west-1
```

Terraform varijanta:

```hcl
resource "aws_db_snapshot_copy" "dr" {
  source_db_snapshot_identifier = aws_db_instance.prod.latest_restorable_time
  target_db_snapshot_identifier = "prod-dr-${formatdate("YYYYMMDD", timestamp())}"
  target_db_instance_identifier = "project-a-prod-dr"
  
  provider = aws.dr_region  # aws provider konfiguriran za DR regiju
}
```

---

## Cost: RDS Snapshot storage

AWS naplaćuje snapshot storage po GB/mj:
- **Same region:** ~$0.095/GB/mj (us-east-1, eu-west-1)
- **Cross-region copy:** isti rate + data transfer troškovi

Za project-A (20GB baza), 30 snapshota:
```
20 GB × 30 snapshots × $0.095 = $57/mj
```

Uz deduplication (EBS snapshot su incremental nakon prvog), stvarna naplaćena veličina je manja — samo izmijenjeni blokovi se naplaćuju po snapshot-u.

### S3 Lifecycle policy za mysqldump fajlove

Paralelno, dump fajlovi u S3:

```hcl
resource "aws_s3_bucket_lifecycle_configuration" "db_dumps" {
  bucket = aws_s3_bucket.state.id

  rule {
    id     = "db-dumps-retention"
    status = "Enabled"

    filter {
      prefix = "db-dumps/"
    }

    expiration {
      days = 30  # čuvaj dump fajlove 30 dana
    }

    transition {
      days          = 7
      storage_class = "STANDARD_IA"  # jeftiniji storage nakon 7 dana
    }
  }
}
```

### RDS Automated Backup vs Manual Snapshot

RDS ima i **automated backups** (retention window, point-in-time recovery) koji su besplatni do veličine same instance. Manual snapshots (koje mi kreiramo) se naplaćuju zasebno.

Za pipeline: koristimo manual snapshots jer imamo kontrolu nad retention-om i možemo ih referirati po imenu. Automated backups su za disaster recovery, ne za env provisioning.

---

## Automatski snapshot pri Terraform apply za novi env

Terraform `null_resource` + `local-exec` za kreiranje snapshot-a kao preduvjet:

```hcl
resource "null_resource" "prod_snapshot_before_restore" {
  # Pokreni samo kad se kreira nova dev instanca (ne pri update-u)
  triggers = {
    db_instance_id = "project-a-dev-${var.review_app_id}"
  }

  provisioner "local-exec" {
    command = <<-EOT
      SNAPSHOT_ID="review-${var.review_app_id}-$(date +%Y%m%d%H%M)"
      aws rds create-db-snapshot \
        --db-instance-identifier project-a-prod \
        --db-snapshot-identifier "$SNAPSHOT_ID"
      aws rds wait db-snapshot-completed \
        --db-snapshot-identifier "$SNAPSHOT_ID"
      echo "$SNAPSHOT_ID" > /tmp/snapshot_id.txt
    EOT
  }
}

resource "aws_db_instance" "review" {
  depends_on = [null_resource.prod_snapshot_before_restore]

  identifier          = "project-a-review-${var.review_app_id}"
  snapshot_identifier = file("/tmp/snapshot_id.txt")
  ...
}
```

Upozorenje: `local-exec` radi na Terraform runner mašini. `/tmp/snapshot_id.txt` je privremeni fajl — u CI kontekstu ovo funkcionira jer je runner efemeralan po joba. U produkcijskom Terraform Enterprise/Cloud setup-u, bolji pristup je koristiti external data source ili poseban pipeline korak.

---

## Usporedba: mysqldump vs RDS Snapshot

| Kriterij | mysqldump | RDS Snapshot |
|---|---|---|
| Veličina baze | < 5 GB | > 5 GB |
| Lokalni dev | Da (Docker) | Ne (samo AWS) |
| Brzina kreiranja | Sporo (linearno s veličinom) | Brzo (< 1 min) |
| Brzina restore-a | Sporo | Brzo (ali lazy load warmup) |
| Portabilnost | MySQL-kompatibilni target | Samo AWS RDS |
| Granularnost | Specifične tabele, schema subset | Cijela instanca |
| Cost | S3 storage (~$0.023/GB/mj) | EBS snapshot (~$0.095/GB/mj) |
| Terraform integracija | Ručni koraci ili null_resource | Native `snapshot_identifier` |
| Schema migracije | Primijeni nakon restore-a | Primijeni nakon restore-a |

Za project-A: ostajemo na mysqldump dok baza ne preraste 5GB. Snapshot workflow dokumentiramo sad da ne budemo iznenađeni kad dođe taj trenutak.
