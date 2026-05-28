# 07 — Terraform best practices

## Remote state uvek

Lokalni state fajl je prihvatljiv samo za personalne eksperimente.
Za svaki tim ili CI/CD pipeline, remote state je obavezan.

```hcl
terraform {
  backend "s3" {
    bucket         = "firma-terraform-state"
    key            = "helloworld/dev/terraform.tfstate"
    region         = "eu-central-1"
    encrypt        = true                         # enkriptovan na S3
    dynamodb_table = "terraform-state-lock"       # locking
  }
}
```

S3 bucket za state mora imati:
- Server-side enkripicja (SSE-S3 ili SSE-KMS)
- Versioning omogućen (rollback state-a ako se pokvari)
- Blokiran javni pristup
- MFA delete opcija za prod state bucket

DynamoDB tabela za locking treba samo jednu kolonu: `LockID` (String, partition key).

## NIKAD ne edituj state ručno

`.tfstate` je JSON koji Terraform interno održava. Ručna editacija skoro uvijek
rezultira korumpiranim state-om.

Jedina dozvoljena operacija koja direktno mijenja state je `terraform state` komanda:

```bash
# Premjesti resurs u state-u (refactoring)
terraform state mv aws_instance.old_name aws_instance.new_name

# Ukloni resurs iz state-a bez brisanja u cloudu
terraform state rm aws_s3_bucket.imported_bucket

# Uvezi postojeći cloud resurs u state
terraform import aws_s3_bucket.existing firma-existing-bucket

# Pogledaj resurse u state-u
terraform state list
terraform state show aws_eks_cluster.main
```

Ako je state korumpiran i mora se popraviti — prvo napravi backup, zatim
`terraform state pull > state.json`, edituj, `terraform state push state.json`.
Nikad direktno na S3.

## Pin verzije provider-a i modula

```hcl
terraform {
  required_version = ">= 1.6, < 2.0"   # ne stariji od 1.6, ne 2.x

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.31"   # 5.31.x
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.25"
    }
  }
}
```

Za module:

```hcl
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "= 20.8.4"   # egzaktna verzija za prod
}
```

Zašto: provider `5.32` može imati breaking change u ponasanju resursa.
Bez piniranja, `terraform init -upgrade` bi povukao novu verziju i mogao razbiti plan.

`terraform.lock.hcl` — Terraform automatski generiše ovaj fajl sa hash-evima
preuzetih providera. Commitaj ga u Git. CI/CD ce koristiti egzaktno iste provider verzije.

## terraform fmt i terraform validate u CI

```bash
# Formatira sve .tf fajlove po Terraform konvenciji
terraform fmt -recursive

# Provjeri sintaksu i interne konzistencije
terraform validate
```

U `.gitlab-ci.yml`:

```yaml
tf:validate:
  stage: validate
  script:
    - terraform fmt -check -recursive   # -check failuje ako format nije ispravan
    - cd terraform/envs/dev && terraform init -backend=false
    - terraform validate
  rules:
    - changes:
        - terraform/**/*
```

`-backend=false` za validate — ne treba stvarni backend, samo provjeravamo sintaksu.

Pre-commit hook lokalno:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/antonbabenko/pre-commit-terraform
    rev: v1.86.0
    hooks:
      - id: terraform_fmt
      - id: terraform_validate
      - id: terraform_docs
```

## Secrets nikad u kodu

Ne stavljati passwords, API key-eve, certificates u `.tf` fajlove ili `.tfvars`.

**AWS Secrets Manager:**

```hcl
data "aws_secretsmanager_secret_version" "db_password" {
  secret_id = "helloworld/${var.environment}/db-password"
}

resource "aws_db_instance" "main" {
  password = data.aws_secretsmanager_secret_version.db_password.secret_string
}
```

**SSM Parameter Store:**

```hcl
data "aws_ssm_parameter" "gitlab_token" {
  name = "/helloworld/gitlab-token"
}
```

Secrets se kreiraju jedanput ručno (ili kroz zasebni privilegovani proces),
a Terraform ih samo čita. Secrets nikad ne prolaze kroz Git.

## prevent_destroy za prod resurse

```hcl
# modules/eks/main.tf
resource "aws_eks_cluster" "main" {
  name = var.cluster_name

  lifecycle {
    prevent_destroy = var.environment == "prod" ? true : false
    # ili jednostavnije — staviti u prod/main.tf override
  }
}
```

Bolje rjesenje — zasebni lifecycle po env:

```hcl
# envs/prod/overrides.tf
resource "aws_eks_cluster" "main" {
  lifecycle {
    prevent_destroy = true
  }
}
```

Terraform merguje lifecycle blokove iz override fajlova.
`*_override.tf` ili `*_override.tf.json` Terraform automatski učitava zadnji
i merguje sa osnovnim resource konfiguracijom.

## Plan output u MR komentaru

Svaki `terraform plan` u CI treba biti vidljiv u MR-u. Inženjeri moraju
vidjeti šta će se promijeniti u infrastrukturi, ne samo u kodu.

```yaml
tf:plan:staging:
  script:
    - cd terraform/envs/staging
    - terraform init
    - terraform plan -var-file=staging.tfvars -no-color 2>&1 | tee plan.txt
    - |
      # Objavi plan kao GitLab MR komentar
      PLAN=$(cat plan.txt)
      curl --request POST \
        --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
        --data "body=<details><summary>Terraform plan: staging</summary>\n\n\`\`\`\n${PLAN}\n\`\`\`\n</details>" \
        "${CI_API_V4_URL}/projects/${CI_PROJECT_ID}/merge_requests/${CI_MERGE_REQUEST_IID}/notes"
```

Alternativno, koristiti `terraform-plan-to-github-comment` akcije ili
atlantis.io za automatizovan plan-u-PR workflow.

## Koristiti locals za izbjegavanje ponavljanja

Loše:

```hcl
resource "aws_eks_cluster" "main" {
  name = "dev-helloworld"
  tags = { Environment = "dev", Project = "helloworld", ManagedBy = "terraform" }
}

resource "aws_vpc" "main" {
  tags = { Environment = "dev", Project = "helloworld", ManagedBy = "terraform" }
}
```

Dobro:

```hcl
locals {
  name        = "${var.environment}-helloworld"
  common_tags = {
    Environment = var.environment
    Project     = "helloworld"
    ManagedBy   = "terraform"
  }
}

resource "aws_eks_cluster" "main" {
  name = local.name
  tags = local.common_tags
}

resource "aws_vpc" "main" {
  tags = local.common_tags
}
```

## AI workflow za Terraform plan

Terraform plan output je savršen za AI analizu — strukturiran, čitljiv, predvidiv format.

```
Dobio sam ovaj terraform plan output. Objasni mi šta će se promijeniti
i da li postoji nešto što bi trebalo pažljivo razmotriti prije apply-a:

[terraform plan output]
```

Posebno korisno za:
- `~ update in-place` vs `- destroy, + create` — šta uzrokuje recreate?
- Neočekivani resursi u planu — zašto se mijenja nešto što nisi dirnut?
- Procjena rizika promjene

```
Ovaj Terraform plan kaže da će aws_eks_cluster biti destroyan i recreated.
Šta to znači za workloads koji tamo rade? Kako da izbjegnem downtime?

[terraform plan output za EKS]
```
