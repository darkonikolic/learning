# 07 — Manuelni Destroy Redosled

## Cilj

Ručno obrisati sve što je kreirano u ovom modulu. Ispravan redosled je kritičan — AWS ima dependency graf između resursa i neće dozvoliti brisanje resursa dok postoje zavisni. Ovo je tačno ono što `terraform destroy` radi automatski, ali moraš razumjeti svaki korak.

---

## Zašto Redosled Brisanja Bitan

AWS resursi imaju meke i tvrde zavisnosti:

- **Tvrda zavisnost**: VPC se ne može obrisati dok postoji subnet u njemu. ENI koji drži subnet aktivan može biti od EKS node grupe, NAT gatewaya, RDS instance, ElastiCache. Brisanje VPC-a prije ovih → `DependencyViolation` greška.

- **Meka zavisnost**: ElastiCache subnet group se može obrisati prije ElastiCache clustera — ali AWS neće dozvoliti jer je cluster još uvijek referencira.

Pravilo: brisi "listove" stabla zavisnosti prije "korijena". Listovi su resursi koje nitko drugi ne referencira.

---

## Kompletan Destroy Redosled za project-a-dev

### 1. Kubernetes Workloads

```bash
# Briše namespace i sve K8s resurse unutar njega
docker run --rm -v ~/.aws:/root/.aws -v ~/.kube:/root/.kube \
  bitnami/kubectl:1.29 delete namespace project-a-dev
```

Čekaj dok namespace ne nestane:
```bash
docker run --rm -v ~/.aws:/root/.aws -v ~/.kube:/root/.kube \
  bitnami/kubectl:1.29 get namespace project-a-dev
# Mora: Error from server (NotFound)
```

Zašto prvi? Ako je ALB Ingress bio deployovan s proper anotacijama, AWS Load Balancer Controller kreira i briše ALB automatski zajedno s namespace-om. Ako obrišeš EKS cluster prvi, ALB ostaje "siročad" i naplaćuje se.

### 2. ALB Controller Uninstall

```bash
docker run --rm -v ~/.aws:/root/.aws -v ~/.kube:/root/.kube \
  -v ~/.helm:/root/.helm \
  alpine/helm:3.14 uninstall aws-load-balancer-controller -n kube-system
```

Ovo uklanja K8s objekte ALB Controller-a (Deployment, ServiceAccount, RBAC). Ne briše AWS resurse koje je controller kreirao — to je uradio korak 1.

### 3. Provjera Load Balancera u EC2

**Console → EC2 → Load Balancers**

Filtriraj po VPC: `project-a-dev-vpc`. Ako postoje zaostali ALB-ovi koji se nisu obrisali automatski:
- Označi → Actions → Delete load balancer
- Confirm

Česti uzrok zaostalih ALB-ova: namespace obrisan direktno bez `kubectl delete namespace` (npr. `kubectl delete deployment` bez brisanja Ingress objekta, ili ALB Controller nije bio instaliran kad je Ingress kreiran).

### 4. EKS Node Group Delete

**Console → EKS → Clusters → project-a-dev → Compute tab → Node Groups → project-a-dev-nodes → Delete**

- Ukucaj naziv za potvrdu: `project-a-dev-nodes`
- Delete

Čekaj ~5 minuta. AWS terminira EC2 instance, drains nodove, briše Auto Scaling Group.

Prati u konzoli: **EC2 → Instances** — instance prolaze kroz `Terminating` pa nestaju.

Dok čekaš, možeš paralelno pokrenuti brisanje RDS i ElastiCache (nemaju vezu s EKS).

### 5. EKS Cluster Delete

**Console → EKS → Clusters → project-a-dev → Delete**

- Ukucaj naziv: `project-a-dev`
- Delete

Čekaj ~10 minuta. Ovo briše control plane, ENI-je koje je control plane koristio, i add-one.

**Greška koju dobijač ako Node Group još postoji**: `Cannot delete cluster, existing node groups must be deleted first`

### 6. RDS Read Replica Delete

**Console → RDS → Databases → project-a-dev-mysql-replica → Actions → Delete**

- Create final snapshot: **No**
- Retain automated backups: **No**
- Confirm: ukucaj `delete me`
- Delete

Traje ~3 minute. Mora se obrisati prije mastera jer je master source replikacije.

### 7. RDS Master Delete

**Console → RDS → Databases → project-a-dev-mysql**

Ako je Deletion Protection uključena:
- Actions → Modify → Deletion protection: uncheck → Continue → Apply immediately

