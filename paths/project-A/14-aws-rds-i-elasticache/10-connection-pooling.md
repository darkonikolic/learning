# 10 — Connection Pooling: MySQL na Kubernetes

## Problem bez connection pooling-a

Svaki Go pod otvara vlastiti pool konekcija prema MySQL. Kad horizontalno skalaš:

```
10 pods × 10 conn = 100 MySQL konekcija    → OK
15 pods × 10 conn = 150 MySQL konekcija    → GRANICA (default max_connections=151)
20 pods × 10 conn = 200 MySQL konekcija    → "Too many connections" → app pada
```

MySQL default `max_connections = 151`. Pri 15+ podova aplikacija počinje odbijati konekcije
i vraća `ERROR 1040: Too many connections` — kompletni outage.

---

## Rješenja po prioritetu

### 1. Smanji pool size u aplikaciji (uvijek prvi korak)

```go
// pkg/database/mysql.go
func NewDB(dsn string) (*sql.DB, error) {
    db, err := sql.Open("mysql", dsn)
    if err != nil {
        return nil, fmt.Errorf("sql.Open: %w", err)
    }

    // Konzervativne vrijednosti za Kubernetes deployment
    db.SetMaxOpenConns(5)                  // Max 5 konekcija po pod-u
    db.SetMaxIdleConns(2)                  // 2 idle konekcija (ne zatvara odmah)
    db.SetConnMaxLifetime(5 * time.Minute) // Reciklira konekciju svakih 5 min
    db.SetConnMaxIdleTime(1 * time.Minute) // Zatvori idle konekciju nakon 1 min

    if err := db.PingContext(context.Background()); err != nil {
        return nil, fmt.Errorf("db.Ping: %w", err)
    }

    return db, nil
}

// Rezultat: 20 pods × 5 conn = 100 ukupno — sigurno ispod limita
```

**Zašto ove vrijednosti:**
- `MaxOpenConns(5)` — Go service je brz, 5 konekcija po podu je dovoljno
- `MaxIdleConns(2)` — Drži 2 vruće konekcije, ostale zatvori kad nema prometa
- `ConnMaxLifetime(5m)` — Sprječava "stale connection" probleme s MySQL `wait_timeout`

### 2. Povećaj max_connections na RDS (brz fix, ne riješava suštinu)

```hcl
# terraform/modules/rds/parameter_group.tf
resource "aws_db_parameter_group" "main" {
  name   = "project-a-${var.env}-mysql8"
  family = "mysql8.0"

  parameter {
    name         = "max_connections"
    value        = "500"
    apply_method = "immediate"
    # Napomena: svaka konekcija troši ~10MB RAM-a
    # db.t3.micro (1GB RAM): realnih max ~80-100 konekcija
    # db.t3.medium (4GB RAM): realnih max ~300-400 konekcija
  }

  parameter {
    name         = "wait_timeout"
    value        = "300" # Zatvori idle konekciju nakon 5 min (default je 8h!)
    apply_method = "immediate"
  }

  parameter {
    name         = "interactive_timeout"
    value        = "300"
    apply_method = "immediate"
  }

  tags = {
    Environment = var.env
    Project     = "project-a"
  }
}
```

### 3. AWS RDS Proxy (pravi fix za produkciju)

RDS Proxy sjedi između aplikacije i RDS instance. Pooluje konekcije:
1000 pods → RDS Proxy → 50 stvarnih DB konekcija.

```
App Pods ──→ RDS Proxy ──→ RDS Instance
(1000 konekcija)  (pooluje)  (50 konekcija)
```

```hcl
# terraform/modules/rds/proxy.tf

resource "aws_iam_role" "rds_proxy" {
  name = "project-a-${var.env}-rds-proxy"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "rds.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "rds_proxy_secrets" {
  name = "rds-proxy-secrets-access"
  role = aws_iam_role.rds_proxy.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["secretsmanager:GetSecretValue"]
      Resource = [var.db_credentials_secret_arn]
    }]
  })
}

resource "aws_db_proxy" "main" {
  name                   = "project-a-${var.env}"
  debug_logging          = false
  engine_family          = "MYSQL"
  idle_client_timeout    = 1800 # Zatvori idle app konekciju nakon 30 min
  require_tls            = true
  role_arn               = aws_iam_role.rds_proxy.arn
  vpc_security_group_ids = [var.rds_security_group_id]
  vpc_subnet_ids         = var.private_subnet_ids

  auth {
    auth_scheme = "SECRETS"
    iam_auth    = "DISABLED"
    secret_arn  = var.db_credentials_secret_arn
    # Secret mora biti u formatu: {"username":"...","password":"..."}
  }

  tags = {
    Environment = var.env
    Project     = "project-a"
  }
}

resource "aws_db_proxy_default_target_group" "main" {
  db_proxy_name = aws_db_proxy.main.name

  connection_pool_config {
    connection_borrow_timeout    = 120 # Čekaj max 2 min na slobodnu konekciju
    max_connections_percent      = 100 # Koristi 100% max_connections RDS instance
    max_idle_connections_percent = 50  # Drži max 50% idle konekcija u poolu
  }
}

resource "aws_db_proxy_target" "main" {
  db_proxy_name          = aws_db_proxy.main.name
  target_group_name      = aws_db_proxy_default_target_group.main.name
  db_instance_identifier = aws_db_instance.main.id
}

output "proxy_endpoint" {
  description = "RDS Proxy endpoint — koristi ovo u aplikaciji umjesto direktnog RDS endpointa"
  value       = aws_db_proxy.main.endpoint
}
```

