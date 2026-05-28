# GitLab Repo Struktura i CI/CD Setup

## Kreiranje GitLab projekta

Na GitLab UI:
1. New Project → Blank project
2. Project name: `project-a`
3. Visibility: Private
4. Deselektuj "Initialize repository with a README"

## Branch protection rules

Settings → Repository → Protected Branches:

| Branch | Merge | Push | Allowed to force push |
|--------|-------|------|----------------------|
| `main` | Maintainers | No one | No |

Settings → Merge Requests:
- Merge method: Merge commit
- Squash commits: Encourage
- Require pipeline to succeed before merge: ON
- Require a thread to be resolved before merge: ON
- Number of approvals: 1 (za tim projekat)

## GitLab Environments

Settings → CI/CD → Environments (kreira se automatski kad se pipeline pokrene,
ali možeš pre-konfigurisati):

**production environment:**
- Required approval rules: 1 approver
- Deployment branch: `main` only

Ovo znači da `deploy:prod` job neće moći startati bez manual approvala.

## CI/CD Variables

Settings → CI/CD → Variables. Dodaj sve prije nego pokušaš pokrenuti pipeline:

| Variable | Tip | Zaštićena | Masked | Opis |
|----------|-----|-----------|--------|------|
| `AWS_ROLE_ARN_DEV` | Variable | No | No | IAM OIDC role za dev |
| `AWS_ROLE_ARN_STAGING` | Variable | No | No | IAM OIDC role za staging |
| `AWS_ROLE_ARN_PROD` | Variable | Yes | No | IAM OIDC role za prod |
| `AWS_REGION` | Variable | No | No | `eu-west-1` |
| `TF_STATE_BUCKET` | Variable | No | No | `terraform-state-project-a` |
| `TF_STATE_DYNAMODB` | Variable | No | No | `terraform-locks` |
| `DOMAIN_DEV` | Variable | No | No | `dev.firma.com` |
| `DOMAIN_PROD` | Variable | No | No | `firma.com` |
| `GRAFANA_ADMIN_PASSWORD` | Variable | Yes | Yes | Grafana lozinka |
| `SLACK_WEBHOOK_URL` | Variable | Yes | Yes | Za AlertManager |

**Zaštićena (Protected)**: Vidljiva samo jobovima koji rade na protected branchu
(main) ili protected environmentu (production). Review apps na feature branchevima
NE vide ove varijable — koristit će `AWS_ROLE_ARN_DEV`.

**Masked**: Vrijednost se ne prikazuje u job logovima. Uvijek maskuj lozinke i tokene.

### Zašto nema `AWS_ACCESS_KEY_ID` i `AWS_SECRET_ACCESS_KEY`

Koristimo OIDC (OpenID Connect). GitLab CI/CD job dobija JWT token koji može
"redeemovati" za privremene AWS kredencijale. Prednosti:
- Nema dugoročnih secretsa koji mogu procuriti
- AWS credentials ističu automatski (1 sat)
- IAM role je scopovana na specifičan GitLab projekat i branch

## .gitlab-ci.yml Skeleton

```yaml
# .gitlab-ci.yml (skeleton — kompletna verzija u modulu 06)
include:
  - local: '.gitlab/ci/lint.yml'
  - local: '.gitlab/ci/build.yml'
  - local: '.gitlab/ci/terraform.yml'
  - local: '.gitlab/ci/deploy.yml'

variables:
  DOCKER_DRIVER: overlay2
  DOCKER_BUILDKIT: "1"
  IMAGE_TAG: $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA

stages:
  - lint
  - build
  - tf-plan
  - tf-apply
  - deploy
  - verify
  - destroy
```

Koristimo `include` da razdvojimo pipeline na logične fajlove. Sve u
`.gitlab/ci/` direktoriju:

```
.gitlab/
└── ci/
    ├── lint.yml
    ├── build.yml
    ├── terraform.yml
    └── deploy.yml
```

Ovo je posebno korisno sa AI: možeš poslati samo relevantan fajl umjesto cijelog
300-linijskog `.gitlab-ci.yml`.

## .gitignore

```gitignore
# Terraform
**/.terraform/
*.tfstate
*.tfstate.backup
*.tfplan
.terraform.lock.hcl

# Sertifikati (ne commituj private ključeve!)
*.key
*.pem
*.crt
!example.crt

# Docker
.docker/

# Editor
.idea/
.vscode/
*.swp

# OS
.DS_Store
Thumbs.db
```

**Kritično**: `.tfstate` se nikad ne commituje — sadrži produkcione secrets
(database passworde, generated keys). Uvijek koristiti remote state (S3).

## Merge Request template

Kreiraj `.gitlab/merge_request_templates/Default.md`:

```markdown
## Šta je promijenjeno

## Kako testirati

## Checklist
- [ ] Pipeline prošao
- [ ] Testirano na dev environmentu  
- [ ] Terraform plan priložen (ako ima infra promjena)
- [ ] Security implikacije razmotrene
```

## AI prompt za setup

```
Imam GitLab projekat project-a. Kreiram CI/CD setup.
AWS region: eu-west-1
Environments: local (kind), dev (EKS), staging (EKS), prod (EKS)
Auth metoda: AWS OIDC (ne access keys)
Registry: GitLab Container Registry

Napiši mi listu svih CI/CD Variables koje trebam postaviti,
sa objašnjenjem zašto svaka postoji i da li treba biti zaštićena/maskirena.
```
