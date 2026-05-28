# IAM i bezbjednost u AWS-u

## Šta je IAM

Identity and Access Management je AWS-ov sistem za kontrolu pristupa. Svaka radnja u AWS-u — kreiranje EC2, čitanje S3, update EKS — zahtijeva eksplicitnu dozvolu. Po defaultu: sve je zabranjeno.

IAM entiteti:
- **User**: ljudski korisnik sa trajnim kredencijalima (izbjegavati za automatizaciju)
- **Role**: privremeni identitet koji preuzima servis ili korisnik
- **Policy**: JSON dokument koji definira šta je dozvoljeno/zabranjeno
- **Group**: kolekcija korisnika sa zajedničkim politikama

Za project-A: nema IAM usera za CI/CD. Sve ide kroz role.

## Least privilege princip

Svaki servis dobija tačno onoliko prava koliko treba — ništa više. Primjer:

**Loše**: GitLab CI/CD ima `AdministratorAccess` politiku
**Dobro**: GitLab CI/CD može samo `eks:UpdateNodegroupConfig`, `ecr:PutImage`, `s3:PutObject` na specifičnom bucketu

Praktična implementacija: počni sa minimalnim pravima, dodaj kada nešto ne radi, ne dodaj wildcard da "prođe".

## OIDC integracija GitLab → AWS

Ovo je ključno za project-A. Tradicionalni pristup (loš):
```
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=abc123...
```
Ovi se unose u GitLab CI/CD Variables. Problem: trajni kredencijali koji nikad ne ističu, mogu biti ukradeni iz loga, teški za rotaciju.

### Kako OIDC funkcioniše

GitLab je OIDC provider — izdaje JWT tokene za svaki pipeline job. AWS verifikuje token direktno sa GitLabom.

```
GitLab Job staruje
    ↓
GitLab izdaje JWT token (sa claims: project, branch, env)
    ↓
CI/CD skript: aws sts assume-role-with-web-identity
    ↓
AWS STS provjeri token sa GitLab JWKS endpoint-om
    ↓
AWS vraća privremene credentials (15min - 12h)
    ↓
Job koristi credentials, ističu kada job završi
```

AWS Terraform konfiguracija za OIDC:
```hcl
resource "aws_iam_openid_connect_provider" "gitlab" {
  url             = "https://gitlab.com"
  client_id_list  = ["https://gitlab.com"]
  thumbprint_list = ["<gitlab-tls-thumbprint>"]
}

resource "aws_iam_role" "gitlab_ci" {
  name = "gitlab-ci-project-a"
  assume_role_policy = jsonencode({
    Statement = [{
      Action = "sts:AssumeRoleWithWebIdentity"
      Principal = {
        Federated = aws_iam_openid_connect_provider.gitlab.arn
      }
      Condition = {
        StringLike = {
          "gitlab.com:sub" = "project_path:user/project-a:ref_type:branch:ref:*"
        }
      }
    }]
  })
}
```

Condition ograničava: samo pipeline-i iz `user/project-a` repozitorija mogu preuzeti ovu rolu. Granularnija kontrola: samo `main` branch, ili samo `production` environment.

## IRSA: Pod-level AWS pristup

IAM Roles for Service Accounts (IRSA) — isti princip unutar EKS-a. Kubernetes Pod koji treba pristupiti AWS-u (npr. ALB Controller koji kreira load balancere) dobija IAM rolu kroz ServiceAccount anotaciju.

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: aws-load-balancer-controller
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::123456789:role/alb-controller-role
```

Bez IRSA: Pod bi morao koristiti node-ove IAM rolu (previše privilegija) ili staticke kredencijale (opasno).

## Terraform IAM moduli za project-A

Svaka rola je eksplicitno definisana po environmentu:

```
iam/
├── gitlab-ci-role.tf      ← OIDC role za pipeline
├── eks-node-role.tf       ← Worker node role
├── alb-controller-role.tf ← IRSA za ALB controller
└── autoscaler-role.tf     ← IRSA za cluster autoscaler
```

Svaki environment (dev/staging/prod) ima vlastitu GitLab CI rolu sa različitim pravima — prod rola zahtijeva manual approval u pipeline-u.
