# 01 — IaC i Terraform koncepti

## Infrastruktura kao kod — zašto

Zamisliz situaciju: imaš AWS EKS cluster koji si kliknuo kroz konzolu.
Radi savrseno. Tri mjeseca kasnije trebas identičan cluster za staging.
Sjećas li se svakog kliknutog podešavanja? Node group instance type? Subnet CIDR?
Security group rules? IAM politike?

IaC (Infrastructure as Code) rješava ovaj problem: sva konfiguracija je u fajlovima.
Git repozitorijum čuva sve promjene, ko ih je napravio i zašto (commit poruke).
Novi cluster kreiras pokretanjem jedne komande. Nema klikanja.

Tri ključne prednosti:

**Reproduktivnost** — isti kod uvijek kreira isti rezultat.
Dev i prod okruženja su identična osim eksplicitnih razlika u varijabilima.

**Version control** — svaka promjena infrastrukture prolazi kroz Git.
Audit trail za compliance. Mogućnost rollback-a.

**Automatizacija** — CI/CD pipeline može kreirati i uništavati okruženja bez
ljudske intervencije. Review env za svaki MR? Automatski.

## Terraform vs alternativa

**Terraform (HashiCorp)** — HCL jezik, provider ekosistem za svaki cloud/servis,
state management, plan/apply workflow.

**Ansible** — fokus na konfiguraciju servera (software, files, services).
Proceduralni pristup, ne deklarativan. Bolje za upravljanje OS-om nego cloud resursima.
Često se koristi zajedno sa Terraform: Terraform kreira VM, Ansible konfiguriše OS.

**Pulumi** — programski jezici (Python, TypeScript, Go) umjesto HCL.
Moćniji za složenu logiku, ali teži za čitanje. Tim mora znati programski jezik.

**AWS CDK** — AWS-specific. TypeScript/Python. Samo za AWS.

**Zašto Terraform za project-A:**
- Multi-cloud podrška (AWS danas, možda GCP sutra)
- Veliki ekosistem gotovih modula (terraform-aws-modules)
- Plan output — vidis šta će se promijeniti prije primjene
- Standardni alat koji zna većina DevOps inženjera
- OpenTofu je open-source fork ako HashiCorp licenca postane problem

## HCL — HashiCorp Configuration Language

HCL je deklarativan jezik. Opisuješ šta hoces, ne kako da to postignes.

```hcl
resource "aws_s3_bucket" "app_assets" {
  bucket = "firma-helloworld-assets"
  
  tags = {
    Environment = "prod"
    Project     = "helloworld"
  }
}
```

Ovo kaze: "Zelim S3 bucket sa ovim imenom i tagovima."
Terraform je odgovoran za to kako ce taj bucket nastati.

Human-readable: čovjek može pročitati i razumjeti infrastrukturu bez
poznavanja AWS API-ja.

## Desired state vs current state

Terraform drzi dva stanja:

**Desired state** — ono što piše u `.tf` fajlovima. Šta hoceš da postoji.

**Current state** — ono što je zapisano u `.tfstate` fajlu. Šta Terraform misli da postoji.

Kada pokreneš `terraform plan`, Terraform:
1. Učita desired state iz `.tf` fajlova
2. Učita current state iz `.tfstate`
3. Povuče actual state sa cloud API-ja
4. Poredi sve tri verzije
5. Ispiše šta treba kreirati, mijenjati ili uništiti

Ako neko ručno promijeni resurs u AWS konzoli mimo Terraform-a,
`terraform plan` će to detektovati i predložiti vraćanje na desired state.
Ovo je **drift detection** — detekcija odstupanja od željenog stanja.

## Terraform CREATE i DESTROY

Terraform nije samo za kreiranje infrastrukture. Destroy je jednako važan.

Za project-A, postoje scenariji gdje infrastruktura živi kratko:
- Review env za MR: kreira se kad se MR otvori, uništava kad se zatvori
- Dev cluster: može se uništiti svake noći da uštedi novac

```bash
# Kreira sve resurse u state-u
terraform apply

# Uništava sve resurse u state-u, u obrnutom redosledu
terraform destroy
```

Destroy je siguran jer Terraform zna redosled — ne možeš uništiti VPC
dok u njemu postoje resursi. Terraform planira ispravan redosled brisanja.

## Veza sa project-A

Kompletna AWS infrastruktura živi u kodu:

```
terraform/
├── modules/
│   ├── vpc/          ← VPC, subnets, routing
│   ├── eks/          ← EKS cluster i node groups
│   └── iam/          ← IAM roles i policies
└── envs/
    ├── dev/          ← dev.tfvars + main.tf koji poziva module
    ├── staging/
    ├── prod/
    └── dynamic/      ← za review envs (MR-specifični)
```

Komanda za kreiranje dev okruženja:

```bash
cd terraform/envs/dev
terraform init
terraform apply -var-file=dev.tfvars
```

Komanda za uništavanje review env-a kad se MR zatvori:

```bash
cd terraform/envs/dynamic
terraform destroy -var="env_name=mr-123" -var-file=base.tfvars
```
