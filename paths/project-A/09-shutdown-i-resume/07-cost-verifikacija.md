# 07 — Cost Verifikacija

Potvrdi da je sve ugašeno i da nema neočekivanih troškova.
Pokreni odmah nakon `terraform destroy` i svako jutro.

---

## Cost Check Skripta

```bash
#!/bin/bash
# scripts/cost-check.sh
# Koristi se: bash scripts/cost-check.sh [ENV]

set -euo pipefail

ENV=${1:-dev}
REGION="eu-west-1"

echo "=== ACTIVE RESOURCES: $ENV ==="
echo "Time: $(date)"
echo "Region: $REGION"
echo ""

# ─── EKS ──────────────────────────────────────────────────────────────────
echo "EKS Clusters:"
CLUSTERS=$(aws eks list-clusters \
  --query "clusters[?contains(@,'project-a')]" \
  --output json 2>/dev/null)

if [ "$CLUSTERS" = "[]" ] || [ -z "$CLUSTERS" ]; then
  echo "  None  ✓  (\$0/h)"
else
  echo "$CLUSTERS" | tr -d '[]"' | tr ',' '\n' | while read -r cluster; do
    [ -z "$cluster" ] && continue
    STATUS=$(aws eks describe-cluster --name "$cluster" \
      --query 'cluster.status' --output text 2>/dev/null || echo "unknown")
    echo "  $cluster  →  $STATUS  (ACTIVE: \$0.10/h = \$2.40/dan)"
  done
fi

# ─── EKS NODE GROUPS ──────────────────────────────────────────────────────
echo ""
echo "EC2 Instances (EKS nodes):"
INSTANCES=$(aws ec2 describe-instances \
  --filters \
    "Name=tag:kubernetes.io/cluster/project-a-$ENV,Values=owned" \
    "Name=instance-state-name,Values=running,pending" \
  --query 'Reservations[*].Instances[*].{ID:InstanceId,Type:InstanceType,State:State.Name}' \
  --output json 2>/dev/null)

if [ "$INSTANCES" = "[]" ] || [ -z "$INSTANCES" ]; then
  echo "  None  ✓  (\$0/h)"
else
  echo "$INSTANCES" | python3 -c "
import json, sys
data = json.load(sys.stdin)
costs = {'t3.micro': 0.0114, 't3.small': 0.023, 't3.medium': 0.047, 't3.large': 0.094}
for item in data:
    itype = item.get('Type', 'unknown')
    cost = costs.get(itype, 0)
    print(f'  {item[\"ID\"]}  {itype}  {item[\"State\"]}  (\${cost}/h)')
" 2>/dev/null || echo "$INSTANCES"
fi

# ─── RDS ──────────────────────────────────────────────────────────────────
echo ""
echo "RDS Instances:"
aws rds describe-db-instances \
  --query "DBInstances[?contains(DBInstanceIdentifier,'project-a')].{
    ID:DBInstanceIdentifier,
    Status:DBInstanceStatus,
    Class:DBInstanceClass,
    Storage:AllocatedStorage
  }" \
  --output table 2>/dev/null || echo "  None  ✓"

# ─── ElastiCache ──────────────────────────────────────────────────────────
echo ""
echo "ElastiCache:"
REDIS=$(aws elasticache describe-replication-groups \
  --query "ReplicationGroups[?contains(ReplicationGroupId,'project-a')].{
    ID:ReplicationGroupId,
    Status:Status
  }" \
  --output table 2>/dev/null)
[ -n "$REDIS" ] && echo "$REDIS" || echo "  None  ✓  (\$0/h)"

# ─── NAT Gateways ─────────────────────────────────────────────────────────
echo ""
echo "NAT Gateways:"
NATS=$(aws ec2 describe-nat-gateways \
  --filter \
    "Name=tag:Environment,Values=$ENV" \
    "Name=state,Values=available,pending" \
  --query 'NatGateways[*].{ID:NatGatewayId,State:State,Subnet:SubnetId}' \
  --output table 2>/dev/null)
if echo "$NATS" | grep -q "NatGateway"; then
  echo "$NATS"
  echo "  ACTIVE NAT Gateway: \$0.045/h = \$1.08/dan"
else
  echo "  None  ✓  (\$0/h)"
fi

# ─── Load Balancers ───────────────────────────────────────────────────────
echo ""
echo "Load Balancers:"
ALBS=$(aws elbv2 describe-load-balancers \
  --query "LoadBalancers[?contains(LoadBalancerName,'project-a')].{
    Name:LoadBalancerName,
    State:State.Code,
    Type:Type
  }" \
  --output table 2>/dev/null)
if echo "$ALBS" | grep -q "project-a"; then
  echo "$ALBS"
  echo "  ACTIVE ALB: \$0.022/h = \$0.53/dan"
else
  echo "  None  ✓  (\$0/h)"
fi

# ─── Elastic IPs ──────────────────────────────────────────────────────────
echo ""
echo "Unattached Elastic IPs (koštaju \$0.005/h ako nisu u upotrebi):"
EIPS=$(aws ec2 describe-addresses \
  --query "Addresses[?AssociationId==null && contains(Tags[?Key=='Environment'].Value|[0],'$ENV')].{
    IP:PublicIp,
    AllocationId:AllocationId
  }" \
  --output table 2>/dev/null)
if echo "$EIPS" | grep -q "\\."; then
  echo "$EIPS"
  echo "  WARNING: Unattached EIP costs \$0.005/h = \$3.60/mj each"
else
  echo "  None  ✓  (\$0/h)"
fi

# ─── VPC (samo informativno) ──────────────────────────────────────────────
echo ""
echo "VPCs:"
aws ec2 describe-vpcs \
  --filters "Name=tag:Environment,Values=$ENV" \
  --query 'Vpcs[*].{ID:VpcId,CIDR:CidrBlock}' \
  --output table 2>/dev/null || echo "  None  ✓"

# ─── Cost Explorer ────────────────────────────────────────────────────────
echo ""
echo "=== AWS COST: LAST 24H ==="
YESTERDAY=$(date -u -d "1 day ago" +%Y-%m-%d 2>/dev/null || date -u -v-1d +%Y-%m-%d)
TODAY=$(date -u +%Y-%m-%d)

COST=$(aws ce get-cost-and-usage \
  --time-period "Start=$YESTERDAY,End=$TODAY" \
  --granularity DAILY \
  --metrics UnblendedCost \
  --filter "{\"Tags\":{\"Key\":\"Environment\",\"Values\":[\"$ENV\"]}}" \
  --query 'ResultsByTime[0].Total.UnblendedCost.Amount' \
  --output text 2>/dev/null || echo "")

if [ -n "$COST" ] && [ "$COST" != "None" ]; then
  printf "Yesterday (%s): \$%.4f\n" "$YESTERDAY" "$COST"
else
  echo "Cost Explorer: Enable in AWS Console (Billing → Cost Explorer → Enable)"
  echo "Alternative: Check manually at https://console.aws.amazon.com/billing"
fi

# ─── Ukupna procjena ──────────────────────────────────────────────────────
echo ""
echo "=== HOURLY COST ESTIMATE ==="
TOTAL_PER_HOUR=0

# EKS clusters
EKS_COUNT=$(aws eks list-clusters \
  --query "length(clusters[?contains(@,'project-a')])" \
  --output text 2>/dev/null || echo "0")
if [ "$EKS_COUNT" -gt "0" ] 2>/dev/null; then
  echo "  EKS clusters ($EKS_COUNT): \$$(echo "$EKS_COUNT * 0.10" | bc)/h"
  TOTAL_PER_HOUR=$(echo "$TOTAL_PER_HOUR + $EKS_COUNT * 0.10" | bc)
fi

# EC2 nodes
EC2_COUNT=$(aws ec2 describe-instances \
  --filters \
    "Name=tag:kubernetes.io/cluster/project-a-$ENV,Values=owned" \
    "Name=instance-state-name,Values=running" \
  --query 'length(Reservations[*].Instances[*])' \
  --output text 2>/dev/null || echo "0")
if [ "$EC2_COUNT" -gt "0" ] 2>/dev/null; then
  echo "  EKS nodes ($EC2_COUNT × t3.medium): \$$(echo "$EC2_COUNT * 0.047" | bc)/h"
  TOTAL_PER_HOUR=$(echo "$TOTAL_PER_HOUR + $EC2_COUNT * 0.047" | bc)
fi

# NAT
NAT_COUNT=$(aws ec2 describe-nat-gateways \
  --filter "Name=tag:Environment,Values=$ENV" "Name=state,Values=available" \
  --query 'length(NatGateways)' \
  --output text 2>/dev/null || echo "0")
if [ "$NAT_COUNT" -gt "0" ] 2>/dev/null; then
  echo "  NAT Gateways ($NAT_COUNT): \$$(echo "$NAT_COUNT * 0.045" | bc)/h"
  TOTAL_PER_HOUR=$(echo "$TOTAL_PER_HOUR + $NAT_COUNT * 0.045" | bc)
fi

if [ "$TOTAL_PER_HOUR" = "0" ]; then
  echo "  Total: \$0/h  ✓  Environment is off"
else
  DAILY=$(echo "$TOTAL_PER_HOUR * 24" | bc)
  MONTHLY=$(echo "$TOTAL_PER_HOUR * 24 * 30" | bc)
  printf "  ─────────────────────────────────────\n"
  printf "  Hourly:  \$%.3f/h\n" "$TOTAL_PER_HOUR"
  printf "  Daily:   \$%.2f/dan\n" "$DAILY"
  printf "  Monthly: \$%.2f/mj\n" "$MONTHLY"
fi
echo "========================================="
```

