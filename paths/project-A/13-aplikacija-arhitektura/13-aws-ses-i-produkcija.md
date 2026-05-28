# 13. AWS SES i Produkcija

## Zašto SES a ne SMTP relay ili SendGrid

- **Cijena:** $0.10 / 1000 emailova. Besplatno prvih 62 000/mj ako šalješ iz EC2/EKS.
- **Pouzdanost:** AWS infrastruktura, globalni deliverability.
- **Integracija:** IAM policy + Secrets Manager = nema hardcoded kredencijala.
- **SPF/DKIM/DMARC:** Automatski via Route53 TXT/CNAME recordima.

---

## Terraform: SES domenski identitet i DKIM

```hcl
# terraform/modules/ses/main.tf

variable "domain" {
  description = "Domena za slanje emaila, npr. firma.com"
  type        = string
}

variable "route53_zone_id" {
  description = "Route53 Hosted Zone ID za domenu"
  type        = string
}

variable "aws_region" {
  description = "AWS region gdje je SES aktivan"
  type        = string
  default     = "eu-west-1"
}

variable "secret_arn" {
  description = "ARN Secrets Manager secretа gdje se čuvaju SES kredencijali"
  type        = string
}

# --- Domenski identitet ---

resource "aws_ses_domain_identity" "main" {
  domain = var.domain
}

# --- DKIM (DomainKeys Identified Mail) ---
# Potpisuje svaki email kriptografski — ključno za deliverability

resource "aws_ses_domain_dkim" "main" {
  domain = aws_ses_domain_identity.main.domain
}

# --- Route53: Domain verification TXT record ---

resource "aws_route53_record" "ses_verification" {
  zone_id = var.route53_zone_id
  name    = "_amazonses.${var.domain}"
  type    = "TXT"
  ttl     = 600
  records = [aws_ses_domain_identity.main.verification_token]
}

# --- Route53: DKIM CNAME records (AWS generira 3 tokena) ---

resource "aws_route53_record" "ses_dkim" {
  count   = 3
  zone_id = var.route53_zone_id
  name    = "${aws_ses_domain_dkim.main.dkim_tokens[count.index]}._domainkey.${var.domain}"
  type    = "CNAME"
  ttl     = 600
  records = ["${aws_ses_domain_dkim.main.dkim_tokens[count.index]}.dkim.amazonses.com"]
}

# --- Route53: SPF record (dopušta SES slanje u ime domene) ---

resource "aws_route53_record" "spf" {
  zone_id = var.route53_zone_id
  name    = var.domain
  type    = "TXT"
  ttl     = 600
  records = ["v=spf1 include:amazonses.com ~all"]
}

# --- Route53: DMARC record ---

resource "aws_route53_record" "dmarc" {
  zone_id = var.route53_zone_id
  name    = "_dmarc.${var.domain}"
  type    = "TXT"
  ttl     = 600
  records = ["v=DMARC1; p=quarantine; rua=mailto:dmarc-reports@${var.domain}"]
}
```

---

## Terraform: IAM user i SMTP kredencijali

```hcl
# terraform/modules/ses/iam.tf

# Dedicated IAM user samo za SES SMTP slanje
resource "aws_iam_user" "ses_smtp" {
  name = "project-a-ses-smtp"
  path = "/service-accounts/"

  tags = {
    Purpose = "SES SMTP sending for project-a"
  }
}

# Policy: dozvola isključivo za SendRawEmail
resource "aws_iam_user_policy" "ses_smtp" {
  name   = "ses-send-only"
  user   = aws_iam_user.ses_smtp.name
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "AllowSESSend"
        Effect   = "Allow"
        Action   = ["ses:SendRawEmail"]
        Resource = "*"
      }
    ]
  })
}

# Access key (ID + Secret)
resource "aws_iam_access_key" "ses_smtp" {
  user = aws_iam_user.ses_smtp.name
}

# VAŽNO: SES SMTP password NIJE isti kao AWS Secret Access Key!
# AWS automatski derivira SMTP password iz Secret Key-a.
# Terraform output: aws_iam_access_key.ses_smtp.ses_smtp_password_v4

# Spremi kredencijale u Secrets Manager (ne u Terraform state!)
resource "aws_secretsmanager_secret_version" "ses_credentials" {
  secret_id = var.secret_arn
  secret_string = jsonencode({
    smtp_username = aws_iam_access_key.ses_smtp.id
    smtp_password = aws_iam_access_key.ses_smtp.ses_smtp_password_v4
    smtp_host     = "email-smtp.${var.aws_region}.amazonaws.com"
    smtp_port     = 587
  })
}
```

