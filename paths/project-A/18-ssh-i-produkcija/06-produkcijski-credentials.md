# 06 — Produkcijski Credentials: Dobijanje i Upravljanje

## Kubeconfig za Produkciju

### Korak 1: IAM Permission

Tvoja IAM rola mora imati `eks:DescribeCluster` da bi mogla generisati kubeconfig:

```json
{
  "Effect": "Allow",
  "Action": [
    "eks:DescribeCluster",
    "eks:ListClusters"
  ],
  "Resource": "arn:aws:eks:eu-west-1:123456789012:cluster/project-a-prod"
}
```

### Korak 2: Generisanje Kubeconfig-a

```bash
# Provjeri koji AWS profil koristiš
aws sts get-caller-identity

# Generiši kubeconfig za prod cluster
aws eks update-kubeconfig \
  --name project-a-prod \
  --region eu-west-1 \
  --alias prod

# Output: Added new context prod to ~/.kube/config
```

### Korak 3: Verifikacija Pristupa

```bash
# Provjeri koji context je aktivan
kubectl config current-context

# Što smijemo raditi?
kubectl auth can-i get pods -n project-a-prod
kubectl auth can-i update deployments -n project-a-prod
kubectl auth can-i delete secrets -n project-a-prod  # treba biti: no

# Prikaži sva dopuštenja u namespace-u
kubectl auth can-i --list -n project-a-prod
```

---

## Kubeconfig Sigurnost

### Token Expiry u EKS

EKS kubeconfig ne sadrži trajne kredencijale — sadrži komandu koja generira kratkotrajan token:

```yaml
# Iz ~/.kube/config (EKS sekcija)
users:
- name: prod
  user:
    exec:
      apiVersion: client.authentication.k8s.io/v1beta1
      command: aws
      args:
      - eks
      - get-token
      - --cluster-name
      - project-a-prod
```

Svaki `kubectl` poziv osvježava token putem `aws eks get-token`. Token vrijedi 15 minuta. Nema trajnih tokena koji mogu biti ukradeni iz kubeconfig fajla.

**Implication:** ako AWS session ističe (STS token), kubectl komande počinju failovati sa `Unauthorized`. Refresh:
```bash
aws sso login  # za AWS SSO setup
# ili
aws configure  # za novo access key/secret
```

### Dijeljenje Kubeconfig-a: Ne

Svaka osoba ima svoju IAM rolu → vlastiti kubeconfig. Dijeljenjem kubeconfig-a:
- Gubite individualni audit trail (CloudTrail vidi "ko je radio šta")
- Jedna osoba ima pristup tuđeg identiteta

Ako kolega treba pristup, dodaje se u odgovarajuću IAM grupu, ne šalje mu se tvoj kubeconfig.

### Zaštita na Disku

```bash
# Provjeri dozvole
ls -la ~/.kube/config
# Mora biti -rw------- (600) ili stroži

# Postavi ispravne dozvole
chmod 600 ~/.kube/config
chmod 700 ~/.kube/
```

### Git Zaštita

`.gitignore` u svakom projektu:
```
# Ne smije u git
.kube/
kubeconfig
kubeconfig-*
*.kubeconfig
```

Provjeri da nije commitovano:
```bash
git log --all --full-history -- '**kubeconfig*' '**/.kube/**'
# Prazno = dobro
```

---

## AWS Konzolni Pristup za Prod

### Izolacija Prod Accounta

Preporučena arhitektura: produkcija je u zasebnom AWS accountu (ne isti account kao dev). Ovo je standard za ozbiljan produkcijski setup:

```
AWS Organization
├── dev account (123456789000)     — slobodan pristup
├── staging account (123456789001) — ograničen pristup
└── prod account (123456789002)    — MFA obavezno, audit sve
```

### MFA za Prod

MFA (Multi-Factor Authentication) je obavezan za sve akcije u prod accountu. Konfiguracija u IAM politici:

```json
{
  "Effect": "Deny",
  "Action": "*",
  "Resource": "*",
  "Condition": {
    "BoolIfExists": {
      "aws:MultiFactorAuthPresent": "false"
    }
  }
}
```

Ova politika blokira sve akcije ako MFA nije aktiviran u sesiji.

### AWS SSO (Identity Center) za Timove

Za timove preporučujem AWS SSO (Identity Center) umjesto individualnih IAM usera:

```bash
# Konfiguracija SSO profila
aws configure sso
# Prati wizard: SSO start URL, region, account ID, permission set

# Login
aws sso login --profile prod-readonly

# Provjeri identitet
aws sts get-caller-identity --profile prod-readonly
```

SSO sesija ističe automatski (obično 1-8 sati, po policy-ju tvoje organizacije).

### Cross-Account Pristup (assume-role)

Ako imaš pristup prod accountu kroz role assumption:

```bash
# Preuzmi produkcijsku rolu (privremeno, 1 sat)
aws sts assume-role \
  --role-arn arn:aws:iam::123456789002:role/ProdReadOnly \
  --role-session-name "darko-debug-$(date +%Y%m%d)" \
  --duration-seconds 3600

# Kreiraj profil sa privremenim credentials
# (output sadrži AccessKeyId, SecretAccessKey, SessionToken)
export AWS_ACCESS_KEY_ID=<from-output>
export AWS_SECRET_ACCESS_KEY=<from-output>
export AWS_SESSION_TOKEN=<from-output>

# Provjeri
aws sts get-caller-identity
```

