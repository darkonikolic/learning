# Multi-environment setup

## Isti moduli, različiti parametri

Snaga modularnog pristupa: `envs/dev/main.tf` i `envs/prod/main.tf` su gotovo identični — jedina razlika su vrijednosti varijabli. Ako popraviš bug u `modules/vpc/main.tf`, popravka važi za sve environment-e.

## `envs/dev/main.tf`

```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Kubernetes provider koristi EKS cluster credentials
provider "kubernetes" {
  host                   = module.eks.cluster_endpoint
  cluster_ca_certificate = base64decode(module.eks.cluster_ca)
  exec {
    api_version = "client.authentication.k8s.io/v1beta1"
    command     = "aws"
    args        = ["eks", "get-token", "--cluster-name", module.eks.cluster_name]
  }
}

provider "helm" {
  kubernetes {
    host                   = module.eks.cluster_endpoint
    cluster_ca_certificate = base64decode(module.eks.cluster_ca)
    exec {
      api_version = "client.authentication.k8s.io/v1beta1"
      command     = "aws"
      args        = ["eks", "get-token", "--cluster-name", module.eks.cluster_name]
    }
  }
}

module "vpc" {
  source = "../../modules/vpc"

  env_name           = "dev"
  cluster_name       = "project-a-dev"
  vpc_cidr           = var.vpc_cidr
  availability_zones = var.availability_zones
  enable_nat_gateway = var.enable_nat_gateway
}

module "eks" {
  source = "../../modules/eks"

  cluster_name       = "project-a-dev"
  env_name           = "dev"
  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  node_instance_type = var.node_instance_type
  desired_nodes      = var.desired_nodes
  min_nodes          = var.min_nodes
  max_nodes          = var.max_nodes
}

module "iam" {
  source = "../../modules/iam"

  cluster_name          = "project-a-dev"
  env_name              = "dev"
  oidc_provider_arn     = module.eks.oidc_provider_arn
  oidc_provider_url     = module.eks.oidc_provider_url
  gitlab_project_path   = var.gitlab_project_path
  gitlab_oidc_provider_arn = var.gitlab_oidc_provider_arn
  region                = var.aws_region
  account_id            = data.aws_caller_identity.current.account_id
}

data "aws_caller_identity" "current" {}
```

## `envs/dev/dev.tfvars`

```hcl
aws_region         = "eu-west-1"
vpc_cidr           = "10.0.0.0/16"
availability_zones = ["eu-west-1a"]   # jedan AZ za dev (ušteda)
enable_nat_gateway = false             # bez NAT za dev (ušteda $32/mj)

node_instance_type = "t3.medium"
desired_nodes      = 1
min_nodes          = 1
max_nodes          = 3

gitlab_project_path      = "user/project-a"
gitlab_oidc_provider_arn = "arn:aws:iam::123456789:oidc-provider/gitlab.com"
```

## `envs/staging/staging.tfvars`

```hcl
aws_region         = "eu-west-1"
vpc_cidr           = "10.1.0.0/16"
availability_zones = ["eu-west-1a", "eu-west-1b"]  # HA za staging
enable_nat_gateway = true

node_instance_type = "t3.large"
desired_nodes      = 2
min_nodes          = 2
max_nodes          = 5

gitlab_project_path      = "user/project-a"
gitlab_oidc_provider_arn = "arn:aws:iam::123456789:oidc-provider/gitlab.com"
```

## `envs/prod/prod.tfvars`

```hcl
aws_region         = "eu-west-1"
vpc_cidr           = "10.2.0.0/16"
availability_zones = ["eu-west-1a", "eu-west-1b", "eu-west-1c"]  # 3 AZ za prod
enable_nat_gateway = true

node_instance_type = "t3.xlarge"
desired_nodes      = 3
min_nodes          = 3
max_nodes          = 10

gitlab_project_path      = "user/project-a"
gitlab_oidc_provider_arn = "arn:aws:iam::123456789:oidc-provider/gitlab.com"
```

## Backend konfiguracija po environmentu

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

### `envs/prod/backend.tf`

```hcl
terraform {
  backend "s3" {
    bucket         = "project-a-terraform-state"
    key            = "prod/terraform.tfstate"   # jedina razlika — key
    region         = "eu-west-1"
    encrypt        = true
    dynamodb_table = "project-a-terraform-locks"
  }
}
```

Isti S3 bucket, različiti key. State je fizički odvojen — nema rizika od cross-environment kontaminacije.

## Workflow

```bash
# Dev deploy
cd terraform/envs/dev
terraform init
terraform plan -var-file=dev.tfvars -out=dev.plan
terraform apply dev.plan

# Staging deploy (isti komandi, drugi direktorij)
cd terraform/envs/staging
terraform init
terraform plan -var-file=staging.tfvars -out=staging.plan
terraform apply staging.plan
```

`terraform init` mora biti pokrenut svaki put u novom direktoriju ili nakon promjene providera — inicijalizuje backend i download-uje provider pluginove.

## Razlike koje su namjerne

| Parametar | Dev | Staging | Prod |
|-----------|-----|---------|------|
| AZ count | 1 | 2 | 3 |
| NAT Gateway | Ne | Da | Da |
| Node type | t3.medium | t3.large | t3.xlarge |
| Node count | 1 | 2 | 3+ |
| Spot instances | Da | Da | Ne |
| prevent_destroy | Ne | Ne | Da |

Staging je namjerno bliži prod-u nego dev-u. Problemi sa HA, NAT, multi-AZ pojavljuju se u staging-u, ne u prod-u.
