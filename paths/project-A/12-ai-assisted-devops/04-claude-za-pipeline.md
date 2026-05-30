# Claude za GitLab Pipeline

## CLAUDE.md kontekst za pipeline rad

Dodaj u `CLAUDE.md` da Claude generiše pipeline koji odgovara tvom setup-u:

```markdown
## GitLab CI validation checklist
- Svaki job ima stage, rules: (ne only/except), i jasne needs:.
- Path-based rules: changes: da se ne build-uje sve pri svakom commitu.
- Bez plaintext secrets — koristi CI/CD variables (masked, protected).
- interruptible: true za feature grane.
- AWS auth: OIDC (CI_JOB_JWT_V2) — ne access key/secret u variables.
- Docker push: CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA format.
- Helm deploy: --wait --timeout 5m minimum.
```

## Generisanje kompleksnog .gitlab-ci.yml

Pipeline je jedan od najkompleksnijih fajlova u projektu — ima mnogo opcija,
sintaksa je specifična za GitLab, i greške u njemu su skupe (čekaš 10 minuta
da saznaš da imaš typo u YAML-u).

### Kompletan pipeline od nule

```
Napiši .gitlab-ci.yml koji radi sljedeće:
1. Build Docker image i push u GitLab Container Registry
   - Tag: $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA
   - Trivy scan image, failuj na HIGH/CRITICAL vulnerabilnosti
2. Helm deploy na EKS za main branch (dev environment)
   - AWS OIDC auth (ne access key/secret)
   - helm upgrade --install --wait --timeout 5m
3. Review app za svaki MR
   - Deploy na namespace mr-$CI_MERGE_REQUEST_IID
   - URL: https://mr-$CI_MERGE_REQUEST_IID.dev.firma.com
   - on_stop: destroy review app kada se MR zatvori
4. Manual deploy na prod (protected environment, zahtjeva approval)

Koristim: GitLab 16.x, AWS EKS 1.29, Helm 3, Terraform 1.7
Objasni svaki job.
```

### Analiza sporog pipeline-a

```
Ovaj pipeline traje 18 minuta. Evo lista jobova i trajanja:
- lint: 2m
- docker-build: 8m
- helm-lint: 1m
- tf-plan: 4m
- deploy-dev: 3m

Identifikuj bottlenecke i predloži optimizacije za:
1. Paralelizaciju jobova koji ne zavise jedni o drugima
2. Docker build optimizaciju (layer caching, multi-stage)
3. Terraform koji ne treba da radi na svakom push-u
```

Tipične Claude preporuke: docker build cache sa `--cache-from`, paralelni lint
jobovi, `tf-plan` samo na MR, `needs` keyword za preskakanje čekanja.

### Terraform plan kao MR komentar

```
Napiši GitLab CI job koji:
1. Radi terraform plan
2. Sprema plan u artifact
3. Komentariše plan output na MR-u koristeći GitLab API
   (GITLAB_TOKEN je CI/CD variable)

Format komentara treba biti Markdown sa kodom u code bloku.
Ažuriraj komentar ako već postoji (ne kreiraj novi svaki put).
```

## AWS OIDC Setup sa AI

Umjesto AWS access key/secret u CI/CD variables (sigurnosni rizik), koristi OIDC.

### Terraform za OIDC IAM role

```
Napiši Terraform koji kreira IAM role za GitLab CI/CD sa OIDC:
- GitLab instanca: gitlab.com
- Projekt: moj-user/project-a (namespace iz CI_PROJECT_PATH)
- Role dozvoljavaju: assume role samo iz main brancha i MR jobova
- Minimalne permisije za:
  * EKS: eks:DescribeCluster (za kubeconfig update)
  * ECR/GitLab registry auth: nije potrebno za GitLab registry
  * Helm deploy: Kubernetes API calls (via kubeconfig, ne IAM direktno)
  * Terraform state: S3 get/put/delete na bucket terraform-state-project-a

Objasni OIDC trust policy condition blok.
```

