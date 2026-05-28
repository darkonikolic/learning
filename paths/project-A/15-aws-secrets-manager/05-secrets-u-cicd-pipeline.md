# 05 — Secrets u CI/CD pipeline

## GitLab CI: OIDC umjesto dugoročnih access keys

Dugoročni AWS access keys u GitLab CI su najčešći izvor security incidenta u cloud projektima. Kada GitLab CI job završi, access key ostaje validan — potencijalno godinama.

OIDC eliminiše ovaj problem: GitLab generiše kratkoživući JWT token za svaki job, koji se zamjenjuje za privremene AWS STS credentials.

### AWS konfiguracija — OIDC Provider

```hcl
# terraform/modules/gitlab-ci/oidc.tf

resource "aws_iam_openid_connect_provider" "gitlab" {
  url = "https://gitlab.example.com"

  client_id_list = ["sts.amazonaws.com"]

  thumbprint_list = [
    data.tls_certificate.gitlab.certificates[0].sha1_fingerprint
  ]
}

data "tls_certificate" "gitlab" {
  url = "https://gitlab.example.com"
}

# CI rola za deploy na EKS
resource "aws_iam_role" "gitlab_ci_deploy" {
  name = "project-a-gitlab-ci-deploy"

  assume_role_policy = data.aws_iam_policy_document.gitlab_ci_assume.json
}

data "aws_iam_policy_document" "gitlab_ci_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.gitlab.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "gitlab.example.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    # Ograničiti na specifični GitLab project i environment
    condition {
      test     = "StringLike"
      variable = "gitlab.example.com:sub"
      # Samo main branch i samo za project-a
      values   = ["project_path:your-group/project-a:ref_type:branch:ref:main"]
    }
  }
}

data "aws_iam_policy_document" "gitlab_ci_deploy_policy" {
  # ECR push
  statement {
    effect = "Allow"
    actions = [
      "ecr:GetAuthorizationToken",
      "ecr:BatchCheckLayerAvailability",
      "ecr:GetDownloadUrlForLayer",
      "ecr:BatchGetImage",
      "ecr:InitiateLayerUpload",
      "ecr:UploadLayerPart",
      "ecr:CompleteLayerUpload",
      "ecr:PutImage",
    ]
    resources = [
      "arn:aws:ecr:${var.aws_region}:${data.aws_caller_identity.current.account_id}:repository/project-a/*"
    ]
  }

  # EKS describe za kubeconfig
  statement {
    effect    = "Allow"
    actions   = ["eks:DescribeCluster"]
    resources = [aws_eks_cluster.main.arn]
  }

  # S3 za Terraform state (read-only u deploy fazi)
  statement {
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:ListBucket",
    ]
    resources = [
      aws_s3_bucket.terraform_state.arn,
      "${aws_s3_bucket.terraform_state.arn}/*",
    ]
  }
}
```

### GitLab CI job sa OIDC

```yaml
# .gitlab-ci.yml

variables:
  AWS_REGION: eu-west-1
  AWS_ROLE_ARN: arn:aws:iam::123456789012:role/project-a-gitlab-ci-deploy
  KUBE_NAMESPACE: project-a

.aws-auth: &aws-auth
  id_tokens:
    GITLAB_OIDC_TOKEN:
      aud: sts.amazonaws.com
  before_script:
    - |
      export $(aws sts assume-role-with-web-identity \
        --role-arn "$AWS_ROLE_ARN" \
        --role-session-name "gitlab-ci-${CI_JOB_ID}" \
        --web-identity-token "$GITLAB_OIDC_TOKEN" \
        --duration-seconds 3600 \
        --query 'Credentials.[AccessKeyId,SecretAccessKey,SessionToken]' \
        --output text | awk '{print "AWS_ACCESS_KEY_ID="$1"\nAWS_SECRET_ACCESS_KEY="$2"\nAWS_SESSION_TOKEN="$3}')
    - aws sts get-caller-identity  # Verifikacija

deploy-prod:
  <<: *aws-auth
  environment: production
  script:
    - aws eks update-kubeconfig --name project-a-prod --region $AWS_REGION
    - kubectl set image deployment/go-service go-service=$CI_REGISTRY_IMAGE/go-service:$CI_COMMIT_SHA -n $KUBE_NAMESPACE
    - kubectl rollout status deployment/go-service -n $KUBE_NAMESPACE
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
```

