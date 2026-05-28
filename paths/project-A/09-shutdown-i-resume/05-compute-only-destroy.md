# 05 — Compute-Only Destroy (Dnevna Pauza)

**Kada koristiti:** Dnevna pauza na kraju radnog dana za tim koji radi svaki dan.
Uštednja ~$4/dan po environmentu. Resume za 8–10 minuta.

---

## Analiza: Šta je skupo, šta je jeftino

```
SKUPO — uništi svako veče:
  EKS Node Group (2× t3.medium):  $0.094/h = $2.26/dan (24h) = $67/mj
  NAT Gateway:                     $0.045/h = $1.08/dan (24h) = $32/mj
  ALB (automatski uz Ingress):     $0.022/h = $0.53/dan (24h) = $16/mj
  ──────────────────────────────────────────────────────────────────
  Ukupno compute:                            ~$3.87/dan = ~$115/mj

JEFTINO — ostavi ili zaustavi:
  RDS stopped (db.t3.micro, 20GB):  $0.003/dan storage = $0.08/mj
  ElastiCache (cache.t3.micro):     $0.017/h → ostavi running (jeftino)
  VPC + Subnets:                    $0
  Security Groups:                  $0
  Route53 records:                  $0.40/mj ukupno
  EKS Control Plane:                $0.10/h = $2.40/dan ← debata ispod

UŠTEDNJA po danu pauze (8h odsustva):
  Bez nodova i NAT:                 ~$1.14/8h = ~$4.10/dan × radnih dana
  Uštednja (radni vikend):          ~$7.74 × 2 dana = ~$15.50/vikend
  Uštednja (godišnje, 250 radnih):  ~$1.025/godišnje po environmentu
```

### EKS Control Plane: Destroy vs Zadrži

```
Zadrži control plane (brži resume):
  Trošak: $72/mj stalno
  Resume: 5–8 minuta (samo nodovi + NAT + ALB)

Destroy control plane (jeftiniji):
  Trošak: $72 × (aktivni dani / ukupni dani) ≈ $22/mj pri 5-dnevnoj radnoj sedmici
  Resume: 12–15 minuta (EKS + nodovi + NAT + ALB)

Preporuka za tim: Zadrži control plane (brži resume, lakše upravljanje)
Preporuka za jednog developlera: Destroy sve (jeftinije)
```

---

## EOD Pause Skripta

```bash
#!/bin/bash
# scripts/eod-pause.sh
# End of Day Pause — scale down compute, stop RDS, delete NAT
# Koristi se: bash scripts/eod-pause.sh [ENV]

set -euo pipefail

ENV=${1:-dev}
CLUSTER_NAME="project-a-$ENV"
NODEGROUP_NAME="project-a-$ENV-nodes"
DB_ID="project-a-$ENV"
REGION="eu-west-1"

echo "=== EOD PAUSE: $ENV ==="
echo "Time: $(date)"
echo ""

# ─── KORAK 1: Scale down EKS nodes ───────────────────────────────────────
echo "[1/4] Scaling down EKS nodes to 0..."

aws eks update-nodegroup-config \
  --cluster-name "$CLUSTER_NAME" \
  --nodegroup-name "$NODEGROUP_NAME" \
  --scaling-config minSize=0,maxSize=3,desiredSize=0 \
  --region "$REGION"

echo "  Waiting for nodes to be terminated (2-5 min)..."

# Čekaj da desired dostigne 0 (not waiting for nodegroup-active jer to ostaje active)
WAIT_SECS=0
MAX_WAIT=300

while true; do
  CURRENT=$(aws ec2 describe-instances \
    --filters \
      "Name=tag:kubernetes.io/cluster/$CLUSTER_NAME,Values=owned" \
      "Name=instance-state-name,Values=running,pending,stopping" \
    --query 'length(Reservations[*].Instances[*])' \
    --output text 2>/dev/null || echo "0")

  [ "$CURRENT" = "0" ] && echo "  ✓ All nodes terminated" && break

  if [ "$WAIT_SECS" -ge "$MAX_WAIT" ]; then
    echo "  WARNING: Nodes still running after ${MAX_WAIT}s. Proceeding."
    break
  fi

  echo "  Nodes still running: $CURRENT. Waiting... (${WAIT_SECS}s/${MAX_WAIT}s)"
  sleep 20
  WAIT_SECS=$((WAIT_SECS + 20))
done

# ─── KORAK 2: Stop RDS ────────────────────────────────────────────────────
echo "[2/4] Stopping RDS..."

DB_STATUS=$(aws rds describe-db-instances \
  --db-instance-identifier "$DB_ID" \
  --query 'DBInstances[0].DBInstanceStatus' \
  --output text 2>/dev/null || echo "not-found")

if [ "$DB_STATUS" = "available" ]; then
  aws rds stop-db-instance --db-instance-identifier "$DB_ID" > /dev/null
  echo "  RDS stop initiated. (Will be confirmed in background)"
  echo "  ✓ RDS stopping"
elif [ "$DB_STATUS" = "stopped" ]; then
  echo "  - RDS already stopped"
elif [ "$DB_STATUS" = "not-found" ]; then
  echo "  - RDS not found, skipping"
else
  echo "  WARNING: RDS status is '$DB_STATUS', cannot stop now"
fi

# ─── KORAK 3: Delete NAT Gateway ──────────────────────────────────────────
echo "[3/4] Deleting NAT Gateway..."

NAT_ID=$(aws ec2 describe-nat-gateways \
  --filter \
    "Name=tag:Environment,Values=$ENV" \
    "Name=state,Values=available" \
  --query 'NatGateways[0].NatGatewayId' \
  --output text 2>/dev/null || echo "None")

if [ "$NAT_ID" = "None" ] || [ -z "$NAT_ID" ]; then
  echo "  - NAT Gateway not found or already deleted"
else
  # Spremi Elastic IP za release
  EIP_ALLOC=$(aws ec2 describe-nat-gateways \
    --nat-gateway-ids "$NAT_ID" \
    --query 'NatGateways[0].NatGatewayAddresses[0].AllocationId' \
    --output text)

  aws ec2 delete-nat-gateway --nat-gateway-id "$NAT_ID" > /dev/null
  echo "  Waiting for NAT Gateway deletion..."
  aws ec2 wait nat-gateway-deleted --nat-gateway-ids "$NAT_ID"

  # Release Elastic IP (otherwise $0.005/h = $3.60/mj za nekorišćen EIP)
  if [ -n "$EIP_ALLOC" ] && [ "$EIP_ALLOC" != "None" ]; then
    aws ec2 release-address --allocation-id "$EIP_ALLOC"
    echo "  ✓ NAT Gateway deleted, Elastic IP released"
  else
    echo "  ✓ NAT Gateway deleted"
  fi
fi

# ─── KORAK 4: Trošak estimate ─────────────────────────────────────────────
echo "[4/4] Cost summary..."
echo ""
echo "=== EOD PAUSE COMPLETE: $ENV ==="
echo "Active (costing money):"
echo "  EKS Control Plane: \$0.10/h = \$0.80 overnight (8h)"
echo "  RDS storage (stopped): ~\$0.003/overnight"
echo ""
echo "Saved vs leaving up:"
echo "  EKS Nodes (2×): \$0.094/h × 8h = \$0.75"
echo "  NAT Gateway:    \$0.045/h × 8h = \$0.36"
echo "  ALB:            \$0.022/h × 8h = \$0.18"
echo "  Total saved:   ~\$1.29 overnight, ~\$3.87 (full day)"
echo ""
echo "To resume tomorrow: bash scripts/morning-start.sh $ENV"
```

