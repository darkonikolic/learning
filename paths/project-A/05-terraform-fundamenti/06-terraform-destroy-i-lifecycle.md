# 06 — Terraform destroy i lifecycle

## terraform destroy

`terraform destroy` uništava sve resurse koje Terraform trenutno prati u state-u.
Izvrsava u obrnutom redosledu od kreiranja — respektuje dependency graph.

```bash
# Prikazuje šta će biti uništeno (bez primjene)
terraform plan -destroy

# Uništava sve resurse (traži potvrdu: "yes")
terraform destroy

# Uništava bez pitanja (za CI/CD)
terraform destroy -auto-approve
```

Primjer redosljeda brisanja za project-A stack:
1. EKS Node Groups (EC2 instance)
2. EKS Cluster
3. NAT Gateways
4. Elastic IPs
5. Private Subnets
6. Public Subnets
7. Internet Gateway
8. VPC

Terraform zna ovaj redosled jer su resursi u dependency grafu:
EKS zavisi od VPC-a, pa se EKS briše prvi.

## Zašto je destroy jednako važan kao create

**Cost management** — AWS naplacuje po satu. EKS cluster koji stoji tokom vikenda
kosta isti novac kao da radi.

Strategija za project-A:
- Dev cluster: destroy svake noći u ponoć, create ujutro (GitLab CI scheduler)
- Review envs: destroy čim se MR zatvori ili merguje
- Staging: stoji neprekidno (CI treba uvijek biti dostupan za testiranje)
- Prod: nikad nije downtime (destroy samo za major migracije)

Ustedevina na dev okruzenjima: 2 x `t3.medium` EKS nodova ≈ $0.08/h = ~$58/mj.
Ako radi samo 8h/dan: $58 × (8/24) = ~$19/mj. Ustedjeno $39/mj bez gubljenja funkcionalnosti.

**Ephemeral environments** — review apps za svaki MR trebaju biti privremene.
Bez destroy, akumuliraš cluster resurse za svaki MR koji je ikad otvoren.

**Clean state za testiranje** — pouzdano testiranje infrastruktura promjena zahtijeva
čist početak. Destroy + apply garantuje da testiiraš kreiranje, ne patch.

## Lifecycle meta-arguments

Lifecycle blok kontroliše ponašanje Terraform-a prema specifičnom resursu.

### prevent_destroy

```hcl
resource "aws_s3_bucket" "terraform_state" {
  bucket = "firma-terraform-state"

  lifecycle {
    prevent_destroy = true
  }
}
```

`prevent_destroy = true` — Terraform odbija `destroy` za ovaj resurs, čak i u
okviru `terraform destroy` koji briše sve. Mora se ručno ukloniti iz konfiguracije
da bi se resurs mogao obrisati.

Koristiti za: S3 state bucket, prod database, sve što bi gubitak podataka bio katastrofičan.

### create_before_destroy

```hcl
resource "aws_launch_template" "app" {
  name_prefix   = "helloworld-"
  image_id      = data.aws_ami.amazon_linux.id

  lifecycle {
    create_before_destroy = true
  }
}
```

Defaultno, Terraform unistate stari resurs pa kreira novi (downtime).
Sa `create_before_destroy = true`, kreira novi resurs, a tek onda briše stari (zero downtime).

Neophodan za resurse koji moraju uvijek biti dostupni tokom zamjene.

### ignore_changes

```hcl
resource "aws_eks_node_group" "main" {
  cluster_name  = aws_eks_cluster.main.name
  node_role_arn = aws_iam_role.node.arn
  
  scaling_config {
    desired_size = 2
    min_size     = 1
    max_size     = 5
  }

  lifecycle {
    ignore_changes = [
      scaling_config[0].desired_size  # AWS Auto Scaling mijenja ovo, ne Terraform
    ]
  }
}
```

`ignore_changes` — Terraform ignoriše promjene na navedenim atributima tokom plan-a.
Korisno kada Kubernetes HPA ili AWS Auto Scaling mjenja broj nodova — ne zelimo da
`terraform plan` kaže "drift detected" svaki put kad autoscaler promijeni desired_size.

## Destroy workflow — sigurno brisanje

Nikad `terraform destroy` bez plana. Uvijek:

```bash
# Korak 1: Pogledaj šta će biti uništeno
terraform plan -destroy -var-file=dev.tfvars

# Korak 2: Review output pažljivo
# Provjeri da li je navedeno ono što očekuješ
# Pazi na resurse sa prevent_destroy (terraform ce failovati ako ih ima)

# Korak 3: Primjeni destroy
terraform destroy -var-file=dev.tfvars
# Upiši "yes" kad pita
```

U CI/CD pipelinu, plan output se sprema kao artifact:

```yaml
tf:plan-destroy:review:
  script:
    - terraform plan -destroy -var="env_name=${MR_ENV}" -out=destroy.plan
  artifacts:
    paths: [destroy.plan]
    
tf:destroy:review:
  script:
    - terraform apply destroy.plan
  when: manual
  needs: [tf:plan-destroy:review]
```

## Partial destroy — brisanje specifičnih resursa

```bash
# Obriši samo EKS node group, ne cijeli stack
terraform destroy -target=aws_eks_node_group.main -var-file=dev.tfvars

# Obriši modul (sve resurse unutar modula)
terraform destroy -target=module.eks -var-file=dev.tfvars
```

Koristiti oprezno — partial destroy može ostaviti infrastructure u nekonzistentnom stanju.
Primjena: smanjivanje troška kad cluster nije potreban, ali VPC infrastruktura treba ostati.

## Veza sa project-A

### Nightly destroy/create za dev

```yaml
# .gitlab-ci.yml
destroy:dev:nightly:
  stage: cleanup
  script:
    - cd terraform/envs/dev
    - terraform init
    - terraform destroy -var-file=dev.tfvars -auto-approve
  rules:
    - if: '$CI_PIPELINE_SOURCE == "schedule"'
  only:
    - schedules

create:dev:morning:
  stage: setup
  script:
    - cd terraform/envs/dev
    - terraform init
    - terraform apply -var-file=dev.tfvars -auto-approve
  rules:
    - if: '$CI_PIPELINE_SOURCE == "schedule"'
```

### Review env lifecycle

```yaml
deploy:review:
  script:
    - terraform apply -var="env_name=mr-${CI_MERGE_REQUEST_IID}"
  environment:
    name: review/mr-$CI_MERGE_REQUEST_IID
    on_stop: destroy:review

destroy:review:
  script:
    - terraform destroy -var="env_name=mr-${CI_MERGE_REQUEST_IID}" -auto-approve
  environment:
    name: review/mr-$CI_MERGE_REQUEST_IID
    action: stop
  when: manual
```

`on_stop: destroy:review` — GitLab automatski ponudi destroy job
kad se environment zatvori (MR merge ili close).
