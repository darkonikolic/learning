# 07 — Cost Optimizacija

## Cost Breakdown po Okruženju

Cijene su aproksimativne za `eu-west-1` (Ireland), On-Demand, Maj 2025.

### Dev Okruženje (minimalna konfiguracija)

| Resurs | Konfiguracija | Cijena/mj |
|---|---|---|
| RDS db.t3.small Single-AZ | 2 vCPU, 2GB RAM, gp3 20GB | ~$27 |
| ElastiCache cache.t3.micro | 1 vCPU, 0.5GB RAM | ~$12 |
| RDS Storage (gp3, 20GB) | Uključeno u instancu za bazu | $0 (do 20GB) |
| RDS Backup Storage | 7 dana, ~20GB baza | ~$2 |
| **Total data layer (dev)** | | **~$41/mj** |

**Dev strategija: destroy overnight**

```hcl
# terraform/environments/dev/schedule.tf
# Iskoristi AWS Instance Scheduler ili custom Lambda

resource "aws_scheduler_schedule" "rds_stop_night" {
  name = "project-a-dev-rds-stop"

  flexible_time_window {
    mode = "OFF"
  }

  schedule_expression = "cron(0 20 * * ? *)"   # 20:00 UTC svaki dan
  schedule_expression_timezone = "Europe/Sarajevo"

  target {
    arn      = "arn:aws:scheduler:::aws-sdk:rds:stopDBInstance"
    role_arn = aws_iam_role.scheduler.arn

    input = jsonencode({
      DbInstanceIdentifier = "project-a-dev-mysql-master"
    })
  }
}

resource "aws_scheduler_schedule" "rds_start_morning" {
  name = "project-a-dev-rds-start"

  flexible_time_window {
    mode = "OFF"
  }

  schedule_expression = "cron(0 7 * * ? *)"    # 07:00 UTC radnim danom
  schedule_expression_timezone = "Europe/Sarajevo"

  target {
    arn      = "arn:aws:scheduler:::aws-sdk:rds:startDBInstance"
    role_arn = aws_iam_role.scheduler.arn

    input = jsonencode({
      DbInstanceIdentifier = "project-a-dev-mysql-master"
    })
  }
}
```

**Stop/start ušteda**: RDS zaustavljen 12h/dan × 7 dana = uštedimo ~50% instance troška.
Ali: RDS automatski startuje nakon 7 dana ako ga ne startujemo ručno (AWS ograničenje).

---

### Staging Okruženje

| Resurs | Konfiguracija | Cijena/mj |
|---|---|---|
| RDS db.t3.medium Multi-AZ | 2 vCPU, 4GB RAM, gp3 20GB | ~$130 |
| ElastiCache cache.t3.micro | 1 vCPU, 0.5GB RAM | ~$12 |
| RDS Backup Storage | 14 dana | ~$4 |
| **Total data layer (staging)** | | **~$146/mj** |

**Staging optimizacija**: Ako staging nema 24/7 load testing, razmatranje Single-AZ za staging:
- db.t3.medium Single-AZ: ~$65/mj vs Multi-AZ ~$130/mj
- Kompromis: Staging ne testira Multi-AZ failover ponašanje
- Preporuka: Koristi Multi-AZ u staging SAMO kada aktivno testiraš, inače Single-AZ

---

### Prod Okruženje

| Resurs | Konfiguracija | Cijena/mj |
|---|---|---|
| RDS db.t3.medium Multi-AZ (master) | 2 vCPU, 4GB RAM, gp3 50GB | ~$140 |
| RDS db.t3.medium Read Replica | 2 vCPU, 4GB RAM, gp3 50GB | ~$65 |
| ElastiCache cache.t3.small (primary+replica) | 2 vCPU, 1.37GB RAM | ~$48 |
| RDS Backup Storage | 30 dana, ~50GB baza | ~$15 |
| Enhanced Monitoring | 60s granularnost | ~$3 |
| Performance Insights | 7 dana (besplatno) | $0 |
| CloudWatch Alarms | 6 alarma | ~$2 |
| **Total data layer (prod)** | | **~$273/mj** |

**Realistična prod konfiguracija summary:**

```
RDS Master (Multi-AZ):        ~$140/mj
RDS Read Replica:              ~$65/mj
ElastiCache (2 node):          ~$48/mj
Backup + Monitoring:           ~$20/mj
─────────────────────────────────────
TOTAL:                        ~$273/mj
```

