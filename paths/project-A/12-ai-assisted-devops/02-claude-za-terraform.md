# Claude za Terraform

## CLAUDE.md snippet za Terraform projekte

Dodaj ovo u `CLAUDE.md` na početku svakog Terraform projekta:

```markdown
## Terraform validation checklist
- required_version i required_providers pinovani (bez ~> Latest ili bez verzije).
- Nema secrets u .tf/.tfvars fajlovima koji se commit-uju — koristi variable bez default-a.
- Svaki resurs nosi standardne tagove: env, project, owner.
- State je remote (S3 + DynamoDB lock), ne lokalni.
- Moduli imaju source sa pinovanom verzijom ili lokalnim relativnim putem.
- Destruktivne izmjene (forces replacement) — uvijek provjeri ručno u plan outputu.
- AWS provider: ~5.0 (ne stariji — kubernetes_network_config mijenja strukturu u v5).
- Region: eu-west-1.
```

Kada Claude generiše Terraform kod, ove napomene su automatski u kontekstu i
sprječavaju najčešće greške (hardcoded AMI ID-ovi, `"Action": "*"`, bez remote state).

## `/plan` workflow prije `terraform apply`

Nikad ne pokrećeš `terraform apply` direktno. Workflow u Claude Code terminalu:

```
/plan

"Imam završen Terraform modul za EKS. Trebaš provjeriti plan output
i identifikovati sve destruktivne promjene ili potencijalne troškove
prije apply-a."
```

Claude će pregledati plan output koji mu zalijepiš i identificovati:
- `# forces replacement` linije (resursi koji se brišu i ponovo kreiraju)
- Potencijalne troškove (novi ELB, RDS, NAT gateway)
- Sigurnosne probleme (široke security group rules, javni S3 bucket)

Tek nakon Claude pregleda — i tvog ručnog pregleda — pokreni `terraform apply tfplan`.

## Efikasni promptovi za Terraform

Loš prompt daje generički kod koji možda radi, ali ne razumiješ zašto.
Dobar prompt daje kod sa objašnjenjem, verzijama i konkretnim kontekstom.

### Generisanje EKS clustera

```
Napiši Terraform modul za EKS cluster sa sljedećim:
- AWS provider ~5.0, Terraform 1.7+
- Managed node group (t3.medium, min 1 / max 3 / desired 1)
- OIDC provider (potreban za IRSA)
- Cluster Autoscaler IRSA role
- Kubernetes verzija 1.29
- Tagovi: Environment = var.env_name, Project = "project-a"

Objasni svaki resurs i zašto postoji.
Pokaži i output vrijednosti koje bi trebalo eksportovati.
```

Šta dobijaš: `aws_eks_cluster`, `aws_eks_node_group`, `aws_iam_openid_connect_provider`,
`aws_iam_role` za autoscaler, outputs. Plus objašnjenje zašto OIDC postoji
(da bi podovi mogli preuzeti IAM permisije bez da node ima široke permisije).

### Analiza terraform plan outputa

Nakon `terraform plan -out=tfplan && terraform show tfplan`, prijepi output u Claude:

```
Ovaj terraform plan output sam dobio za dev okruženje. Pregled:
[prijepi plan output]

Pitanja:
1. Šta će se tačno promeniti i ima li nešto destruktivno (forces replacement)?
2. Da li ima nešto što može povećati AWS troškove?
3. Da li postoji nešto rizično što bih trebao provjeriti?
```

Ovo je posebno korisno kada plan prikazuje 50+ resursa i ne znaš šta gledati.
Claude identificuje `# forces replacement` linije i objasni zašto dolazi do
destrukcije (npr. promijenio si `availability_zone` na EBS volumenu).

### Refaktorisanje u module

```
Imam ovaj Terraform kod koji je sve u jednom fajlu:
[prijepi main.tf]

Refaktoriši ga u module sa sljedećom strukturom:
- modules/vpc/ — sve VPC resurse
- modules/eks/ — EKS cluster i node group
- modules/iam/ — IAM roleovi i politike

Svaki modul treba: variables.tf, main.tf, outputs.tf
Ulazne varijable treba da budu: env_name, aws_region, instance_type, node_count
```

## Iterativni workflow sa Terraformom

