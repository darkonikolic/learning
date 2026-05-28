# 03 — Terraform: AWS Secrets Manager

## Kreiranje SM secrets za project-a

### DB master password — kompletan lifecycle

```hcl
# terraform/modules/database/secrets.tf

# Generisanje jakog password-a
resource "random_password" "rds_master" {
  length           = 32
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
  # Isključiti znakove koji prave probleme u URL-ovima i MySQL connection string-ovima
  # @ / ' " space su isključeni defaultno
}

resource "random_password" "rds_app_user" {
  length           = 32
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

# SM Secret za master password
resource "aws_secretsmanager_secret" "rds_master" {
  name        = "/project-a/${var.environment}/rds/master-password"
  description = "RDS master password for project-a ${var.environment}"

  kms_key_id = aws_kms_key.secrets.arn  # Koristiti vlastiti KMS key, ne AWS managed

  recovery_window_in_days = var.environment == "prod" ? 30 : 7
  # Prod: 30 dana recovery window — accidentalno brisanje se može oporaviti
  # Dev: 7 dana — brže cleanup

  tags = {
    Environment = var.environment
    Service     = "rds"
    ManagedBy   = "terraform"
    Rotation    = "aws-managed"
  }
}

resource "aws_secretsmanager_secret_version" "rds_master" {
  secret_id = aws_secretsmanager_secret.rds_master.id

  # SM rotation Lambda za RDS očekuje ovaj JSON format:
  secret_string = jsonencode({
    username = "admin"
    password = random_password.rds_master.result
    engine   = "mysql"
    host     = aws_db_instance.main.endpoint
    port     = 3306
    dbname   = var.db_name
  })

  # lifecycle ignore_changes jer SM rotation Lambda ažurira ovu verziju
  lifecycle {
    ignore_changes = [secret_string]
  }
}

# SM Secret za app user password
resource "aws_secretsmanager_secret" "rds_app_user" {
  name        = "/project-a/${var.environment}/rds/app-user-password"
  description = "RDS app user password for project-a ${var.environment}"
  kms_key_id  = aws_kms_key.secrets.arn
  recovery_window_in_days = var.environment == "prod" ? 30 : 7

  tags = {
    Environment = var.environment
    Service     = "rds"
    ManagedBy   = "terraform"
  }
}

resource "aws_secretsmanager_secret_version" "rds_app_user" {
  secret_id = aws_secretsmanager_secret.rds_app_user.id

  secret_string = jsonencode({
    username = "appuser"
    password = random_password.rds_app_user.result
    engine   = "mysql"
    host     = aws_db_instance.main.endpoint
    port     = 3306
    dbname   = var.db_name
  })

  lifecycle {
    ignore_changes = [secret_string]
  }
}
```

### KMS key za secrets enkripciju

```hcl
# terraform/modules/database/kms.tf

resource "aws_kms_key" "secrets" {
  description             = "KMS key for project-a ${var.environment} secrets"
  deletion_window_in_days = 30
  enable_key_rotation     = true  # Automatska godišnja rotacija KMS key materijala

  policy = data.aws_iam_policy_document.kms_secrets.json
}

resource "aws_kms_alias" "secrets" {
  name          = "alias/project-a-${var.environment}-secrets"
  target_key_id = aws_kms_key.secrets.key_id
}

data "aws_iam_policy_document" "kms_secrets" {
  # Root account ima pun pristup (za emergency recovery)
  statement {
    sid     = "RootAccess"
    effect  = "Allow"
    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"]
    }
    actions   = ["kms:*"]
    resources = ["*"]
  }

  # SM service može koristiti key
  statement {
    sid    = "SecretsManagerAccess"
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["secretsmanager.amazonaws.com"]
    }
    actions = [
      "kms:Decrypt",
      "kms:GenerateDataKey",
      "kms:CreateGrant",
    ]
    resources = ["*"]
  }

  # ESO IRSA rola može decrypt
  statement {
    sid    = "ESOAccess"
    effect = "Allow"
    principals {
      type        = "AWS"
      identifiers = [aws_iam_role.eso_irsa.arn]
    }
    actions = [
      "kms:Decrypt",
      "kms:DescribeKey",
    ]
    resources = ["*"]
  }
}
```

