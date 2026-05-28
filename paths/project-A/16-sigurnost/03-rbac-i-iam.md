# 03 — RBAC i IAM

## K8s RBAC za project-a

Kubernetes RBAC kontroliše ko može raditi šta sa K8s API objektima. Tri ServiceAccount-a za naš projekt:

### 1. GitLab CI ServiceAccount

CI treba deployovati aplikacije (update Deployment images), ali nema razloga čitati Secrets ili izvršavati komande unutar podova.

```yaml
# k8s/base/rbac/gitlab-ci-sa.yaml

apiVersion: v1
kind: ServiceAccount
metadata:
  name: gitlab-ci
  namespace: project-a
  annotations:
    description: "Used by GitLab CI for deployments. No exec, no secret read."
automountServiceAccountToken: false  # Token se kreira eksplicitno, ne automatski
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: gitlab-ci-deploy
  namespace: project-a
rules:
  # Deployovi — update image, patch spec
  - apiGroups: ["apps"]
    resources: ["deployments"]
    verbs: ["get", "list", "update", "patch"]
  # Rollout status praćenje
  - apiGroups: ["apps"]
    resources: ["replicasets"]
    verbs: ["get", "list"]
  # Pod listing za debug (ne exec)
  - apiGroups: [""]
    resources: ["pods"]
    verbs: ["get", "list"]
  # Services — za blue/green ili canary deploy
  - apiGroups: [""]
    resources: ["services"]
    verbs: ["get", "list", "update", "patch"]
  # Nije potrebno: secrets, configmaps, exec, portforward
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
```

**Attack vector koji ovaj RBAC sprječava:**  
Ako GitLab CI job bude kompromitovan (maliciozan MR koji mijenja pipeline), napadač može deployovati maliciozan image ali **ne može** pročitati DB passwords, Redis tokens, ili izvršiti komande unutar postojećih podova.

### 2. Developer ServiceAccount

Developeri trebaju debugovati aplikacije — pregledati logove, opisati podove. Ne trebaju direktan pristup Secrets objektima.

```yaml
# k8s/base/rbac/developer-sa.yaml

apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: developer-readonly
  namespace: project-a
rules:
  - apiGroups: [""]
    resources: ["pods"]
    verbs: ["get", "list", "describe"]
  - apiGroups: [""]
    resources: ["pods/log"]
    verbs: ["get"]
  - apiGroups: ["apps"]
    resources: ["deployments", "replicasets"]
    verbs: ["get", "list"]
  - apiGroups: [""]
    resources: ["services", "endpoints"]
    verbs: ["get", "list"]
  - apiGroups: [""]
    resources: ["events"]
    verbs: ["get", "list"]
  # EKSPLICITNO ODSUTNO:
  # - secrets: nikakav pristup
  # - pods/exec: nema shell pristupa u podovima
  # - pods/portforward: nema direktnog port forwardinga na bazu
```

**Šta ovo znači u praksi:**  
Developer može `kubectl logs go-service-xxx` i `kubectl describe pod go-service-xxx`, ali ne može `kubectl exec -it go-service-xxx -- /bin/sh` niti `kubectl get secret go-service-secrets -o yaml`.

```bash
# Testiranje RBAC restrikcija
kubectl auth can-i exec pods --as=system:serviceaccount:project-a:developer-sa -n project-a
# No

kubectl auth can-i get secrets --as=system:serviceaccount:project-a:developer-sa -n project-a
# No

kubectl auth can-i get pods/log --as=system:serviceaccount:project-a:developer-sa -n project-a
# Yes
```

### 3. Monitoring ServiceAccount

Prometheus scraper treba čitati pod metadata i service endpoints za service discovery:

```yaml
# k8s/base/rbac/monitoring-sa.yaml

apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole  # Cluster-wide jer Prometheus scrape sve namespace-ove
metadata:
  name: prometheus-scraper
rules:
  - apiGroups: [""]
    resources:
      - nodes
      - nodes/metrics
      - services
      - endpoints
      - pods
    verbs: ["get", "list", "watch"]
  - apiGroups: ["extensions", "networking.k8s.io"]
    resources: ["ingresses"]
    verbs: ["get", "list", "watch"]
  - nonResourceURLs: ["/metrics", "/metrics/cadvisor"]
    verbs: ["get"]
  # EKSPLICITNO ODSUTNO: secrets, configmaps sa credentials, exec
```

---

## IAM Principle of Least Privilege — audit checklist

### EKS node role — minimalno

