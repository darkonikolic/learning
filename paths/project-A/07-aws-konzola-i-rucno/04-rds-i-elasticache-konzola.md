# 04 — RDS i ElastiCache kroz AWS Konzolu

## Cilj

Kreirati MySQL bazu i Redis cache ručno. Razumjeti mrežnu izolaciju (private subnets), security group pravila i secrets management. Ovo je stanje podataka projekta — mora biti izolovano od interneta.

---

## RDS Subnet Group

Subnet group govori RDS-u u kojim subnetima smije plasirati DB instance. Mora sadržavati subnete iz minimum 2 AZ (AWS zahtjev za Multi-AZ mogućnost, čak i kad je isključena).

**Console → RDS → Subnet groups → Create DB subnet group**

- **Name**: `project-a-dev-db-subnet-group`
- **Description**: Private subnets for project-a-dev databases
- **VPC**: `project-a-dev-vpc`
- **Availability Zones**: eu-west-1a, eu-west-1b
- **Subnets**: izaberi `project-a-dev-private-1a` i `project-a-dev-private-1b`
- Create

---

## Security Group za RDS

**VPC → Security Groups → Create security group**

- **Name**: `rds-sg`
- **Description**: MySQL access from EKS nodes
- **VPC**: `project-a-dev-vpc`

**Inbound rules**:

| Type | Protocol | Port | Source |
|------|----------|------|--------|
| MySQL/Aurora | TCP | 3306 | eks-nodes-sg |

Source nije IP range nego referenca na drugu SG. Ovo znači: samo resursi koji imaju `eks-nodes-sg` attachanu mogu pristupiti na port 3306. Ako nodovi dobiju novu SG ili izgube eks-nodes-sg — pristup puca. Sigurniji i fleksibilniji od IP opsega.

**Outbound**: ostavi default (All traffic) — RDS treba outbound za replikaciju i maintainance windows.

Create security group

---

## Lozinka u AWS Secrets Manager (PRIJE RDS-a)

Nikad ne kucaj lozinku direktno u RDS wizard. Koristi Secrets Manager.

**Console → Secrets Manager → Store a new secret**

- **Secret type**: Other type of secret
- **Key/value pairs**:
  - Key: `username`, Value: `admin`
  - Key: `password`, Value: (generiraj: klikni "Generate" ili unesi jaku lozinku)
- Next
- **Secret name**: `project-a/dev/mysql`
- **Description**: MySQL master credentials for project-a-dev
- Next → Next → Store

Kopiraj Secret ARN — trebaće za aplikaciju.

---

## Kreiranje RDS MySQL Instance

**Console → RDS → Databases → Create database**

### Database creation method

- **Standard create** (ne Easy create — sakriva opcije)

### Engine options

- **Engine type**: MySQL
- **Engine version**: MySQL 8.0.35 (ili najnoviji 8.0.x)

### Templates

- **Dev/Test** — isključuje Multi-AZ, manji instance type

> Produkcija koristi "Production" template koji forsira Multi-AZ i gp3 storage.

### Settings

- **DB instance identifier**: `project-a-dev-mysql`
- **Master username**: `admin`
- **Credentials management**: **Manage master credentials in AWS Secrets Manager**
  - Ako ova opcija nije dostupna: izaberi "Self managed" i unesi lozinku iz Secrets Managera koji si kreirao

### Instance configuration

- **DB instance class**: Burstable classes → `db.t3.micro`
  - t3.micro: 1 vCPU, 1GB RAM — dovoljno za dev, ne za prod
  - db.t3.small i dalje za produkciju s konkretnim load-om

### Storage

- **Storage type**: gp3
- **Allocated storage**: 20 GiB
- **Storage autoscaling**: Enable, Maximum storage threshold: 100 GiB

gp3 je noviji i jeftiniji od gp2. 20GB je minimum, autoscaling štiti od punog diska.

### Availability & durability

- **Multi-AZ deployment**: **Do not create a standby instance** (Dev/Test template)

Za produkciju: Multi-AZ daje automatski failover u ~60 sekundi ako primarni AZ padne.

### Connectivity

- **Compute resource**: Don't connect to an EC2 compute resource (ručno konfigurišemo)
- **VPC**: `project-a-dev-vpc`
- **DB Subnet group**: `project-a-dev-db-subnet-group`
- **Public access**: **No** — ovo je ključno. Nikad ne izlagati bazu internetu.
- **VPC security group**: izaberi `rds-sg` (ukloni default ako je dodat)
- **Availability Zone**: eu-west-1a

### Database authentication

- **Password authentication**

### Additional configuration

- **Initial database name**: `projecta`
  - Ako ostaviš prazno, baza se kreira bez default scheme-a
- **Backup retention period**: 7 days
- **Enable automated backups**: ✓
- **Backup window**: No preference (ili postavi na noćne sate)
- **Enable deletion protection**: za dev isključi (lakše brisanje)

Create database — traje ~5-10 minuta.

---

## Read Replica

Nakon što je master DB u stanju **Available**:

**RDS → Databases → project-a-dev-mysql → Actions → Create read replica**

- **DB instance identifier**: `project-a-dev-mysql-replica`
- **Region**: eu-west-1 (isti region)
- **Availability Zone**: eu-west-1b (drugi AZ od mastera)
- **Instance type**: db.t3.micro
- **Public access**: No
- Create read replica