---

## Pristup RDS Produkciji (Read-Only Debug)

### Metoda 1: SSM Port-Forward (preporučeno)

Bez otvaranja security group-a, bez bastion hosta:

```bash
# Terminal 1: Otvori tunnel
aws ssm start-session \
  --target i-1234567890abcdef0 \
  --document-name AWS-StartPortForwardingSessionToRemoteHost \
  --parameters '{
    "host": ["prod-rds.cluster.eu-west-1.rds.amazonaws.com"],
    "portNumber": ["3306"],
    "localPortNumber": ["13306"]
  }'

# Terminal 2: Spoji se (ČUVAJ ŠTA PIŠEŠ)
mysql -h 127.0.0.1 -P 13306 -u readonly_user -p
```

### Metoda 2: Credentials iz Secrets Manager

```bash
# Dohvati DB credentials iz Secrets Manager
aws secretsmanager get-secret-value \
  --secret-id /project-a/prod/db-credentials \
  --region eu-west-1 \
  --query SecretString \
  --output text | jq .

# Ili specifično polje
aws secretsmanager get-secret-value \
  --secret-id /project-a/prod/db-credentials \
  --query 'SecretString' \
  --output text | jq -r '.password'
```

**Sigurnost:** ne čuvaj output u terminalu historiji. Koristiti:
```bash
# Postavi kao varijablu (neće se pojaviti u history-u ako počinješ sa space)
 DB_PASS=$(aws secretsmanager get-secret-value \
  --secret-id /project-a/prod/db-credentials \
  --query 'SecretString' --output text | jq -r '.password')
```

### Pravila za Prod DB Pristup

**Obavezno:**
- Koristiti read-only korisnika (`readonly_user`), nikad `root` ili aplikativnog usera
- Svaki query počinje sa `SELECT` — nikad DDL ili DML u produkciji
- Ako moraš raditi izmjene (iznimna situacija), uvijek u transakciji sa `BEGIN; ... ROLLBACK;` najprije (da vidiš efekt bez commita)

```sql
-- Sigurno testiranje izmjene (ROLLBACK na kraju)
BEGIN;
UPDATE users SET status = 'inactive' WHERE last_login < '2024-01-01';
SELECT ROW_COUNT();  -- Provjeri broj redova
ROLLBACK;  -- NE COMMIT dok nisi siguran
```

---

## Rotacija Credentials

### Kada Rotirati

- **Odmah:** sumnja da je credential kompromitovan, nestao laptop, bivši zaposleni imao pristup
- **Redovno:** IAM access key svaka 90 dana (best practice), DB password svaka 6-12 mjeseci
- **Automatski:** koristiti AWS Secrets Manager automatic rotation (rotira DB password i ažurira Secrets Manager, bez downtime-a)

### Rotacija Vlastitog IAM Access Key-a

```bash
# 1. Kreiraj novi access key
aws iam create-access-key --user-name darko.nikolic

# 2. Ažuriraj ~/.aws/credentials sa novim key-em
# Testiraj da novi key radi:
AWS_ACCESS_KEY_ID=<new-key> AWS_SECRET_ACCESS_KEY=<new-secret> \
  aws sts get-caller-identity

# 3. Deaktiviraj stari key
aws iam update-access-key \
  --access-key-id <old-key-id> \
  --status Inactive \
  --user-name darko.nikolic

# 4. Nakon što stvrdneš da sve radi sa novim key-em: obriši stari
aws iam delete-access-key \
  --access-key-id <old-key-id> \
  --user-name darko.nikolic
```

Uvijek je korak: kreiraj novi → testiraj → deaktiviraj stari → obriši stari. Nikad direktno briši aktivni key.

### Hitna Rotacija (Kompromitovan Credential)

```bash
# 1. Odmah deaktiviraj sve access key-eve za korisnika
aws iam list-access-keys --user-name darko.nikolic
aws iam update-access-key --access-key-id <key-id> --status Inactive --user-name darko.nikolic

# 2. Provjeri recent aktivnost u CloudTrail
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=Username,AttributeValue=darko.nikolic \
  --start-time "2024-01-13T00:00:00Z" \
  --max-results 50

# 3. Revoke aktivne sesije (forsiraj re-autentifikaciju)
aws iam delete-user-policy --user-name darko.nikolic --policy-name AllowAll
# ili: IAM → Users → Security credentials → Sign-out all active sessions

# 4. Inform security tim
```

---

## Credential Inventory

Drži popis svih produkcijskih credentiala:

| Tip | Gdje se čuva | Pristup | Rotacija |
|-----|-------------|---------|----------|
| IAM Access Key | `~/.aws/credentials` | Individualan | 90 dana |
| SSH Private Key | `~/.ssh/project-a-prod.pem` | Individualan | 6 mj ili keypair rotation |
| RDS Password | AWS Secrets Manager | ServiceAccount | Auto (30 dana) |
| Redis auth token | AWS Secrets Manager | ServiceAccount | 90 dana |
| Kubeconfig | `~/.kube/config` | Individualan | Refresh po STS token |
| GitLab token | `~/.netrc` ili env | Individualan | 6 mj |