```hcl
# terraform/modules/eks/node-iam.tf

# AWS managed policies koje EKS worker node MORA imati
data "aws_iam_policy" "eks_worker_node" {
  name = "AmazonEKSWorkerNodePolicy"
}

data "aws_iam_policy" "ecr_readonly" {
  name = "AmazonEC2ContainerRegistryReadOnly"
}

data "aws_iam_policy" "cni" {
  name = "AmazonEKS_CNI_Policy"
}

# Custom policy za EBS CSI driver
data "aws_iam_policy_document" "ebs_csi" {
  statement {
    effect = "Allow"
    actions = [
      "ec2:CreateSnapshot",
      "ec2:AttachVolume",
      "ec2:DetachVolume",
      "ec2:ModifyVolume",
      "ec2:DescribeAvailabilityZones",
      "ec2:DescribeInstances",
      "ec2:DescribeSnapshots",
      "ec2:DescribeTags",
      "ec2:DescribeVolumes",
      "ec2:DescribeVolumesModifications",
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role" "eks_node" {
  name = "project-a-${var.environment}-eks-node"

  # Bez IMDSv1 pristupa — aplikacije ne smiju dobiti node credentials
  # IRSA je pravi mehanizam za per-pod credentials
}

# Audit: node role NE SMIJE imati:
# - AmazonS3FullAccess
# - AmazonRDSFullAccess
# - SecretsManagerReadWrite
# - AdministratorAccess
# - IAMFullAccess

resource "aws_iam_role_policy" "eks_node_audit_deny" {
  name = "explicit-deny-sensitive"
  role = aws_iam_role.eks_node.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "DenySecretsAccess"
        Effect = "Deny"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:PutSecretValue",
        ]
        Resource = "*"
      }
    ]
  })
  # Node ne smije čitati secrets — samo IRSA rola za ESO
}
```

### ESO IRSA — samo GetSecretValue za specifične ARN-ove

```hcl
data "aws_iam_policy_document" "eso_minimal" {
  statement {
    effect  = "Allow"
    actions = ["secretsmanager:GetSecretValue", "secretsmanager:DescribeSecret"]
    resources = [
      "arn:aws:secretsmanager:${var.aws_region}:${data.aws_caller_identity.current.account_id}:secret:/project-a/${var.environment}/*"
    ]
  }

  # Ne treba: ListSecrets, CreateSecret, PutSecretValue, DeleteSecret, RotateSecret
}
```

### GitLab CI role — precizno scoped

```hcl
data "aws_iam_policy_document" "gitlab_ci_minimal" {
  # ECR — samo za project-a repozitorijume
  statement {
    effect    = "Allow"
    actions   = ["ecr:GetAuthorizationToken"]
    resources = ["*"]  # Ova akcija ne podržava resource-level permission
  }

  statement {
    effect = "Allow"
    actions = [
      "ecr:BatchCheckLayerAvailability",
      "ecr:InitiateLayerUpload",
      "ecr:UploadLayerPart",
      "ecr:CompleteLayerUpload",
      "ecr:PutImage",
      "ecr:BatchGetImage",
      "ecr:GetDownloadUrlForLayer",
    ]
    resources = [
      "arn:aws:ecr:${var.aws_region}:${data.aws_caller_identity.current.account_id}:repository/project-a/*"
    ]
  }

  # EKS — samo describe, ne manage
  statement {
    effect    = "Allow"
    actions   = ["eks:DescribeCluster"]
    resources = [aws_eks_cluster.main.arn]
  }

  # S3 Terraform state — read-only za plan, write za apply
  statement {
    effect = "Allow"
    actions = var.ci_role_type == "plan" ? [
      "s3:GetObject",
      "s3:ListBucket",
    ] : [
      "s3:GetObject",
      "s3:PutObject",
      "s3:ListBucket",
    ]
    resources = [
      aws_s3_bucket.terraform_state.arn,
      "${aws_s3_bucket.terraform_state.arn}/*",
    ]
  }

  # DynamoDB za Terraform state locking
  statement {
    effect = "Allow"
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:DeleteItem",
    ]
    resources = [aws_dynamodb_table.terraform_locks.arn]
  }

  # Eksplicitni deny za produkcijske secretse iz CI
  statement {
    effect  = "Deny"
    actions = ["secretsmanager:GetSecretValue"]
    resources = [
      "arn:aws:secretsmanager:*:*:secret:/project-a/prod/*"
    ]
  }
}
```

---

## AWS IAM Access Analyzer

