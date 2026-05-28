# AWS koncepti za DevOps inženjera

## Zašto AWS, a ne "sve ručno"

AWS nije samo hosting — to je API za infrastrukturu. Svaki server, mreža, sertifikat, DNS zapis postoji kao resurs kojim upravljaš programski. DevOps inženjer ne kreira infrastrukturu kroz web konzolu — kreira je kroz kod (Terraform), a konzolu koristi samo za posmatranje.

Princip projekta A: **ništa ručno kroz konzolu**. Sve što postoji u AWS-u nastalo je kroz Terraform. Ako nije u kodu, ne postoji.

## Geografska organizacija: regioni i AZ

**Region** je fizička lokacija (eu-west-1 = Irska, us-east-1 = Sjeverna Virdžinija). Biraju se po:
- Latenciji prema korisnicima
- Zakonskim zahtjevima (GDPR → EU regioni)
- Dostupnosti servisa (novi servisi prvo u us-east-1)
- Cijeni (varira po regionu)

**Availability Zone (AZ)** je izolovani datacenter unutar regiona. eu-west-1 ima eu-west-1a, eu-west-1b, eu-west-1c. Resursi raspoređeni kroz više AZ preživljavaju pad jednog datacentra.

Za project-A: eu-west-1, dva AZ za HA. Dev env može koristiti jedan AZ radi uštede.

## Šta DevOps treba znati (za razliku od cloud arhitekta)

Cloud arhitekt dizajnira sistem. DevOps inženjer implementira, automatizira i održava. Fokus DevOps inženjera:

- **Kako se resursi kreiraju i brišu** (Terraform lifecycle)
- **Kako se servis autentifikuje prema AWS-u** (IAM role, OIDC)
- **Kako se konfigurišu pipelines** da deployuju na AWS
- **Šta košta** i kako kontrolisati troškove

Ne treba: dizajnirati VPC arhitekturu od nule, birati DB engine, optimizovati Reserved Instances strategiju (to su arhitektove odluke).

## Servisi u project-A

| Servis | Uloga u projektu |
|--------|-----------------|
| **EKS** | Managed Kubernetes — gdje živi nginx |
| **ECR** | Container registry (alternativa GitLab registriju) |
| **ALB** | HTTPS load balancer ispred EKS-a |
| **Route53** | DNS — `app.dev.firma.com` → ALB |
| **ACM** | SSL sertifikati za ALB |
| **S3** | Terraform remote state storage |
| **IAM** | Ko šta smije raditi |
| **VPC** | Izolirana mreža za sve resurse |
| **CloudWatch** | Logovi i metrike (osnovno, Prometheus/Grafana za više) |

## AWS Free Tier i cost awareness

Free tier postoji, ali EKS ga ne pokriva. Šta je besplatno:
- t2.micro EC2 instanca (750h/mj, jednu godinu)
- S3: 5 GB storage
- Route53: nije besplatno ($0.50/hosted zone/mj)
- ACM: besplatan za resurse integrisane sa AWS (ALB, CloudFront)

Šta košta za dev okruženje (realan estimat):
- EKS control plane: **$0.10/h = $72/mj**
- EC2 t3.medium worker node (×1): **~$30/mj**
- ALB: **~$16/mj**
- NAT Gateway: **$32/mj** (ovo boli — 1 gateway = $32 fiksno + transfer)

Ukupno dev env: **~$150/mj** ako stalno radi. Strategija: kreirati po potrebi, uništiti poslje.

## Princip: konzola je samo za čitanje

AWS web konzola je koristan alat za istraživanje i debugging. Nije alat za kreiranje infrastrukture. Razlozi:
- Ručne izmjene nisu u kodu → niko ne zna šta postoji
- Terraform state se desinhronizuje → plan pokazuje lažne razlike
- Nema audit trail-a osim CloudTrail logova
- Ne može se replicirati za staging/prod

Jedina iznimka: bootstrap S3 bucketa za Terraform state (jaje-kokoška problem — modul 07).
