# Terraform struktura projekta

## Zašto je struktura bitna

Terraform može biti jedna `main.tf` datoteka sa svim resursima. To funkcioniše za "hello world" demo, ali ne za projekt koji ima 3 environment-a, timsm saradnju i 6 meseci životnog vijeka.

Dobra struktura rješava tri problema:
1. **Izolacija state-a**: greška u dev ne može uticati na prod state
2. **Ponovljivost**: isti modul kreira iste resurse u svakom environmentu
3. **Čitljivost**: novi član tima može razumjeti gdje je što bez vodača

## Kompletna Terraform struktura za project-A

```
terraform/
├── modules/
│   ├── vpc/
│   │   ├── main.tf        ← svi VPC resursi
│   │   ├── variables.tf   ← input parametri
│   │   └── outputs.tf     ← eksportovane vrijednosti
│   ├── eks/
│   │   ├── main.tf        ← EKS cluster, node groups, add-ons
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── iam/
│   │   ├── main.tf        ← IAM role, politike, OIDC provider
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── alb-controller/
│   │   ├── main.tf        ← Helm release, IRSA role
│   │   ├── variables.tf
│   │   └── outputs.tf
│   └── dns/
│       ├── main.tf        ← Route53 records, ACM certificate
│       ├── variables.tf
│       └── outputs.tf
├── envs/
│   ├── dev/
│   │   ├── main.tf        ← poziva module sa dev parametrima
│   │   ├── dev.tfvars     ← varijable specifične za dev
│   │   ├── backend.tf     ← S3 remote state za dev
│   │   └── providers.tf   ← AWS, Kubernetes, Helm provider konfiguracija
│   ├── staging/
│   │   ├── main.tf
│   │   ├── staging.tfvars
│   │   ├── backend.tf
│   │   └── providers.tf
│   ├── prod/
│   │   ├── main.tf
│   │   ├── prod.tfvars
│   │   ├── backend.tf
│   │   └── providers.tf
│   └── dynamic/
│       ├── main.tf        ← namespace + Route53 za review envs
│       ├── variables.tf
│       └── backend.tf     ← state key uključuje env_name varijablu
└── bootstrap/
    ├── main.tf            ← S3 bucket + DynamoDB za state management
    └── outputs.tf
```

## Uloga svakog sloja

### `modules/` — gradivni blokovi

Modul ne zna za environment. `modules/vpc/main.tf` kreira VPC bez hardkodiranih CIDR-ova ili environment naziva. Sve su parametri. Isti modul se koristi za dev, staging, prod — samo sa drugačijim values.

Modul ima jasno definirani interface:
- `variables.tf`: šta modul prima
- `outputs.tf`: šta modul vraća (korisno za međumodulne zavisnosti)

### `envs/` — environment-specifična kompozicija

`envs/dev/main.tf` ne kreira resurse direktno — poziva module:

```hcl
module "vpc" {
  source = "../../modules/vpc"

  env_name           = "dev"
  vpc_cidr           = var.vpc_cidr
  availability_zones = var.availability_zones
}

module "eks" {
  source = "../../modules/eks"

  cluster_name       = "project-a-dev"
  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  node_instance_type = var.node_instance_type
}
```

### `bootstrap/` — jednom se pokreće

Bootstrap kreira S3 bucket i DynamoDB tabelu koji su potrebni za remote state. Ovo je jedini Terraform koji koristi lokalni state. Nakon kreiranja, nikad se ne briše.

## Zašto ovakav pristup, a ne Terragrunt

Terragrunt je wrapper koji dodaje DRY (Don't Repeat Yourself) principe na Terraform. Za project-A: Terraform native moduli su dovoljni. Terragrunt dodaje kompleksnost (novi alat, nova sintaksa) bez proporcionalne koristi za projekt ovog obima.

Kada razmotriti Terragrunt: 10+ environment-a, 20+ modula, multi-account AWS setup.

## State izolacija

Svaki environment ima vlastiti `backend.tf` sa različitim S3 key-em:
- dev state: `s3://project-a-state/dev/terraform.tfstate`
- staging state: `s3://project-a-state/staging/terraform.tfstate`
- prod state: `s3://project-a-state/prod/terraform.tfstate`

`terraform plan` u `envs/dev/` nikad ne čita prod state. Izolacija je fizička.
