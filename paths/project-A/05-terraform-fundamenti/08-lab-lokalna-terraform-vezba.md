# 08 — LAB: Lokalna Terraform vježba

## Cilj

Naučiti Terraform workflow bez AWS troškova.
Koristimo `local` provider koji kreira lokalne fajlove i direktorijume —
savrseno za učenje plan/apply/destroy ciklusa bez ijednog centa troška.

## Terraform kao Docker kontejner

Svi alati idu kroz Docker — to je pravilo project-A.

```bash
# Alias za lakše korišćenje
alias tf='docker run --rm -it \
  -v $(pwd):/workspace \
  -w /workspace \
  hashicorp/terraform:1.7 '

# Provjeri verziju
tf version
```
> **Podman:** `alias tf='podman run --rm -it -v $(pwd):/workspace -w /workspace hashicorp/terraform:1.7 '`

Ili direktno bez aliasa:

```bash
docker run --rm -it \
  -v $(pwd):/workspace \
  -w /workspace \
  hashicorp/terraform:1.7 version
```
> **Podman:** `podman run --rm -it -v $(pwd):/workspace -w /workspace hashicorp/terraform:1.7 version`

## Priprema radnog direktorijuma

```bash
mkdir -p ~/terraform-lab && cd ~/terraform-lab
```

## Korak 1: main.tf sa local providerom

Kreiraj `main.tf`:

```hcl
terraform {
  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.4"
    }
  }
}

# Kreira direktorijum sa environment fajlovima
resource "local_file" "app_config" {
  content  = <<-EOT
    environment = ${var.environment}
    app_name    = ${var.app_name}
    replicas    = ${var.replica_count}
    image_tag   = ${var.image_tag}
    created_at  = ${timestamp()}
  EOT
  filename = "${path.module}/output/${var.environment}-config.txt"
}

resource "local_file" "deploy_script" {
  content  = <<-EOT
    #!/bin/bash
    # Auto-generated deploy script za ${var.environment}
    
    ENV="${var.environment}"
    IMAGE="${var.app_name}:${var.image_tag}"
    REPLICAS="${var.replica_count}"
    
    echo "Deploying $IMAGE sa $REPLICAS replika na $ENV..."
    
    helm upgrade --install ${var.app_name}-$ENV ./helm/${var.app_name} \
      --set image.tag=${var.image_tag} \
      --set replicaCount=${var.replica_count} \
      --namespace ${var.app_name}-$ENV \
      --create-namespace
  EOT
  filename        = "${path.module}/output/deploy-${var.environment}.sh"
  file_permission = "0755"
}
```

## Korak 2: variables.tf

```hcl
variable "environment" {
  description = "Okruzenje: dev, staging, prod"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Okruzenje mora biti: dev, staging ili prod."
  }
}

variable "app_name" {
  description = "Ime aplikacije"
  type        = string
  default     = "helloworld"
}

variable "replica_count" {
  description = "Broj replika"
  type        = number
  default     = 1

  validation {
    condition     = var.replica_count >= 1 && var.replica_count <= 10
    error_message = "Broj replika mora biti izmedju 1 i 10."
  }
}

variable "image_tag" {
  description = "Docker image tag"
  type        = string
  default     = "latest"
}
```

## Korak 3: outputs.tf

```hcl
output "config_file_path" {
  description = "Putanja do generisanog config fajla"
  value       = local_file.app_config.filename
}

output "deploy_script_path" {
  description = "Putanja do generisanog deploy skripta"
  value       = local_file.deploy_script.filename
}

output "environment_summary" {
  description = "Pregled konfiguracije okruzenja"
  value = {
    environment   = var.environment
    app_name      = var.app_name
    replica_count = var.replica_count
    image_tag     = var.image_tag
  }
}
```

## Korak 4: terraform init

```bash
docker run --rm -it \
  -v $(pwd):/workspace \
  -w /workspace \
  hashicorp/terraform:1.7 init
```
> **Podman:** `podman run --rm -it -v $(pwd):/workspace -w /workspace hashicorp/terraform:1.7 init`

Ocekivani output:
```
Initializing the backend...
Initializing provider plugins...
- Finding hashicorp/local versions matching "~> 2.4"...
- Installing hashicorp/local v2.4.1...
Terraform has been successfully initialized!
```