---

## Morning Start Skripta

```bash
#!/bin/bash
# scripts/morning-start.sh
# Koristi se: bash scripts/morning-start.sh [ENV]

set -euo pipefail

ENV=${1:-dev}
CLUSTER_NAME="project-a-$ENV"
NODEGROUP_NAME="project-a-$ENV-nodes"
DB_ID="project-a-$ENV"
REGION="eu-west-1"

echo "=== MORNING START: $ENV ==="
echo "Time: $(date)"
echo ""

# ─── KORAK 1: Terraform apply za NAT i EIP ────────────────────────────────
echo "[1/4] Recreating NAT Gateway and Elastic IP..."

cd "terraform/envs/$ENV"
terraform init -input=false -no-color 2>&1 | tail -3

terraform apply \
  -target=module.vpc.aws_eip.nat \
  -target=module.vpc.aws_nat_gateway.main \
  -target=module.vpc.aws_route.private_nat_gateway \
  -var-file=$ENV.tfvars \
  -auto-approve \
  -no-color

echo "  ✓ NAT Gateway created"
cd - > /dev/null

# ─── KORAK 2: Start RDS ───────────────────────────────────────────────────
echo "[2/4] Starting RDS..."

DB_STATUS=$(aws rds describe-db-instances \
  --db-instance-identifier "$DB_ID" \
  --query 'DBInstances[0].DBInstanceStatus' \
  --output text 2>/dev/null || echo "not-found")

if [ "$DB_STATUS" = "stopped" ]; then
  aws rds start-db-instance --db-instance-identifier "$DB_ID" > /dev/null
  echo "  Waiting for RDS to be available (3-5 min)..."
  aws rds wait db-instance-available --db-instance-identifier "$DB_ID"

  DB_ENDPOINT=$(aws rds describe-db-instances \
    --db-instance-identifier "$DB_ID" \
    --query 'DBInstances[0].Endpoint.Address' \
    --output text)
  echo "  ✓ RDS available: $DB_ENDPOINT"

elif [ "$DB_STATUS" = "available" ]; then
  echo "  - RDS already running"
else
  echo "  WARNING: RDS status is '$DB_STATUS'"
fi

# ─── KORAK 3: Scale up EKS nodes ─────────────────────────────────────────
echo "[3/4] Scaling up EKS nodes..."

aws eks update-nodegroup-config \
  --cluster-name "$CLUSTER_NAME" \
  --nodegroup-name "$NODEGROUP_NAME" \
  --scaling-config minSize=1,maxSize=3,desiredSize=2 \
  --region "$REGION"

echo "  Waiting for nodes to be Ready..."

# Čekaj da kubectl vidi nodove kao Ready
WAIT_SECS=0
MAX_WAIT=600

until kubectl wait nodes --all --for=condition=Ready --timeout=30s &>/dev/null; do
  if [ "$WAIT_SECS" -ge "$MAX_WAIT" ]; then
    echo "  WARNING: Nodes not ready after ${MAX_WAIT}s"
    kubectl get nodes
    break
  fi
  echo "  Waiting for nodes... (${WAIT_SECS}s/${MAX_WAIT}s)"
  sleep 30
  WAIT_SECS=$((WAIT_SECS + 30))
done

NODE_COUNT=$(kubectl get nodes --no-headers 2>/dev/null | grep -c " Ready " || echo "0")
echo "  ✓ Nodes ready: $NODE_COUNT"

# ─── KORAK 4: URL-ovi (ALB je ostao, Ingress resursi su ostali) ───────────
echo "[4/4] Fetching URLs..."
echo "  Note: ALB may need 1-2 minutes to pass health checks after nodes come up"
echo ""
bash scripts/get-urls.sh "$ENV"
echo ""
echo "=== MORNING START COMPLETE ==="
echo "Ready to work!"
```

