# 04 — SSL i Certifikati na ALB

## Kako TLS termination radi na ALB

```
Browser → [TLS handshake] → ALB → [plain HTTP] → Pod

TLS handshake detalji:
1. Client Hello: browser šalje podržane cipher suites, TLS verzije
2. Server Hello: ALB bira cipher suite, šalje certificate
3. Certificate verification: browser validira cert chain (Root CA → Intermediate → Leaf cert)
4. Key exchange: DH/ECDH, obje strane izvode session key
5. Finished: encrypted komunikacija počinje
```

**Šta ALB radi:** Drži private key certifikata. Dekriptuje sav dolazni HTTPS saobraćaj, šalje plain HTTP prema podovima. Podovi ne znaju za TLS — vide samo HTTP requestove sa `X-Forwarded-Proto: https` headerom.

**Zašto je ovo dobro:** Pods ne moraju upravljati certifikatima. TLS offload = manji CPU na podovima. Centralizovano certificate management na ALB/ACM nivou.

---

## ACM (AWS Certificate Manager) — Managed Certificates

Najjednostavniji put: AWS automatski kreira, potpisuje i obnavlja certifikate.

### Kreiranje u konzoli

```
ACM → Request certificate → Request a public certificate
Domain names: *.firma.com
Validation method: DNS validation (preporučeno — automatski sa Route53)
→ Next → Review → Confirm
```

ACM kreira CNAME record koji treba dodati u DNS. Ako koristiš Route53:

```
ACM → Certificate → Create records in Route53 (jedan klik)
```

ACM automatski dodaje CNAME, validira cert u roku 5-10 minuta.

**DNS validation vs Email validation:**
- DNS validation: dodaš CNAME, ACM automatski obnavlja (preporučeno)
- Email validation: AWS šalje mail na admin@firma.com, treba ručno kliknuti — ne može se automatski obnoviti

### Kreiranje Terraformom (production standard)

```hcl
# modules/ssl/main.tf

resource "aws_acm_certificate" "main" {
  domain_name               = "*.firma.com"
  subject_alternative_names = ["firma.com"]  # apex domena osobno
  validation_method         = "DNS"

  lifecycle {
    create_before_destroy = true  # KRITIČNO: nova cert kreira se prije brisanja stare
    # Bez ovoga: Terraform briše stari cert, ALB ostaje bez certa → downtime
  }

  tags = {
    Environment = var.environment
    Project     = "project-a"
  }
}

resource "aws_route53_record" "cert_validation" {
  for_each = {
    for dvo in aws_acm_certificate.main.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }

  zone_id = aws_route53_zone.main.zone_id
  name    = each.value.name
  type    = each.value.type
  records = [each.value.record]
  ttl     = 60

  allow_overwrite = true  # za slučaj da record već postoji od prethodnog apply-a
}

resource "aws_acm_certificate_validation" "main" {
  certificate_arn         = aws_acm_certificate.main.arn
  validation_record_fqdns = [for record in aws_route53_record.cert_validation : record.fqdn]

  timeouts {
    create = "10m"  # ACM validacija može potrajati
  }
}

# Output ARN za korištenje u ALB/Ingress
output "certificate_arn" {
  value = aws_acm_certificate_validation.main.certificate_arn
}
```

**`create_before_destroy`** je obavezan za certifikate. Bez njega: `terraform apply` briše stari cert, kreira novi, ALB je kratko bez validnog certa. Sa njim: novi cert je gotov i attach-an prije nego se stari briše.

### Auto-renewal

ACM automatski obnavlja managed certifikate **60 dana prije isteka**. ALB automatski primjenjuje novi certifikat bez downtime, bez restarta, bez intervencije. Jedini preduslov: DNS validation CNAME mora ostati u Route53.

---

## Custom/Imported Certifikati

Kad koristiš vlastiti CA, certifikat od third-party CA koji nije u ACM, ili self-signed cert za internal tools.

```bash
# Generisanje self-signed cert (samo za dev/internal, nikad produkcija)
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes \
  -subj "/CN=*.firma.com/O=Firma d.o.o./C=BA"

# Import u ACM
aws acm import-certificate \
  --certificate fileb://cert.pem \
  --private-key fileb://key.pem \
  --certificate-chain fileb://chain.pem \
  --region eu-west-1

# Provjeri import
aws acm list-certificates --region eu-west-1 \
  --query 'CertificateSummaryList[?DomainName==`*.firma.com`]'
```

**Razlike od managed certa:**
- ACM **ne obnavlja** imported certifikate automatski
- Moraš pratiti expiry i ručno reimportovati (ili automatizovati)
- Preporuča se CloudWatch alarm na `aws/acm DaysToExpiry < 30`

```bash
# Postavi alarm (uradi jednom po importovanom certu)
aws cloudwatch put-metric-alarm \
  --alarm-name "cert-expiry-firma.com" \
  --metric-name DaysToExpiry \
  --namespace AWS/CertificateManager \
  --statistic Minimum \
  --period 86400 \
  --threshold 30 \
  --comparison-operator LessThanThreshold \
  --dimensions Name=CertificateArn,Value=arn:aws:acm:eu-west-1:123:certificate/abc \
  --alarm-actions arn:aws:sns:eu-west-1:123:pagerduty-alerts
```

---

## Multi-Domain Certifikati

**Wildcard** `*.firma.com` pokriva:
- app.firma.com
- dev.firma.com
- api.firma.com
- monitoring.firma.com