---

## Reserved Instances: 40% Uštede za Prod

Za produkcione resurse koji rade 24/7, Reserved Instances (RI) su standardna praksa.

### RDS Reserved Instances

```
On-Demand:  db.t3.medium Multi-AZ = ~$130/mj
1-godišnji RI (No Upfront): ~$78/mj  (40% ušteda)
1-godišnji RI (All Upfront): ~$70/mj + jednokratna uplata
3-godišnji RI (All Upfront): ~$52/mj + jednokratna uplata (60% ušteda)
```

**Kada kupiti RI:**
- Tek kada si siguran da će instanca biti ista tip/veličina 12+ mjeci
- Kupuj **After** što si optimizovao instance sizing (ne rezerviraj oversized instance)
- Počni s 1-godišnjim — lakše za upgrade ako baza naraste

```bash
# Provjeri trenutnu upotrebu instance tipa (je li konzistentna?)
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name CPUUtilization \
  --dimensions Name=DBInstanceIdentifier,Value=project-a-prod-mysql-master \
  --start-time $(date -d '30 days ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date +%Y-%m-%dT%H:%M:%S) \
  --period 86400 \
  --statistics Average,Maximum

# Ako Average CPU < 20% i Maximum < 60% kroz 30 dana:
# Razmisli da li je db.t3.medium oversized, ili je normalan pattern
```

### ElastiCache Reserved Nodes

```
On-Demand:  cache.t3.small = ~$24/mj per node × 2 = $48/mj
1-godišnji RI: ~$14/mj per node × 2 = $28/mj (42% ušteda)
```

---

## Instance Sizing: Kako Odabrati

### RDS Instance Class Guidelines

```
db.t3.small  (2GB RAM):  dev/poc, < 50 concurrent connections
db.t3.medium (4GB RAM):  small prod, 50-150 connections, < 1000 queries/sec
db.t3.large  (8GB RAM):  medium prod, 150-300 connections
db.r6g.large (16GB RAM): large prod, write-heavy workloads, > 1000 queries/sec
db.r6g.xlarge (32GB RAM): high performance, analytics queries
```

**Pravilo**: InnoDB buffer pool veličina (75% RAM) treba da stane cjelokupni "hot dataset" (frequently accessed data). Ako database ima 10GB podataka ali samo 2GB se aktivno koristi — db.t3.medium (4GB × 75% = 3GB buffer pool) je dovoljan.

### Provjera pravog sizing-a

```sql
-- Koliko working seta stane u buffer pool?
SELECT
  (SELECT variable_value FROM information_schema.global_status
   WHERE variable_name = 'Innodb_buffer_pool_pages_total') AS total_pages,
  (SELECT variable_value FROM information_schema.global_status
   WHERE variable_name = 'Innodb_buffer_pool_pages_free') AS free_pages,
  ROUND(
    (1 - (
      (SELECT variable_value FROM information_schema.global_status WHERE variable_name = 'Innodb_buffer_pool_pages_free') /
      (SELECT variable_value FROM information_schema.global_status WHERE variable_name = 'Innodb_buffer_pool_pages_total')
    )) * 100, 2
  ) AS buffer_pool_fill_pct;

-- Ako je fill_pct > 95% → buffer pool je premalen, razmatranje upgrada
-- Ako je fill_pct < 50% → možda je instance prevelika
```

---

## Aurora Serverless v2: Kada Ima Smisla

### Šta je Aurora Serverless v2

Aurora Serverless v2 automatski skalira kapacitet između minimalnog i maksimalnog ACU (Aurora Capacity Unit):
- 1 ACU = ~2GB RAM
- Skalira se u sekundama (za razliku od v1 koji je imao "pause" i hladni start)
- Naplaćuje se po sekundi za stvarnu upotrebu

### Cost Comparison

```
Aurora Serverless v2:
  Minimum: 0.5 ACU = ~$36/mj (uvijek naplaćuje minimum)
  Maximum: 8 ACU = ~$580/mj (peak load)
  Prosječna upotreba 2 ACU × $0.12/ACU/h = ~$87/mj

RDS db.t3.medium:
  Fiksno: ~$65/mj (Single-AZ) ili ~$130/mj (Multi-AZ)
```

### Kada Aurora Serverless v2 IMA smisla

