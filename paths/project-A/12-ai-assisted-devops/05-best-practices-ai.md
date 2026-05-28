# Best Practices za AI u DevOps-u

## Šta uvijek davati AI kao kontekst

AI generiše bolji kod kada zna tačno okruženje. Uvijek uključi:

**Verzije alata:**
```
Terraform 1.7, AWS provider ~5.0
Kubernetes 1.29 (EKS)
Helm 3.14
GitLab CI 16.x
Docker buildx
```

**Cloud provider specifičnosti:**
```
AWS region: eu-west-1
EKS networking: VPC CNI
Load Balancer: AWS ALB Controller (ne nginx ingress na EKS)
Cert management: ACM (ne cert-manager na AWS)
```

**Existing konfiguracija:**
```
Imam VPC sa CIDR 10.0.0.0/16, private subnets 10.0.1-3.0/24
EKS cluster se zove project-a-dev
S3 bucket za state: terraform-state-project-a
```

**Ograničenja:**
```
Sve mora biti u Docker kontejnerima (ne bare metal alati)
IAM permisije: koristim OIDC, ne access keys
Registry: GitLab Container Registry (ne ECR)
```

Bez ovog konteksta, AI može generisati kod za AWS us-east-1, sa nginx ingress
umjesto ALB, sa cert-manager umjesto ACM — i sve to će izgledati ispravno ali
neće raditi u tvom setup-u.

## Verifikuj prije deploya

Zlatno pravilo: nikad ne deployas AI-generisan kod direktno na produkciju bez
da ga razumiješ i testiraš.

**Pipeline za svaki AI-generisan Terraform:**
```bash
# Korak 1: Validacija sintakse
terraform validate

# Korak 2: Formatiranje (da je konzistentno)
terraform fmt -diff

# Korak 3: Statička analiza
docker run --rm -v $(pwd):/src aquasec/tfsec /src --no-color

# Korak 4: Plan review — čitaj output liniju po liniju
terraform plan -out=tfplan

# Korak 5: Provjeri destruktivne promjene
terraform show -json tfplan | \
  jq '.resource_changes[] | select(.change.actions | contains(["delete"]))'

# Tek nakon što razumiješ svaku liniju plana:
terraform apply tfplan
```

**Za AI-generisan Kubernetes manifest:**
```bash
# Provjeri sigurnost
docker run --rm -v $(pwd):/data kubesec/kubesec:latest scan /data/deployment.yaml

# Dry run na klasteru
kubectl apply --dry-run=client -f deployment.yaml

# Provjeri diff ako resource već postoji
kubectl diff -f deployment.yaml
```

## Prompt Engineering za DevOps

### Budi specifičan sa verzijama

Loše:
```
Napiši Terraform za EKS.
```

Dobro:
```
Napiši Terraform 1.7 za EKS 1.29 koristeći AWS provider ~5.0.
Managed node group sa t3.medium, OIDC provider, Cluster Autoscaler IRSA.
Namespace je eu-west-1. Koristim VPC sa ID-om koji dolazi kao varijabla.
```

Razlika: AI neće generisati deprecated `kubernetes_network_config` sintaksu
koja je promijenjena u AWS provider v5.

### Traži objašnjenja uz kod

Svaki AI prompt za generisanje koda treba imati:
```
... i objasni:
1. Zašto svaki resurs postoji
2. Šta se dešava ako ga obrišem
3. Koji su tradeoffs ovog pristupa
```

Ovo te tjera da razumiješ kod, i tjera AI da generiše bolji kod
(jer mora biti u stanju da ga objasni).

### Traži alternative

```
Imam ovo rješenje za deployment review apps:
[opis/kod]

Postoji li jednostavniji način? Koje su prednosti i mane oba pristupa?
```

Često AI generiše kompleksno rješenje kada postoji jednostavnije.

### Traži sigurnosni review kao odvojeni korak

Ne pitaj "napiši sigurno" — pitaj odvojeno:
```
Evo finalne verzije ovog [Terraform/Helm/pipeline]. 
Uradi sigurnosni review i identificiraj:
- Svaki resurs/konfiguracija koja ima preširoke permisije
- Secreti koji mogu biti exposed u logovima
- Konfiguracije koje su OK za dev ali loše za prod
- Sve što ima [x] rizik od sigurnosnog incidenta
```

## Granice AI znanja

**Knowledge cutoff**: AI ima datum do kojeg zna informacije. Za AWS servise koji se
brzo mijenjaju (EKS, ALB annotations), uvijek provjeri aktuelnu dokumentaciju.

Znakovi zastarjelog savjeta:
- Koristi `apiVersion: extensions/v1beta1` (deprecated u K8s 1.22+)
- Preporučuje `kubectl create serviceaccount` bez IRSA za AWS permisije
- Koristi `eksctl` gdje Terraform ima bolji native support

**Hallucinated API calls**: AI može izmisliti Terraform resource argumente koji
ne postoje. Uvijek provjeri `terraform validate` — failovaće na nepostojećim
argumentima. Za neobične argumente, provjeri u Terraform Registry dokumentaciji.

**Zastarjeli primjeri**: AI može generisati best practice koji je bio tačan
godinu-dvije ranije. Primjer: preporučivanje Fargate za EKS bez napomene o
kompleksnosti networking-a, ili preporučivanje LoadBalancer Service umjesto
ALB Ingress.

**Regionalne razlike**: AI može generisati kod koji radi u us-east-1 ali ne u
eu-west-1 (dostupnost instance tipova, AZ-ovi, AMI ID-ovi).

## AI u timu

**Code review AI-generisanog koda**: Kada radiš PR sa AI-generisanim kodom,
naznači to u PR opisu. Revieweri trebaju znati da posebno paze na:
- Logiku koja izgleda ispravna ali ima subtilnu grešku
- Sigurnosne implikacije koje AI nije uočio
- Troškove koji nisu očigledni iz koda

**Dokumentovanje AI-assisted rješenja**: U commit poruci ili PR opisu:
```
feat: dodaj EKS cluster sa Cluster Autoscalerom

Terraform modul generisan uz asistenciju Claude-a i refaktorizovan.
Testirano na dev environmentu, plan reviewan ručno.
Sigurnosni review pokazao preširoke IAM permisije — smanji na least privilege
u follow-up tasku.
```

**Dijeli promptove**: Ako nađeš dobar prompt koji generiše kvalitetan kod,
podijeli sa timom. "Evo prompta kojim sam generisao EKS modul" je vrijedno znanje.

## Veza sa project-A

Kroz modul 11, svaki put kada koristiš AI:
1. Uključi verzije iz ovog projekta (Terraform 1.7, EKS 1.29, AWS eu-west-1)
2. Uključi existing konfiguraciju (VPC CIDR, cluster name, bucket name)
3. Traži objašnjenje uz svaki generisani kod
4. Provjeri sa `terraform validate` / `kubectl dry-run` / `helm lint`
5. Nikad ne applyuj na prod bez dev testa

Ovo nije teorija — modul 11 je dizajniran da prolaziš sa AI otvorenim u drugom
prozoru. Svaki lab korak ima hint za prompt koji možeš koristiti.
