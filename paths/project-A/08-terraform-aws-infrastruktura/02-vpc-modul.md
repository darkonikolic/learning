# VPC modul

## Šta modul kreira

VPC modul je osnova za sve ostalo. EKS treba VPC ID i subnet ID-eve. ALB treba public subnet-e. Bez ovog modula, ništa drugo ne može biti kreirano.

Resursi u modulu:
- 1× VPC
- 2× Public subnet (po jedan u svakom AZ)
- 2× Private subnet (po jedan u svakom AZ)
- 1× Internet Gateway
- 1× NAT Gateway (opciono za dev)
- Route tables i associations

## `modules/vpc/variables.tf`

```hcl
variable "env_name" {
  description = "Naziv environmenta (dev, staging, prod)"
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR blok za VPC (npr. 10.0.0.0/16)"
  type        = string
}

variable "availability_zones" {
  description = "Lista AZ-ova za deployment"
  type        = list(string)
  default     = ["eu-west-1a", "eu-west-1b"]
}

variable "enable_nat_gateway" {
  description = "Kreirati NAT Gateway (false za dev cost saving)"
  type        = bool
  default     = true
}

variable "cluster_name" {
  description = "EKS cluster naziv — za subnet tagove"
  type        = string
}
```

## `modules/vpc/main.tf`

```hcl
locals {
  # Generiše CIDR za subnete od VPC CIDR-a
  # VPC 10.0.0.0/16 → public: 10.0.1.0/24, 10.0.2.0/24
  #                  → private: 10.0.10.0/24, 10.0.11.0/24
  public_cidrs  = [for i, az in var.availability_zones : cidrsubnet(var.vpc_cidr, 8, i + 1)]
  private_cidrs = [for i, az in var.availability_zones : cidrsubnet(var.vpc_cidr, 8, i + 10)]
}

# VPC — izolirana mreža
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true   # potrebno za EKS
  enable_dns_hostnames = true   # potrebno za EKS

  tags = {
    Name = "project-a-${var.env_name}"
    "kubernetes.io/cluster/${var.cluster_name}" = "shared"
  }
}

# Public subneti — za ALB i NAT Gateway
resource "aws_subnet" "public" {
  count = length(var.availability_zones)

  vpc_id            = aws_vpc.main.id
  cidr_block        = local.public_cidrs[count.index]
  availability_zone = var.availability_zones[count.index]

  # ALB instances u public subnetu moraju imati javne IP
  map_public_ip_on_launch = false  # ne EKS nodovi, samo ALB

  tags = {
    Name = "project-a-${var.env_name}-public-${var.availability_zones[count.index]}"
    "kubernetes.io/cluster/${var.cluster_name}" = "shared"
    "kubernetes.io/role/elb"                    = "1"  # ALB controller traga za ovim tagom
  }
}

# Private subneti — za EKS worker nodove
resource "aws_subnet" "private" {
  count = length(var.availability_zones)

  vpc_id            = aws_vpc.main.id
  cidr_block        = local.private_cidrs[count.index]
  availability_zone = var.availability_zones[count.index]

  tags = {
    Name = "project-a-${var.env_name}-private-${var.availability_zones[count.index]}"
    "kubernetes.io/cluster/${var.cluster_name}" = "shared"
    "kubernetes.io/role/internal-elb"           = "1"  # internal load balancer tag
  }
}

# Internet Gateway — vrata između VPC i interneta
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "project-a-${var.env_name}-igw"
  }
}

# Elastic IP za NAT Gateway
resource "aws_eip" "nat" {
  count  = var.enable_nat_gateway ? 1 : 0
  domain = "vpc"
}

# NAT Gateway — outbound internet za private subnet resurse
# Kreira se samo u prvom public subnetu (jedan NAT je dovoljan za dev/staging)
resource "aws_nat_gateway" "main" {
  count = var.enable_nat_gateway ? 1 : 0

  allocation_id = aws_eip.nat[0].id
  subnet_id     = aws_subnet.public[0].id  # mora biti u public subnetu

  tags = {
    Name = "project-a-${var.env_name}-nat"
  }

  depends_on = [aws_internet_gateway.main]
}

# Route table za public subnete — sav saobraćaj prema IGW
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = { Name = "project-a-${var.env_name}-public-rt" }
}

# Route table za private subnete — outbound kroz NAT
resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id

  dynamic "route" {
    for_each = var.enable_nat_gateway ? [1] : []
    content {
      cidr_block     = "0.0.0.0/0"
      nat_gateway_id = aws_nat_gateway.main[0].id
    }
  }

  tags = { Name = "project-a-${var.env_name}-private-rt" }
}

# Asocijacije route table-a sa subnetima
resource "aws_route_table_association" "public" {
  count          = length(aws_subnet.public)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "private" {
  count          = length(aws_subnet.private)
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private.id
}
```

## `modules/vpc/outputs.tf`

```hcl
output "vpc_id" {
  value = aws_vpc.main.id
}

output "public_subnet_ids" {
  value = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  value = aws_subnet.private[*].id
}
```

## Zašto 2 AZ

Jedan AZ znači: ako AWS ima incident u eu-west-1a, cijeli dev environment pada. Dva AZ: ALB distribuira saobraćaj, EKS scheduluje Podove u oba. Cijena je minimalna (dupli broj subneta — besplatni resursi).

Za dev, dozvoljeno je koristiti jedan AZ (`availability_zones = ["eu-west-1a"]`) radi bržeg terraform apply.