---

## AWS Budget Alert (Terraform)

Postavi PRIJE nego pokreneš bilo koji environment. Ovo je sigurnosna mreža.

```hcl
# terraform/modules/budgets/main.tf

variable "monthly_limit_usd" {
  type    = number
  default = 50
}

variable "alert_email" {
  type        = string
  description = "Email adresa za cost alerts"
}

variable "project" {
  type    = string
  default = "project-a"
}

# ─── Monthly Budget ────────────────────────────────────────────────────────
resource "aws_budgets_budget" "monthly" {
  name              = "${var.project}-monthly-budget"
  budget_type       = "COST"
  limit_amount      = tostring(var.monthly_limit_usd)
  limit_unit        = "USD"
  time_unit         = "MONTHLY"
  time_period_start = "2024-01-01_00:00"

  # Alert na 80% — upozorenje, akcija nije potrebna odmah
  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 80
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.alert_email]
  }

  # Alert na 100% — AKCIJA: provjeri što je upaljeno i ugasi
  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.alert_email]
  }

  # Forecast alert na 90% — upozorenje da si na putu da premasiš
  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 90
    threshold_type             = "PERCENTAGE"
    notification_type          = "FORECASTED"
    subscriber_email_addresses = [var.alert_email]
  }

  tags = {
    Project = var.project
  }
}

# ─── Cost Anomaly Detection ────────────────────────────────────────────────
resource "aws_ce_anomaly_monitor" "main" {
  name              = "${var.project}-anomaly-monitor"
  monitor_type      = "DIMENSIONAL"
  monitor_dimension = "SERVICE"
}

resource "aws_ce_anomaly_subscription" "main" {
  name      = "${var.project}-anomaly-alert"
  frequency = "DAILY"

  # Alert ako dnevni trošak premaši threshold
  threshold_expression {
    dimension {
      key           = "ANOMALY_TOTAL_IMPACT_ABSOLUTE"
      values        = ["5"]
      match_options = ["GREATER_THAN_OR_EQUAL"]
    }
  }

  monitor_arn_list = [aws_ce_anomaly_monitor.main.arn]

  subscriber {
    type    = "EMAIL"
    address = var.alert_email
  }
}

# Output za provjeru
output "budget_name" {
  value = aws_budgets_budget.monthly.name
}

output "monthly_limit" {
  value = "${var.monthly_limit_usd} USD"
}
```