Read Replica koristi za read-heavy workloade (analitika, reporting). PHP/Go aplikacija treba imati odvojene konekcije za write (master) i read (replica).

---

## ElastiCache Redis

### Security Group za Redis

**VPC → Security Groups → Create security group**

- **Name**: `redis-sg`
- **Description**: Redis access from EKS nodes
- **VPC**: `project-a-dev-vpc`

Inbound:

| Type | Protocol | Port | Source |
|------|----------|------|--------|
| Custom TCP | TCP | 6379 | eks-nodes-sg |

Create

### Redis Auth Token u Secrets Manager

**Secrets Manager → Store a new secret**

- **Secret type**: Other type of secret
- Key: `auth_token`, Value: generiraj 32+ karaktera (mix slova/brojeva/znakova)
- **Secret name**: `project-a/dev/redis`
- Store

### Kreiranje ElastiCache Redis Clustera

**Console → ElastiCache → Redis OSS caches → Create Redis OSS cache**

- **Deployment option**: Design your own cache → Easy create OFF (koristiti Custom)

#### Cluster info

- **Name**: `project-a-dev-redis`
- **Description**: Session cache and job queue for project-a-dev

#### Location

- **AWS Cloud**
- **Multi-AZ**: Off (dev)
- **Auto-failover**: Off

#### Cluster settings

- **Engine version**: 7.1
- **Port**: 6379
- **Parameter group**: default.redis7 (ne mijenjaj za sada)
- **Node type**: `cache.t3.micro`
- **Number of replicas**: 0 (dev; prod = 1 minimum)

#### Subnet group settings

- **Create new**: ✓
  - **Name**: `project-a-dev-redis-subnet-group`
  - **VPC**: project-a-dev-vpc
  - **Subnets**: private-1a, private-1b
- **Availability zone**: eu-west-1a

#### Security

- **Encryption in transit**: Enable
- **Access control**: Redis AUTH default user access
  - Upiši auth token iz Secrets Managera
- **Security groups**: `redis-sg`

Create — traje ~5 minuta.

---

## Verifikacija

```bash
# Lista RDS instance — mora biti available
docker run --rm -v ~/.aws:/root/.aws amazon/aws-cli:latest \
  rds describe-db-instances \
  --query 'DBInstances[*].[DBInstanceIdentifier,DBInstanceStatus,Endpoint.Address]' \
  --output table

# Lista ElastiCache clusters
docker run --rm -v ~/.aws:/root/.aws amazon/aws-cli:latest \
  elasticache describe-cache-clusters \
  --query 'CacheClusters[*].[CacheClusterId,CacheClusterStatus]' \
  --output table
```

### Test konekcije s EKS poda

```bash
# Privremeni debug pod s MySQL clientom
docker run --rm -v ~/.aws:/root/.aws -v ~/.kube:/root/.kube \
  bitnami/kubectl:1.29 run mysql-client --rm -it \
  --image=mysql:8.0 \
  --restart=Never \
  -- mysql -h <RDS_ENDPOINT> -u admin -p
```

RDS endpoint nađeš u: **RDS → Databases → project-a-dev-mysql → Connectivity & security → Endpoint**

---

## Destroy Redosled za RDS i ElastiCache

Obrisati PRIJE brisanja VPC-a (imaju ENI-je u private subnetima).

1. **Read Replica**:
   - RDS → Databases → project-a-dev-mysql-replica → Actions → Delete
   - "Create final snapshot": No (dev)
   - "Retain automated backups": No
   - Confirm: `delete me`
   - Traje ~3 minute

2. **RDS Master**:
   - RDS → Databases → project-a-dev-mysql → Actions → Delete
   - "Create final snapshot": No
   - "Retain automated backups": No
   - Confirm: `delete me`
   - Traje ~3-5 minuta
   - **Deletion protection** mora biti isključena (Settings → Modify → uncheck Deletion protection → Apply immediately)

3. **ElastiCache Redis**:
   - ElastiCache → Redis OSS caches → project-a-dev-redis → Actions → Delete
   - "Create final backup": No (dev)
   - Delete
   - Traje ~2 minute

4. **Secrets Manager** (opcionalno odmah):
   - Secrets Manager → project-a/dev/mysql → Actions → Delete secret
   - Minimum scheduled deletion: 7 dana (AWS default zaštita)
   - Za immediate delete: `aws secretsmanager delete-secret --secret-id project-a/dev/mysql --force-delete-without-recovery`

5. **Subnet groups**:
   - RDS → Subnet groups → project-a-dev-db-subnet-group → Delete
   - ElastiCache → Subnet groups → project-a-dev-redis-subnet-group → Delete

6. **Security Groups**: rds-sg, redis-sg (u VPC konzoli)

---

## Česte Greške

**"Cannot delete, has pending maintenance"** — RDS je schedulirao maintenance. Pričekaj ili promijeni maintenance window na odmah.

**Konekcija sa poda odbija** — skoro uvijek SG problem. Provjeri da pod ima `eks-nodes-sg` i da RDS SG ima inbound rule od `eks-nodes-sg` na 3306.

**"Endpoint does not exist"** — aplikacija koristi pogrešan endpoint. RDS endpoint se dobija tek kad je instance Available, ne pri kreiranju.

**Redis AUTH failed** — auth token mora biti identičan onom pri kreiranju clustera. Provjeri Secrets Manager vrijednost.
