# 02 — AWS ALB Konzola i Ručno Kreiranje

Prije nego automatizuješ sa Terraformom ili Kubernetes Ingress, jednom prođi kroz konzolu. Razumiješ šta svaka opcija znači, vidješ stvarnu AWS terminologiju, lakše debuguješ probleme.

---

## Korak 1: Security Group za ALB

Prije ALB-a, treba SG koji mu dozvoljava inbound saobraćaj.

**EC2 → Security Groups → Create security group**

- Name: `project-a-dev-alb-sg`
- Description: `ALB inbound HTTP and HTTPS`
- VPC: `project-a-dev-vpc`

**Inbound rules:**
| Type | Protocol | Port | Source | Razlog |
|---|---|---|---|---|
| HTTPS | TCP | 443 | 0.0.0.0/0 | sav internet traffic |
| HTTP | TCP | 80 | 0.0.0.0/0 | redirect na HTTPS |

**Outbound rules:** All traffic → 0.0.0.0/0 (default, ostaviti)

**Bitno:** ALB SG mora imati outbound prema EKS worker node SG na odgovarajućim portovima. EKS worker node SG mora imati inbound od ALB SG. Ovo je čest propust koji uzrokuje 502 greške.

---

## Korak 2: Target Group

Target Group definira **kuda** ALB šalje saobraćaj i kako provjerava zdravlje targeta.

**EC2 → Target Groups → Create target group**

**Basic configuration:**
- Target type: `IP addresses` (preporučeno za K8s — direktno na pod IP, ne NodePort)
  - *Alternativa: Instance (NodePort) — za starije setupe ili kad ne koristiš VPC CNI*
- Target group name: `project-a-dev-frontend-tg`
- Protocol: HTTP
- Port: 80
- VPC: `project-a-dev-vpc`
- Protocol version: HTTP1

**Health checks:**
- Protocol: HTTP
- Path: `/health`
- Port: traffic port (isti port)
- Healthy threshold: 2 (2 uspješna check-a → HEALTHY)
- Unhealthy threshold: 2 (2 neuspješna → UNHEALTHY, remove iz rotation)
- Timeout: 5 seconds
- Interval: 15 seconds
- Success codes: `200`

**Zašto interval 15s, ne 5s?** Kraći interval = više health check requestova na pod. Na velikom clusteru sa 100 targeta i 5s intervalom, ALB šalje 20 requestova/s samo za health checks. 15s je dobar balans.

Ponovi za PHP service:
- Name: `project-a-dev-php-tg`
- Port: 9000 (ili koji god port php-fpm/nginx sluša)
- Health check path: `/health`

**Register Targets** (preskočiti ako koristiš K8s ALB Controller — on to radi automatski):
- Upiši IP adrese EKS worker nodova ili pod IP-ova
- Port: onaj koji si definisao

---

## Korak 3: Kreiranje ALB

**EC2 → Load Balancers → Create Load Balancer → Application Load Balancer**

### Basic Configuration
- Name: `project-a-dev-alb`
- Scheme: `Internet-facing` — primamo saobraćaj s interneta
  - *Internal: za internal mikroservisnu komunikaciju unutar VPC*
- IP address type: `IPv4`
  - *Dualstack: IPv4 + IPv6, potrebno samo ako imaš IPv6 zahtjev*

### Network Mapping
- VPC: `project-a-dev-vpc`
- Mappings — OBAVEZNO odaberi **PUBLIC** subnetove u **oba AZ**:
  - `eu-west-1a`: `project-a-dev-public-subnet-1a`
  - `eu-west-1b`: `project-a-dev-public-subnet-1b`

**Zašto public subneti?** ALB mora biti dostupan s interneta. Private subneti nemaju IGW routing. Najčešća greška: stavi ALB u private subnet i pitaš se zašto nije dostupan izvana.

**Zašto oba AZ?** High availability. Ako `eu-west-1a` ima problem, `eu-west-1b` preuzima. AWS zahtijeva minimum 2 AZ za ALB.

### Security Groups
- Odaberi `project-a-dev-alb-sg` (kreiran u koraku 1)
- Ukloni default SG ako se automatski dodao

### Listeners and Routing

**Listener 1 — HTTP:80 (redirect na HTTPS):**
- Protocol: HTTP, Port: 80
- Default action: Redirect to URL
  - Protocol: HTTPS
  - Port: 443
  - Status code: 301 (Permanent redirect)
  
**Zašto 301 a ne 302?** Browseri i SEO toolovi cachuju 301. Korisnik jednom posjeti http://app.firma.com, browser zapamti da uvijek idi na https. 302 je privremeni redirect, browser uvijek pita ponovo.

**Listener 2 — HTTPS:443:**
- Protocol: HTTPS, Port: 443
- Default action: Forward to → `project-a-dev-frontend-tg`

