# 05 — Workspaces i environments

## Workspace vs zasebni direktorijumi

Terraform nudi dvije strategije za upravljanje višestrukim okruženjima.

**Terraform workspaces** — jedan direktorijum, više state fajlova.
Prebacivanje između okruženja sa `terraform workspace select dev`.

**Zasebni direktorijumi** — svako okruženje ima vlastiti `envs/dev/`, `envs/staging/`, `envs/prod/`.
Svaki direktorijum ima vlastiti state i vlastiti `terraform apply`.

## Zašto zasebni direktorijumi za project-A

### Izolacija state-a

Sa workspacima, svi state fajlovi su u istom backend S3 bucket-u, ali pod različitim ključevima.
Greška u workspace managementu (npr. zaboraviti prebaciti workspace) može primjeniti
promjene na pogrešno okruženje.

Sa zasebnim direktorijumima, `cd envs/prod && terraform apply` — nemoguće je
greškom primjeniti prod promjene dok si u dev direktorijumu.

### Različite konfiguracije backend-a

```hcl
# envs/dev/versions.tf
terraform {
  backend "s3" {
    bucket = "firma-terraform-state"
    key    = "helloworld/dev/terraform.tfstate"
    region = "eu-central-1"
  }
}

# envs/prod/versions.tf
terraform {
  backend "s3" {
    bucket = "firma-terraform-state-prod"  # zasebni bucket za prod!
    key    = "helloworld/prod/terraform.tfstate"
    region = "eu-central-1"
  }
}
```

Prod može imati strožije IAM permisije na state bucket — samo prod CI/CD rola
ima pristup prod state-u.

### Različiti AWS accounti

Velika organizacija može imati zasebne AWS accounte za dev i prod.
Workspacesi ne podrzavaju različite AWS accounte — zasebni direktorijumi da.

## Workspace koristiti samo za ephemeral okruženja

Jedini legitiman slucaj za workspacese u project-A:
dynamic review environments koji su identični osim env_name varijable.

```bash
# CI job za otvaranje MR
terraform workspace new mr-${CI_MERGE_REQUEST_IID}
terraform apply -var="env_name=mr-${CI_MERGE_REQUEST_IID}"

# CI job za zatvaranje MR
terraform workspace select mr-${CI_MERGE_REQUEST_IID}
terraform destroy -var="env_name=mr-${CI_MERGE_REQUEST_IID}"
terraform workspace select default
terraform workspace delete mr-${CI_MERGE_REQUEST_IID}
```

Alternativno, čak i za review envs, zasebni state key je sigurniji:

```hcl
# envs/dynamic/versions.tf — bez hardkodiranog key-a
terraform {
  backend "s3" {
    bucket = "firma-terraform-state"
    # key se proslijedi kao -backend-config argument
    region = "eu-central-1"
  }
}
```

```bash
terraform init -backend-config="key=helloworld/mr-${MR_ID}/terraform.tfstate"
terraform apply -var="env_name=mr-${MR_ID}"
```

## Struktura project-A envs direktorijuma

```
terraform/envs/
├── dev/
│   ├── versions.tf     ← backend config za dev
│   ├── main.tf         ← module pozivi
│   ├── variables.tf    ← variable deklaracije
│   ├── outputs.tf
│   └── dev.tfvars      ← vrijednosti za dev
├── staging/
│   ├── versions.tf
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   └── staging.tfvars
├── prod/
│   ├── versions.tf
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   └── prod.tfvars
└── dynamic/
    ├── versions.tf     ← bez hardkodiranog backend key-a
    ├── main.tf         ← minimalni resursi za review env
    ├── variables.tf    ← env_name, image_tag
    └── base.tfvars     ← zajedničke vrijednosti za sve review envs
```

## Terraform variables fajl po env

```hcl
# dev.tfvars
environment                = "dev"
aws_region                 = "eu-central-1"
cluster_node_count         = 2
cluster_node_instance_type = "t3.medium"
vpc_cidr                   = "10.10.0.0/16"
enable_nat_gateway         = true
single_nat_gateway         = true    # jedan NAT gateway za dev (ustedivanje)

# prod.tfvars
environment                = "prod"
aws_region                 = "eu-central-1"
cluster_node_count         = 5
cluster_node_instance_type = "t3.xlarge"
vpc_cidr                   = "10.30.0.0/16"
enable_nat_gateway         = true
single_nat_gateway         = false   # NAT gateway po AZ za HA
```

`single_nat_gateway` je dobar primjer cost vs availability tradeoff:
- Dev: jedan NAT gateway = manje troska, prihvatljiv single point of failure
- Prod: NAT po AZ = viši trošak ali nema downtime pri AZ failure-u

## Praktičan primjer — isti modul, različiti parametri

```hcl
# envs/dev/main.tf
module "vpc" {
  source = "../../modules/vpc"

  environment        = var.environment      # "dev"
  vpc_cidr           = var.vpc_cidr         # "10.10.0.0/16"
  availability_zones = ["eu-central-1a", "eu-central-1b"]
  single_nat_gateway = var.single_nat_gateway  # true
}

# envs/prod/main.tf — identičan poziv, drugačije vrijednosti
module "vpc" {
  source = "../../modules/vpc"

  environment        = var.environment      # "prod"
  vpc_cidr           = var.vpc_cidr         # "10.30.0.0/16"
  availability_zones = ["eu-central-1a", "eu-central-1b", "eu-central-1c"]
  single_nat_gateway = var.single_nat_gateway  # false
}
```

`main.tf` je identičan. Razlika je isključivo u `.tfvars` fajlovima.

## Veza sa project-A

GitLab CI struktura za Terraform:

```yaml
# .gitlab-ci.yml (terraform jobs)

tf:plan:dev:
  stage: plan
  script:
    - cd terraform/envs/dev
    - terraform init
    - terraform plan -var-file=dev.tfvars -out=plan.tfplan
  artifacts:
    paths: [terraform/envs/dev/plan.tfplan]

tf:apply:dev:
  stage: apply
  script:
    - cd terraform/envs/dev
    - terraform init
    - terraform apply plan.tfplan
  when: manual   # čeka odobrenje
  needs: [tf:plan:dev]

tf:destroy:review:
  stage: cleanup
  script:
    - cd terraform/envs/dynamic
    - terraform init -backend-config="key=helloworld/mr-${CI_MERGE_REQUEST_IID}/terraform.tfstate"
    - terraform destroy -var="env_name=mr-${CI_MERGE_REQUEST_IID}" -auto-approve
  when: manual
  environment:
    name: review/mr-$CI_MERGE_REQUEST_IID
    action: stop
```

`when: manual` za apply i destroy prod — niko ne deploya u produkciju bez klikanja.