1. **Neravnomjeran workload** — aplikacija ima veliku razliku između peak i off-peak (npr. 100x više trafficka radnim danom)
2. **Dev/staging okruženja** s rijetkom upotrebom (0.5 ACU minimum < fiksna RDS cijena)
3. **Startups** koji ne znaju kolika je baza potrebna — elastic scaling bez over-provisioning
4. **Batch processing** — kratki bursts heavy write workload-a, onda tišina

### Kada Aurora Serverless v2 NEMA smisla (naš slučaj)

1. **Stabilan workload** — ako znamo da imamo ~100 QPS konstantno, fiksna instanca je predvidljivija i jeftinija
2. **Latencija skaliranja** — iako je brže od v1, skaliranje nije instantno. Iznenadni traffic spike može kratko povući visoku latenciju
3. **Cijena na prod peaked workloads** — Aurora I/O cijena je viša od gp3 storage I/O
4. **Vendor lock-in** — Aurora je AWS proprietary, mysqldump kompatibilnost postoji ali edge cases se pojavljuju

### Aurora vs RDS MySQL: Tehničke razlike

| Aspekt | RDS MySQL 8.0 | Aurora MySQL |
|---|---|---|
| Storage | EBS (gp3) | Shared distributed storage (6-way replication) |
| Failover | ~60s DNS switch | ~30s (writer failover), ~10s (reader) |
| Read Replicas | Max 5 (cross-region) | Max 15 (in-region), Global Database |
| PITR granularnost | 5 min | 1 sekunda (Aurora Backtrack) |
| Max storage | 64TB | 128TB (auto-scaling) |
| Replication | Async binlog | Quorum-based storage layer |
| Cost premium | Baseline | +20-30% viša cijena instance |

**Zaključak za naš projekt**: RDS MySQL 8.0 s gp3 storage je optimalan izbor. Aurora bi se razmatrala ako:
- Narast na > 5 read replicas
- Trebamo < 30s failover (terapeutski critical systems)
- Baza naraste > 10TB
- Workload postane ekstremno spiky (Aurora Serverless v2)

---

## Cost Dashboard: Terraform za AWS Cost Allocation Tags

```hcl
# Svi resursi moraju imati konzistentne tagove za cost allocation

locals {
  cost_tags = {
    Project     = "project-a"
    Environment = var.env_name
    Component   = "data-layer"
    ManagedBy   = "terraform"
    CostCenter  = var.env_name == "prod" ? "production" : "development"
  }
}

# U AWS Cost Explorer, filtriraj po Environment = prod/dev/staging
# da vidiš trošak po okruženju
```

### AWS Budgets Alert

```hcl
resource "aws_budgets_budget" "rds_monthly" {
  name         = "project-a-${var.env_name}-rds-monthly"
  budget_type  = "COST"
  limit_amount = var.env_name == "prod" ? "350" : "60"
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  cost_filters = {
    Service = ["Amazon Relational Database Service", "Amazon ElastiCache"]
    TagKeyValue = ["project$project-a", "environment$${var.env_name}"]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 80
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.alert_email]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "FORECASTED"   # Prognozovano prekoračenje
    subscriber_email_addresses = [var.alert_email]
  }
}
```

---

## Rezime: Trošak po Okruženju

```
┌─────────────────────────────────────────────────────────────────┐
│                    Monthly Cost Summary                          │
├──────────────────┬────────────────┬─────────────────────────────┤
│ Environment      │ On-Demand/mj   │ Nakon RI (1yr, prod only)   │
├──────────────────┼────────────────┼─────────────────────────────┤
│ Dev              │ ~$41           │ N/A (stop/start optimizovan) │
│ Staging          │ ~$146          │ N/A (možda Single-AZ: ~$77) │
│ Prod             │ ~$273          │ ~$165 (40% RI ušteda)        │
├──────────────────┼────────────────┼─────────────────────────────┤
│ TOTAL (3 env)    │ ~$460/mj       │ ~$283/mj (RI na prod)        │
└──────────────────┴────────────────┴─────────────────────────────┘

Godišnja ušteda s RI na prod: ($273 - $165) × 12 = ~$1,296/godišnje
```

**Optimizacijski prioriteti:**
1. Stop/start dev instanci overnight (odmah, besplatno)
2. Provjeri da je dev Single-AZ bez replike (odmah)
3. Kupi 1-godišnje RI za prod nakon 1-2 mjeseca operacije (znaj pattern)
4. Razmisli Single-AZ za staging ako nema HA testing potrebe