IAM Access Analyzer automatski identifikuje over-permissive polícy i external access:

```hcl
# terraform/modules/security/access-analyzer.tf

resource "aws_accessanalyzer_analyzer" "project_a" {
  analyzer_name = "project-a-${var.environment}"
  type          = "ACCOUNT"  # Analizira resource-based polícy u accountu

  tags = {
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

# CloudWatch Event kada Access Analyzer pronađe finding
resource "aws_cloudwatch_event_rule" "access_analyzer_finding" {
  name        = "project-a-access-analyzer-finding"
  description = "Alert on new IAM Access Analyzer findings"

  event_pattern = jsonencode({
    source      = ["aws.access-analyzer"]
    detail-type = ["Access Analyzer Finding"]
    detail = {
      status = ["ACTIVE"]
    }
  })
}

resource "aws_cloudwatch_event_target" "access_analyzer_sns" {
  rule = aws_cloudwatch_event_rule.access_analyzer_finding.name
  arn  = aws_sns_topic.security_alerts.arn
}
```

**Što Access Analyzer detektuje:**
- S3 bucket koji je dostupan externally (public ili cross-account)
- IAM role kojoj može pristupiti external principal
- KMS key koji je cross-account shared
- Lambda function sa resource-based polícy koja dozvoljava external access
- SQS queue sa public access

```bash
# Listanje aktivnih findings
aws accessanalyzer list-findings \
    --analyzer-arn arn:aws:access-analyzer:eu-west-1:123456789:analyzer/project-a-prod \
    --filter '{"status": {"eq": ["ACTIVE"]}}'
```

---

## Terraform za sve RBAC i IAM

Nikad ručno kreirati IAM role, politike, ili K8s RBAC objekte. Razlozi:

1. **Drift detection:** Terraform plan pokazuje svako ručno napravljenu izmjenu kao "needs update"
2. **Auditabilnost:** Svaka promjena IAM politike je git commit sa autorom i razlogom
3. **Reproducibilnost:** Novi environment (staging → prod) dobija identičan RBAC setup
4. **Accidentalni pristup:** Console klikanje ne ostavlja trail i lako napraviti grešku

```bash
# Detekcija IAM drift-a (ručno napravljene promjene)
# Terraform plan u CI svaki dan (scheduled pipeline)
# Svaki "~ update" na IAM resource koji nema odgovarajući git commit = red flag

terraform plan -detailed-exitcode
# Exit code 2 = changes detected → alert u Slack
```

---

## Audit trail — ko je promijenio šta

```hcl
# CloudTrail za IAM i K8s API call logging
resource "aws_cloudtrail" "main" {
  name                          = "project-a-${var.environment}"
  s3_bucket_name                = aws_s3_bucket.cloudtrail.id
  include_global_service_events = true  # IAM je global service
  is_multi_region_trail         = true
  enable_log_file_validation    = true  # Detektovati tampering

  event_selector {
    read_write_type           = "All"
    include_management_events = true

    data_resource {
      type   = "AWS::SecretsManager::Secret"
      values = ["arn:aws:secretsmanager:*:*:secret:/project-a/*"]
    }
  }
}

# S3 bucket za CloudTrail logs — enkriptovan i access-protected
resource "aws_s3_bucket" "cloudtrail" {
  bucket = "project-a-cloudtrail-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3_bucket_policy" "cloudtrail" {
  bucket = aws_s3_bucket.cloudtrail.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AWSCloudTrailAclCheck"
        Effect = "Allow"
        Principal = {
          Service = "cloudtrail.amazonaws.com"
        }
        Action   = "s3:GetBucketAcl"
        Resource = aws_s3_bucket.cloudtrail.arn
      },
      {
        Sid    = "AWSCloudTrailWrite"
        Effect = "Allow"
        Principal = {
          Service = "cloudtrail.amazonaws.com"
        }
        Action   = "s3:PutObject"
        Resource = "${aws_s3_bucket.cloudtrail.arn}/AWSLogs/*"
        Condition = {
          StringEquals = {
            "s3:x-amz-acl" = "bucket-owner-full-control"
          }
        }
      },
      {
        Sid    = "DenyPublicAccess"
        Effect = "Deny"
        Principal = "*"
        Action    = "s3:*"
        Resource  = [
          aws_s3_bucket.cloudtrail.arn,
          "${aws_s3_bucket.cloudtrail.arn}/*",
        ]
        Condition = {
          Bool = {
            "aws:SecureTransport" = "false"
          }
        }
      }
    ]
  })
}
```