**Ne pokriva:**
- firma.com (apex domena — treba eksplicitno dodati kao SAN)
- sub.sub.firma.com (wildcard je samo jedan nivo dubine)

**Više certova na jednom ALB-u (SNI):**

ALB podržava Server Name Indication (SNI) — klijent u TLS ClientHello šalje hostname, ALB vraća odgovarajući cert.

```
ALB HTTPS:443 listener → može imati više certifikata:
  *.firma.com   → za app.firma.com, dev.firma.com
  *.partner.com → za portal.partner.com (B2B integracija)
  default cert  → za ostale zahtjeve
```

U konzoli: ALB → Listeners → HTTPS:443 → View/edit certificates → Add certificate

---

## SSL Security Policy

Definira koji TLS protokoli i cipher suites ALB prihvata.

**Preporučeni za produkciju:** `ELBSecurityPolicy-TLS13-1-2-2021-06`

```
Podržava: TLS 1.2, TLS 1.3
Odbija: TLS 1.0, TLS 1.1 (SSLv3 odbijen već godinama)

Cipher suites (TLS 1.2):
  ECDHE-RSA-AES128-GCM-SHA256  ✓
  ECDHE-RSA-AES256-GCM-SHA384  ✓
  AES128-GCM-SHA256             ✓ (bez forward secrecy, ali ok)
  RC4, DES, 3DES                ✗ (zastarjelo, odbijeno)
```

**Zašto TLS 1.0/1.1 treba odbiti:**
- BEAST attack (TLS 1.0 CBC mode)
- POODLE attack (SSLv3)
- PCI DSS 3.2+ zahtijeva TLS 1.2 minimum
- Preglednik koji ne podržava TLS 1.2 ne postoji u aktivnoj upotrebi od 2015.

**Legacy compatibility** (ako imaš starije klijente/IoT uređaje koji ne podržavaju TLS 1.2):
`ELBSecurityPolicy-TLS-1-1-2017-01` — kompromis, ali ne za nove projekte.

---

## Provjera TLS iz Terminala

```bash
# Provjeri cert info
openssl s_client -connect app.firma.com:443 -servername app.firma.com 2>/dev/null \
  | openssl x509 -noout -dates -subject -issuer

# Output:
# subject=CN=*.firma.com, O=Firma, C=BA
# issuer=CN=Amazon RSA 2048 M02, O=Amazon, C=US
# notBefore=Jan 15 00:00:00 2024 GMT
# notAfter=Feb 15 23:59:59 2025 GMT

# Provjeri koji TLS protokol se koristi
openssl s_client -connect app.firma.com:443 -tls1_2 2>&1 | grep "Protocol"
# Protocol: TLSv1.2

openssl s_client -connect app.firma.com:443 -tls1_3 2>&1 | grep "Protocol"
# Protocol: TLSv1.3

# Provjeri da TLS 1.0 je odbijen
openssl s_client -connect app.firma.com:443 -tls1 2>&1 | grep -E "alert|handshake"
# handshake failure  ← OK, TLS 1.0 odbijen

# Detaljan cert chain
openssl s_client -connect app.firma.com:443 -showcerts 2>/dev/null \
  | openssl x509 -noout -text | grep -A 5 "Subject Alternative"

# Provjeri expiry u danima
echo | openssl s_client -connect app.firma.com:443 -servername app.firma.com 2>/dev/null \
  | openssl x509 -noout -enddate | awk -F= '{print $2}' \
  | xargs -I{} date -j -f "%b %d %T %Y %Z" "{}" +%s \
  | xargs -I{} sh -c 'echo $(( ({} - $(date +%s)) / 86400 )) days until expiry'

# SSL Labs grade (online provjera)
# https://www.ssllabs.com/ssltest/analyze.html?d=app.firma.com
# Cilj: A ili A+
```

**Provjera certifikata u ACM:**

```bash
# Lista svih certova
aws acm list-certificates --region eu-west-1 \
  --query 'CertificateSummaryList[].[DomainName,Status,RenewalEligibility]' \
  --output table

# Detalji specifičnog certa
aws acm describe-certificate \
  --certificate-arn arn:aws:acm:eu-west-1:123:certificate/abc \
  --query 'Certificate.[DomainName,Status,NotAfter,RenewalSummary]'
```

---

## HSTS (HTTP Strict Transport Security)

Nakon što imaš HTTPS, dodaj HSTS header koji govori browseru da uvijek koristi HTTPS:

```yaml
# U Ingress anotacijama (ALB response headers)
alb.ingress.kubernetes.io/response-header-modifier: >
  [{"action":{"type":"AddHeader","header":{"name":"Strict-Transport-Security","value":"max-age=31536000; includeSubDomains"}}}]
```

Ili u nginx konfiguraciji:
```nginx
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```

**Oprez sa HSTS:** Jednom kad browser zapamti HSTS, nema HTTP fallbacka godinu dana (max-age=31536000). Ako ugasiš HTTPS (npr. cert istekne), korisnici ne mogu pristupiti sajtu ni putem HTTP dok HSTS ne istekne. Uvijek testiraj na dev domeni prvo.

**HSTS Preloading:** Možeš prijaviti domenu na https://hstspreload.org — Chrome/Firefox ugradi u listu domena koje uvijek idu na HTTPS direktno, bez prvog HTTP zahtjeva. Ireverzibilno (uklanjanje traje mjesecima), samo za produkciju.