---

## Šta NIKAD ne ide u .gitlab-ci.yml ili git

```yaml
# OVAKO NE — primjeri koji se nalaze u breachovanim repozitorijumima

variables:
  AWS_ACCESS_KEY_ID: "AKIAIOSFODNN7EXAMPLE"        # NE
  AWS_SECRET_ACCESS_KEY: "wJalrXUtn/EXAMPLE/KEY"   # NE
  DB_PASSWORD: "SuperSecret123"                     # NE
  REDIS_AUTH: "my-redis-auth-token"                 # NE
  DOCKER_PASSWORD: "registry-password"              # NE
  STRIPE_SECRET_KEY: "sk_live_xxxxxxxxxxxxx"        # NE
```

Sve što treba biti secret ide u:
- GitLab CI/CD Variables (Settings → CI/CD → Variables) — encrypted at rest
- File Variables za kubeconfig, sertifikate, credentials fajlove

---

## Kubeconfig za CI — File Variable

Kubeconfig sa admin credentials je posebno osjetljiv. Ne treba biti u repozitorijumu.

```bash
# Generisanje kubeconfig za CI ServiceAccount (ograničeni pristup)
# Umjesto admin kubeconfig, kreirati dedicated SA sa minimalnim RBAC

kubectl apply -f - <<EOF
apiVersion: v1
kind: ServiceAccount
metadata:
  name: gitlab-ci
  namespace: project-a
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: gitlab-ci-deploy
  namespace: project-a
rules:
  - apiGroups: ["apps"]
    resources: ["deployments"]
    verbs: ["get", "list", "update", "patch"]
  - apiGroups: [""]
    resources: ["pods"]
    verbs: ["get", "list"]
  - apiGroups: [""]
    resources: ["services"]
    verbs: ["get", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: gitlab-ci-deploy
  namespace: project-a
subjects:
  - kind: ServiceAccount
    name: gitlab-ci
    namespace: project-a
roleRef:
  kind: Role
  name: gitlab-ci-deploy
  apiGroup: rbac.authorization.k8s.io
EOF

# Generisati token i base64 encoded kubeconfig
SA_TOKEN=$(kubectl create token gitlab-ci -n project-a --duration=8760h)
CLUSTER_CA=$(kubectl config view --raw -o jsonpath='{.clusters[0].cluster.certificate-authority-data}')
CLUSTER_SERVER=$(kubectl config view --raw -o jsonpath='{.clusters[0].cluster.server}')

# Kreirati kubeconfig
cat > /tmp/ci-kubeconfig.yaml <<KUBECONFIG
apiVersion: v1
kind: Config
clusters:
  - cluster:
      certificate-authority-data: ${CLUSTER_CA}
      server: ${CLUSTER_SERVER}
    name: project-a-prod
contexts:
  - context:
      cluster: project-a-prod
      namespace: project-a
      user: gitlab-ci
    name: project-a-prod
current-context: project-a-prod
users:
  - name: gitlab-ci
    user:
      token: ${SA_TOKEN}
KUBECONFIG

# base64 encode za GitLab File Variable
base64 -w 0 /tmp/ci-kubeconfig.yaml
# Ovu vrijednost uploadovati kao GitLab CI File Variable: KUBE_CONFIG
```

U GitLab CI/CD Variables: `KUBE_CONFIG` tipa File, Protected, Masked, scoped na `production` environment.

```yaml
# Korišćenje u .gitlab-ci.yml
deploy:
  script:
    - mkdir -p ~/.kube
    - cp "$KUBE_CONFIG" ~/.kube/config
    - chmod 600 ~/.kube/config
    - kubectl get pods -n project-a
```

---

## Terraform plan u CI — ograničeni SM pristup

