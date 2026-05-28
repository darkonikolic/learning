# Terraform Infrastruktura

## Pregled arhitekture

Terraform u project-A je organizovan u tri sloja:

1. **bootstrap/** — kreira S3 bucket i DynamoDB za remote state (jednom, ručno)
2. **modules/** — reusable moduli: vpc, eks, iam
3. **envs/** — environment-specifična konfiguracija koja poziva module

Zašto ovako? Moduli se ne mijenjaju često. `envs/dev/main.tf` se mijenja za
dev-specifične parametre. `modules/eks/main.tf` se mijenja kada trebaš novu
EKS funkcionalnost za sve environmente.

## Korak 1: Bootstrap (jednom)

```hcl
# terraform/bootstrap/main.tf
terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
}

provider "aws" { region = var.aws_region }

resource "aws_s3_bucket" "tf_state" {
  bucket = var.state_bucket_name

  lifecycle {
    prevent_destroy = true  # Ovaj bucket NIKAD ne brišeš
  }
}

resource "aws_s3_bucket_versioning" "tf_state" {
  bucket = aws_s3_bucket.tf_state.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "tf_state" {
  bucket = aws_s3_bucket.tf_state.id
  rule {
    apply_server_side_encryption_by_default { sse_algorithm = "AES256" }
  }
}

resource "aws_dynamodb_table" "tf_locks" {
  name         = "terraform-locks"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"
  attribute {
    name = "LockID"
    type = "S"
  }
}
```

```bash
cd terraform/bootstrap
terraform init
terraform apply -var="aws_region=eu-west-1" \
  -var="state_bucket_name=terraform-state-project-a"
```

Ovo radiš jednom, ručno, sa admin kredencijalima. Nakon ovoga, sav ostali
Terraform koristi ovaj S3 bucket za state.

## Korak 2: VPC modul

```hcl
# terraform/modules/vpc/variables.tf
variable "env_name"     { type = string }
variable "aws_region"   { type = string }
variable "vpc_cidr"     { type = string, default = "10.0.0.0/16" }
variable "single_nat"   { type = bool, default = true }  # false za prod
```

```hcl
# terraform/modules/vpc/main.tf
locals {
  azs = ["${var.aws_region}a", "${var.aws_region}b", "${var.aws_region}c"]
}

resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name                                              = "project-a-${var.env_name}"
    "kubernetes.io/cluster/project-a-${var.env_name}" = "shared"
  }
}

resource "aws_subnet" "private" {
  count             = 3
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 4, count.index)
  availability_zone = local.azs[count.index]

  tags = {
    Name                                               = "private-${local.azs[count.index]}"
    "kubernetes.io/cluster/project-a-${var.env_name}"  = "shared"
    "kubernetes.io/role/internal-elb"                  = "1"
  }
}

resource "aws_subnet" "public" {
  count                   = 3
  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 4, count.index + 3)
  availability_zone       = local.azs[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name                                               = "public-${local.azs[count.index]}"
    "kubernetes.io/cluster/project-a-${var.env_name}"  = "shared"
    "kubernetes.io/role/elb"                           = "1"
  }
}
```

Tagovi `kubernetes.io/role/elb = 1` na public subnets su obavezni za AWS ALB
Controller — bez njih ne može kreirati load balancer.

## Korak 3: EKS modul

```hcl
# terraform/modules/eks/variables.tf
variable "env_name"      { type = string }
variable "cluster_name"  { type = string }
variable "k8s_version"   { type = string, default = "1.29" }
variable "vpc_id"        { type = string }
variable "private_subnet_ids" { type = list(string) }
variable "instance_type" { type = string, default = "t3.medium" }
variable "desired_nodes" { type = number, default = 1 }
variable "min_nodes"     { type = number, default = 1 }
variable "max_nodes"     { type = number, default = 3 }
```

Ključni EKS resursi: `aws_eks_cluster`, `aws_eks_node_group`, 
`aws_iam_openid_connect_provider` (za IRSA), IRSA role za Cluster Autoscaler
i AWS Load Balancer Controller.

```bash
# AI prompt za kompletan EKS modul:
# "Napiši terraform/modules/eks/main.tf sa: EKS 1.29, managed node group,
# OIDC provider, IRSA role za Cluster Autoscaler i AWS LB Controller.
# Varijable su definirane u variables.tf. Objasni svaki IAM trust policy."
```

## Korak 4: IAM modul

```hcl
# terraform/modules/iam/main.tf — GitLab CI/CD OIDC role

data "aws_iam_openid_connect_provider" "gitlab" {
  url = "https://gitlab.com"
}

resource "aws_iam_role" "gitlab_ci_dev" {
  name = "project-a-gitlab-ci-${var.env_name}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Federated = data.aws_iam_openid_connect_provider.gitlab.arn
      }
      Action = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringLike = {
          "gitlab.com:sub" = "project_path:${var.gitlab_project_path}:ref_type:branch:ref:*"
        }
      }
    }]
  })
}
```

Condition na `project_path` znači da samo CI/CD jobovi iz tvog projekta mogu
preuzeti ovu role — ne svako ko ima GitLab account.

## Korak 5: Dev environment

```hcl
# terraform/envs/dev/main.tf
terraform {
  backend "s3" {
    bucket         = "terraform-state-project-a"
    key            = "envs/dev/terraform.tfstate"
    region         = "eu-west-1"
    dynamodb_table = "terraform-locks"
    encrypt        = true
  }
}

module "vpc" {
  source     = "../../modules/vpc"
  env_name   = "dev"
  aws_region = "eu-west-1"
  single_nat = true  # Jedna NAT gateway za dev (jeftiniji)
}

module "eks" {
  source             = "../../modules/eks"
  env_name           = "dev"
  cluster_name       = "project-a-dev"
  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  instance_type      = "t3.medium"
  desired_nodes      = 1
}
```

```hcl
# terraform/envs/dev/dev.tfvars
env_name      = "dev"
aws_region    = "eu-west-1"
instance_type = "t3.medium"
desired_nodes = 1
domain_suffix = "dev.firma.com"
```

## Pokretanje i brisanje

```bash
cd terraform/envs/dev

# Inicijalizacija
terraform init

# Plan (uvijek provjeri prije apply)
terraform plan -var-file=dev.tfvars -out=tfplan

# Primijeni
terraform apply tfplan

# Provjeri kreiran klaster
aws eks update-kubeconfig --name project-a-dev --region eu-west-1
kubectl get nodes

# Kada završiš — BRIŠI da izbjegneš troškove
terraform destroy -var-file=dev.tfvars
```

`terraform destroy` mora raditi čisto — bez errora, bez zaostalih resursa.
Testiraj ovo na dev env prije nego pređeš na staging/prod.

## AI workflow za terraform plan

Nakon svakog `terraform plan`, prijepi output u Claude:

```
Ovaj terraform plan output za dev environment:
[prijepi cijeli plan]

1. Šta se kreira/mijenja/briše?
2. Postoje li "forces replacement" resursi? Zašto?
3. Da li procjenjuješ da će ovo povećati AWS troškove?
4. Ima li nešto što mi se čini rizično?
```

Ovo je posebno korisno kod prvih nekoliko applyja dok se privikavaš na to
šta svaki Terraform resurs znači u AWS konzoli.
