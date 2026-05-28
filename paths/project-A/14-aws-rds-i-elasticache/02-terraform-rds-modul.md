# 02 — Terraform RDS Modul

## Struktura Modula

```
terraform/
├── modules/
│   └── rds/
│       ├── main.tf
│       ├── variables.tf
│       ├── outputs.tf
│       └── locals.tf
└── environments/
    ├── dev/
    │   └── main.tf   (poziva modul s dev varijablama)
    └── prod/
        └── main.tf   (poziva modul s prod varijablama)
```

---

## `terraform/modules/rds/variables.tf`

```hcl
variable "env_name" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "instance_class" {
  description = "RDS instance class"
  type        = string
  # dev: db.t3.small, staging: db.t3.medium, prod: db.t3.medium ili db.r6g.large
}

variable "allocated_storage" {
  description = "Initial allocated storage in GB"
  type        = number
  default     = 20
}

variable "max_allocated_storage" {
  description = "Maximum storage for autoscaling (0 = disabled)"
  type        = number
  default     = 100
}

variable "master_username" {
  description = "Master DB username"
  type        = string
  default     = "admin"
}

variable "db_name" {
  description = "Initial database name"
  type        = string
  default     = "project_a"
}

variable "multi_az" {
  description = "Enable Multi-AZ deployment"
  type        = bool
  default     = false
  # dev = false, staging = false, prod = true
}

variable "create_replica" {
  description = "Create read replica"
  type        = bool
  default     = false
  # prod = true
}

variable "backup_retention_period" {
  description = "Days to retain automated backups"
  type        = number
  default     = 7
  # prod: 30
}

variable "backup_window" {
  description = "Preferred backup window (UTC)"
  type        = string
  default     = "03:00-04:00"
}

variable "maintenance_window" {
  description = "Preferred maintenance window"
  type        = string
  default     = "Sun:04:00-Sun:05:00"
}

variable "apply_immediately" {
  description = "Apply changes immediately or during maintenance window"
  type        = bool
  default     = false
  # Expert: false za prod (čeka maintenance window), true za dev (brže iteracije)
}

variable "deletion_protection" {
  description = "Enable deletion protection"
  type        = bool
  default     = false
  # prod = true — Terraform destroy će failovati ako ne isključiš ručno
}

variable "private_subnet_ids" {
  description = "List of private subnet IDs for RDS subnet group"
  type        = list(string)
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "eks_worker_security_group_id" {
  description = "EKS worker nodes security group ID (allowed to connect to RDS)"
  type        = string
}

variable "tags" {
  description = "Common tags"
  type        = map(string)
  default     = {}
}
```

---

## `terraform/modules/rds/locals.tf`

```hcl
locals {
  name_prefix = "project-a-${var.env_name}"

  common_tags = merge(var.tags, {
    Module      = "rds"
    Environment = var.env_name
    ManagedBy   = "terraform"
  })

  # Parameter group settings koje se razlikuju po instanci
  # innodb_buffer_pool_size kao % RAM-a — isti formula, AWS zamjeni {DBInstanceClassMemory}
  buffer_pool_size = "{DBInstanceClassMemory*3/4}"
}
```

---

## `terraform/modules/rds/main.tf`

