# IAM role za project-A

## Pregled potrebnih rola

| Rola | Ko preuzima | Šta smije |
|------|-------------|-----------|
| `eks-cluster-role` | EKS control plane | Upravljati VPC, EC2 za K8s |
| `eks-node-role` | EC2 worker nodovi | Pridružiti se clusteru, pullati ECR |
| `alb-controller-role` | ALB Controller Pod (IRSA) | Kreirati/brisati ALB resurse |
| `cluster-autoscaler-role` | Autoscaler Pod (IRSA) | Skalirati Auto Scaling grupe |
| `gitlab-ci-role` | GitLab CI/CD pipeline (OIDC) | Deploy na EKS, push ECR, S3 state |

## IAM role za ALB Controller (IRSA)

ALB Controller mora kreirati i brisati AWS resurse (ALB, Target Groups, Listeners, Security Groups). Treba IAM rolu sa specifičnim pravima.

```hcl
# modules/iam/alb-controller-role.tf

data "aws_iam_policy_document" "alb_controller_assume" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    effect  = "Allow"

    principals {
      type        = "Federated"
      identifiers = [var.oidc_provider_arn]
    }

    condition {
      test     = "StringEquals"
      variable = "${var.oidc_provider_url}:sub"
      values   = ["system:serviceaccount:kube-system:aws-load-balancer-controller"]
    }

    condition {
      test     = "StringEquals"
      variable = "${var.oidc_provider_url}:aud"
      values   = ["sts.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "alb_controller" {
  name               = "${var.cluster_name}-alb-controller"
  assume_role_policy = data.aws_iam_policy_document.alb_controller_assume.json
}

# AWS managed politika za ALB Controller (AWS je održava)
resource "aws_iam_role_policy_attachment" "alb_controller" {
  role       = aws_iam_role.alb_controller.name
  policy_arn = aws_iam_policy.alb_controller.arn
}
```

## IAM role za Cluster Autoscaler (IRSA)

```hcl
resource "aws_iam_policy" "cluster_autoscaler" {
  name = "${var.cluster_name}-cluster-autoscaler"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "autoscaling:DescribeAutoScalingGroups",
          "autoscaling:DescribeAutoScalingInstances",
          "autoscaling:DescribeLaunchConfigurations",
          "autoscaling:DescribeScalingActivities",
          "autoscaling:DescribeTags",
          "ec2:DescribeInstanceTypes",
          "ec2:DescribeLaunchTemplateVersions"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "autoscaling:SetDesiredCapacity",
          "autoscaling:TerminateInstanceInAutoScalingGroup"
        ]
        # Samo na ASG-ovima koji pripadaju ovom clusteru
        Resource = "*"
        Condition = {
          StringEquals = {
            "autoscaling:ResourceTag/kubernetes.io/cluster/${var.cluster_name}" = "owned"
          }
        }
      }
    ]
  })
}
```

## GitLab CI/CD role (OIDC)

Ovo je najvažnija rola — koristi je svaki GitLab pipeline za deployment.

```hcl
# modules/iam/gitlab-ci-role.tf

resource "aws_iam_role" "gitlab_ci" {
  name = "project-a-gitlab-ci-${var.env_name}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = "sts:AssumeRoleWithWebIdentity"
      Principal = {
        Federated = var.gitlab_oidc_provider_arn
      }
      Condition = {
        StringLike = {
          # Samo pipelines iz ovog projekta
          "gitlab.com:sub" = "project_path:${var.gitlab_project_path}:ref_type:branch:ref:*"
        }
      }
    }]
  })
}

resource "aws_iam_policy" "gitlab_ci" {
  name = "project-a-gitlab-ci-${var.env_name}"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      # EKS: update kubeconfig i deploy
      {
        Effect = "Allow"
        Action = [
          "eks:DescribeCluster",
          "eks:ListClusters"
        ]
        Resource = "arn:aws:eks:${var.region}:${var.account_id}:cluster/project-a-${var.env_name}"
      },
      # S3: čitanje i pisanje Terraform state-a
      {
        Effect = "Allow"
        Action = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"]
        Resource = "arn:aws:s3:::project-a-terraform-state/${var.env_name}/*"
      },
      {
        Effect   = "Allow"
        Action   = ["s3:ListBucket"]
        Resource = "arn:aws:s3:::project-a-terraform-state"
      },
      # DynamoDB: Terraform state locking
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:DeleteItem"
        ]
        Resource = "arn:aws:dynamodb:${var.region}:${var.account_id}:table/project-a-terraform-locks"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "gitlab_ci" {
  role       = aws_iam_role.gitlab_ci.name
  policy_arn = aws_iam_policy.gitlab_ci.arn
}
```

## Praktičan primjer: least privilege u akciji

Loša praksa:
```hcl
# NE RADITI OVO
resource "aws_iam_role_policy_attachment" "gitlab_admin" {
  role       = aws_iam_role.gitlab_ci.name
  policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
}
```

Dobra praksa: eksplicitne akcije na eksplicitnim resursima. Ako pipeline pokuša da kreira nešto što nije u politici, dobija `AccessDenied` — što je ispravno ponašanje. Dodaješ dozvole kada zaista trebaju, ne "za svaki slučaj".

## Outputs za IAM modul

```hcl
output "gitlab_ci_role_arn" {
  value = aws_iam_role.gitlab_ci.arn
}

output "alb_controller_role_arn" {
  value = aws_iam_role.alb_controller.arn
}

output "cluster_autoscaler_role_arn" {
  value = aws_iam_role.cluster_autoscaler.arn
}
```

Ovi output-i se prosljeđuju u Helm values za ALB Controller i Autoscaler ServiceAccount anotacije.
