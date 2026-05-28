# HTTPS i Sertifikati

## Pregled strategije po environmentu

| Environment | Sertifikat | Ko ga kreira | Renewal |
|-------------|-----------|-------------|---------|
| Lokalni (kind) | Self-signed | `openssl` ručno | Ručno (godišnje) |
| Dev/Staging (AWS) | Let's Encrypt wildcard | `certbot` + Route53 DNS | Ručno (90 dana) |
| Prod (AWS) | ACM managed | Terraform (DNS validation) | Automatski |

Zašto tri različita pristupa? Lokalno ne možeš dobiti CA-trusted cert za
`app.local` jer DNS ne postoji javno. Let's Encrypt radi za wildcard domene na
dev ali zahtjeva DNS challenge. ACM je managed servis koji automatski obnavlja
sertifikat i integrisan je sa ALB.

## Lokalni razvoj — Self-signed

```bash
# Kreiraj self-signed cert za app.local i monitoring.local
openssl req -x509 -nodes -days 365 \
  -keyout tls/app.local.key \
  -out tls/app.local.crt \
  -subj "/CN=app.local/O=project-a" \
  -addext "subjectAltName=DNS:app.local,DNS:monitoring.local"

# Provjeri cert
openssl x509 -in tls/app.local.crt -text -noout | grep -E "Subject:|DNS:"
```

`-addext "subjectAltName=DNS:app.local"` je obavezno — moderni browseri
ignorišu CN i gledaju samo SAN (Subject Alternative Names). Bez ovoga,
browser će prikazati upozorenje čak i ako si dodao cert u trusted store.

### Kubernetes TLS Secret

```bash
kubectl create secret tls helloworld-tls \
  --cert=tls/app.local.crt \
  --key=tls/app.local.key \
  --namespace helloworld-local

# Provjeri
kubectl get secret helloworld-tls -n helloworld-local -o jsonpath='{.data.tls\.crt}' | \
  base64 -d | openssl x509 -text -noout | grep "Not After"
```

### Helm values za lokalni TLS

```yaml
# values/local.yaml
ingress:
  tls: true
  tlsSecretName: helloworld-tls
  annotations:
    kubernetes.io/ingress.class: nginx
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
```

Browser će prikazati "Your connection is not private" — ovo je očekivano za
self-signed. Klikni "Advanced" → "Proceed to app.local" za lokalni razvoj.

### Dodaj u trusted store (opcionalno)

```bash
# macOS — dodaj u system keychain
sudo security add-trusted-cert -d -r trustRoot \
  -k /Library/Keychains/System.keychain tls/app.local.crt

# Linux
sudo cp tls/app.local.crt /usr/local/share/ca-certificates/app.local.crt
sudo update-ca-certificates
```

## AWS Dev/Staging — Let's Encrypt Wildcard

Let's Encrypt može dati wildcard cert za `*.dev.firma.com` ali zahtjeva
DNS-01 challenge (moraš kreirati TXT record u DNS-u da dokažeš vlasništvo).

```bash
# Certbot u Docker kontejneru (pravilo: Docker everywhere)
docker run --rm \
  -v $(pwd)/letsencrypt:/etc/letsencrypt \
  -v $(pwd)/letsencrypt-lib:/var/lib/letsencrypt \
  certbot/dns-route53 certonly \
  --dns-route53 \
  --dns-route53-propagation-seconds 30 \
  -d "*.dev.firma.com" \
  -d "dev.firma.com" \
  --email tvoj-email@firma.com \
  --agree-tos \
  --non-interactive

# Certbot automatski kreira i briše DNS TXT record na Route53
# Potrebna IAM permisija: route53:ChangeResourceRecordSets na hosted zone
```

### Import u ACM

```bash
# Importuj cert u ACM
aws acm import-certificate \
  --certificate fileb://letsencrypt/live/dev.firma.com/cert.pem \
  --private-key fileb://letsencrypt/live/dev.firma.com/privkey.pem \
  --certificate-chain fileb://letsencrypt/live/dev.firma.com/chain.pem \
  --region eu-west-1

# Zapamti ARN koji dobiješ — treba za ALB annotation
# Izlaz: { "CertificateArn": "arn:aws:acm:eu-west-1:123456789:certificate/abc..." }
```

### Helm values za dev (ALB + importovan cert)

```yaml
# values/dev.yaml
ingress:
  host: app.dev.firma.com
  tls: true
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/certificate-arn: "arn:aws:acm:eu-west-1:123456789:certificate/abc"
    alb.ingress.kubernetes.io/ssl-redirect: "443"
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTP": 80}, {"HTTPS": 443}]'
```

Let's Encrypt cert traje 90 dana. Postavi reminder ili cron job koji ponavlja
`certbot renew` i `aws acm import-certificate --certificate-arn <existing-arn>`.

## AWS Prod — ACM Managed

Za produkciju, ACM kreira i automatski obnavlja cert. Terraform konfiguracija:

```hcl
# U terraform/envs/prod/main.tf ili modules/iam/main.tf

# ACM sertifikat za prod domenu
resource "aws_acm_certificate" "prod" {
  domain_name               = "firma.com"
  subject_alternative_names = ["*.firma.com"]  # wildcard za subdomene
  validation_method         = "DNS"

  lifecycle {
    create_before_destroy = true  # Bez downtime pri renewal
  }

  tags = {
    Environment = "prod"
    Project     = "project-a"
  }
}

# DNS validation record u Route53
data "aws_route53_zone" "prod" {
  name = "firma.com."
}

resource "aws_route53_record" "cert_validation" {
  for_each = {
    for dvo in aws_acm_certificate.prod.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = data.aws_route53_zone.prod.zone_id
}

# Čekaj da cert bude ISSUED (DNS propagation može trajati do 30 min)
resource "aws_acm_certificate_validation" "prod" {
  certificate_arn         = aws_acm_certificate.prod.arn
  validation_record_fqdns = [for record in aws_route53_record.cert_validation : record.fqdn]
}

output "cert_arn" {
  value = aws_acm_certificate_validation.prod.certificate_arn
}
```

### Helm values za prod (ACM cert)

```yaml
# values/prod.yaml
ingress:
  host: app.firma.com
  tls: true
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/certificate-arn: "${ACM_CERT_ARN}"  # iz Terraform output
    alb.ingress.kubernetes.io/ssl-redirect: "443"
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTP": 80}, {"HTTPS": 443}]'
```

`ACM_CERT_ARN` proslijeđuješ kroz CI/CD variable ili Terraform output.

## Rotacija sertifikata

| Tip | Kada ističe | Akcija |
|-----|------------|--------|
| Self-signed lokalni | 365 dana | Ponoviti `openssl` komandu, update Kubernetes secret |
| Let's Encrypt (ACM import) | 90 dana | `certbot renew` + `aws acm import-certificate --renew` |
| ACM managed | Automatski (~60 dana prije isteka) | Ništa — ACM obnavlja automatski |

Za Let's Encrypt, postavi AWS EventBridge scheduled rule ili GitLab scheduled
pipeline koji provjerava datum isteka i pokreće renewal.

## Provjera HTTPS

```bash
# Provjeri cert detalje za bilo koji URL
echo | openssl s_client -connect app.dev.firma.com:443 -servername app.dev.firma.com 2>/dev/null | \
  openssl x509 -text -noout | grep -E "Subject:|Issuer:|Not After"

# Provjeri da li HTTP redirect na HTTPS radi
curl -I http://app.dev.firma.com
# Očekivano: HTTP/1.1 301 Moved Permanently, Location: https://app.dev.firma.com/
```
