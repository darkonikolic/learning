# Route53 i HTTPS

## Route53: AWS DNS servis

DNS (Domain Name System) prevodi `app.dev.firma.com` u IP adresu ALB-a. Route53 je AWS-ov DNS servis koji Terraform može u potpunosti upravljati.

**Hosted Zone** je kontejner za DNS zapise jednog domena. Ako posjeduješ `firma.com`, kreiraš hosted zone za njega. Route53 ti daje 4 NS (nameserver) adrese koje postaviš kod registrara (GoDaddy, Namecheap, itd.).

Cijena: $0.50/mj per hosted zona + $0.40/milion DNS upita. Praktično zanemarivo.

## DNS Record tipovi za project-A

| Tip | Primjer | Namjena |
|-----|---------|---------|
| **A record (Alias)** | `app.dev.firma.com → ALB DNS` | Mapiranje subdomene na ALB |
| **CNAME** | `mr-42.dev.firma.com → ALB DNS` | Dynamic review envs |
| **TXT** | `_acme-challenge.firma.com` | ACM DNS validacija |
| **NS** | `firma.com → ns-xxx.awsdns-xx.com` | Delegacija na Route53 |

ALB ne dobija statičku IP adresu — dobija DNS ime poput `k8s-dev-app-abc123.eu-west-1.elb.amazonaws.com`. Zato se koristi **Alias A record**, ne CNAME na root domenu.

## Subdomeni po environmentu

Pattern za project-A:
```
app.firma.com          → prod ALB
app.staging.firma.com  → staging ALB
app.dev.firma.com      → dev ALB
mr-42.dev.firma.com    → review env (dynamic)
mr-43.dev.firma.com    → review env (dynamic)
```

Terraform kreira ove recorde:
```hcl
resource "aws_route53_record" "app_dev" {
  zone_id = data.aws_route53_zone.main.zone_id
  name    = "app.dev.firma.com"
  type    = "A"

  alias {
    name                   = aws_lb.dev.dns_name
    zone_id                = aws_lb.dev.zone_id
    evaluate_target_health = true
  }
}
```

## ACM: besplatni SSL sertifikati

AWS Certificate Manager izdaje i auto-renews SSL sertifikate za domene kojim upravljaš u Route53. Sertifikat je besplatan kada se koristi sa AWS resursima (ALB, CloudFront).

DNS validacija: ACM generiše TXT record koji moraš dodati u DNS da dokažeš vlasništvo domene. Terraform može ovo automatizovati:

```hcl
resource "aws_acm_certificate" "app" {
  domain_name               = "app.firma.com"
  subject_alternative_names = ["*.dev.firma.com", "*.staging.firma.com"]
  validation_method         = "DNS"
}

resource "aws_route53_record" "cert_validation" {
  for_each = {
    for dvo in aws_acm_certificate.app.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }
  zone_id = data.aws_route53_zone.main.zone_id
  name    = each.value.name
  type    = each.value.type
  records = [each.value.record]
  ttl     = 60
}

resource "aws_acm_certificate_validation" "app" {
  certificate_arn         = aws_acm_certificate.app.arn
  validation_record_fqdns = [for record in aws_route53_record.cert_validation : record.fqdn]
}
```

`subject_alternative_names` sa wildcard `*.dev.firma.com` pokriva sve review enviromente pod dev subdomenom.

## Custom sertifikat: import u ACM

Ako organizacija ima vlastiti sertifikat (kupljen od DigiCert, Sectigo, itd.), može se importovati:

```bash
aws acm import-certificate \
  --certificate fileb://certificate.pem \
  --private-key fileb://private-key.pem \
  --certificate-chain fileb://chain.pem
```

Importovani sertifikati se **ne renewaju automatski** — ACM šalje upozorenje 45 dana prije isteka.

## Let's Encrypt wildcard importovan u ACM

Opcija za project-A bez płaćenog sertifikata i bez zavisnosti od Route53 vlasništva:

```bash
# Certbot DNS challenge za wildcard
certbot certonly --manual --preferred-challenges dns \
  -d "*.firma.com" -d "firma.com"

# Importuj u ACM
aws acm import-certificate \
  --certificate fileb://fullchain.pem \
  --private-key fileb://privkey.pem
```

Let's Encrypt wildcard `*.firma.com` pokriva prod, `*.dev.firma.com` pokriva sve dev subdomene. Renewal svaka 3 mjeseca — može biti automatizovan kroz cron job ili GitLab scheduled pipeline koji import-uje novi sertifikat.

## Tok od DNS do HTTPS

```
Korisnik otvori https://app.dev.firma.com
    ↓
Browser upita DNS (Route53)
    ↓
Route53 vrati ALB DNS: k8s-dev-app-abc.eu-west-1.elb.amazonaws.com
    ↓
Browser se konektuje na ALB IP:443
    ↓
ALB prezentira ACM sertifikat (*.dev.firma.com)
    ↓
TLS handshake uspješan
    ↓
ALB prosljeđuje request na nginx Pod (HTTP:80, privatna mreža)
    ↓
nginx servisac index.html
```
