# 12. Email Service i Mailpit

## Strategija po okruženju

| Okruženje | Email backend | Kako provjeriš email |
|-----------|--------------|----------------------|
| Local / Dev | Mailpit container | http://localhost:8025 |
| Staging | Mailpit u K8s namespace | https://mail.dev.firma.com |
| Production | AWS SES | Pravi inbox |

Mailpit je moderni zamjena za Mailhog. Hvata sve odlazne SMTP poruke i prikazuje ih u web UI-u — pravi email nikada ne napušta tvoju mrežu u non-prod okruženjima.

---

## Docker Compose konfiguracija

Mailpit dodaješ u `docker-compose.override.yml` kako bi ostao odvojen od `docker-compose.yml` (koji idu u prod image build):

```yaml
# docker-compose.override.yml
services:
  mailpit:
    image: axllent/mailpit:latest
    container_name: mailpit
    ports:
      - "1025:1025"   # SMTP — go-service šalje ovdje
      - "8025:8025"   # Web UI — pregledaš emailove ovdje
    environment:
      MP_MAX_MESSAGES: 100
      MP_SMTP_AUTH_ACCEPT_ANY: true
      MP_SMTP_AUTH_ALLOW_INSECURE: true
    networks:
      - app-network
    profiles: []   # Uvijek aktivan u dev (ne koristi Docker profile)
```

`docker-compose.override.yml` se automatski merguje s `docker-compose.yml` pri `docker compose up`. Ne trebaš eksplicitno navesti fajl.

**Provjera rada:**
```bash
docker compose up -d mailpit
curl -s http://localhost:8025/api/v1/messages | jq '.total'
# Output: 0 (prazno, čeka emailove)
```

> **Podman:** `podman compose up -d mailpit`

---

## Go: Email konfiguracija

```go
// internal/email/config.go
package email

import "os"

type Config struct {
    SMTPHost     string
    SMTPPort     int
    SMTPUsername string
    SMTPPassword string
    FromAddress  string
    FromName     string
}

func NewConfig(env string) Config {
    if env == "development" || env == "staging" {
        return Config{
            SMTPHost:    "mailpit", // Docker/K8s service name
            SMTPPort:    1025,
            FromAddress: "noreply@project-a.local",
            FromName:    "Project-A Dev",
            // Bez username/password — Mailpit prihvata sve
        }
    }
    // Production: AWS SES via SMTP
    return Config{
        SMTPHost:     os.Getenv("SES_SMTP_HOST"),     // email-smtp.eu-west-1.amazonaws.com
        SMTPPort:     587,
        SMTPUsername: os.Getenv("SES_SMTP_USERNAME"), // iz AWS Secrets Manager
        SMTPPassword: os.Getenv("SES_SMTP_PASSWORD"),
        FromAddress:  "noreply@firma.com",
        FromName:     "Project-A",
    }
}
```

---

## Go: Email sender

```go
// internal/email/service.go
package email

import (
    "context"
    "fmt"
    "net/smtp"
)

type Service struct {
    config Config
}

func NewService(config Config) *Service {
    return &Service{config: config}
}

func (s *Service) SendVerificationEmail(ctx context.Context, to, token, baseURL string) error {
    verifyURL := fmt.Sprintf("%s/verify?token=%s", baseURL, token)

    subject := "Verify your email"
    body := fmt.Sprintf(`Hello,

Click the link below to verify your email address:
%s

This link expires in 24 hours.

If you did not register, ignore this email.
`, verifyURL)

    msg := fmt.Sprintf(
        "From: %s <%s>\r\nTo: %s\r\nSubject: %s\r\nContent-Type: text/plain; charset=UTF-8\r\n\r\n%s",
        s.config.FromName,
        s.config.FromAddress,
        to,
        subject,
        body,
    )

    addr := fmt.Sprintf("%s:%d", s.config.SMTPHost, s.config.SMTPPort)

    var auth smtp.Auth
    if s.config.SMTPUsername != "" {
        auth = smtp.PlainAuth("", s.config.SMTPUsername, s.config.SMTPPassword, s.config.SMTPHost)
    }

    return smtp.SendMail(addr, auth, s.config.FromAddress, []string{to}, []byte(msg))
}
```