---

## Automatska rotacija za RDS MySQL

AWS ima managed Lambda rotator za RDS MySQL/PostgreSQL. Terraform konfiguriše rotaciju:

```hcl
# terraform/modules/database/rotation.tf

# Rotation Lambda — AWS managed, ne trebate pisati Lambda kod
resource "aws_secretsmanager_secret_rotation" "rds_master" {
  secret_id           = aws_secretsmanager_secret.rds_master.id
  rotation_lambda_arn = data.aws_lambda_function.rds_rotator.arn

  rotation_rules {
    automatically_after_days = 30  # Rotirati svakih 30 dana
    # Za prod: 30 dana; za payment processing: 7-14 dana
  }
}

# AWS managed rotation Lambda postoji u svakom regionu
data "aws_lambda_function" "rds_rotator" {
  function_name = "SecretsManagerRDSMySQLRotationSingleUser"
  # Alternativa za bolju sigurnost: "SecretsManagerRDSMySQLRotationMultiUser"
  # MultiUser rotacija kreira novi user, mijenja password, onda briše stari
  # SingleUser može imati kratki period gdje stari password više ne radi
}

# Lambda mora imati pristup RDS-u — VPC konfiguracija
resource "aws_lambda_function_event_invoke_config" "rds_rotator" {
  # Lambda treba biti u istom VPC-u kao RDS
  # Konfiguracija je na SM strani, Lambda je AWS managed
}

# Security group za rotation Lambda
resource "aws_security_group" "rotation_lambda" {
  name        = "project-a-${var.environment}-rotation-lambda"
  description = "SG for SM rotation Lambda"
  vpc_id      = var.vpc_id

  egress {
    from_port       = 3306
    to_port         = 3306
    protocol        = "tcp"
    security_groups = [aws_security_group.rds.id]
  }

  egress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # SM API endpoint
    description = "SM API access via VPC endpoint ideally"
  }
}
```

**Preporuka: MultiUser rotacija za produkciju**

SingleUser rotacija mijenja password direktno — postoji ~1 sekunda prozor kada stari password ne radi a novi nije distribuiran. MultiUser:
1. Kreira `appuser_clone` sa novim passwordom
2. Ažurira SM secret da pokazuje na `appuser_clone`
3. ESO osvježava K8s Secret
4. Rolling restart poda
5. Briše stari `appuser`

Zero-downtime, ali zahtijeva da aplikacija nema hardkodiran username.

---

## IAM politike — IRSA per service

Svaki K8s servis čita SAMO svoje secrets:

```hcl
# terraform/modules/eks-apps/iam.tf

# Go service IRSA
data "aws_iam_policy_document" "go_service_secrets" {
  statement {
    effect  = "Allow"
    actions = ["secretsmanager:GetSecretValue"]
    resources = [
      "arn:aws:secretsmanager:${var.aws_region}:${data.aws_caller_identity.current.account_id}:secret:/project-a/${var.environment}/go-service/*",
      "arn:aws:secretsmanager:${var.aws_region}:${data.aws_caller_identity.current.account_id}:secret:/project-a/${var.environment}/rds/app-user-password*",
      "arn:aws:secretsmanager:${var.aws_region}:${data.aws_caller_identity.current.account_id}:secret:/project-a/${var.environment}/redis/auth-token*",
    ]
  }

  # Eksplicitni deny za prod secrets iz non-prod environment
  statement {
    effect  = "Deny"
    actions = ["secretsmanager:*"]
    resources = [
      "arn:aws:secretsmanager:${var.aws_region}:${data.aws_caller_identity.current.account_id}:secret:/project-a/prod/*",
    ]
    condition {
      test     = "StringNotEquals"
      variable = "aws:RequestedRegion"
      values   = [var.aws_region]
    }
  }
}

# PHP service IRSA — nema pristup go-service secrets
data "aws_iam_policy_document" "php_service_secrets" {
  statement {
    effect  = "Allow"
    actions = ["secretsmanager:GetSecretValue"]
    resources = [
      "arn:aws:secretsmanager:${var.aws_region}:${data.aws_caller_identity.current.account_id}:secret:/project-a/${var.environment}/php-service/*",
      "arn:aws:secretsmanager:${var.aws_region}:${data.aws_caller_identity.current.account_id}:secret:/project-a/${var.environment}/redis/auth-token*",
    ]
  }
}
```

