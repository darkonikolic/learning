# 03 — RDS Stop/Start Bez Gubitka Podataka

**Kada koristiti:** Produkcijsko okruženje, kratka pauza (noć, vikend).
Podaci ostaju netaknuti. Plaćaš samo storage dok je RDS stopped.

---

## Osnove: Šta znači "stopped" RDS

AWS RDS Stop zaustavlja database engine. Instance ostaje u AWS-u sa svim podacima.
Dok je stopped:
- Podaci su sigurni (EBS volume ne briše se)
- Endpoint ostaje isti (DNS se ne mijenja)
- Naplaćuje se samo storage
- Instance se **automatski starta nakon 7 dana** — AWS ograničenje, ne može se promijeniti

---

## Stop RDS Instance

```bash
# Stop RDS
aws rds stop-db-instance \
  --db-instance-identifier project-a-prod

# Provjeri status (asinkrona operacija, traje 1-2 minute)
echo "Waiting for RDS to stop..."
aws rds wait db-instance-stopped \
  --db-instance-identifier project-a-prod

echo "RDS status:"
aws rds describe-db-instances \
  --db-instance-identifier project-a-prod \
  --query 'DBInstances[0].{Status:DBInstanceStatus,Class:DBInstanceClass}' \
  --output table

echo "Billing: only storage (~\$2.30/mj for 20GB gp3)"
```

## Stop ElastiCache (Redis)

```bash
# ElastiCache Serverless — ne podržava stop, moraš delete/create
# ElastiCache Cluster Mode (Replication Group) — podržava stop od 2023
aws elasticache stop-replication-group \
  --replication-group-id project-a-prod

# Provjeri status
aws elasticache describe-replication-groups \
  --replication-group-id project-a-prod \
  --query 'ReplicationGroups[0].Status' \
  --output text
```

---

## Start RDS Instance

```bash
# Start RDS
aws rds start-db-instance \
  --db-instance-identifier project-a-prod

echo "Waiting for RDS to be available (3-5 minutes)..."
aws rds wait db-instance-available \
  --db-instance-identifier project-a-prod

echo "RDS endpoint:"
aws rds describe-db-instances \
  --db-instance-identifier project-a-prod \
  --query 'DBInstances[0].Endpoint.Address' \
  --output text

# Start ElastiCache
aws elasticache start-replication-group \
  --replication-group-id project-a-prod
```

---

## Kritično: AWS 7-Dnevni Limit

**Problem:** AWS automatski starta stopped RDS instance nakon 7 dana.
Ako te zanimaju troškovi, ovo ti uništi plan jer instance počinje koštati opet.

**Rješenje:** Lambda koja re-stopuje RDS svakih 6 dana (prije AWS 7-dnevnog limita).

### Terraform: Auto-Stop Lambda