```hcl
# ─────────────────────────────────────────────────────────────────────────────
# Subnet Group — RDS mora biti u private subnets
# ─────────────────────────────────────────────────────────────────────────────
resource "aws_db_subnet_group" "this" {
  name       = "${local.name_prefix}-rds"
  subnet_ids = var.private_subnet_ids

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-rds-subnet-group"
  })
}

# ─────────────────────────────────────────────────────────────────────────────
# Parameter Group
# ─────────────────────────────────────────────────────────────────────────────
resource "aws_db_parameter_group" "mysql8" {
  family = "mysql8.0"
  name   = "${local.name_prefix}-mysql8"

  parameter {
    name  = "innodb_buffer_pool_size"
    value = local.buffer_pool_size
  }

  parameter {
    name  = "max_connections"
    value = "200"
  }

  parameter {
    name  = "slow_query_log"
    value = "1"
  }

  parameter {
    name  = "long_query_time"
    value = "1"
  }

  parameter {
    name  = "log_output"
    value = "FILE"
  }

  parameter {
    name  = "character_set_server"
    value = "utf8mb4"
  }

  parameter {
    name  = "collation_server"
    value = "utf8mb4_unicode_ci"
  }

  parameter {
    name  = "time_zone"
    value = "UTC"
  }

  parameter {
    name  = "innodb_flush_log_at_trx_commit"
    value = "1"
  }

  tags = local.common_tags

  lifecycle {
    create_before_destroy = true
    # Neophodan zbog: stari parameter group ostaje vezan za instancu dok se nova ne kreira
  }
}

# ─────────────────────────────────────────────────────────────────────────────
# Security Group
# ─────────────────────────────────────────────────────────────────────────────
resource "aws_security_group" "rds" {
  name        = "${local.name_prefix}-rds"
  description = "RDS MySQL access from EKS workers only"
  vpc_id      = var.vpc_id

  ingress {
    description     = "MySQL from EKS worker nodes"
    from_port       = 3306
    to_port         = 3306
    protocol        = "tcp"
    security_groups = [var.eks_worker_security_group_id]
    # Expert: ne koristi cidr_blocks za EKS pod CIDR — pod IPs su nestabilni
    # Referenciraj security group EKS worker node-ova
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-rds-sg"
  })
}

# ─────────────────────────────────────────────────────────────────────────────
# Secrets Manager — master password
# ─────────────────────────────────────────────────────────────────────────────
resource "random_password" "master" {
  length           = 32
  special          = true
  override_special = "!#$%^&*()-_=+[]{}|;:,.<>?"
}

resource "aws_secretsmanager_secret" "rds_master" {
  name                    = "${local.name_prefix}/rds/master"
  description             = "RDS master credentials for ${var.env_name}"
  recovery_window_in_days = var.env_name == "prod" ? 30 : 0
  # prod: 30 dana recovery window (zaštita od accidental delete)
  # dev/staging: 0 = immediate delete (brže iteracije)

  tags = local.common_tags
}

resource "aws_secretsmanager_secret_version" "rds_master" {
  secret_id = aws_secretsmanager_secret.rds_master.id

  secret_string = jsonencode({
    username = var.master_username
    password = random_password.master.result
    host     = aws_db_instance.master.address
    port     = 3306
    dbname   = var.db_name
    # Go service koristi ovaj JSON direktno via External Secrets Operator
  })

  # Lifecycle: secret_string ne smije biti u planu kao "known after apply"
  # za buduće apply-e — koristi ignore_changes za host ako je rotacija odvojena
}

# ─────────────────────────────────────────────────────────────────────────────
# RDS Master Instance
# ─────────────────────────────────────────────────────────────────────────────
resource "aws_db_instance" "master" {
  identifier = "${local.name_prefix}-mysql-master"

  engine         = "mysql"
  engine_version = "8.0"
  instance_class = var.instance_class

  db_name  = var.db_name
  username = var.master_username
  password = random_password.master.result

  allocated_storage     = var.allocated_storage
  max_allocated_storage = var.max_allocated_storage
  # max_allocated_storage > 0 → Storage Autoscaling uključen
  # AWS automatski povećava storage u 10GB inkrementima kada slobodan prostor padne ispod 10%

  storage_type      = "gp3"
  storage_encrypted = true
  # gp3 je noviji i jeftiniji od gp2 za isti IOPS, uvijek koristi gp3

  multi_az            = var.multi_az
  db_subnet_group_name = aws_db_subnet_group.this.name

  vpc_security_group_ids = [aws_security_group.rds.id]
  parameter_group_name   = aws_db_parameter_group.mysql8.name

  backup_retention_period = var.backup_retention_period
  backup_window           = var.backup_window
  maintenance_window      = var.maintenance_window

  # Backup window i maintenance window NE SMIJU se preklapati
  # Terraform će javiti grešku ako se preklapaju

  auto_minor_version_upgrade  = true
  # Minor patch automatski u maintenance window
  # Major verzija: NE automatski (8.0 → 8.4 zahtijeva eksplicitnu akciju)

  deletion_protection = var.deletion_protection
  # prod: true — ne može se destroy-ati bez prethodnog ručnog disabla

  skip_final_snapshot = var.env_name != "prod"
  # prod: false → pravi final snapshot pri destroy-u (zaštita)
  # dev/staging: true → brže čišćenje okruženja

  final_snapshot_identifier = var.env_name == "prod" ? "${local.name_prefix}-final-snapshot" : null

  enabled_cloudwatch_logs_exports = ["slowquery", "error"]
  # Automatski export logova u CloudWatch Logs
  # Log grupe: /aws/rds/instance/{identifier}/slowquery

  monitoring_interval = var.env_name == "prod" ? 60 : 0
  # Enhanced Monitoring: 60s interval za prod, disable za dev
  # Zahtijeva monitoring_role_arn ako interval > 0
  monitoring_role_arn = var.env_name == "prod" ? aws_iam_role.rds_enhanced_monitoring[0].arn : null

  performance_insights_enabled          = var.env_name == "prod"
  performance_insights_retention_period = var.env_name == "prod" ? 7 : null
  # Performance Insights: 7 dana besplatno, 731 dana = $0.02/vCPU/hour

  apply_immediately = var.apply_immediately
  # KRITIČNO: false za prod
  # true → svaka Terraform promjena (parameter group, instance class) se odmah primjenjuje
  # false → čeka naredni maintenance window (nedjeljom 04:00-05:00 UTC)

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-mysql-master"
    Role = "master"
  })

  lifecycle {
    prevent_destroy = false
    # Postavi na true za prod u environments/prod/main.tf override-u
    # Ne možeš koristiti var.env_name == "prod" u lifecycle bloku (ne podržava expressions)

    ignore_changes = [
      password,
      # Nakon initijalnog kreiranja, password rotacija ide kroz Secrets Manager
      # Terraform ne treba pratiti password promjene
    ]
  }
}

# ─────────────────────────────────────────────────────────────────────────────
# Enhanced Monitoring IAM Role (samo za prod)
# ─────────────────────────────────────────────────────────────────────────────
resource "aws_iam_role" "rds_enhanced_monitoring" {
  count = var.env_name == "prod" ? 1 : 0
  name  = "${local.name_prefix}-rds-monitoring"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "monitoring.rds.amazonaws.com" }
    }]
  })

  managed_policy_arns = ["arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"]

  tags = local.common_tags
}

# ─────────────────────────────────────────────────────────────────────────────
# Read Replica (opcionalno, samo za prod)
# ─────────────────────────────────────────────────────────────────────────────
resource "aws_db_instance" "replica" {
  count = var.create_replica ? 1 : 0

  identifier = "${local.name_prefix}-mysql-replica"

  replicate_source_db = aws_db_instance.master.identifier
  # Ne treba specificirati engine, username, password — preuzima s mastera

  instance_class = var.instance_class

  # Replica mora biti u drugom AZ od mastera (za pravi rack diversity)
  availability_zone = data.aws_availability_zones.available.names[1]
  # Masters je u names[0] (Multi-AZ standby u names[1] interne, replica u names[1] eksplicitno)
  # Ovo osigurava da replica nije u istom AZ kao i master

  parameter_group_name   = aws_db_parameter_group.mysql8.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  storage_type      = "gp3"
  storage_encrypted = true

  # Replica ne treba backup (master ima)
  backup_retention_period = 0
  skip_final_snapshot     = true

  auto_minor_version_upgrade = true

  monitoring_interval = var.env_name == "prod" ? 60 : 0
  monitoring_role_arn = var.env_name == "prod" ? aws_iam_role.rds_enhanced_monitoring[0].arn : null

  apply_immediately = var.apply_immediately

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-mysql-replica"
    Role = "replica"
  })
}

data "aws_availability_zones" "available" {
  state = "available"
}
```

