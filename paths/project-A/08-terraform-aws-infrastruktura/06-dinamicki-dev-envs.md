# Dinamički review environment-i

## Šta su review enviroments i zašto su korisni

Svaki GitLab MR (Merge Request) dobija vlastiti deployment URL gdje može biti pregledano. Umjesto "provjeri screenshot u MR-u", reviewer otvara `https://mr-42.dev.firma.com` i direktno testira promjene.

Benefiti:
- Vizualno testiranje bez lokalnog setup-a
- QA može testirati bez pristupa lokalne mašine
- Automatski destroy kada se MR zatvori (nema orphan resursa)
- Paralelno testiranje više MR-ova istovremeno

## Šta se NE kreira za review env

**Ne novi EKS cluster** — to bi koštalo $72+ po MR-u. Ako team ima 5 otvorenih MR-ova, to je $360/mj samo za review envs.

Review env koristi **eksistirajući dev cluster**, ali dobija vlastiti namespace. Namespace je K8s izolaciona granica — mrežna separacija, vlastiti resource limits, vlastiti Secrets.

## Šta se kreira za review env

| Resurs | Gdje | Cijena |
|--------|------|--------|
| K8s namespace | Dev cluster | $0 |
| Helm release | U namespace-u | $0 |
| GitLab registry Secret | U namespace-u | $0 |
| Route53 CNAME | `mr-42.dev.firma.com` | ~$0 |
| **Ukupno** | | **~$0** (workload na existing nodovima) |

## `envs/dynamic/main.tf`

```hcl
variable "env_name" {
  description = "MR identifikator (npr. mr-42)"
  type        = string
}

variable "base_domain" {
  description = "Base domain (npr. dev.firma.com)"
  type        = string
  default     = "dev.firma.com"
}

variable "image_tag" {
  description = "Docker image tag za deployment"
  type        = string
}

variable "gitlab_registry_username" {
  type      = string
  sensitive = true
}

variable "gitlab_registry_password" {
  type      = string
  sensitive = true
}

# Data source: referencira eksistirajući dev cluster
data "aws_eks_cluster" "dev" {
  name = "project-a-dev"
}

data "aws_route53_zone" "dev" {
  name = var.base_domain
}

provider "kubernetes" {
  host                   = data.aws_eks_cluster.dev.endpoint
  cluster_ca_certificate = base64decode(data.aws_eks_cluster.dev.certificate_authority[0].data)
  exec {
    api_version = "client.authentication.k8s.io/v1beta1"
    command     = "aws"
    args        = ["eks", "get-token", "--cluster-name", "project-a-dev"]
  }
}

# Kubernetes namespace za ovaj review env
resource "kubernetes_namespace" "review" {
  metadata {
    name = "helloworld-${var.env_name}"
    labels = {
      environment = "review"
      mr          = var.env_name
    }
  }
}

# GitLab registry credentials za image pull
resource "kubernetes_secret" "gitlab_registry" {
  metadata {
    name      = "gitlab-registry-secret"
    namespace = kubernetes_namespace.review.metadata[0].name
  }

  type = "kubernetes.io/dockerconfigjson"

  data = {
    ".dockerconfigjson" = jsonencode({
      auths = {
        "registry.gitlab.com" = {
          username = var.gitlab_registry_username
          password = var.gitlab_registry_password
          auth     = base64encode("${var.gitlab_registry_username}:${var.gitlab_registry_password}")
        }
      }
    })
  }
}

# Helm deployment helloworld applikacije
resource "helm_release" "helloworld" {
  name       = "helloworld"
  chart      = "../../../helm/helloworld"  # lokalni chart
  namespace  = kubernetes_namespace.review.metadata[0].name

  set {
    name  = "image.tag"
    value = var.image_tag
  }

  set {
    name  = "ingress.host"
    value = "${var.env_name}.${var.base_domain}"
  }

  set {
    name  = "ingress.enabled"
    value = "true"
  }

  depends_on = [kubernetes_secret.gitlab_registry]
}

# Route53 CNAME za review env
resource "aws_route53_record" "review" {
  zone_id = data.aws_route53_zone.dev.zone_id
  name    = "${var.env_name}.${var.base_domain}"
  type    = "CNAME"
  ttl     = 60

  # ALB DNS iz dev environmenta (dijele isti ALB)
  records = [data.aws_eks_cluster.dev.endpoint]
}
```

## `envs/dynamic/backend.tf`

```hcl
terraform {
  backend "s3" {
    bucket         = "project-a-terraform-state"
    # key se prosljeđuje kao -backend-config parametar, ne hardkodirano
    region         = "eu-west-1"
    encrypt        = true
    dynamodb_table = "project-a-terraform-locks"
  }
}
```

Init sa dinamičkim key-om:
```bash
terraform init -backend-config="key=dynamic/${env_name}/terraform.tfstate"
```

## GitLab CI/CD integracija

```yaml
# .gitlab-ci.yml
deploy-review:
  stage: deploy
  environment:
    name: review/$CI_MERGE_REQUEST_IID
    url: https://mr-$CI_MERGE_REQUEST_IID.dev.firma.com
    on_stop: destroy-review
  script:
    - cd terraform/envs/dynamic
    - terraform init -backend-config="key=dynamic/mr-${CI_MERGE_REQUEST_IID}/terraform.tfstate"
    - terraform apply -auto-approve
        -var="env_name=mr-${CI_MERGE_REQUEST_IID}"
        -var="image_tag=${CI_COMMIT_SHORT_SHA}"
  only:
    - merge_requests

destroy-review:
  stage: deploy
  environment:
    name: review/$CI_MERGE_REQUEST_IID
    action: stop
  script:
    - helm uninstall helloworld -n helloworld-mr-${CI_MERGE_REQUEST_IID}
    - cd terraform/envs/dynamic
    - terraform init -backend-config="key=dynamic/mr-${CI_MERGE_REQUEST_IID}/terraform.tfstate"
    - terraform destroy -auto-approve -var="env_name=mr-${CI_MERGE_REQUEST_IID}"
  when: manual
  only:
    - merge_requests
```

## Pattern imenovanja

```
MR #42 → env_name = mr-42
        → namespace = helloworld-mr-42
        → URL = https://mr-42.dev.firma.com
        → state key = dynamic/mr-42/terraform.tfstate
```

Konzistentan pattern: isti broj svuda. Ako treba debugging, `kubectl -n helloworld-mr-42 logs` odmah znaš namespace.