Provjeri sta je kreirano:
```bash
ls -la .terraform/
ls -la .terraform/providers/
```

## Korak 5: terraform plan

```bash
docker run --rm -it \
  -v $(pwd):/workspace \
  -w /workspace \
  hashicorp/terraform:1.7 plan
```
> **Podman:** `podman run --rm -it -v $(pwd):/workspace -w /workspace hashicorp/terraform:1.7 plan`

Citaj plan pazljivo:
- `+` zeleno — resurs ce biti KREIRAN
- `~` zuto — resurs ce biti IZMIJENJEN
- `-` crveno — resurs ce biti OBRISAN
- `-/+` — resurs ce biti OBRISAN i REKREIRA

Pokusaj sa drugačijim varijablama:

```bash
docker run --rm -it \
  -v $(pwd):/workspace \
  -w /workspace \
  hashicorp/terraform:1.7 plan \
    -var="environment=prod" \
    -var="replica_count=3" \
    -var="image_tag=v1.2.0"
```
> **Podman:** `podman run --rm -it -v $(pwd):/workspace -w /workspace hashicorp/terraform:1.7 plan -var="environment=prod" -var="replica_count=3" -var="image_tag=v1.2.0"`

## Korak 6: terraform apply

```bash
mkdir -p output   # Terraform nece kreirati parent direktorijum

docker run --rm -it \
  -v $(pwd):/workspace \
  -w /workspace \
  hashicorp/terraform:1.7 apply
```
> **Podman:** `podman run --rm -it -v $(pwd):/workspace -w /workspace hashicorp/terraform:1.7 apply`

Upiši `yes` kada pita.

Provjeri šta je kreirano:
```bash
ls -la output/
cat output/dev-config.txt
cat output/deploy-dev.sh
```

## Korak 7: Razumi outputs

```bash
docker run --rm \
  -v $(pwd):/workspace \
  -w /workspace \
  hashicorp/terraform:1.7 output

docker run --rm \
  -v $(pwd):/workspace \
  -w /workspace \
  hashicorp/terraform:1.7 output -json
```
> **Podman:** `podman run --rm -v $(pwd):/workspace -w /workspace hashicorp/terraform:1.7 output` (i `output -json`)

JSON format je koristan u CI/CD skriptama:

```bash
IMAGE_TAG=$(docker run --rm -v $(pwd):/workspace -w /workspace \
  hashicorp/terraform:1.7 output -raw image_tag)
```
> **Podman:** `IMAGE_TAG=$(podman run --rm -v $(pwd):/workspace -w /workspace hashicorp/terraform:1.7 output -raw image_tag)`

## Korak 8: Kreiraj dev.tfvars

```hcl
# dev.tfvars
environment   = "dev"
replica_count = 1
image_tag     = "latest"

# prod.tfvars
environment   = "prod"
replica_count = 3
image_tag     = "v1.2.0"
```

Apply sa tfvars:

```bash
docker run --rm -it \
  -v $(pwd):/workspace \
  -w /workspace \
  hashicorp/terraform:1.7 apply -var-file=prod.tfvars
```
> **Podman:** `podman run --rm -it -v $(pwd):/workspace -w /workspace hashicorp/terraform:1.7 apply -var-file=prod.tfvars`

Provjeri output direktorijum — sad imas `prod-config.txt`.

## Korak 9: terraform destroy

```bash
docker run --rm -it \
  -v $(pwd):/workspace \
  -w /workspace \
  hashicorp/terraform:1.7 destroy
```
> **Podman:** `podman run --rm -it -v $(pwd):/workspace -w /workspace hashicorp/terraform:1.7 destroy`

Provjeri da su fajlovi obrisani:
```bash
ls -la output/
```

## Korak 10: State fajl inspekcija

```bash
cat terraform.tfstate | python3 -m json.tool | head -50
```

Vidi kako Terraform prati kreirane resurse.
Pokusaj obrisati `terraform.tfstate` i ponovo pokreni `terraform plan` —
Terraform mislila da ništa ne postoji i ponudio bi recreate.

## Bonus — minimalan S3 bucket ako imas AWS

Ako imaš AWS credentials i zelite testirati sa stvarnim resursima (S3 bucket kosta ~$0):