---

## Čitanje SM secrets u Terraformu

Za RDS kreiranje trebate password koji je upravo generisan i pohranjen u SM:

```hcl
# Čitanje SM secret unutar Terraform (npr. za RDS initial password)
data "aws_secretsmanager_secret_version" "rds_master" {
  secret_id = aws_secretsmanager_secret.rds_master.id

  depends_on = [aws_secretsmanager_secret_version.rds_master]
}

resource "aws_db_instance" "main" {
  # ...
  username = jsondecode(data.aws_secretsmanager_secret_version.rds_master.secret_string)["username"]
  password = jsondecode(data.aws_secretsmanager_secret_version.rds_master.secret_string)["password"]

  lifecycle {
    ignore_changes = [password]
    # Nakon inicijalne kreacije, SM rotation Lambda kontroliše password
    # Terraform ne smije overwriteati rotiran password
  }
}
```

**Upozorenje:** `data "aws_secretsmanager_secret_version"` vrijednost se čuva u Terraform state. Terraform state je osjetljiv fajl — mora biti enkriptovan (S3 + SSE-KMS) i access-controlled.

---

## Secret versioning i cross-env izolacija

```hcl
# terraform/environments/prod/backend.tf
terraform {
  backend "s3" {
    bucket         = "project-a-terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "eu-west-1"
    encrypt        = true
    kms_key_id     = "arn:aws:kms:eu-west-1:123456789:key/prod-state-key"
    dynamodb_table = "project-a-terraform-locks"

    # Prod state bucket policy: samo prod CI role ima pristup
  }
}

# Nikad ne koristiti terraform workspace za prod/staging razliku
# Workspace dijeli state backend — lakše napraviti grešku
# Koristiti separate directories sa separate backends
```

**Expert pattern — Secret versioning za zero-downtime rotaciju:**

SM čuva prethodne verzije secrets. AWS managed rotation automatski kreira novu verziju sa `AWSCURRENT` staging label i premješta staru na `AWSPREVIOUS`. Aplikacija može eksplicitno tražiti `AWSPREVIOUS` za graceful transition period:

```go
// Go service: proba AWSCURRENT, fallback na AWSPREVIOUS pri auth grešci
// Ovo radi automatski kod DB driver-a — connection pool retry sa novim credentials
// Za vlastite tokens (JWT): verifikacija prihvata i CURRENT i PREVIOUS verziju
func (a *Auth) ValidateToken(tokenStr string) (*Claims, error) {
    for _, stage := range []string{"AWSCURRENT", "AWSPREVIOUS"} {
        secret := getSecretVersion("/project-a/prod/go-service/jwt-secret", stage)
        if claims, err := jwt.Parse(tokenStr, secret); err == nil {
            return claims, nil
        }
    }
    return nil, ErrInvalidToken
}
```

---

## Terraform state security — osjetljivi outputs

```hcl
# NIKAD ovako:
output "db_password" {
  value = random_password.rds_master.result
  # Ovo je u Terraform state i u terraform output plaintext
}

# Umjesto toga, eksportovati samo SM ARN:
output "db_password_secret_arn" {
  value       = aws_secretsmanager_secret.rds_master.arn
  description = "ARN of SM secret. Use SM API to retrieve actual value."
  sensitive   = false  # ARN nije osjetljiv
}

# Za sensitive Terraform outputs koristiti sensitive = true:
output "rds_endpoint" {
  value     = aws_db_instance.main.endpoint
  sensitive = false  # Endpoint nije secret
}
```

Svaki `sensitive = true` output je maskiran u Terraform plan/apply output, ali **i dalje je plaintext u state fajlu**. State enkripcija je obavezna.