```hcl
# CI rola za terraform plan (read-only za większość resursa)
data "aws_iam_policy_document" "gitlab_ci_tf_plan" {
  # Terraform plan treba čitati SM metadata (ne secret values)
  statement {
    effect = "Allow"
    actions = [
      "secretsmanager:DescribeSecret",  # Metadata, ne vrijednost
      "secretsmanager:ListSecrets",
      "secretsmanager:ListSecretVersionIds",
    ]
    resources = ["*"]
  }

  # Eksplicitni deny za GetSecretValue na prod (plan radi bez nje)
  statement {
    effect  = "Deny"
    actions = ["secretsmanager:GetSecretValue"]
    resources = [
      "arn:aws:secretsmanager:*:*:secret:/project-a/prod/*"
    ]
  }

  # Terraform plan za non-sensitive operations
  statement {
    effect = "Allow"
    actions = [
      "ec2:Describe*",
      "eks:Describe*",
      "rds:Describe*",
      "elasticache:Describe*",
      "iam:Get*",
      "iam:List*",
    ]
    resources = ["*"]
  }
}
```

Terraform plan **ne smije čitati produkcijske passwords**. State fajl već ima sve potrebne reference. Ako plan zahtijeva `GetSecretValue`, to je znak lošeg Terraform dizajna (npr. `data "aws_secretsmanager_secret_version"` u output bloku koji se uvijek evaluira).

---

## GitLab Secret Detection job

```yaml
# .gitlab-ci.yml — secret scanning
include:
  - template: Security/Secret-Detection.gitlab-ci.yml

secret_detection:
  stage: test
  variables:
    SECRET_DETECTION_HISTORIC_SCAN: "false"  # Samo diff, ne cijeli history
    SECRET_DETECTION_LOG_OPTIONS: "--all"

  # Custom rules za project-a specifične patterns
  # (GitLab koristi gitleaks pod haupom)
```

Za historijsko skeniranje (jednom, pri onboardingu projekta na SM):

```bash
# Skeniranje cijelog git historijata
docker run --rm \
    -v $(pwd):/repo \
    zricethezav/gitleaks:latest \
    detect \
    --source /repo \
    --report-path /repo/gitleaks-report.json \
    --report-format json \
    --no-git false \
    --verbose
```

---

## Pre-commit hook: detect-secrets / gitleaks

```bash
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
        exclude: |
          (?x)^(
            .env.example|
            docs/.*|
            .*\.test\.go
          )$

  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.0
    hooks:
      - id: gitleaks
```

Setup za novi developer:

```bash
pip install pre-commit detect-secrets
pre-commit install

# Kreirati baseline (ignoriše poznate false positive)
detect-secrets scan > .secrets.baseline
# Reviewovati baseline: sve što je tu je intentionally false positive
git add .secrets.baseline
git commit -m "chore: add detect-secrets baseline"
```

`.gitleaks.toml` za project-specific patterns:

```toml
# .gitleaks.toml
[extend]
useDefault = true

[[rules]]
id = "project-a-api-key"
description = "Project-A internal API key"
regex = '''project-a-[a-zA-Z0-9]{32}'''
tags = ["key", "project-a"]

[allowlist]
description = "Known false positives"
regexes = [
    '''EXAMPLE_KEY_REPLACE_ME''',
    '''sk_test_[a-zA-Z0-9]+''',  # Stripe test keys su OK
]
paths = [
    '''.secrets.baseline''',
    '''\.env\.example''',
]
```

---

## Failure modes u CI secrets managementu

**Token expiry mid-pipeline:**  
STS token traje 3600 sekundi. Dugi pipeline jobovi (Terraform koji čeka) mogu istećati. Mitigation: koristiti `--duration-seconds 3600` i strukturirati pipeline da kritični deploy job traje < 1h.

**OIDC audience mismatch:**  
Ako GitLab instance URL nije tačno unešen kao OIDC provider URL, assume-role će failati. Provjeriti: `gitlab.example.com` vs `https://gitlab.example.com` — konzistentnost je ključna.

**Variable masking limitation:**  
GitLab maskira varijable u log output samo ako su registrovane za masking. Varijabla koja se derivira (`$DERIVED_VAR=$MASKED_VAR`) nije automatski maskirana. Nikad logovati derived credentials.

**Terraform state race condition:**  
Dva simultana CI jobovi koji rade `terraform apply` mogu koruptovati state. DynamoDB locking rješava ovo — koristiti uvijek.
