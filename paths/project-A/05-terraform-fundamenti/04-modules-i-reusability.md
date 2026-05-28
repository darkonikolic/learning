# 04 — Modules i reusability

## Module = reusable Terraform blok

Modul je direktorijum sa `.tf` fajlovima koji prima inputs (variables),
kreira resurse i vraca outputs. Kao funkcija u programiranju.

Bez modula, svako okruženje bi imalo copy-paste isti kod za VPC, EKS, IAM.
Promjena security group rule-a značila bi editovanje na 3 mjesta.

Sa modulima:
- VPC logika živi na jednom mjestu
- Dev, staging, prod je pozivaju sa različitim parametrima
- Promjena se radi jedanput

## Root module vs child module

**Root module** — direktorijum odakle pokreces `terraform apply`.
Svaki `envs/dev/`, `envs/staging/`, `envs/prod/` je root modul.

**Child module** — modul koji root poziva. Živi u `modules/` direktorijumu.
Root mu proslijeđuje inputs, dobija outputs.

## Struktura projekta sa modulima

```
terraform/
├── modules/
│   ├── vpc/
│   │   ├── main.tf         ← VPC, subnets, NAT gateway, routing
│   │   ├── variables.tf    ← input parametri
│   │   └── outputs.tf      ← vpc_id, subnet_ids
│   ├── eks/
│   │   ├── main.tf         ← EKS cluster, node groups, OIDC provider
│   │   ├── variables.tf    ← cluster_name, node_count, vpc_id...
│   │   └── outputs.tf      ← cluster_endpoint, cluster_name, oidc_arn
│   └── iam/
│       ├── main.tf         ← IAM roles za EKS, IRSA, node groups
│       ├── variables.tf
│       └── outputs.tf      ← role ARN-ovi
└── envs/
    ├── dev/
    │   ├── main.tf         ← poziva module
    │   ├── variables.tf
    │   ├── outputs.tf
    │   └── dev.tfvars
    ├── staging/
    │   ├── main.tf
    │   ├── variables.tf
    │   ├── outputs.tf
    │   └── staging.tfvars
    ├── prod/
    └── dynamic/            ← za review environments
```

## Module inputs i outputs

Primjer VPC modula:

```hcl
# modules/vpc/variables.tf
variable "environment" {
  type = string
}

variable "vpc_cidr" {
  type    = string
  default = "10.0.0.0/16"
}

variable "availability_zones" {
  type    = list(string)
}
```

```hcl
# modules/vpc/outputs.tf
output "vpc_id" {
  value = aws_vpc.main.id
}

output "private_subnet_ids" {
  value = aws_subnet.private[*].id
}

output "public_subnet_ids" {
  value = aws_subnet.public[*].id
}
```

Root modul poziva vpc modul:

```hcl
# envs/dev/main.tf

module "vpc" {
  source = "../../modules/vpc"

  environment        = var.environment
  vpc_cidr           = var.vpc_cidr
  availability_zones = ["eu-central-1a", "eu-central-1b", "eu-central-1c"]
}

module "eks" {
  source = "../../modules/eks"

  cluster_name    = "${var.environment}-helloworld"
  vpc_id          = module.vpc.vpc_id             # output VPC modula
  subnet_ids      = module.vpc.private_subnet_ids  # output VPC modula
  node_count      = var.cluster_node_count
  instance_type   = var.cluster_node_instance_type

  depends_on = [module.vpc]   # explicit dependency ako Terraform ne može sam zaključiti
}

module "iam" {
  source = "../../modules/iam"

  environment      = var.environment
  eks_cluster_name = module.eks.cluster_name
  oidc_provider_arn = module.eks.oidc_provider_arn
}
```

`module.vpc.vpc_id` — pristup output-u child modula.
Format: `module.IME_MODULA.OUTPUT_NAME`

## Versioning modula

Za interne module koji žive u istom repozitorijumu, koristis relativne putanje.

Za module iz Git repozitorijuma:

```hcl
module "vpc" {
  source = "git::https://gitlab.com/firma/terraform-modules.git//vpc?ref=v2.3.0"
  ...
}
```

`?ref=v2.3.0` — pinuje na tag. Bez pina, uvijek bi se vukla main grana
i promjena u modulu bi mogla razbiti tvoj deployment bez tvog znanja.

Za javne module iz Terraform Registry:

```hcl
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.0"   # 20.x, ne 21.x
  ...
}
```

## Praktičan primjer — VPC modul sa inputs za CIDR i env name

```hcl
# modules/vpc/main.tf

locals {
  name = "${var.environment}-helloworld"
  azs  = var.availability_zones
  
  private_cidrs = [for i, az in local.azs : cidrsubnet(var.vpc_cidr, 4, i)]
  public_cidrs  = [for i, az in local.azs : cidrsubnet(var.vpc_cidr, 4, i + length(local.azs))]
}

resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = { Name = "${local.name}-vpc" }
}

resource "aws_subnet" "private" {
  count             = length(local.azs)
  vpc_id            = aws_vpc.main.id
  cidr_block        = local.private_cidrs[count.index]
  availability_zone = local.azs[count.index]

  tags = { Name = "${local.name}-private-${local.azs[count.index]}" }
}

resource "aws_subnet" "public" {
  count                   = length(local.azs)
  vpc_id                  = aws_vpc.main.id
  cidr_block              = local.public_cidrs[count.index]
  availability_zone       = local.azs[count.index]
  map_public_ip_on_launch = true

  tags = { Name = "${local.name}-public-${local.azs[count.index]}" }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  tags   = { Name = "${local.name}-igw" }
}

resource "aws_nat_gateway" "main" {
  count         = length(local.azs)
  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id
  tags          = { Name = "${local.name}-nat-${count.index}" }
}

resource "aws_eip" "nat" {
  count  = length(local.azs)
  domain = "vpc"
}
```

Isti modul, isti kod — razlika je samo u `var.vpc_cidr` i `var.environment`.
Dev dobija `10.10.0.0/16`, prod dobija `10.30.0.0/16`. Nema copy-paste.

## Veza sa project-A

EKS modul koristi VPC output:

```hcl
# envs/dev/main.tf (skraceno)
module "vpc" {
  source             = "../../modules/vpc"
  environment        = "dev"
  vpc_cidr           = "10.10.0.0/16"
  availability_zones = data.aws_availability_zones.available.names
}

module "eks" {
  source         = "../../modules/eks"
  cluster_name   = "dev-helloworld"
  vpc_id         = module.vpc.vpc_id
  subnet_ids     = module.vpc.private_subnet_ids
  node_count     = 2
  instance_type  = "t3.medium"
}
```

Ista `main.tf` struktura za staging i prod — samo drugačije vrijednosti varijabli.