---

## `terraform/modules/rds/outputs.tf`

```hcl
output "master_endpoint" {
  description = "RDS master endpoint (write operations)"
  value       = aws_db_instance.master.address
  # Primjer: project-a-prod-mysql-master.abc123.eu-west-1.rds.amazonaws.com
}

output "replica_endpoint" {
  description = "RDS replica endpoint (read operations)"
  value       = var.create_replica ? aws_db_instance.replica[0].address : aws_db_instance.master.address
  # Fallback na master ako replica ne postoji (dev/staging)
}

output "master_port" {
  value = aws_db_instance.master.port
}

output "db_name" {
  value = aws_db_instance.master.db_name
}

output "secret_arn" {
  description = "Secrets Manager ARN za RDS credentials"
  value       = aws_secretsmanager_secret.rds_master.arn
}

output "security_group_id" {
  description = "RDS security group ID (za referenciranje iz drugih modula)"
  value       = aws_security_group.rds.id
}
```

---

## Pozivanje Modula po Okruženju

### `terraform/environments/dev/main.tf`

```hcl
module "rds" {
  source = "../../modules/rds"

  env_name        = "dev"
  instance_class  = "db.t3.small"
  allocated_storage = 20
  max_allocated_storage = 50

  multi_az        = false   # dev ne treba Multi-AZ
  create_replica  = false   # dev ne treba repliku
  backup_retention_period = 7

  apply_immediately  = true   # Dev: odmah primijeni promjene
  deletion_protection = false

  private_subnet_ids           = module.vpc.private_subnet_ids
  vpc_id                       = module.vpc.vpc_id
  eks_worker_security_group_id = module.eks.worker_security_group_id
}
```

