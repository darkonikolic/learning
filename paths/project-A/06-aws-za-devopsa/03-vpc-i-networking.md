# VPC i networking u AWS-u

## Šta je VPC

Virtual Private Cloud je izolirana mrežna okoline unutar AWS-a. Svaki AWS nalog dolazi sa default VPC-om, ali za produkciju kreiraš vlastiti. Resursi unutar VPC-a međusobno komuniciraju privatno — ne kroz internet.

VPC je regionalni resurs. Proteže se kroz sve AZ u regionu, ali subneti su vezani za jednu AZ.

## Subneti: public vs private

**Public subnet**: ima rutu do Internet Gateways-a. Resursi mogu dobiti javne IP adrese i biti dostupni sa interneta.
- Gdje ide: ALB (jedina stvar koja treba biti javno dostupna), NAT Gateway

**Private subnet**: nema direktnu rutu do interneta. Resursi mogu inicirati outbound saobraćaj (kroz NAT), ali ne mogu biti direktno dosegnuti sa interneta.
- Gdje ide: EKS worker nodovi, baze podataka

Zašto ovakav split: attack surface reduction. Ako je EKS node kompromitovan, napadač nema direktan javni IP. Sav ulazni saobraćaj mora proći kroz ALB koji terminira HTTPS i prosljeđuje HTTP unutar private mreže.

## Internet Gateway i NAT Gateway

**Internet Gateway (IGW)**: vrata između VPC-a i interneta. Jedan po VPC-u. Besplatan.

**NAT Gateway**: omogućava resursima u private subnet-u da iniciraju outbound konekcije (pull Docker image, package update) bez primanja inbound saobraćaja. Skupo: **$32/mj** fiksno + $0.045/GB podataka.

Za dev env: NAT Gateway je opcioni. EKS node-ovi mogu biti u public subnetu (bez javnih IP-a, ali s IGW rutom) da se uštedi $32/mj. Za prod: NAT je obavezan.

## Security Groups

Stateful firewall koji se primjenjuje na EC2 instance, EKS node-ove, RDS. "Stateful" znači: ako dozvoliš outbound konekciju, odgovor dolazi automatski bez posebnog inbound pravila.

```
Security Group: alb-sg
  Inbound: 443 (HTTPS) sa 0.0.0.0/0
  Inbound: 80 (HTTP) sa 0.0.0.0/0 → redirect na 443
  Outbound: sve

Security Group: eks-nodes-sg
  Inbound: 0-65535 od alb-sg (ALB šalje saobraćaj na node portove)
  Inbound: 0-65535 između eks-nodes-sg (node-to-node komunikacija)
  Outbound: sve
```

Nikad ne koristiti `0.0.0.0/0` za inbound na worker node-ove.

## CIDR planiranje za multi-environment

CIDR (Classless Inter-Domain Routing) definiše opseg IP adresa. `/16` daje 65.536 adresa, `/24` daje 256.

Planiranje za project-A — svaki environment ima vlastiti VPC:

| Environment | VPC CIDR | Public Subnet (AZ-a) | Public Subnet (AZ-b) | Private Subnet (AZ-a) | Private Subnet (AZ-b) |
|-------------|----------|---------------------|---------------------|----------------------|----------------------|
| dev | 10.0.0.0/16 | 10.0.1.0/24 | 10.0.2.0/24 | 10.0.10.0/24 | 10.0.11.0/24 |
| staging | 10.1.0.0/16 | 10.1.1.0/24 | 10.1.2.0/24 | 10.1.10.0/24 | 10.1.11.0/24 |
| prod | 10.2.0.0/16 | 10.2.1.0/24 | 10.2.2.0/24 | 10.2.10.0/24 | 10.2.11.0/24 |

Zašto odvojeni VPC-ovi: kompletna izolacija između environmenta. Dev incident ne utiče na prod mrežu.

## Dijagram mreže za project-A

```
Internet
    |
    | (HTTPS 443)
    ↓
Internet Gateway
    |
    ↓
Public Subnet (10.0.1.0/24 — AZ-a)
    ├── ALB (prima HTTPS, terminira SSL, prosljeđuje HTTP)
    └── NAT Gateway (outbound za private subnet)
         |
         ↓ (HTTP 80, interno)
Private Subnet (10.0.10.0/24 — AZ-a)
    └── EKS Worker Node
            └── nginx Pod (port 80)
```

Isti pattern ponavlja se u AZ-b za HA. ALB automatski distribuira saobraćaj između AZ.

## EKS specifični networking

EKS koristi VPC CNI plugin koji dodjeljuje AWS VPC IP adrese direktno Podovima. Svaki Pod dobija svoju IP adresu iz subnet CIDR-a (ne iz overlay mreže kao Calico/Flannel).

Implikacija: subnet treba imati dovoljno IP adresa. Ako running 50 Podova u subnet-u sa /24 (256 IP) i 10 nodova koji svaki rezervišu nekoliko IP, može ostati malo prostora. Za prod: koristiti /22 ili veće subnet-ove.

Subnet tag obavezan za EKS:
```
kubernetes.io/cluster/project-a-dev = shared
kubernetes.io/role/internal-elb = 1  (za private subnete)
kubernetes.io/role/elb = 1           (za public subnete)
```

Terraform VPC modul u modulu 07 dodaje ove tagove automatski.