**Upozorenje:** `ses_smtp_password_v4` se sprema u Terraform state. Koristi remote state s enkripcijom (S3 + SSE-KMS) ili `terraform state rm` i ručno upravljanje ovim secretom ako je sigurnost kritična.

---

## Terraform: outputs.tf

```hcl
# terraform/modules/ses/outputs.tf

output "ses_domain_identity_arn" {
  value       = aws_ses_domain_identity.main.arn
  description = "ARN SES domenskog identiteta"
}

output "ses_verification_token" {
  value       = aws_ses_domain_identity.main.verification_token
  description = "Token za Route53 TXT verifikacijski record"
}

output "smtp_host" {
  value       = "email-smtp.${var.aws_region}.amazonaws.com"
  description = "SES SMTP endpoint"
}

output "smtp_username" {
  value       = aws_iam_access_key.ses_smtp.id
  sensitive   = true
  description = "SMTP username (IAM Access Key ID)"
}
```

---

## SES Sandbox → Production Access

Svaki novi AWS account počinje u **SES Sandbox modu**:

| Ograničenje | Sandbox | Production |
|-------------|---------|-----------|
| Primatelji | Samo verifikovane adrese | Bilo koja adresa |
| Dnevni limit | 200 emailova | Nema limita |
| Sending rate | 1 email/sekundi | Po requestu |

**Zahtjev za Production Access:**

```
AWS Console → Simple Email Service → Account Dashboard
→ "Request Production Access" dugme
→ Popuni formu:
   - Mail type: Transactional
   - Website URL: https://firma.com
   - Use case description:
     "We send transactional emails: email verification on registration,
      password reset, and account notifications. We never send marketing
      email. All recipients opt-in via registration form."
   - Additional contacts: devops@firma.com
→ Submit

Approval: 24-48h od strane AWS Support tima.
```

---

## Provjera SES konfiguracije via AWS CLI

```bash
# 1. Provjeri status verifikacije domene
aws ses get-identity-verification-attributes \
  --identities firma.com \
  --region eu-west-1
# VerificationStatus treba biti "Success"

# 2. Provjeri DKIM status
aws ses get-identity-dkim-attributes \
  --identities firma.com \
  --region eu-west-1
# DkimVerificationStatus: "Success", DkimEnabled: true

# 3. Test email (samo dok si u sandboxu ili ako je primatelj verificiran)
aws ses send-email \
  --from noreply@firma.com \
  --to test@firma.com \
  --subject "SES test" \
  --text "Email from SES works!" \
  --region eu-west-1

# 4. Provjeri sending statistics
aws ses get-send-statistics --region eu-west-1 | \
  jq '.SendDataPoints | sort_by(.Timestamp) | last'
```

---

## Go: čitanje SES kredencijala iz Secrets Manager

