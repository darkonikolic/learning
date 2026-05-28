# EKS modul

## Šta modul kreira

EKS modul kreira kompletan Kubernetes cluster spreman za deployovanje workload-a:
- EKS cluster (control plane)
- Managed Node Group (worker nodovi)
- EKS Add-ons (VPC CNI, CoreDNS, kube-proxy, EBS CSI)
- OIDC provider (za IRSA)
- Security Groups za cluster i nodove

## `modules/eks/variables.tf`

```hcl
variable "cluster_name" {
  type = string
}

variable "kubernetes_version" {
  type    = string
  default = "1.29"
}

variable "vpc_id" {
  type = string
}

variable "private_subnet_ids" {
  type = list(string)
}

variable "node_instance_type" {
  type    = string
  default = "t3.medium"
}

variable "desired_nodes" {
  type    = number
  default = 1
}

variable "min_nodes" {
  type    = number
  default = 1
}

variable "max_nodes" {
  type    = number
  default = 3
}

variable "env_name" {
  type = string
}
```

## `modules/eks/main.tf`

```hcl
# IAM role za EKS control plane
resource "aws_iam_role" "eks_cluster" {
  name = "${var.cluster_name}-cluster-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "eks.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "eks_cluster_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  role       = aws_iam_role.eks_cluster.name
}

# Security Group za EKS cluster
resource "aws_security_group" "eks_cluster" {
  name   = "${var.cluster_name}-cluster-sg"
  vpc_id = var.vpc_id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# EKS Cluster — managed control plane
resource "aws_eks_cluster" "main" {
  name     = var.cluster_name
  version  = var.kubernetes_version
  role_arn = aws_iam_role.eks_cluster.arn

  vpc_config {
    subnet_ids              = var.private_subnet_ids
    security_group_ids      = [aws_security_group.eks_cluster.id]
    endpoint_private_access = true   # API server dostupan iz VPC
    endpoint_public_access  = true   # API server dostupan sa interneta (za lokalni kubectl)
  }

  depends_on = [aws_iam_role_policy_attachment.eks_cluster_policy]
}

# IAM role za worker nodove
resource "aws_iam_role" "eks_nodes" {
  name = "${var.cluster_name}-node-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
    }]
  })
}

# Node role treba ove managed politike
resource "aws_iam_role_policy_attachment" "node_policies" {
  for_each = toset([
    "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy",
    "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy",          # VPC CNI
    "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly",  # ECR pull
  ])

  policy_arn = each.value
  role       = aws_iam_role.eks_nodes.name
}

# Managed Node Group — AWS kreira i upravlja EC2 instancema
resource "aws_eks_node_group" "main" {
  cluster_name    = aws_eks_cluster.main.name
  node_group_name = "${var.cluster_name}-nodes"
  node_role_arn   = aws_iam_role.eks_nodes.arn
  subnet_ids      = var.private_subnet_ids

  instance_types = [var.node_instance_type]
  capacity_type  = var.env_name == "prod" ? "ON_DEMAND" : "SPOT"

  scaling_config {
    desired_size = var.desired_nodes
    min_size     = var.min_nodes
    max_size     = var.max_nodes
  }

  update_config {
    max_unavailable = 1  # tokom update-a, max 1 node nedostupan
  }

  depends_on = [aws_iam_role_policy_attachment.node_policies]
}

# EKS Add-ons — managed verzije core komponenti
resource "aws_eks_addon" "vpc_cni" {
  cluster_name = aws_eks_cluster.main.name
  addon_name   = "vpc-cni"
  depends_on   = [aws_eks_node_group.main]
}

resource "aws_eks_addon" "coredns" {
  cluster_name = aws_eks_cluster.main.name
  addon_name   = "coredns"
  depends_on   = [aws_eks_node_group.main]  # CoreDNS treba node-ove za scheduling
}

resource "aws_eks_addon" "kube_proxy" {
  cluster_name = aws_eks_cluster.main.name
  addon_name   = "kube-proxy"
}

resource "aws_eks_addon" "ebs_csi" {
  cluster_name = aws_eks_cluster.main.name
  addon_name   = "aws-ebs-csi-driver"
  depends_on   = [aws_eks_node_group.main]
}

# OIDC Provider — omogućava IRSA (IAM Role za ServiceAccount)
data "tls_certificate" "eks" {
  url = aws_eks_cluster.main.identity[0].oidc[0].issuer
}

resource "aws_iam_openid_connect_provider" "eks" {
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [data.tls_certificate.eks.certificates[0].sha1_fingerprint]
  url             = aws_eks_cluster.main.identity[0].oidc[0].issuer
}
```

## `modules/eks/outputs.tf`

```hcl
output "cluster_name" {
  value = aws_eks_cluster.main.name
}

output "cluster_endpoint" {
  value = aws_eks_cluster.main.endpoint
}

output "cluster_ca" {
  value = aws_eks_cluster.main.certificate_authority[0].data
}

output "oidc_provider_arn" {
  value = aws_iam_openid_connect_provider.eks.arn
}

output "oidc_provider_url" {
  value = replace(aws_eks_cluster.main.identity[0].oidc[0].issuer, "https://", "")
}
```

## Node sizing po environmentu

```hcl
# envs/dev/dev.tfvars
node_instance_type = "t3.medium"
desired_nodes      = 1
min_nodes          = 1
max_nodes          = 3

# envs/staging/staging.tfvars
node_instance_type = "t3.large"
desired_nodes      = 2
min_nodes          = 2
max_nodes          = 5

# envs/prod/prod.tfvars
node_instance_type = "t3.xlarge"
desired_nodes      = 3
min_nodes          = 3
max_nodes          = 10
```

EKS cluster traje 10-15 minuta za kreiranje. `depends_on` u Add-onovima je bitan — CoreDNS Podovi ne mogu biti scheduled dok nema worker nodova.
