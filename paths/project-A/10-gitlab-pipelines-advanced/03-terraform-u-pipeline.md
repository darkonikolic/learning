# 03 — Terraform u pipeline-u

## Teorija

Terraform u CI/CD pipeline-u znači da **infrastruktura prolazi isti review process kao kod**.
Niko ne radi `terraform apply` lokalno na produkciji. Svaka promjena ide kroz MR,
plan je vidljiv, apply je auditovan.

---

## Zašto Terraform kroz pipeline, ne lokalno

Lokalni `terraform apply` na produkciji ima kritične probleme:

- Ko je to uradio? Kada? Nema loga.
- State file može biti zastario — netko drugi je mijenjao infrastrukturu.
- Nema review-a plana — grješku vidiš tek kad je šteta napravljena.
- Credentials su na lokalnoj mašini — sigurnosni rizik.

Pipeline rješava sve ovo: svaki apply je commit, svaki plan je reviewovan, credentials
su u GitLab-u (ne na laptopima), state je zaključan tokom apply-a.

---

## Terraform workflow u CI

### Na svakom MR: plan kao komentar

```yaml
terraform:plan:
  stage: tf-plan
  image:
    name: hashicorp/terraform:1.7
    entrypoint: [""]
  script:
    - terraform init -backend-config="bucket=$TF_STATE_BUCKET"
    - terraform plan -out=tfplan -no-color 2>&1 | tee plan.txt
    - |
      # Postavi plan output kao MR komentar
      PLAN=$(cat plan.txt)
      curl --request POST \
        --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
        --data "body=\`\`\`\n${PLAN}\n\`\`\`" \
        "$CI_API_V4_URL/projects/$CI_PROJECT_ID/merge_requests/$CI_MERGE_REQUEST_IID/notes"
  artifacts:
    paths:
      - tfplan
    expire_in: 1 day
  rules:
    - if: $CI_MERGE_REQUEST_IID
```

Plan output kao MR komentar znači: reviewer vidi točno šta će se promijeniti u AWS-u
**bez ulaska u CI log**. Ovo je ključno za efikasan review.

### Na merge u main: apply

```yaml
terraform:apply:
  stage: tf-apply
  image:
    name: hashicorp/terraform:1.7
    entrypoint: [""]
  script:
    - terraform init -backend-config="bucket=$TF_STATE_BUCKET"
    - terraform apply -auto-approve
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
```

### Manuelni destroy job

```yaml
terraform:destroy:dev:
  stage: destroy
  image:
    name: hashicorp/terraform:1.7
    entrypoint: [""]
  when: manual
  script:
    - terraform init -backend-config="bucket=$TF_STATE_BUCKET"
    - terraform destroy -auto-approve
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
```

---

## GitLab predefinisani Terraform templates

GitLab nudi gotove template-e koje možeš uključiti:

```yaml
include:
  - template: Terraform/Base.gitlab-ci.yml

variables:
  TF_ROOT: ${CI_PROJECT_DIR}/terraform
  TF_STATE_NAME: default
```

Template automatski kreira `validate`, `plan`, `apply`, `destroy` jobove.
Korisno za početak, ali za project-A pišemo vlastite da razumijemo šta se dešava.

---

## AWS autentifikacija: OIDC (ne access keys)

**Nikad ne stavljaj AWS access keys u GitLab varijable** kao `AWS_ACCESS_KEY_ID`.
Ključevi mogu curiti, ne rotiraju se automatski, vezani su za korisnika.

OIDC (OpenID Connect) znači: **GitLab se autentifikuje u AWS bez secrets**.
GitLab dobija token koji AWS direktno verifikuje.

```yaml
variables:
  AWS_ROLE_ARN: $DEV_AWS_ROLE_ARN

id_tokens:
  AWS_OIDC_TOKEN:
    aud: https://gitlab.com

before_script:
  - >
    export $(printf "AWS_ACCESS_KEY_ID=%s AWS_SECRET_ACCESS_KEY=%s AWS_SESSION_TOKEN=%s"
    $(aws sts assume-role-with-web-identity
    --role-arn $AWS_ROLE_ARN
    --role-session-name "GitLabCI-$CI_JOB_ID"
    --web-identity-token $AWS_OIDC_TOKEN
    --duration-seconds 3600
    --query 'Credentials.[AccessKeyId,SecretAccessKey,SessionToken]'
    --output text))
```

U AWS-u: IAM Role s trust policy koji dopušta `gitlab.com` OIDC provider-u da assume-a ulogu.
Svaki environment (dev/staging/prod) ima vlastitu IAM rolu s minimalnim permisijama.

---

## State lock u CI: šta ako pipeline padne usred apply-a

Terraform koristi **state lock** — dok `apply` radi, drugi procesi ne mogu mijenjati state.
Ako pipeline padne (timeout, runner crash), lock ostaje.

Rješenje:
1. `terraform force-unlock LOCK_ID` — manuelni job u pipeline-u
2. Ili direktno u S3/DynamoDB gdje je state pohranjen

Za project-A: S3 bucket za state + DynamoDB za locking (Terraform preporučeni setup):

```hcl
terraform {
  backend "s3" {
    bucket         = "project-a-tf-state"
    key            = "dev/terraform.tfstate"
    region         = "eu-central-1"
    dynamodb_table = "project-a-tf-locks"
    encrypt        = true
  }
}
```

---

## Kompletan terraform stage u .gitlab-ci.yml

```yaml
.terraform_base:
  image:
    name: hashicorp/terraform:1.7
    entrypoint: [""]
  before_script:
    - cd $TF_DIR
    - terraform init -backend-config="bucket=$TF_STATE_BUCKET"
                     -backend-config="key=$TF_STATE_KEY"

terraform:validate:
  extends: .terraform_base
  stage: tf-plan
  script:
    - terraform validate
  rules:
    - if: $CI_MERGE_REQUEST_IID
    - if: $CI_COMMIT_BRANCH == "main"

terraform:plan:dev:
  extends: .terraform_base
  stage: tf-plan
  variables:
    TF_DIR: terraform/environments/dev
    TF_STATE_KEY: dev/terraform.tfstate
    AWS_ROLE_ARN: $DEV_AWS_ROLE_ARN
  script:
    - terraform plan -no-color | tee plan.txt
  artifacts:
    paths: [plan.txt]
    expire_in: 1 day

terraform:apply:dev:
  extends: .terraform_base
  stage: tf-apply
  variables:
    TF_DIR: terraform/environments/dev
    TF_STATE_KEY: dev/terraform.tfstate
    AWS_ROLE_ARN: $DEV_AWS_ROLE_ARN
  script:
    - terraform apply -auto-approve
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
```

---

## Veza sa project-A

Infrastruktura za project-A (EKS cluster, VPC, RDS ako dodaš, Route53 records) —
sve kreira i briše Terraform kroz pipeline. Niko nema `terraform apply` na laptopu.
Svaka infra promjena je commit, reviewovana, auditovana.
