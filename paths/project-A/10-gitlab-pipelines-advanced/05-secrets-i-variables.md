# 05 — Secrets i variables

## Teorija

Secrets su najčešći izvor sigurnosnih incidenata u CI/CD. Jedan exposed AWS key u
GitHub/GitLab logu = kompromitovana infrastruktura. Pravilno upravljanje secretima
nije opcija — to je osnova.

---

## Zašto nikad secrets direktno u .gitlab-ci.yml

```yaml
# POGREŠNO — nikad ovako
script:
  - AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE terraform apply
  - kubectl --token=eyJhbGci... get pods
```

`.gitlab-ci.yml` je u repou. Svako ko ima pristup repou — ili ikad bude imao — vidi key.
Git historija pamti sve. Čak i ako odmah obrišeš commit, key je bio izložen.

---

## GitLab CI/CD Variables: tipovi

**Settings → CI/CD → Variables**

| Tip | Opis | Primjena |
|-----|------|----------|
| Variable | Obični string | URL-ovi, nazivi bucketa |
| File | Sadržaj se upisuje u temp fajl | kubeconfig, SSL certifikati |
| Masked | Vrijednost se ne prikazuje u logovima | passwords, tokens |
| Protected | Dostupna samo u protected branches/tags | prod credentials |

Kombinuješ ih: production kubeconfig je `File + Protected + Masked`.

---

## Scoping: project, group, environment

**Project scope** — varijabla je dostupna samo u jednom projektu.

**Group scope** — varijabla je dostupna svim projektima u GitLab grupi.
Korisno za dijeljene credentials (npr. Slack webhook URL koji koriste svi projekti).

**Environment scope** — varijabla se koristi samo kad job deploya u specifični environment:

```
KUBE_CONFIG   →  dev     →  base64 kubeconfig za dev EKS cluster
KUBE_CONFIG   →  staging →  base64 kubeconfig za staging EKS cluster
KUBE_CONFIG   →  prod    →  base64 kubeconfig za prod EKS cluster
```

Isti naziv `KUBE_CONFIG`, GitLab automatski ubrizgava pravu vrijednost na osnovu
`environment: name:` u job definiciji.

---

## AWS credentials: OIDC (preporučeno)

Pogledaj `03-terraform-u-pipeline.md` za detaljan OIDC setup.

Za varijable: postavi samo `AWS_ROLE_ARN` kao GitLab varijablu, scoped po environmentu:

```
DEV_AWS_ROLE_ARN     →  arn:aws:iam::111111111111:role/GitLabCI-Dev
STAGING_AWS_ROLE_ARN →  arn:aws:iam::222222222222:role/GitLabCI-Staging
PROD_AWS_ROLE_ARN    →  arn:aws:iam::333333333333:role/GitLabCI-Prod
```

Nikad `AWS_ACCESS_KEY_ID` i `AWS_SECRET_ACCESS_KEY` ako možeš izbjeći.

---

## Kubeconfig: File type variable

```bash
# Encode kubeconfig za dev cluster
cat dev-kubeconfig.yaml | base64 -w 0
```

U GitLab:
```
Key:   KUBE_CONFIG_DEV
Type:  Variable
Value: <base64 output>
Mask:  yes
Protect: yes (samo za protected branches)
Environment scope: dev
```

U `.gitlab-ci.yml`:

```yaml
before_script:
  - mkdir -p ~/.kube
  - echo "$KUBE_CONFIG_DEV" | base64 -d > ~/.kube/config
  - chmod 600 ~/.kube/config
```

Zašto base64? Kubeconfig je multi-line YAML. GitLab masked variables ne podržavaju
multi-line vrijednosti direktno. Base64 ga pretvara u jedan string.

---

## Registry credentials: automatski dostupni

GitLab automatski eksponira credentials za vlastiti Container Registry:

```
$CI_REGISTRY           →  registry.gitlab.com
$CI_REGISTRY_USER      →  gitlab-ci-token
$CI_REGISTRY_PASSWORD  →  automatski generirani job token
$CI_REGISTRY_IMAGE     →  registry.gitlab.com/group/project
```

```yaml
build:
  script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA
```

Nema manuelnog postavljanja registry credentials u GitLab Variables.

---

## Secrets u K8s: Terraform kreira Secret iz GitLab variable

Aplikacija u K8s koja treba secret (npr. database password) ne čita ga iz environment
varijable pipeline-a. Terraform kreira K8s Secret iz vrijednosti koja je u GitLab varijabli:

```hcl
resource "kubernetes_secret" "db_password" {
  metadata {
    name      = "helloworld-secrets"
    namespace = "helloworld-dev"
  }
  data = {
    DB_PASSWORD = var.db_password
  }
}
```

Varijabla `var.db_password` dolazi iz Terraform varijable, koja se postavlja u pipeline-u:

```yaml
script:
  - terraform apply -var="db_password=$DB_PASSWORD_DEV" -auto-approve
```

`DB_PASSWORD_DEV` je GitLab varijabla, masked, protected, scoped za dev environment.

---

## Checklista za secrets management u project-A

- [ ] Nikakvi secrets u `.gitlab-ci.yml`
- [ ] AWS: OIDC umjesto access keys
- [ ] Kubeconfig: File/Variable, base64, masked, protected
- [ ] Registry: koristi automatske `$CI_REGISTRY_*` varijable
- [ ] Aplikacijski secrets: Terraform kreira K8s Secrets iz GitLab variables
- [ ] Production varijable: protected scope, dostupne samo na `main` i tagovima
- [ ] Rotacija: dokumentiraj kada i kako rotirati svaki secret

---

## AI workflow

Tražiti Claude da napravi rotacijski plan za secrets:

> "Imam sljedeće secrets u GitLab CI/CD: AWS OIDC role ARN, kubeconfig za 3 clustera,
> Slack webhook, database password. Napravi rotacijski plan — koliko često rotirati svaki,
> koji je rizik ako ga ne rotiraš, i kako procedure izgledaju za svaki tip."

---

## Veza sa project-A

Za project-A minimalni set varijabli u GitLab:

```
KUBE_CONFIG_DEV      →  Variable, masked, protected, scope: dev
KUBE_CONFIG_STAGING  →  Variable, masked, protected, scope: staging
KUBE_CONFIG_PROD     →  Variable, masked, protected, scope: prod
DEV_AWS_ROLE_ARN     →  Variable, scope: dev
STAGING_AWS_ROLE_ARN →  Variable, scope: staging
PROD_AWS_ROLE_ARN    →  Variable, scope: prod
SLACK_WEBHOOK_URL    →  Variable, masked (group level — dijeli sa svim projektima)
```

Svaka varijabla ima jasnu svrhu, scope i nivo zaštite.
