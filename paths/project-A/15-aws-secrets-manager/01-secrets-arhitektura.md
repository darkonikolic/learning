# 01 — Secrets arhitektura: zašto Kubernetes Secrets nisu dovoljni

## Zašto `env` u K8s Secret nije encryption

Kubernetes Secret objekt čuva podatke kao base64-encoded string. Base64 je **enkodiranje, ne enkripcija** — svako ko ima `kubectl get secret db-credentials -o yaml` dobija plaintext credentials za 30 sekundi.

Napadački vektori koji se otvaraju sa K8s Secrets:

**etcd backup exposure:**  
etcd je key-value store koji čuva cijelo stanje klastera, uključujući sve Secrets. Backup etcd-a = dump svih secretsa u plaintext. Tipični scenariji izloženosti:
- Velero backup S3 bucket sa slabim ACL-om
- etcd snapshot koji završi na pogrešnom S3 bucketu
- Kompromitovani etcd endpoint (defaultno nije TLS na starijim verzijama)

```bash
# Šta napadač uradi sa etcd pristupom:
etcdctl get /registry/secrets/production/db-credentials --print-value-only | base64 -d
# → username: admin, password: SuperSecret123
```

**kubectl audit log bypass:**  
Ako developer ima `get` na Deployments ali ne na Secrets, i dalje može pročitati env vars kroz:
```bash
kubectl describe pod go-service-7d9f8b-xxx
# Env section prikazuje sve env vars, uključujući one iz secretRef
```

**Memory dump / /proc exposure:**  
Env vars su vidljive u `/proc/<pid>/environ` svakom procesu koji ima pristup host-u. Container escape → čitanje tuđih env vars.

**Log injection:**  
Aplikacija logguje exception koji sadrži env vars (npr. PHP `var_dump($_ENV)` u error handler). Credentials završe u CloudWatch Logs, dostupni svima koji imaju `logs:GetLogEvents`.

---

## EKS Envelope Encryption — minimum što treba uključiti

Ako ipak koristite K8s Secrets (za neosjetljive podatke), **obavezno** uključiti envelope encryption na EKS:

```hcl
# terraform/modules/eks/main.tf
resource "aws_eks_cluster" "main" {
  # ...
  encryption_config {
    provider {
      key_arn = aws_kms_key.eks_secrets.arn
    }
    resources = ["secrets"]
  }
}
```

Ovo enkriptuje secrets u etcd koristeći KMS. Ali to rješava samo etcd exposure — ne rješava ostale vektore gore.

---

## AWS Secrets Manager vs SSM Parameter Store vs HashiCorp Vault

### Decision matrix za project-a stack

| Kriterij | Secrets Manager | SSM Param Store | Vault |
|---|---|---|---|
| Managed rotation | Da (Lambda rotators za RDS, Redshift, etc.) | Ne | Da (dynamic secrets) |
| Fine-grained IAM | Per-secret IAM | Per-parameter IAM | Policy-based |
| Cross-account access | Da (Resource policy) | Ograničeno | Da |
| Cost | $0.40/secret/month + $0.05/10k API calls | Free tier za Standard, $0.05/advanced | Self-hosted (ops overhead) ili Vault Cloud |
| Dynamic secrets | Ne | Ne | Da (DB credentials expire) |
| Audit trail | CloudTrail | CloudTrail | Vault audit device |
| K8s integration | External Secrets Operator | ESO ili SSM Agent | Vault Agent Injector |

### Kada koji za project-a:

**AWS Secrets Manager** — za naš stack, za:
- RDS master password (managed rotation postoji)
- Redis AUTH token
- Produkcijski API ključevi (third-party servisi)
- TLS sertifikati (ako ne koristite cert-manager)
- GitLab Registry credentials

**SSM Parameter Store** — za config, ne credentials:
- Feature flags (`/project-a/prod/features/new-checkout: true`)
- Non-sensitive konfiguracija (`/project-a/prod/app/log-level: INFO`)
- Hijerarhijska organizacija — SSM ima `GetParametersByPath`

**HashiCorp Vault** — ne u ovoj fazi, ali:
- Kada trebate dynamic secrets (kratkoživući DB credentials generisani po zahtjevu)
- Multi-cloud deployment
- Kompleksnije enterprise audit zahtjeve
- Tipično uvodi se kada compliance (SOC2, PCI-DSS Level 1) to eksplicitno zahtijeva

---