**Napomena:** `smtp.SendMail` je blokirajuć. U registration handleru pozivat ćeš ga u goroutini kako bi HTTP odgovor bio odmah poslan korisniku (vidi fajl 14).

---

## Provjera emaila u Mailpit lokalno

```
http://localhost:8025
→ Inbox: prikazuje sve uhvaćene emailove u realnom vremenu
→ Klikni na email → vidi formatirani sadržaj
→ Kopiraj verification link iz tijela emaila
→ Otvori link u browseru → provjeri cijeli flow
```

**Mailpit REST API** (korisno za Playwright testove):
```bash
# Svi emailovi
curl http://localhost:8025/api/v1/messages

# Najnoviji email
curl http://localhost:8025/api/v1/messages | jq '.messages[0]'

# Obrisi sve (reset između testova)
curl -X DELETE http://localhost:8025/api/v1/messages
```

---

## K8s deployment za Mailpit (dev/staging namespace)

```yaml
# k8s/dev/mailpit.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mailpit
  namespace: project-a-dev
spec:
  replicas: 1
  selector:
    matchLabels:
      app: mailpit
  template:
    metadata:
      labels:
        app: mailpit
    spec:
      containers:
        - name: mailpit
          image: axllent/mailpit:latest
          ports:
            - containerPort: 1025  # SMTP
            - containerPort: 8025  # Web UI
          env:
            - name: MP_MAX_MESSAGES
              value: "500"
            - name: MP_SMTP_AUTH_ACCEPT_ANY
              value: "true"
            - name: MP_SMTP_AUTH_ALLOW_INSECURE
              value: "true"
          resources:
            requests:
              cpu: 10m
              memory: 32Mi
            limits:
              cpu: 50m
              memory: 64Mi
---
apiVersion: v1
kind: Service
metadata:
  name: mailpit
  namespace: project-a-dev
spec:
  selector:
    app: mailpit
  ports:
    - name: smtp
      port: 1025
      targetPort: 1025
    - name: web
      port: 8025
      targetPort: 8025
---
# Ingress za Mailpit web UI u dev (dostupan timu)
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: mailpit
  namespace: project-a-dev
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTPS": 443}]'
spec:
  rules:
    - host: mail.dev.firma.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: mailpit
                port:
                  number: 8025
```

**Sigurnost:** Mailpit ingress u dev ne treba biti javno dostupan. Dodaj IP whitelist annotation ili basic auth ako je eksponiran na internetu:
```yaml
annotations:
  alb.ingress.kubernetes.io/inbound-cidrs: "10.0.0.0/8,YOUR_OFFICE_IP/32"
```

---

## Helm values za email konfiguraciju

```yaml
# values/dev.yaml
email:
  smtpHost: mailpit
  smtpPort: 1025
  fromAddress: noreply@project-a.local
  fromName: "Project-A Dev"
  requireAuth: false
  deployMailpit: true  # Helm chart kreira Mailpit Deployment u namespace-u

# values/staging.yaml
email:
  smtpHost: mailpit
  smtpPort: 1025
  fromAddress: noreply@staging.firma.com
  fromName: "Project-A Staging"
  requireAuth: false
  deployMailpit: true

# values/prod.yaml
email:
  smtpHost: email-smtp.eu-west-1.amazonaws.com
  smtpPort: 587
  fromAddress: noreply@firma.com
  fromName: "Project-A"
  requireAuth: true
  deployMailpit: false  # Prod koristi pravi SES, nema Mailpit-a
```

**Helm template za uvjetno kreiranje Mailpit-a:**
```yaml
# templates/mailpit.yaml
{{- if .Values.email.deployMailpit }}
# ... Mailpit Deployment i Service iz gornjeg K8s yaml-a
{{- end }}
```

**Go service ConfigMap koji koristi ove vrijednosti:**
```yaml
# templates/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: go-service-config
data:
  SMTP_HOST: {{ .Values.email.smtpHost | quote }}
  SMTP_PORT: {{ .Values.email.smtpPort | quote }}
  EMAIL_FROM: {{ .Values.email.fromAddress | quote }}
  EMAIL_FROM_NAME: {{ .Values.email.fromName | quote }}
```

SMTP username i password idu kroz `Secret`, ne ConfigMap.