```hcl
# terraform/modules/rds/variables.tf (relevantne varijable)
variable "db_credentials_secret_arn" {
  description = "ARN Secrets Manager sekreta sa DB kredencijalima"
  type        = string
}

variable "rds_security_group_id" {
  description = "Security group ID za RDS instancu"
  type        = string
}

variable "private_subnet_ids" {
  description = "Liste privatnih subnet ID-ova za RDS Proxy"
  type        = list(string)
}

variable "env" {
  description = "Environment: dev, staging, prod"
  type        = string
}
```

### Go DSN konfiguracija za RDS Proxy

```go
// pkg/database/mysql.go

func buildDSN() string {
    host     := os.Getenv("DB_HOST")     // RDS Proxy endpoint u prod, "mysql" u docker-compose
    port     := os.Getenv("DB_PORT")     // 3306
    user     := os.Getenv("DB_USER")
    password := os.Getenv("DB_PASSWORD")
    dbname   := os.Getenv("DB_NAME")

    // parseTime=true: automatski parsira MySQL DATETIME u time.Time
    // tls=true: obavezno za RDS Proxy (require_tls = true)
    tlsParam := "false"
    if os.Getenv("APP_ENV") != "development" {
        tlsParam = "true"
    }

    return fmt.Sprintf(
        "%s:%s@tcp(%s:%s)/%s?parseTime=true&tls=%s&timeout=10s&readTimeout=30s&writeTimeout=30s",
        user, password, host, port, dbname, tlsParam,
    )
}
```

```yaml
# helm/project-a/values.yaml (per-environment)
# values-prod.yaml
env:
  DB_HOST: "project-a-prod.proxy-abc123.eu-west-1.rds.amazonaws.com"  # RDS Proxy
  DB_PORT: "3306"
  APP_ENV: "production"

# values-dev.yaml
env:
  DB_HOST: "project-a-dev.abc123.eu-west-1.rds.amazonaws.com"  # Direktno na RDS (dev nema proxy)
  DB_PORT: "3306"
  APP_ENV: "development"
```

---

## Kada koristiti RDS Proxy

| Scenario | Preporuka |
|---|---|
| Dev: 1-3 pods | Skip proxy, povećaj `max_connections` |
| Staging: 3-10 pods | Pool size u app (5 conn/pod) dovoljan |
| Prod: 10+ pods ili auto-scaling | RDS Proxy |
| Lambda funkcije | Uvijek RDS Proxy (Lambda ne drži konekcije) |

## Cijena RDS Proxy

```
db.t3.micro RDS Proxy:   $0.015/sat = ~$11/mj
db.t3.medium RDS Proxy:  $0.030/sat = ~$22/mj
db.r5.large RDS Proxy:   $0.090/sat = ~$65/mj

Proxy se naplaćuje per vCPU RDS instance, ne po instancu proxy-ja.
```

---

## Monitoring konekcija

```bash
# Provjera broja aktivnih konekcija (direktno na DB):
kubectl exec -n project-a-prod deployment/go-service -- \
  sh -c 'mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" \
  -e "SHOW STATUS LIKE \"Threads_connected\"; SHOW STATUS LIKE \"Max_used_connections\";"'
```

```go
// Prometheus metrics za pool konekcija (dodaj u metrics handler):
func recordDBStats(db *sql.DB, reg prometheus.Registerer) {
    openConns := prometheus.NewGaugeFunc(prometheus.GaugeOpts{
        Name: "db_open_connections",
        Help: "Number of open DB connections",
    }, func() float64 { return float64(db.Stats().OpenConnections) })

    inUseConns := prometheus.NewGaugeFunc(prometheus.GaugeOpts{
        Name: "db_in_use_connections",
        Help: "Number of DB connections currently in use",
    }, func() float64 { return float64(db.Stats().InUse) })

    waitCount := prometheus.NewGaugeFunc(prometheus.GaugeOpts{
        Name: "db_wait_count_total",
        Help: "Total number of connections waited for",
    }, func() float64 { return float64(db.Stats().WaitCount) })

    reg.MustRegister(openConns, inUseConns, waitCount)
}
```

**CloudWatch alert:**
```hcl
# terraform/modules/monitoring/rds_alerts.tf
resource "aws_cloudwatch_metric_alarm" "db_connections_high" {
  alarm_name          = "project-a-${var.env}-db-connections-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "DatabaseConnections"
  namespace           = "AWS/RDS"
  period              = 60
  statistic           = "Maximum"
  threshold           = 400 # Alert pri 80% max_connections (500)

  dimensions = {
    DBInstanceIdentifier = var.db_instance_id
  }

  alarm_actions = [var.sns_alert_topic_arn]

  tags = {
    Environment = var.env
    Project     = "project-a"
  }
}
```

---

## Sažetak strategije

```
Development:  docker-compose MySQL ← direktna konekcija, bez pool-a
Staging:      RDS, max_connections=200, pool=3/pod, bez Proxy-ja
Production:   RDS, max_connections=500, pool=5/pod, RDS Proxy obavezan
```

Redosljed implementacije:
1. Postavi konzervativne pool vrijednosti u aplikaciji (`MaxOpenConns(5)`)
2. Poveći `max_connections` u RDS parameter grupi
3. Dodaj Prometheus metrics za `db_open_connections`
4. Kad prođeš 10 produkcionih podova — uključi RDS Proxy