### SSL Certificate (za HTTPS listener)
- Certificate source: From ACM
- Ako nema certifikata: klikni "Request new ACM certificate"
  - Domain: `*.firma.com` (wildcard pokriva sve subdomene)
  - Validation: DNS validation (dodaj CNAME u Route53)
  - Čekaj 5-10 minuta dok ACM izda cert

**SSL security policy:** `ELBSecurityPolicy-TLS13-1-2-2021-06`
- Podržava TLS 1.2 i 1.3
- Odbija TLS 1.0 i 1.1 (ranjive, PCI DSS compliance zahtijeva odbijanje)
- Moderne cipher suite

### Klikni Create Load Balancer

---

## Korak 4: Listener Rules za Path Routing

Defaultni HTTPS listener forward sve na frontend TG. Treba dodati pravilo za `/api`.

**EC2 → Load Balancers → project-a-dev-alb → Listeners → HTTPS:443 → View/edit rules**

**Add Rule:**
- Name: `api-routing`
- Conditions:
  - Path: `/api/*`
- Actions:
  - Forward to: `project-a-dev-php-tg`
- Priority: 1 (niži broj = viši prioritet, provjeri se prvi)

**Redosled pravila je bitan:**
```
Priority 1: path /api/*  → php-tg    ← provjeri se prvo
Priority 2: path /*      → frontend-tg  ← default, uhvati sve ostalo
```

Ako okrenuš redosled, `/*` uhvati sve uključujući `/api/` i PHP nikad ne primi request.

---

## Korak 5: Route53 DNS

**Route53 → Hosted Zones → firma.com → Create Record**

- Record name: `app`
- Record type: `A`
- Alias: ON
- Route traffic to: Alias to Application and Classic Load Balancer
- Region: eu-west-1
- Load balancer: odaberi `project-a-dev-alb`
- TTL: 60 (kratko za dev, 300 za prod)

**Zašto Alias A record umjesto CNAME?** AWS Alias record je besplatan (CNAME se naplaćuje po queryu), nema latencije za DNS resolution, i radi na apex domeni (`firma.com`) gdje CNAME nije dopušten po DNS standardu.

---

## Verifikacija

```bash
# DNS resolution
dig app.firma.com +short
# Treba vratiti IP adrese ALB-a (2+ adrese za HA)

# HTTPS konekcija
curl -v https://app.firma.com/health
# Treba: HTTP 200, cert info u verbose outputu

# HTTP → HTTPS redirect
curl -I http://app.firma.com
# Treba: HTTP/1.1 301 Moved Permanently
# Location: https://app.firma.com/

# ALB direktno (provjeri bez DNS)
curl -H "Host: app.firma.com" https://project-a-dev-alb-123456.eu-west-1.elb.amazonaws.com/health --resolve project-a-dev-alb-123456.eu-west-1.elb.amazonaws.com:443:$(dig +short project-a-dev-alb-123456.eu-west-1.elb.amazonaws.com | head -1)
```

---

## Monitoring Tab

**EC2 → Load Balancers → project-a-dev-alb → Monitoring**

Ključne metrike koje gledati odmah:

| Metrika | Šta znači | Alarm prag |
|---|---|---|
| Request Count | ukupan broj requestova | info |
| Target Response Time | latencija backend-a | > 2s = problem |
| HTTP 5XX (Target) | backend greške | > 0 = istraga |
| HTTP 5XX (ELB) | ALB greške (unhealthy targets) | > 0 = kritično |
| Healthy Host Count | broj zdravih targeta | < 1 = outage |

**Target Groups → project-a-dev-frontend-tg → Targets tab**: Vidi health status svakog registrovanog targeta. Ako piše "unhealthy", klikni na target i vidi reason (timeout, connection refused, wrong status code).

---

## Česte Greške pri Ručnom Kreiranju

**ALB u private subnetima:** Nije dostupan s interneta. Idi u ALB → Edit subnets, promijeni na public.

**Worker node SG ne dozvoljava ALB:** ALB healthcheck failuje. EKS worker node SG mora imati inbound od `project-a-dev-alb-sg` na portovima koje koristiš.

**Target group pogrešan port:** PHP radi na 9000, ti registriraš 8080. Health check prolazi jer `/health` endpoint postoji na oba porta, ali API zahtjevi failuju.

**SSL cert nije u eu-west-1:** ACM certifikati su regionalni (osim za CloudFront koji zahtijeva us-east-1). ALB u eu-west-1 može koristiti samo certove iz eu-west-1.

**HTTP/2 vs HTTP/1.1:** ALB defaultno nudi HTTP/2 prema klijentima, ali prema targetima uvijek koristi HTTP/1.1. Ako tvoj PHP/Go servis ima HTTP/2 specifičnu logiku, treba to uzeti u obzir.