```go
// internal/secrets/aws.go
package secrets

import (
    "context"
    "encoding/json"
    "fmt"

    "github.com/aws/aws-sdk-go-v2/config"
    "github.com/aws/aws-sdk-go-v2/service/secretsmanager"
)

type SESCredentials struct {
    SMTPUsername string `json:"smtp_username"`
    SMTPPassword string `json:"smtp_password"`
    SMTPHost     string `json:"smtp_host"`
    SMTPPort     int    `json:"smtp_port"`
}

func GetSESCredentials(ctx context.Context, secretARN string) (SESCredentials, error) {
    cfg, err := config.LoadDefaultConfig(ctx)
    if err != nil {
        return SESCredentials{}, fmt.Errorf("load aws config: %w", err)
    }

    client := secretsmanager.NewFromConfig(cfg)
    result, err := client.GetSecretValue(ctx, &secretsmanager.GetSecretValueInput{
        SecretId: &secretARN,
    })
    if err != nil {
        return SESCredentials{}, fmt.Errorf("get secret: %w", err)
    }

    var creds SESCredentials
    if err := json.Unmarshal([]byte(*result.SecretString), &creds); err != nil {
        return SESCredentials{}, fmt.Errorf("parse secret: %w", err)
    }

    return creds, nil
}
```

**Upotreba pri startu Go servisa:**
```go
// cmd/server/main.go
func main() {
    ctx := context.Background()
    env := os.Getenv("APP_ENV") // "production"

    var emailCfg email.Config
    if env == "production" {
        secretARN := os.Getenv("SES_SECRET_ARN")
        creds, err := secrets.GetSESCredentials(ctx, secretARN)
        if err != nil {
            log.Fatalf("cannot load SES credentials: %v", err)
        }
        emailCfg = email.Config{
            SMTPHost:     creds.SMTPHost,
            SMTPPort:     creds.SMTPPort,
            SMTPUsername: creds.SMTPUsername,
            SMTPPassword: creds.SMTPPassword,
            FromAddress:  "noreply@firma.com",
            FromName:     "Project-A",
        }
    } else {
        emailCfg = email.NewConfig(env)
    }

    emailSvc := email.NewService(emailCfg)
    // ... ostatak inicijalizacije
}
```

**EKS Pod annotation za Secrets Manager pristup (IRSA):**
```yaml
# Pod spec u Helm template-u
spec:
  serviceAccountName: go-service  # SA s IRSA annotation
  containers:
    - name: go-service
      env:
        - name: APP_ENV
          value: production
        - name: SES_SECRET_ARN
          value: arn:aws:secretsmanager:eu-west-1:123456789:secret:project-a/ses-credentials
```

```yaml
# ServiceAccount s IRSA
apiVersion: v1
kind: ServiceAccount
metadata:
  name: go-service
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::123456789:role/project-a-go-service
```

IAM Role treba permission za `secretsmanager:GetSecretValue` na specifičnom ARN-u.

---

## SES monitoring i alarmi

```hcl
# terraform/modules/ses/monitoring.tf

# Alarm ako bounce rate pređe 5%
resource "aws_cloudwatch_metric_alarm" "ses_bounce_rate" {
  alarm_name          = "ses-bounce-rate-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Reputation.BounceRate"
  namespace           = "AWS/SES"
  period              = 3600  # 1 sat
  statistic           = "Average"
  threshold           = 0.05  # 5%
  alarm_actions       = [var.sns_alarm_topic_arn]
  alarm_description   = "SES bounce rate over 5% — AWS može suspendovati nalog"
}

# Alarm ako complaint rate pređe 0.1%
resource "aws_cloudwatch_metric_alarm" "ses_complaint_rate" {
  alarm_name          = "ses-complaint-rate-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Reputation.ComplaintRate"
  namespace           = "AWS/SES"
  period              = 3600
  statistic           = "Average"
  threshold           = 0.001  # 0.1%
  alarm_actions       = [var.sns_alarm_topic_arn]
  alarm_description   = "SES complaint rate over 0.1% — kritično za deliverability"
}
```

**Bounce i complaint rate su kritični.** AWS može automatski pauzirati nalog ako:
- Bounce rate > 10%
- Complaint rate > 0.5%

Za transakcijske emailove (verifikacija, reset lozinke) ove granice ne bi trebale biti problem — emailove šalješ samo na adrese koje je korisnik sam upisao.