Zatim:
- Actions → Delete
- Create final snapshot: **No**
- Retain automated backups: **No**
- Confirm: `delete me`
- Delete

Traje ~5 minuta.

### 8. ElastiCache Cluster Delete

**Console → ElastiCache → Redis OSS caches → project-a-dev-redis → Actions → Delete**

- Create final backup: **No**
- Delete

Traje ~2 minute.

### 9. Secrets Manager

Secrets imaju minimum 7-dnevni scheduled deletion period (zaštita od akcidentalnog brisanja).

**Console → Secrets Manager → project-a/dev/mysql → Actions → Delete secret**
- Waiting period: 7 days (minimum)
- Schedule deletion

**Console → Secrets Manager → project-a/dev/redis → Actions → Delete secret**

Za immediate delete bez waiting perioda (SAMO za dev, NIKAD za prod):
```bash
docker run --rm -v ~/.aws:/root/.aws amazon/aws-cli:latest \
  secretsmanager delete-secret \
  --secret-id project-a/dev/mysql \
  --force-delete-without-recovery

docker run --rm -v ~/.aws:/root/.aws amazon/aws-cli:latest \
  secretsmanager delete-secret \
  --secret-id project-a/dev/redis \
  --force-delete-without-recovery
```

### 10. Subnet Groups (RDS i ElastiCache)

**Console → RDS → Subnet groups → project-a-dev-db-subnet-group → Delete**

**Console → ElastiCache → Subnet groups → project-a-dev-redis-subnet-group → Delete**

Ovo oslobađa referencu na subnete — neophodno prije brisanja subnetova.

### 11. NAT Gateway Delete

**Console → VPC → NAT Gateways → project-a-dev-nat → Actions → Delete NAT gateway**

- Confirm: ukucaj `delete`
- Delete

Čekaj da status postane **Deleted** (~1 minutu). NAT gateway naplaćuje se po satu ($0.045/sat) — svaki sat dok postoji naplaćuje.

### 12. Elastic IP Release

**Console → EC2 → Elastic IPs**

Filtriraj po tagu `Name: project-a-dev-nat-eip`:
- Označi → Actions → Release Elastic IP addresses
- Release

EIP koji nije associran s resursom naplaćuje se po satu. Mora se releasati **nakon** NAT Gateway brisanja (dok je NAT aktivan, EIP je associran i ne može se releasati).

### 13. Internet Gateway Detach → Delete

**Console → VPC → Internet Gateways → project-a-dev-igw**

- Actions → **Detach from VPC** → Detach
- Actions → **Delete internet gateway** → Delete

Detach i delete su dvije zasebne operacije. Ne možeš obrisati IGW dok je attachan na VPC.

### 14. Route Tables Delete

**Console → VPC → Route Tables**

Filtriraj po VPC: `project-a-dev-vpc`

Vidiš 3 route tabele:
1. Main route table (automatski kreirana, ne možeš je obrisati)
2. `project-a-dev-rtb-public`
3. `project-a-dev-rtb-private`

Za svaku od 2 i 3:
1. Klikni na route table
2. **Subnet Associations tab → Edit subnet associations** — ukloni sve kvačice → Save
3. **Actions → Delete route table**

Greška: `The routeTable has dependencies and cannot be deleted` → subnet association nije uklonjena, ili je main route table (ne možeš je brisati).

### 15. Subnets Delete

**Console → VPC → Subnets**

Filtriraj po VPC. Označi sva 4 subneta:
- project-a-dev-public-1a
- project-a-dev-public-1b
- project-a-dev-private-1a
- project-a-dev-private-1b

Actions → Delete subnet → Delete

Greška: `The subnet has dependencies` → ENI još postoji u tom subnetu (vidi sekciju ispod).

### 16. Security Groups Delete

**Console → VPC → Security Groups**

Filtriraj po VPC. Označi:
- `eks-nodes-sg`
- `rds-sg`
- `redis-sg`

Actions → Delete security groups → Delete

**Greška**: `resource sg-xxx has a dependent object` — drugi SG referencira ovaj kao source u inbound ruleu. Rješenje:
1. Pronađi koji SG ima rulu koja referencira tvoj SG
2. Obriši tu rulu prvo
3. Pa onda obriši SG

Default SG se ne može obrisati (AWS ga automatski drži).

### 17. VPC Delete

**Console → VPC → Your VPCs → project-a-dev-vpc → Actions → Delete VPC**

- Confirm: ukucaj `delete`
- Delete

Ako dobiješ grešku — vidi sekciju ispod.

---

## Expert Gotcha: Zarobljeni ENI-ji

