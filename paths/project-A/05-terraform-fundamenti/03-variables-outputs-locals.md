# 03 — Variables, outputs i locals

## Variables — input parametri

Variables su ulazni parametri Terraform modula ili konfiguracije.
Omogućavaju isti kod za različita okruženja promjenom vrijednosti.

```hcl
# variables.tf

variable "environment" {
  description = "Okruzenje: dev, staging, prod"
  type        = string
  
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Okruzenje mora biti dev, staging ili prod."
  }
}

variable "aws_region" {
  description = "AWS region za deployment"
  type        = string
  default     = "eu-central-1"
}

variable "cluster_node_count" {
  description = "Broj worker nodova u EKS clusteru"
  type        = number
  default     = 2
}

variable "cluster_node_instance_type" {
  description = "EC2 instance tip za EKS worker nodove"
  type        = string
  default     = "t3.medium"
}

variable "tags" {
  description = "Dodatni tagovi za sve resurse"
  type        = map(string)
  default     = {}
}
```

Validacija je opciona ali korisna — bolje uhvatiti gresku u `plan` fazi
nego kreiranjem pogrešnih resursa.

## terraform.tfvars i .auto.tfvars

Postoje tri načina za proslijeđivanje vrijednosti varijabli:

**Komandna linija:**
```bash
terraform apply -var="environment=dev" -var="cluster_node_count=2"
```

**`-var-file` fajl:**
```bash
terraform apply -var-file=dev.tfvars
```

**`.auto.tfvars`** — automatski učitan bez navodenja:
```bash
# dev.auto.tfvars — učita se automatski u dev/ direktorijumu
environment              = "dev"
cluster_node_count       = 2
cluster_node_instance_type = "t3.medium"
```

**Razlika između `.tfvars` i `.auto.tfvars`:**
- `.tfvars`: mora se eksplicitno navesti sa `-var-file`
- `.auto.tfvars`: Terraform ga automatski učita ako postoji u radnom direktorijumu

Za project-A koristimo eksplicitni `-var-file` u CI/CD jer je preglednije koji fajl se koristi:

```bash
terraform apply -var-file=../../envs/dev/dev.tfvars
```

## Outputs — vrijednosti koje Terraform vraća

Outputs su podaci koje Terraform eksportuje nakon `apply`.
Koriste se za:
- Dobijanje informacija o kreiranim resursima (EKS endpoint, ECR URL)
- Proslijeđivanje vrijednosti između modula
- CI/CD pipeline koji treba URL ili ARN resursa

```hcl
# outputs.tf

output "eks_cluster_endpoint" {
  description = "API endpoint za EKS cluster"
  value       = aws_eks_cluster.main.endpoint
}

output "eks_cluster_name" {
  description = "Ime EKS clustera za kubectl config"
  value       = aws_eks_cluster.main.name
}

output "ecr_repository_url" {
  description = "URL ECR repozitorijuma za Docker push"
  value       = aws_ecr_repository.app.repository_url
}

output "vpc_id" {
  description = "ID kreiranog VPC-a"
  value       = aws_vpc.main.id
}
```

Pristup output vrijednostima:

```bash
terraform output eks_cluster_endpoint
terraform output -json   # svi outputs u JSON formatu
```

U CI/CD pipelinu:

```bash
EKS_ENDPOINT=$(terraform output -raw eks_cluster_endpoint)
aws eks update-kubeconfig --name $(terraform output -raw eks_cluster_name)
```

## Sensitivity za secrets

```hcl
variable "db_password" {
  description = "Database lozinka"
  type        = string
  sensitive   = true   # Terraform nece ispisati ovu vrijednost u logovima
}

output "db_connection_string" {
  value     = "postgresql://app:${var.db_password}@${aws_db_instance.main.address}/app"
  sensitive = true   # Output se nece ispisati u terminalu
}
```

`sensitive = true` ne enkriptuje vrijednost u state fajlu — to radi S3 enkripicja.
Samo sprjecava slucajno logovanje u terminalu ili CI outputu.

## Locals — computed vrijednosti unutar modula

Locals su privremene vrijednosti koje se racunaju unutar modula.
Ne mogu se proslijediti izvana (nije input), ne eksportuju se (nije output).

```hcl
# locals.tf

locals {
  # Kompozitno ime za resurse
  name_prefix = "${var.environment}-helloworld"
  
  # Uvjetno odredivanje velicine clustera
  node_count = var.environment == "prod" ? 3 : var.cluster_node_count
  
  # Zajednicki tagovi za sve resurse u ovom modulu
  common_tags = merge(var.tags, {
    Environment = var.environment
    Module      = "eks"
  })
  
  # Izracunati CIDR blokovi
  private_subnet_cidrs = [
    cidrsubnet(var.vpc_cidr, 8, 1),
    cidrsubnet(var.vpc_cidr, 8, 2),
    cidrsubnet(var.vpc_cidr, 8, 3),
  ]
}
```

Koristenje locals-a u resource-ima:

```hcl
resource "aws_eks_cluster" "main" {
  name = local.name_prefix
  
  tags = local.common_tags
}
```

Zašto locals: izbjegavaju ponavljanje iste logike na više mjesta.
Ako trebas promijeniti naming konvenciju, mjenas na jednom mjestu.

## Praktičan primjer — variables za EKS cluster

```hcl
# dev.tfvars
environment                = "dev"
aws_region                 = "eu-central-1"
cluster_node_count         = 2
cluster_node_instance_type = "t3.medium"
vpc_cidr                   = "10.10.0.0/16"

# staging.tfvars
environment                = "staging"
aws_region                 = "eu-central-1"
cluster_node_count         = 3
cluster_node_instance_type = "t3.large"
vpc_cidr                   = "10.20.0.0/16"

# prod.tfvars
environment                = "prod"
aws_region                 = "eu-central-1"
cluster_node_count         = 5
cluster_node_instance_type = "t3.xlarge"
vpc_cidr                   = "10.30.0.0/16"
```

Svaki env ima vlastiti VPC CIDR — ne mogu se preklapati ako su u istom AWS accountu
i trebaju VPC peering ili Transit Gateway.

## AI workflow

Imas resource blok i trebas outputs:

```
Evo mog Terraform koda koji kreira EKS cluster:

[resource blokovi]

Koja outputs bi imala smisla za ovaj modul?
Šta CI/CD pipeline tipično treba od EKS resursa?
Predloži i sensitive markere gdje su potrebni.
```

Kada je variable bez validacije i nisi siguran koji tip bi bio ispravan:

```
Imam varijablu za cluster_node_instance_type.
Koji AWS EC2 instance tipovi su razumni za EKS worker nodove?
Kako da dodam validaciju koja sprjecava ocigledne greske?
```
