# 02 — Providers, resources i state

## Provider

Provider je plugin koji zna kako da komunicira sa određenim API-jem.
Terraform core ne zna ništa o AWS-u — to zna AWS provider.

```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.25"
    }
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "helloworld"
      ManagedBy   = "terraform"
      Environment = var.environment
    }
  }
}
```

`version = "~> 5.0"` znaci "5.x ali ne 6.x". Pinovanje verzije je važno —
nova major verzija providera može imati breaking changes.

`terraform init` skida provider plugin-ove u `.terraform/` direktorijum.
Ne stavlja se u git (`.gitignore`).

## Resource

Resource je pojedinačna infrastrukturna komponenta kojom Terraform upravlja.

```hcl
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${var.environment}-vpc"
  }
}
```

Sintaksa: `resource "TIP_RESURSA" "LOKALNO_IME" { ... }`

`"aws_vpc"` — tip resursa koji provider definise
`"main"` — lokalno ime unutar Terraform koda za referenciranje

Referenciranje u drugom resource-u:

```hcl
resource "aws_subnet" "public" {
  vpc_id     = aws_vpc.main.id    # referenca na vpc resource
  cidr_block = "10.0.1.0/24"
}
```

Ova referenca automatski kreira **implicit dependency** — Terraform zna da mora
kreirati VPC prije subnet-a.

## Data source

Data source čita informacije o postojećim resursima, ali ih ne kreira i ne upravlja njima.

```hcl
# Pronađi najnoviji Amazon Linux 2 AMI
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }
}

# Koristi u resource-u
resource "aws_instance" "app" {
  ami = data.aws_ami.amazon_linux.id
  ...
}
```

Korisno za: AMI ID-eve, dostupne AZ-ove, postojeće VPC-ove.

## State fajl — srce Terraform-a

`.tfstate` je JSON fajl koji mapira Terraform resurse na stvarne cloud resurse.

Primjer state zapisa za S3 bucket:

```json
{
  "type": "aws_s3_bucket",
  "name": "app_assets",
  "instances": [{
    "attributes": {
      "id": "firma-helloworld-assets",
      "arn": "arn:aws:s3:::firma-helloworld-assets",
      "bucket": "firma-helloworld-assets",
      "region": "eu-central-1"
    }
  }]
}
```

Bez state fajla, Terraform ne zna šta postoji u cloudu.
Ako obrišes state, Terraform misli da ništa nije kreirano.
Posledica: `terraform apply` bi pokušao da kreira sve iznova — greškom ili duplikatom.

**NIKAD ne staviti `.tfstate` u Git:**
- Sadrži tajne u plaintext-u (database passwords, API keys)
- Merge konflikti u state fajlu su opasni
- Svi koji imaju pristup repozitorijumu vide sve tajne

## Remote state — jedino prihvatljivo za tim

Za bilo koji tim (čak i tim od jedne osobe koji koristi CI/CD), state mora biti remote.

```hcl
terraform {
  backend "s3" {
    bucket         = "firma-terraform-state"
    key            = "helloworld/dev/terraform.tfstate"
    region         = "eu-central-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
  }
}
```

S3 čuva state fajl. DynamoDB tabla pruža **state locking** — sprječava da dva
`terraform apply` rade paralelno i korumpiraju state.

Kada neko pokrce `terraform apply`, DynamoDB zapiše lock. Drugi pokušaj vidi lock
i čeka ili failuje sa greškom. Unlock se desi automatski po završetku.

## Četiri osnovne komande

```bash
terraform init
```
Inicijalizuj radni direktorijum. Skida provider plugin-ove. Konfigurira backend.
Pokreni nakon svake promjene u `required_providers` ili `backend` bloku.

```bash
terraform plan
```
Prikaži šta ce se promijeniti. Nikad ne mijenja stvarne resurse.
Uvijek pokreni prije `apply`. U CI/CD: output plana objavi u MR komentaru.

```bash
terraform apply
```
Primijeni promjene. Prikaže plan, traži potvrdu, pa kreira/mijenja/briše resurse.
Za CI/CD bez interakcije: `terraform apply -auto-approve`.

```bash
terraform destroy
```
Uništi sve resurse u state-u. Traži potvrdu.
Za CI/CD: `terraform destroy -auto-approve`.

## Minimalan AWS provider config za project-A

```hcl
# versions.tf
terraform {
  required_version = ">= 1.6"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "firma-terraform-state"
    key            = "helloworld/${var.environment}/terraform.tfstate"
    region         = "eu-central-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
  }
}

# provider.tf
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "helloworld"
      ManagedBy   = "terraform"
      Environment = var.environment
    }
  }
}
```

`default_tags` na provider nivou — svi AWS resursi automatski dobijaju ove tagove.
Ne moraš ih ponavljati na svakom resursu. Korisno za cost allocation i audit.