### Poziv modula u root modulu

```hcl
# terraform/envs/dev/main.tf
module "budgets" {
  source = "../../modules/budgets"

  monthly_limit_usd = 50
  alert_email       = var.alert_email
  project           = "project-a"
}

# terraform/envs/dev/dev.tfvars
alert_email = "darko@example.com"
```

---

## Post-Destroy Verifikacija: Checklist

Pokreni odmah nakon `terraform destroy`:

```bash
# Skraćena provjera (za svakodnevnu upotrebu)
bash scripts/cost-check.sh dev

# Očekivani output kada je sve čisto:
# EKS Clusters:             None  ✓  ($0/h)
# EC2 Instances (nodes):    None  ✓  ($0/h)
# RDS Instances:            (prazno)
# NAT Gateways:             None  ✓  ($0/h)
# Load Balancers:           None  ✓  ($0/h)
# Unattached Elastic IPs:   None  ✓  ($0/h)
# Total: $0/h  ✓  Environment is off
```

### Ako nešto ostane nakon destroy

```bash
# Provjeri terraform state — možda je resource izvan statea
terraform state list

# Pokušaj targeted destroy za orphan resource
terraform destroy -target=aws_eks_cluster.main -var-file=dev.tfvars -auto-approve

# Ako nije u state — obriši ručno i uvezi ili zaboravi
# Primjer: orphan ALB
aws elbv2 delete-load-balancer \
  --load-balancer-arn arn:aws:elasticloadbalancing:eu-west-1:123456789:loadbalancer/app/project-a/abc123

# Primjer: orphan NAT Gateway
aws ec2 delete-nat-gateway --nat-gateway-id nat-xxxxxxxxx
aws ec2 wait nat-gateway-deleted --nat-gateway-ids nat-xxxxxxxxx
aws ec2 release-address --allocation-id eipalloc-xxxxxxxxx  # Oslobodi EIP
```

---

## Brzi Reference: Troškovi po Satu

```
Resurs                    $/h       $/dan(24h)   $/mj(30d)
─────────────────────────────────────────────────────────
EKS Control Plane         0.100     2.40         72.00
EKS Node t3.micro         0.011     0.27          8.03
EKS Node t3.small         0.023     0.55         16.56
EKS Node t3.medium        0.047     1.13         33.84
EKS Node t3.large         0.094     2.26         67.68
RDS db.t3.micro           0.034     0.82         24.48
RDS db.t3.small           0.068     1.63         48.96
NAT Gateway               0.045     1.08         32.40
  + data transfer         0.045/GB  —            —
ALB (LCU included)       ~0.022    ~0.53        ~15.84
ElastiCache cache.t3.micro 0.017   0.41         12.24
────────────────────────────────────────────────────────
Project-A base (2 nodes)  ~0.297   ~7.13       ~213.84
Project-A 8h active work  ~0.297×8 ~2.38/day   ~52/mj aktiv
```

**Memorijska tehnika za procjenu:**
- EKS control plane = $0.10/h = kafa svaki sat
- t3.medium node = $0.047/h ≈ $1.13/dan
- NAT Gateway = $0.045/h ≈ $1.08/dan — uvijek ga obriši na kraju
- RDS t3.micro = $0.034/h ≈ $0.82/dan — stopped je gotovo besplatno