Ne pokušavaš dobiti savršen kod u jednom promptu. Workflow je:

**Korak 1 — Generiši osnovu**
```
Napiši Terraform za VPC sa public i private subnets u eu-west-1.
2 AZ-a, NAT gateway, tagovi za EKS (kubernetes.io/cluster/project-a-dev = shared).
```

**Korak 2 — Pokreni validaciju**
```bash
docker run --rm -v $(pwd):/tf hashicorp/terraform:1.7 -chdir=/tf validate
```

Ako ima errora, prijepi ih nazad u Claude: "validate daje ove greške: [error]".

**Korak 3 — Pitaj za objašnjenje specifičnog dijela**
```
U generisanom kodu imaš ovaj blok:
  lifecycle {
    create_before_destroy = true
  }

Zašto je ovo potrebno na NAT gateway resursu?
```

**Korak 4 — Traži poboljšanja**
```
Ovaj VPC modul radi. Šta bih trebalo dodati za production-readiness?
(ne treba mi sve odmah — samo lista sa objašnjenjem prioriteta)
```

## Verifikacija AI-generisanog Terraform koda

Nikad ne applyuješ direktno. Pipeline za svaki push:

```bash
# 1. Formatiranje
terraform fmt -check -recursive

# 2. Validacija sintakse
terraform validate

# 3. Statička analiza sigurnosti
docker run --rm -v $(pwd):/src aquasec/tfsec /src

# 4. Plan review
terraform plan -out=tfplan
terraform show -json tfplan | jq '.resource_changes[] | select(.change.actions[] | contains("delete"))'
```

Zadnja komanda listuje sve resurse koji će biti obrisani — uvijek provjeri ovo
prije `terraform apply`.

## Česte greške AI-generisanog Terraform koda

**1. Zastarjele verzije providera**

AI može generisati kod za stariji AWS provider. Provjeri:
```hcl
# Ovo možda ne radi sa ~5.0
resource "aws_eks_cluster" "main" {
  # kubernetes_network_config je promjenio strukturu u v5
}
```
Prompt: "Provjeri da li je ovaj kod kompatibilan sa AWS provider 5.x i isprav sve deprecations."

**2. Previše široke IAM permisije**

AI često generisuje `"Action": "*"` ili `"Resource": "*"` za jednostavnost.
Uvijek pitaj: "Smanji ove IAM permisije na least privilege za EKS node koji
treba da: pull Docker image iz ECR, write CloudWatch logs, pull Secrets Manager secret."

**3. Hardkodovane vrijednosti**

```hcl
# Loše — AI često generiše ovako
resource "aws_instance" "worker" {
  ami = "ami-0123456789abcdef0"  # hardkodovan!
  instance_type = "t3.medium"
}
```

Prompt: "Zamjeni sve hardkodovane vrijednosti sa varijablama ili data sourcevima."

**4. Nedostaje `prevent_destroy` za produkciju**

```hcl
# AI ne dodaje ovo automatski
lifecycle {
  prevent_destroy = true  # štiti prod resurse od slučajnog destroy
}
```

**5. State backend nije konfigurisan**

AI generisani kod često nema remote backend. Za project-A:
```hcl
terraform {
  backend "s3" {
    bucket         = var.tf_state_bucket  # iz CI/CD variable
    key            = "envs/dev/terraform.tfstate"
    region         = "eu-west-1"
    dynamodb_table = "terraform-locks"
    encrypt        = true
  }
}
```

## Veza sa project-A

Konkretni promptovi za svaki Terraform dio projekta:

```
# Za bootstrap
"Napiši Terraform koji kreira S3 bucket sa versioning i DynamoDB tabelu
za Terraform state locking. Region eu-west-1, bucket name iz varijable."

# Za modules/vpc
"VPC za EKS u eu-west-1: 3 public, 3 private subnets (po jedna po AZ),
NAT gateway (single za dev, po AZ za prod — varijabla), tagovi za EKS
Load Balancer Controller."

# Za modules/eks
"EKS 1.29, managed node group, OIDC, addon: CoreDNS + kube-proxy + VPC CNI.
IRSA role za: Cluster Autoscaler, AWS Load Balancer Controller, External DNS."
```