```hcl
# Dodaj u main.tf
resource "aws_s3_bucket" "lab" {
  bucket = "terraform-lab-${var.environment}-${random_id.suffix.hex}"

  tags = {
    Environment = var.environment
    ManagedBy   = "terraform"
    Purpose     = "lab"
  }
}

resource "random_id" "suffix" {
  byte_length = 4
}
```

```bash
docker run --rm -it \
  -v $(pwd):/workspace \
  -v ~/.aws:/root/.aws:ro \   # AWS credentials
  -w /workspace \
  -e AWS_PROFILE=default \
  hashicorp/terraform:1.7 apply
```
> **Podman:** `podman run --rm -it -v $(pwd):/workspace -v ~/.aws:/root/.aws:ro -w /workspace -e AWS_PROFILE=default hashicorp/terraform:1.7 apply`

## AI workflow

Kada dobijete grešku iz `terraform plan`:

```
Dobio sam ovu grešku iz terraform plan:

Error: Invalid value for variable
  on variables.tf line 8, in variable "environment":
   8:   validation {
    │ ----------------
    │ var.environment is "staging2"
    │     ├────────────────
    │     │ var.environment is "staging2"

The value must be one of: dev, staging, prod.

Koji tfvars fajl mi je aktivan i šta trebam promijeniti?
```

Kada nisi siguran šta plan prikazuje:

```
Ovaj terraform plan output prikazuje:

  # local_file.app_config must be replaced
  -/+ resource "local_file" "app_config" {
      ~ content  = <<-EOT
          - created_at  = 2024-01-01T10:00:00Z
          + created_at  = 2024-01-02T08:30:00Z
        EOT

Zašto se resurs rekreira? Je li to normalno?
```

---

## Makefile — dodaj u ovom poglavlju

Ovo poglavlje uvodi Terraform. Dodaj u `Makefile` u korenu projekta:

```makefile
# === OBLAST 05: Terraform ===

tf-init: ## Inicijalizuj Terraform radni direktorijum (DIR=. make tf-init)
	docker run --rm \
	  -v $(PWD)/$(DIR):/workspace -w /workspace \
	  hashicorp/terraform:$(TF_VERSION) init

tf-validate: ## Validiraj Terraform sintaksu
	docker run --rm \
	  -v $(PWD):/workspace -w /workspace \
	  hashicorp/terraform:$(TF_VERSION) validate

tf-fmt: ## Formatiraj Terraform fajlove (provjerava stil)
	docker run --rm \
	  -v $(PWD):/workspace -w /workspace \
	  hashicorp/terraform:$(TF_VERSION) fmt -recursive -diff

tf-plan: ## Generiši Terraform plan (ENV=dev make tf-plan)
	docker run --rm \
	  -v $(PWD):/workspace -w /workspace \
	  -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -e AWS_SESSION_TOKEN \
	  hashicorp/terraform:$(TF_VERSION) plan -var="env_name=$(ENV)" -out=tfplan

tf-apply: ## Primijeni Terraform plan (uvijek nakon tf-plan)
	docker run --rm \
	  -v $(PWD):/workspace -w /workspace \
	  -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -e AWS_SESSION_TOKEN \
	  hashicorp/terraform:$(TF_VERSION) apply tfplan

tf-destroy: ## Uništi Terraform resurse (ENV=dev make tf-destroy) ⚠️ DESTRUKTIVNO
	docker run --rm \
	  -v $(PWD):/workspace -w /workspace \
	  -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -e AWS_SESSION_TOKEN \
	  hashicorp/terraform:$(TF_VERSION) destroy -var="env_name=$(ENV)"

tf-output: ## Prikaži Terraform output vrijednosti
	docker run --rm \
	  -v $(PWD):/workspace -w /workspace \
	  hashicorp/terraform:$(TF_VERSION) output

tf-security: ## Statička analiza sigurnosti Terraform koda (tfsec)
	docker run --rm \
	  -v $(PWD):/src \
	  aquasec/tfsec:latest /src --no-color
```

Centralni Makefile već sadrži ove targete — ovo je referenca šta si dodao u ovoj oblasti.

Provjeri da targeti rade:
```bash
DIR=. make tf-init
make tf-validate
make tf-fmt
ENV=dev make tf-plan
make help | grep "^tf-"
```
