# 02 — VPC i Networking kroz AWS Konzolu

## Cilj

Kreirati kompletnu mrežnu infrastrukturu ručno kroz AWS konzolu. Svaki klik razumjeti — Terraform će u modulu 07 napraviti identičnu strukturu automatski, ali bez ovog manuelnog prolaza nećeš razumjeti šta Terraform radi.

---

## VPC Wizard vs Manual

AWS nudi **VPC Wizard** koji kreira sve u jednom koraku. **Ne koristiti ga.** Wizard sakriva šta se kreira i zašto. Manual kreiranje tjera te da razumiješ svaki resurs i njegove veze.

---

## Step-by-Step Kreiranje

### Korak 1 — VPC

**Console → VPC → Your VPCs → Create VPC**

- **Resources to create**: VPC only (ne "VPC and more" — to je wizard)
- **Name tag**: `project-a-dev-vpc`
- **IPv4 CIDR block**: `10.0.0.0/16`
- **IPv6**: No
- **Tenancy**: Default
- Create VPC

CIDR `/16` daje 65.536 IP adresa. Ostavlja prostora za rast i za podjelu na subnete.

### Korak 2 — Public Subnets (2 AZ)

**VPC → Subnets → Create subnet**

Subnet 1:
- **VPC**: project-a-dev-vpc
- **Subnet name**: `project-a-dev-public-1a`
- **Availability Zone**: eu-west-1a
- **IPv4 CIDR**: `10.0.1.0/24`

Klikni **Add new subnet** (ne Create još):

Subnet 2:
- **Subnet name**: `project-a-dev-public-1b`
- **Availability Zone**: eu-west-1b
- **IPv4 CIDR**: `10.0.2.0/24`

Create subnet (kreira oba odjednom)

### Korak 3 — Private Subnets (2 AZ)

**VPC → Subnets → Create subnet**

Subnet 3:
- **Subnet name**: `project-a-dev-private-1a`
- **Availability Zone**: eu-west-1a
- **IPv4 CIDR**: `10.0.3.0/24`

Add new subnet:

Subnet 4:
- **Subnet name**: `project-a-dev-private-1b`
- **Availability Zone**: eu-west-1b
- **IPv4 CIDR**: `10.0.4.0/24`

Create subnet

### Korak 4 — Internet Gateway

**VPC → Internet Gateways → Create internet gateway**

- **Name tag**: `project-a-dev-igw`
- Create

Odmah nakon kreiranja: **Actions → Attach to VPC → project-a-dev-vpc → Attach**

Internet Gateway koji nije attachan na VPC je beskoristan. Attachanje je zasebna akcija — česta greška je zaboraviti ovaj korak.

### Korak 5 — Elastic IP za NAT Gateway

**EC2 → Elastic IPs → Allocate Elastic IP address**

- **Network border group**: eu-west-1
- **Public IPv4 address pool**: Amazon's pool
- Allocate

Dodaj tag:
- Key: `Name`, Value: `project-a-dev-nat-eip`

EIP se naplaćuje ako ga alociraš a ne koristiš. Dok je attachan na NAT Gateway nema extra troška.

### Korak 6 — NAT Gateway

**VPC → NAT Gateways → Create NAT gateway**

- **Name**: `project-a-dev-nat`
- **Subnet**: `project-a-dev-public-1a` (NAT mora biti u PUBLIC subnetu!)
- **Connectivity type**: Public
- **Elastic IP allocation ID**: izaberi EIP kreiran u prethodnom koraku
- Create NAT gateway

NAT Gateway traje ~1 minutu da postane Available. Ovo je managed servis — AWS ga maintaina, ne ti.

**Zašto NAT u public subnetu?** NAT Gateway prima saobraćaj od private subneta i prosljeđuje ga internetu koristeći svoju public IP (EIP). Da bi to radio, mora imati izlaz na internet — što znači mora biti u subnetu koji ima rutu prema IGW.

### Korak 7 — Route Tables

Svaki VPC dobije default Main route table. Ne koristiti je direktno — kreirati eksplicitne.

#### Public Route Table

**VPC → Route Tables → Create route table**

- **Name**: `project-a-dev-rtb-public`
- **VPC**: project-a-dev-vpc
- Create