### Pipeline job koji koristi OIDC

```yaml
# Claude generiše ovaj pattern:
.aws-auth: &aws-auth
  before_script:
    - >
      export $(printf "AWS_ACCESS_KEY_ID=%s AWS_SECRET_ACCESS_KEY=%s AWS_SESSION_TOKEN=%s"
      $(aws sts assume-role-with-web-identity
      --role-arn $AWS_ROLE_ARN
      --role-session-name "gitlab-ci-$CI_PIPELINE_ID"
      --web-identity-token $CI_JOB_JWT_V2
      --duration-seconds 3600
      --query 'Credentials.[AccessKeyId,SecretAccessKey,SessionToken]'
      --output text))
```

## Pipeline Debugging sa AI

Kada job failuje, copy-paste cijeli job log. Nemoj skraćivati — Claude treba
cijeli kontekst da identificira pravi problem.

**Primjer 1 — Docker push failuje**
```
Ovaj GitLab CI job failuje:
[prijepi cijeli job log]

Job radi docker push u GitLab Container Registry.
Variables koje imam postavljene: CI_REGISTRY_USER, CI_REGISTRY_PASSWORD
```

Claude tipično identificuje: `docker login` nije pozvan prije `docker push`,
ili `CI_REGISTRY_PASSWORD` je `$CI_JOB_TOKEN` (ispravno) a ne Personal Access Token.

**Primjer 2 — Helm deploy na EKS ne radi**
```
helm upgrade failuje sa:
Error: INSTALLATION FAILED: Kubernetes cluster unreachable:
Get "https://ABC123.gr7.eu-west-1.eks.amazonaws.com/version": dial tcp: i/o timeout

AWS OIDC auth prošao (vidim AssumeRoleWithWebIdentity success u lozima).
Kubeconfig sam generisao sa: aws eks update-kubeconfig --name project-a-dev

Šta može biti uzrok?
```

Claude: EKS private endpoint + VPC + GitLab runner koji nije u istom VPC-u.
Rješenja: (1) public endpoint za EKS sa IP whitelistom, (2) GitLab runner unutar VPC-a.

## Primjer: kompletan pipeline refiniran sa AI

**Iteracija 1** — Claude generiše osnovni pipeline (80 linija)

**Iteracija 2** — Ti pokreneš, failuje na docker build:
```
Prijepi failed job log, pitaj: "docker build failuje ovako: [log]
Dockerfile je: [prijepi]. Šta nije u redu?"
```

**Iteracija 3** — Docker build prošao, helm deploy ne radi:
```
"Helm deploy failuje: [log]. EKS cluster je private. 
AWS role je: [arn]. Kubeconfig generisanje radi lokalno."
```

**Iteracija 4** — Sve radi, pitaj za optimizaciju:
```
"Pipeline radi. Trajanje je 12 minuta. 
Evo .gitlab-ci.yml: [prijepi].
Kako da optimizujem na ispod 8 minuta?"
```

**Iteracija 5** — Security review:
```
"Finalni .gitlab-ci.yml: [prijepi].
Pregledaj sa sigurnosnog aspekta — posebno IAM permisije,
secreti u logovima, i šta se dešava ako Trivy scan pukne."
```

## Veza sa project-A

Pipeline koji gradiš u modulu 11 proći će tačno ove iteracije.
Svaki od gornjih prompta možeš koristiti direktno sa tvojim kodom.

Ključne CI/CD variables za project-A koje AI treba znati o kontekstu:
- `AWS_ROLE_ARN_DEV` / `AWS_ROLE_ARN_PROD` — OIDC roleovi
- `CI_REGISTRY_IMAGE` — automatski GitLab variable
- `CI_MERGE_REQUEST_IID` — broj MR-a za review apps
- `TF_STATE_BUCKET` — S3 bucket za state
- `KUBE_NAMESPACE` — target namespace per environment