**Najčešći razlog što VPC neće biti obrisan**: ENI (Elastic Network Interface) koji ostaje "zarobljen" — attachment je nestao ali ENI nije releasan.

Gdje nastaju zarobljeni ENI-ji:
- EKS control plane ENI-ji koji se nisu očistili
- RDS ENI koji ostaje u `available` stanju
- Lambda ili VPC endpoint koji nije obrisan

### Kako ih pronaći

**Console → EC2 → Network Interfaces**

Filtriraj:
- Filter: VPC ID → izaberi `project-a-dev-vpc`
- Filter: Status → `available`

Sve ENI u `available` stanju su nezauzete ali blokiraju brisanje subneta/VPC-a.

Za svaki zarobljeni ENI:
- Klikni na njega
- **Actions → Delete**
- Ako je `in-use` — attachment je aktivan, neko resurs ga još drži (provjeri koji u Description koloni)

### CLI verzija:

```bash
docker run --rm -v ~/.aws:/root/.aws amazon/aws-cli:latest \
  ec2 describe-network-interfaces \
  --filters "Name=vpc-id,Values=vpc-XXXXXXXXX" "Name=status,Values=available" \
  --query 'NetworkInterfaces[*].[NetworkInterfaceId,Description,Status]' \
  --output table
```

Brisanje svih available ENI-ja u VPC-u:
```bash
# PAZI: briše sve available ENI-je u VPC-u
VPC_ID="vpc-XXXXXXXXX"
docker run --rm -v ~/.aws:/root/.aws amazon/aws-cli:latest \
  ec2 describe-network-interfaces \
  --filters "Name=vpc-id,Values=$VPC_ID" "Name=status,Values=available" \
  --query 'NetworkInterfaces[*].NetworkInterfaceId' \
  --output text | tr '\t' '\n' | while read eni; do
    echo "Deleting $eni"
    docker run --rm -v ~/.aws:/root/.aws amazon/aws-cli:latest \
      ec2 delete-network-interface --network-interface-id "$eni"
  done
```

---

## Verifikacija: Cost Explorer

Sutra (ili za 24 sata) provjeri Cost Explorer:

**Console → Billing and Cost Management → Cost Explorer**

- Time range: last 7 days
- Granularity: Daily
- Group by: Service

Ako vidIš troškove za:
- **Amazon Elastic Compute Cloud** → provjeri EC2 instances i NAT Gateway
- **Amazon Relational Database Service** → RDS instanca nije obrisana
- **Amazon ElastiCache** → Redis cluster nije obrisan
- **Amazon Elastic Kubernetes Service** → EKS cluster nije obrisan ($0.10/sat)
- **Elastic IP** → EIP nije releasan

Cost Explorer ima delay od ~24 sata pa nula troškova možeš potvrditi tek sutradan.

Za realtime provjeru:
```bash
# Lista svih running EC2 instance
docker run --rm -v ~/.aws:/root/.aws amazon/aws-cli:latest \
  ec2 describe-instances \
  --filters "Name=instance-state-name,Values=running" \
  --query 'Reservations[*].Instances[*].[InstanceId,InstanceType,Tags[?Key==`Name`].Value]' \
  --output table

# Lista NAT Gatewaya koji nisu deleted
docker run --rm -v ~/.aws:/root/.aws amazon/aws-cli:latest \
  ec2 describe-nat-gateways \
  --filter "Name=state,Values=available,pending" \
  --query 'NatGateways[*].[NatGatewayId,State,Tags[?Key==`Name`].Value]' \
  --output table

# Lista EKS clustera
docker run --rm -v ~/.aws:/root/.aws amazon/aws-cli:latest \
  eks list-clusters --output table

# Lista RDS instanci
docker run --rm -v ~/.aws:/root/.aws amazon/aws-cli:latest \
  rds describe-db-instances \
  --query 'DBInstances[*].[DBInstanceIdentifier,DBInstanceStatus]' \
  --output table
```

Sve ove komande trebaju vratiti prazan output (sem header-a) za potvrdu da je destroy kompletan.

---

## Šta Terraform Destroy Radi Drugačije

`terraform destroy` izvršava identičan redosled ali:
- Gradi dependency graf iz state fajla — zna tačan redosled automatski
- Paralelizuje brisanje resursa bez zavisnosti
- Čeka completion svake operacije i provjerava status
- Ažurira state fajl nakon svakog brisanja

Manuelni destroy koji si upravo napravio je identičan, samo ručno. Razumijete sada zašto Terraform `destroy` nekad traje 20-30 minuta — treba proći kroz sve ove korake i čekati AWS da svaki resurs zaista nestane.