Odaberi novu route table → **Routes tab → Edit routes → Add route**:
- **Destination**: `0.0.0.0/0`
- **Target**: Internet Gateway → project-a-dev-igw
- Save

**Subnet Associations tab → Edit subnet associations**:
- Kvačica na: `project-a-dev-public-1a` i `project-a-dev-public-1b`
- Save

#### Private Route Table

Create route table:
- **Name**: `project-a-dev-rtb-private`
- **VPC**: project-a-dev-vpc
- Create

Routes → Edit routes → Add route:
- **Destination**: `0.0.0.0/0`
- **Target**: NAT Gateway → project-a-dev-nat
- Save

Subnet Associations → Edit:
- Kvačica na: `project-a-dev-private-1a` i `project-a-dev-private-1b`
- Save

### Verifikacija Route Tables

**VPC → Subnets → klikni na project-a-dev-public-1a → Route table tab**

Mora pokazati:
```
Destination     Target
10.0.0.0/16     local
0.0.0.0/0       igw-xxxxxxxxx
```

**project-a-dev-private-1a → Route table tab** mora pokazati:
```
Destination     Target
10.0.0.0/16     local
0.0.0.0/0       nat-xxxxxxxxx
```

Ako private subnet ima igw kao target umjesto nat — greška. Instance u private subnetu bi bile direktno dostupne s interneta.

---

## Security Groups

Security Group je stateful firewall na nivou ENI (mrežnog interfejsa). Za razliku od NACL (Network ACL) koji je stateless.

### Default SG

Svaki VPC ima default SG. Default pravilo: sav saobraćaj unutar iste SG je dozvoljen, sav ostali inbound je zabranjen. Ne koristiti default SG — teže je pratiti šta je gdje.

### Kreiranje eks-nodes-sg

**VPC → Security Groups → Create security group**

- **Security group name**: `eks-nodes-sg`
- **Description**: EKS node group communication
- **VPC**: project-a-dev-vpc

**Inbound rules**:

| Type | Protocol | Port | Source | Description |
|------|----------|------|--------|-------------|
| All traffic | All | All | eks-nodes-sg (self) | Node-to-node |
| HTTPS | TCP | 443 | 0.0.0.0/0 | API server inbound |

Da dodaš self-reference (eks-nodes-sg → eks-nodes-sg): u Source dropdown odaberi "Custom" i počni kucati ime SG — pojavit će se ID.

**Outbound rules**: ostavi default (All traffic, 0.0.0.0/0) — nodovi moraju moći pullati Docker images, komunicirati s AWS API-jem.

Create security group

---

## Zašto 2 Availability Zones

EKS control plane zahtijeva minimum 2 AZ za HA. Ako jedno AZ padne:
- Node Group u preostalom AZ preuzima sav saobraćaj
- Kubernetes scheduler premješta podove na zdrave nodove
- RDS Multi-AZ failover (kada ga aktiviraš za prod) radi automatski

Sa jednim AZ: pad AZ = pad cijelog clustera. Ne vrijedi rizik.

---

## Destroy Redosled za Networking

Pogrešan redosled brisanja = AWS greška "DependencyViolation". Ispravan redosled:

1. **NAT Gateway** delete (Console → VPC → NAT Gateways → Actions → Delete)
   - Čekaj da state postane Deleted (~1 min)
2. **Elastic IP** release (EC2 → Elastic IPs → Actions → Release)
   - Ako ne released ostaje na računu
3. **Internet Gateway** detach → delete
   - VPC → Internet Gateways → Actions → Detach from VPC → potvrdi
   - Actions → Delete → potvrdi
4. **Route Tables** delete (sve osim Main — Main se ne može obrisati)
   - Prvo ukloni subnet associations, pa onda obriši
5. **Subnets** delete (sve 4)
6. **Security Groups** delete (eks-nodes-sg; default ne možeš obrisati)
7. **VPC** delete

Ako dobiješ "has dependencies" grešku pri brisanju VPC-a: **VPC → Your VPCs → project-a-dev-vpc → Resource map tab** — prikazuje sve zaostale resurse. Najčešći krivac su "zarobljeni" ENI-ji od EKS-a ili RDS-a koji se nisu očistili sami.