### `terraform/environments/prod/main.tf`

```hcl
module "rds" {
  source = "../../modules/rds"

  env_name        = "prod"
  instance_class  = "db.t3.medium"
  allocated_storage = 50
  max_allocated_storage = 200

  multi_az        = true    # Obavezno za prod
  create_replica  = true    # Read scaling + DR opcija
  backup_retention_period = 30

  apply_immediately   = false  # Čekaj maintenance window
  deletion_protection = true   # Ne može se destroy-ati bez ručnog disable

  private_subnet_ids           = module.vpc.private_subnet_ids
  vpc_id                       = module.vpc.vpc_id
  eks_worker_security_group_id = module.eks.worker_security_group_id

  tags = {
    CostCenter  = "production"
    BackupTier  = "critical"
  }
}
```

### `prevent_destroy` za prod instance

Lifecycle blok ne podržava varijable. Rješenje — override u prod modulu:

```hcl
# terraform/environments/prod/rds_override.tf
# Ovaj fajl override-uje lifecycle za prod resources

# Napomena: lifecycle prevent_destroy ne može se kontrolisati varijablama
# Jedino rješenje je explicit override ili koristiti Terraform workspace guards

resource "null_resource" "prod_guard" {
  # Podsjetnik: prod RDS ima deletion_protection = true
  # Za destroy: aws rds modify-db-instance --db-instance-identifier project-a-prod-mysql-master --no-deletion-protection
  triggers = {
    reminder = "Disable deletion_protection before destroy in prod"
  }
}
```

**Expert alternativa** za `prevent_destroy`: S-Control Policy (SCP) na AWS Organization nivou koja zabranjuje `rds:DeleteDBInstance` bez MFA, neovisno o Terraformu.

---

## Workflow: Izmjena RDS u Produkciji

```bash
# 1. Provjeri šta će se promijeniti
terraform plan -var-file=prod.tfvars

# 2. Ako je apply_immediately = false, promjena ide u maintenance window
# Provjeri kada je naredni maintenance window:
aws rds describe-db-instances \
  --db-instance-identifier project-a-prod-mysql-master \
  --query 'DBInstances[0].PreferredMaintenanceWindow'

# 3. Za hitne promjene (security patch), može se forsirati immediate:
# Promijeni apply_immediately = true SAMO za taj apply, zatim vrati na false

# 4. Provjeri status promjene
aws rds describe-db-instances \
  --db-instance-identifier project-a-prod-mysql-master \
  --query 'DBInstances[0].PendingModifiedValues'
```
