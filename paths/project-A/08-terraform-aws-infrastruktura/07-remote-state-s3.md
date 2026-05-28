# Remote state i S3 backend

## Zašto remote state

Lokalni Terraform state (`terraform.tfstate`) funkcioniše kada jedan developer radi sam. Problem nastaje čim se pojavi drugi developer ili CI/CD pipeline:

- **Conflict**: Dva `terraform apply` paralelno → state korupcija
- **Desinhronizacija**: Developer A primjeni promjene, Developer B ima stari state → plan pokazuje netačno stanje
- **Izgubljen state**: `rm terraform.tfstate` ili pad laptopa → Terraform ne zna šta postoji u AWS-u

Remote state u S3 rješava sve tri probleme: centralizovano skladište, versioning za recovery, DynamoDB locking za sprečavanje paralelnih apply-a.

## Chicken-and-egg problem

Da bi koristio S3 za remote state, S3 bucket mora postojati. Ali ako koristiš Terraform za sve... kako kreiraš S3 bucket koji Terraform treba za storage svog state-a?

Odgovor: bootstrap Terraform koji kreira state infrastrukturu, a sam koristi **lokalni state**. Ovaj lokalni state se commita u git (jer S3 bucket rijetko mijenja, a ne drži produkcione resurse).

## `bootstrap/main.tf`

```hcl
terraform {
  # Bootstrap koristi lokalni state — jedini slučaj
  # Ovaj fajl se NE briše i state se može commitovati
}

provider "aws" {
  region = "eu-west-1"
}

# S3 bucket za Terraform state
resource "aws_s3_bucket" "terraform_state" {
  bucket = "project-a-terraform-state"

  # Štiti od slučajnog brisanja cijelog bucket-a sa state-om
  lifecycle {
    prevent_destroy = true
  }
}

# Versioning: svaka promjena state-a se čuva — recovery je moguć
resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Server-side enkripcija state fajlova (sadrže sensitive podatke)
resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms"
    }
  }
}

# Blokiranje javnog pristupa — state NIKAD ne smije biti javno dostupan
resource "aws_s3_bucket_public_access_block" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# DynamoDB tabela za state locking
resource "aws_dynamodb_table" "terraform_locks" {
  name         = "project-a-terraform-locks"
  billing_mode = "PAY_PER_REQUEST"  # nema fiksnih troškova za tabelu
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  lifecycle {
    prevent_destroy = true
  }
}
```

## `bootstrap/outputs.tf`

```hcl
output "state_bucket_name" {
  value = aws_s3_bucket.terraform_state.bucket
}

output "lock_table_name" {
  value = aws_dynamodb_table.terraform_locks.name
}
```

## Kako DynamoDB locking funkcioniše

```
Developer A: terraform apply
    ↓
Terraform pokušava upisati LockID u DynamoDB
    ↓
Uspjeh → lock je stečen, apply nastavlja

Developer B (istovremeno): terraform apply
    ↓
Terraform pokušava upisati isti LockID
    ↓
Greška: ConditionalCheckFailedException (lock već postoji)
    ↓
"Error: Error acquiring the state lock"
    ↓
Developer B čeka ili forsira oslobođenje (terraform force-unlock)
```

Lock se automatski oslobađa kada `apply` završi (uspješno ili ne). Ako apply crashuje, `terraform force-unlock <lock-id>` oslobađa ručno.

## Backend per environment

### `envs/dev/backend.tf`

```hcl
terraform {
  backend "s3" {
    bucket         = "project-a-terraform-state"
    key            = "dev/terraform.tfstate"
    region         = "eu-west-1"
    encrypt        = true
    dynamodb_table = "project-a-terraform-locks"
  }
}
```

Svaki environment ima vlastiti key u istom bucket-u. Alternativno: odvojeni bucket-i per environment (bolji security boundary za prod).

## Terraform Cloud alternativa

HashiCorp nudi Terraform Cloud (besplatan za manje timove) koji zamjenjuje S3 + DynamoDB setup:
- Remote state storage
- State locking
- Remote execution (plan/apply se izvršava na HashiCorp serverima)
- UI za pregled state-a i run historije

Za project-A koristimo S3 jer: nema zavisnosti od treće strane, all-AWS setup, troškovi su zanemarivi.

## Recovery iz versioned state-a

Ako se state pokvari ili greškom primijene destruktivne promjene:

```bash
# Lista verzija state fajla
aws s3api list-object-versions \
  --bucket project-a-terraform-state \
  --prefix dev/terraform.tfstate

# Povratak na prethodnu verziju
aws s3api get-object \
  --bucket project-a-terraform-state \
  --key dev/terraform.tfstate \
  --version-id <version-id> \
  terraform.tfstate.backup

# Provjeri backup pa uploadi
aws s3 cp terraform.tfstate.backup \
  s3://project-a-terraform-state/dev/terraform.tfstate
```