---

## Terraform Modul: Nodegrupa sa Scale-Down Podrškom

NAT Gateway se briše ručno u EOD skripti, ali mora biti moguće re-kreirati ga
targetiranim `terraform apply`. Provjeri da tvoj VPC modul podržava ovo:

```hcl
# terraform/modules/vpc/nat.tf
# NAT Gateway i EIP moraju biti zasebni resursi (ne inline u vpc resource)
# da bi -target radio precizno.

resource "aws_eip" "nat" {
  domain = "vpc"

  tags = {
    Name        = "project-a-${var.env}-nat-eip"
    Environment = var.env
    Project     = "project-a"
  }

  lifecycle {
    # Sprečava destroy EIP-a ako ga NAT Gateway još koristi
    create_before_destroy = true
  }
}

resource "aws_nat_gateway" "main" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public[0].id

  tags = {
    Name        = "project-a-${var.env}-nat"
    Environment = var.env
    Project     = "project-a"
  }

  depends_on = [aws_internet_gateway.main]
}

resource "aws_route" "private_nat_gateway" {
  count = length(aws_subnet.private)

  route_table_id         = aws_route_table.private[count.index].id
  destination_cidr_block = "0.0.0.0/0"
  nat_gateway_id         = aws_nat_gateway.main.id
}
```

```hcl
# terraform/modules/eks/nodegroup.tf
# Nodegroup min_size mora podržavati 0 za scale-down

resource "aws_eks_node_group" "main" {
  cluster_name    = aws_eks_cluster.main.name
  node_group_name = "project-a-${var.env}-nodes"
  node_role_arn   = aws_iam_role.node.arn
  subnet_ids      = var.private_subnet_ids

  scaling_config {
    min_size     = 0  # Mora biti 0 za EOD scale-down
    max_size     = var.node_max_size
    desired_size = var.node_desired_size
  }

  instance_types = [var.node_instance_type]

  # Lifecycle ignorira desired_size jer ga mijenjamo aws CLI-jem
  lifecycle {
    ignore_changes = [scaling_config[0].desired_size]
  }

  tags = {
    Environment = var.env
    Project     = "project-a"
  }
}
```

---

## Trošak Usporedba: Strategije za Tim od 3 Developera

```
Scenario: 3 developera, dev + staging, 5 dana × 8h tjedno

OPCIJA A — Leave running 24/7:
  Dev:     $7.12/dan × 30d = $213.60/mj
  Staging: $7.12/dan × 30d = $213.60/mj
  Ukupno: ~$427/mj

OPCIJA B — EOD pause (nodes + NAT, zadrži control plane):
  Dev:     $0.10/h EKS × 24h × 30d + $2.37 × 22 radna dana
           = $72 + $52 = $124/mj
  Staging: isto = ~$124/mj
  Ukupno: ~$248/mj  (uštednja: $179/mj = ~$2,148/godišnje)

OPCIJA C — Total destroy svaki dan:
  Dev:     $2.37 × 22 radna dana = $52/mj
  Staging: $2.37 × 22 radna dana = $52/mj
  Ukupno: ~$104/mj  (uštednja: $323/mj = ~$3,876/godišnje)
  Mana:   +10 min za recreate svako jutro = 22 × 10 min = 3.7h/mj "izgubljeno"

OPCIJA D (optimalna za tim) — EOD pause dev, total destroy staging:
  Dev:     ~$124/mj (brži resume, aktivno korišten)
  Staging: ~$52/mj  (destroy/recreate pri potrebi)
  Ukupno: ~$176/mj  (uštednja: $251/mj = ~$3,012/godišnje)
```