```hcl
# terraform/modules/rds/auto-stop.tf

locals {
  lambda_function_name = "project-a-${var.env}-rds-auto-stop"
}

# ─── IAM Role za Lambda ────────────────────────────────────────────────────
resource "aws_iam_role" "lambda_rds_stop" {
  name = "project-a-${var.env}-lambda-rds-stop"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "lambda_rds_stop" {
  name = "rds-stop-policy"
  role = aws_iam_role.lambda_rds_stop.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["rds:StopDBInstance", "rds:DescribeDBInstances"]
        Resource = "arn:aws:rds:${var.region}:${data.aws_caller_identity.current.account_id}:db:${var.db_instance_id}"
      },
      {
        Effect   = "Allow"
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

data "aws_caller_identity" "current" {}

# ─── Lambda source code ────────────────────────────────────────────────────
data "archive_file" "rds_stop_lambda" {
  type        = "zip"
  output_path = "/tmp/rds_stop_${var.env}.zip"

  source {
    content  = <<-PYTHON
import boto3
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    rds = boto3.client('rds')
    instance_id = os.environ['DB_INSTANCE_ID']

    try:
        response = rds.describe_db_instances(DBInstanceIdentifier=instance_id)
        status = response['DBInstances'][0]['DBInstanceStatus']
        logger.info(f"Current status of {instance_id}: {status}")

        if status == 'available':
            rds.stop_db_instance(DBInstanceIdentifier=instance_id)
            logger.info(f"Stopped {instance_id}")
            return {'status': 'stopped', 'instance': instance_id}
        elif status == 'stopped':
            logger.info(f"{instance_id} is already stopped")
            return {'status': 'already_stopped', 'instance': instance_id}
        else:
            logger.warning(f"{instance_id} is in state {status}, cannot stop now")
            return {'status': 'skipped', 'instance': instance_id, 'reason': status}

    except Exception as e:
        logger.error(f"Error stopping {instance_id}: {str(e)}")
        raise
PYTHON
    filename = "index.py"
  }
}

# ─── Lambda Function ───────────────────────────────────────────────────────
resource "aws_lambda_function" "rds_stop" {
  function_name = local.lambda_function_name
  runtime       = "python3.12"
  handler       = "index.handler"
  role          = aws_iam_role.lambda_rds_stop.arn
  filename      = data.archive_file.rds_stop_lambda.output_path
  timeout       = 30

  source_code_hash = data.archive_file.rds_stop_lambda.output_base64sha256

  environment {
    variables = {
      DB_INSTANCE_ID = var.db_instance_id
    }
  }

  tags = {
    Environment = var.env
    Project     = "project-a"
  }
}

# ─── CloudWatch Event Rule (svaki 6 dana) ─────────────────────────────────
resource "aws_cloudwatch_event_rule" "rds_auto_stop" {
  name                = "project-a-${var.env}-rds-auto-stop"
  description         = "Re-stop RDS before AWS 7-day auto-start limit"
  schedule_expression = "rate(6 days)"

  tags = {
    Environment = var.env
    Project     = "project-a"
  }
}

resource "aws_cloudwatch_event_target" "rds_stop" {
  rule = aws_cloudwatch_event_rule.rds_auto_stop.name
  arn  = aws_lambda_function.rds_stop.arn
}

resource "aws_lambda_permission" "allow_cloudwatch_rds_stop" {
  statement_id  = "AllowCloudWatchInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.rds_stop.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.rds_auto_stop.arn
}

# ─── CloudWatch Log Group ─────────────────────────────────────────────────
resource "aws_cloudwatch_log_group" "lambda_rds_stop" {
  name              = "/aws/lambda/${local.lambda_function_name}"
  retention_in_days = 14

  tags = {
    Environment = var.env
    Project     = "project-a"
  }
}
```

### Varijable za modul

```hcl
# terraform/modules/rds/variables.tf (dodaj ove)
variable "db_instance_id" {
  type        = string
  description = "RDS instance identifier"
}

variable "env" {
  type        = string
  description = "Environment name (dev/staging/prod)"
}

variable "region" {
  type        = string
  default     = "eu-west-1"
}
```

---

## Troškovi: Šta se plaća dok je RDS stopped

```
RDS stopped (gp3 20GB):
  $0.115/GB/mj × 20GB = $2.30/mj = $0.08/dan

RDS stopped (gp3 100GB):
  $0.115/GB/mj × 100GB = $11.50/mj = $0.38/dan

ElastiCache stopped (cache.t3.micro):
  $0/dan (Redis cluster billing ne naplaćuje storage zasebno)

Lambda auto-stop (6× pozivanja/mj):
  Praktično $0 (u Free Tier zauvijek)
```

### Šta NE zastaviš, a skupo je

```
EKS Control Plane:          $0.10/h = $72/mj  ← SKUPO
EKS Nodes (2× t3.medium):   $0.047 × 2 = $0.094/h = $67/mj  ← SKUPO
NAT Gateway:                 $0.045/h = $32/mj  ← SKUPO

Ukupno compute bez compute:  ~$2.30/mj  (samo RDS storage)
Ukupno sa compute upaljenim: ~$173/mj   ← predrago za "pauzu"
```

**Zaključak:** RDS Stop ima smisao SAMO ako istovremeno uništiš compute resurse.
Vidjeti `04-snapshot-destroy-restore.md` i `05-compute-only-destroy.md`.

---

## Ručna Provjera RDS Statusa

```bash
# Brza provjera statusa
aws rds describe-db-instances \
  --query 'DBInstances[*].[DBInstanceIdentifier,DBInstanceStatus,DBInstanceClass]' \
  --output table

# Detalji jedne instance
aws rds describe-db-instances \
  --db-instance-identifier project-a-prod \
  --query 'DBInstances[0].{
    Status:DBInstanceStatus,
    Class:DBInstanceClass,
    Engine:Engine,
    EngineVersion:EngineVersion,
    Endpoint:Endpoint.Address,
    AllocatedStorage:AllocatedStorage,
    StorageType:StorageType
  }' \
  --output table
```