## Secret naming konvencija

Konzistentna konvencija je kritična za IAM politike zasnovane na ARN pattern matching.

```
/project-a/{environment}/{service}/{secret-name}
```

Primjeri za naš stack:

```
/project-a/dev/rds/master-password
/project-a/dev/rds/app-user-password
/project-a/dev/redis/auth-token
/project-a/dev/go-service/jwt-secret
/project-a/dev/php-service/session-secret
/project-a/dev/gitlab/registry-token

/project-a/staging/rds/master-password
/project-a/staging/rds/app-user-password
...

/project-a/prod/rds/master-password
/project-a/prod/rds/app-user-password
/project-a/prod/redis/auth-token
/project-a/prod/go-service/jwt-secret
/project-a/prod/php-service/session-secret
/project-a/prod/external-api/stripe-key
/project-a/prod/external-api/sendgrid-key
```

Zašto ova konvencija:

1. **IAM wildcard matching:** IRSA rola za go-service može imati policy `secretsmanager:GetSecretValue` na resource `arn:aws:secretsmanager:eu-west-1:123456789:secret:/project-a/prod/go-service/*` — automatski pokriva sve buduće go-service secrets bez promjene IAM politike.

2. **Environment isolation:** `secretsmanager:GetSecretValue` na `*/prod/*` eksplicitno deny za sve osim prod IRSA rola. Niko iz dev okruženja ne može pročitati prod secret.

3. **Audit clarity:** CloudTrail log koji kaže `GetSecretValue` na `/project-a/prod/rds/master-password` odmah je jasan bez dodatnog konteksta.

4. **Rotation grouping:** Možete rotirati sve `/project-a/prod/rds/*` secrets odjednom.

---

## Koji secrets idu u SM za project-a

**Definitivno u Secrets Manager:**

| Secret | Path | Rotation |
|---|---|---|
| RDS master password | `/project-a/{env}/rds/master-password` | AWS managed (Lambda) |
| RDS app user password | `/project-a/{env}/rds/app-user-password` | AWS managed (Lambda) |
| Redis AUTH token | `/project-a/{env}/redis/auth-token` | Manual (ElastiCache ograničenje) |
| JWT signing secret | `/project-a/{env}/go-service/jwt-secret` | Manual, 90-day policy |
| PHP session secret | `/project-a/{env}/php-service/session-secret` | Manual, 90-day policy |
| Stripe API key | `/project-a/{env}/external-api/stripe-key` | Manual (Stripe rotacija) |
| SendGrid API key | `/project-a/{env}/external-api/sendgrid-key` | Manual |

**U SSM Parameter Store (ne SM):**

```
/project-a/{env}/app/db-host           → RDS endpoint
/project-a/{env}/app/db-name           → Database name
/project-a/{env}/app/redis-host        → ElastiCache endpoint
/project-a/{env}/app/log-level         → INFO/DEBUG
/project-a/{env}/app/feature-flags/*   → Feature toggles
```

**Nikad u SM, SSM, ili bilo koji external store:**

- SSH private keys za deployment (koristiti OIDC/ephemeral credentials)
- AWS access keys za CI (koristiti OIDC → STS AssumeRoleWithWebIdentity)
- Kubeconfig sa admin credentials (koristiti OIDC ili scoped ServiceAccount token)

---

## Attack surface koji ostaje čak i sa SM

SM nije silver bullet. Preostali vektori:

1. **IMDS abuse (Instance Metadata Service):** Ako IMDS v1 je uključen i aplikacija ima SSRF ranjivost, napadač može dobiti EC2 instance credentials → čitati SM secrets. **Mitigation:** IMDSv2 obavezan (`http_tokens = "required"` u Terraform).

2. **Over-permissive IRSA:** Ako IRSA rola čita `*` umjesto specifičnih ARN-ova, kompromitovana aplikacija čita sve secrets. **Mitigation:** Eksplicitni ARN-ovi u IAM policy.

3. **SM API call logging gap:** `GetSecretValue` je logovan ali `DescribeSecret` (koji otkriva metadata) često nije monitoran. **Mitigation:** CloudTrail filter na sve SM API pozive.

4. **Rotation Lambda exposure:** Lambda funkcija koja vrši rotaciju mora imati pristup i SM i RDS. Ako je ta Lambda kompromitovana — game over. **Mitigation:** Lambda u VPC, SG koji dozvoljava samo RDS port, minimalni IAM.
