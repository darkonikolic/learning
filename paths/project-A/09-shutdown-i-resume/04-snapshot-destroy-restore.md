# 04 — Snapshot + Destroy + Restore

**Kada koristiti:** Produkcijsko okruženje, duža pauza (sedmica, mjesec).
Potpuno $0 osim snapshot storage-a (~$0.46/mj za 20GB).

---

## Princip

```
PAUSE:
  1. RDS snapshot (podaci su sigurni)
  2. Helm uninstall (K8s resursi, ALB)
  3. terraform destroy (sva infrastruktura)
  → Trošak: $0/h

RESUME:
  1. terraform apply sa snapshot_identifier
  2. Helm install (K8s resursi, ALB)
  3. App radi sa svim podacima
  → Trošak: normalan
```

---

## Terraform: Podrška za Snapshot Restore

### Modul: RDS sa snapshot podrškom

```hcl
# terraform/modules/rds/variables.tf
variable "snapshot_identifier" {
  type        = string
  default     = ""
  description = "RDS snapshot identifier. Empty = create fresh DB. Non-empty = restore from snapshot."
}

variable "db_name" {
  type        = string
  description = "Database name. Ignored when restoring from snapshot."
}

variable "db_username" {
  type        = string
  description = "Master username"
}

variable "db_password" {
  type        = string
  sensitive   = true
  description = "Master password. When restoring from snapshot, this RESETS the password."
}

variable "db_instance_class" {
  type    = string
  default = "db.t3.micro"
}

variable "allocated_storage" {
  type    = number
  default = 20
}

variable "skip_final_snapshot" {
  type    = bool
  default = false
  description = "Set true for dev/staging. Never true for prod."
}

variable "final_snapshot_identifier" {
  type    = string
  default = ""
  description = "Identifier for final snapshot on destroy. Required if skip_final_snapshot = false."
}
```

```hcl
# terraform/modules/rds/main.tf
resource "aws_db_instance" "main" {
  identifier = "project-a-${var.env}"

  # Engine
  engine         = "mysql"
  engine_version = "8.0"
  instance_class = var.db_instance_class

  # Storage
  allocated_storage     = var.allocated_storage
  max_allocated_storage = var.allocated_storage * 3
  storage_type          = "gp3"
  storage_encrypted     = true

  # Credentials
  db_name  = var.snapshot_identifier == "" ? var.db_name : null
  username = var.db_username
  password = var.db_password

  # Snapshot restore:
  # Ako je snapshot_identifier popunjen, RDS kreira instancu sa podacima iz snapshot-a.
  # db_name se ignorira (preuzima se iz snapshot-a).
  # password se primjenjuje na master usera — ovo je jedini način da reset-uješ password
  # koji je bio u snapshot-u.
  snapshot_identifier = var.snapshot_identifier != "" ? var.snapshot_identifier : null

  # Network
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible    = false

  # Backup
  backup_retention_period = var.env == "prod" ? 7 : 1
  backup_window           = "03:00-04:00"
  maintenance_window      = "sun:04:00-sun:05:00"

  # Destroy behaviour
  skip_final_snapshot       = var.skip_final_snapshot
  final_snapshot_identifier = var.skip_final_snapshot ? null : coalesce(
    var.final_snapshot_identifier,
    "project-a-${var.env}-final-${formatdate("YYYYMMDDhhmm", timestamp())}"
  )
  delete_automated_backups = var.env != "prod"

  # Performance Insights (gratis za db.t3.micro)
  performance_insights_enabled = false

  tags = {
    Environment = var.env
    Project     = "project-a"
  }

  lifecycle {
    # Sprečava da Terraform pokušava promijeniti snapshot_identifier na prazno
    # nakon što je restore završen — inače bi to triggerovalo replace.
    ignore_changes = [snapshot_identifier]
  }
}

resource "aws_db_subnet_group" "main" {
  name       = "project-a-${var.env}"
  subnet_ids = var.private_subnet_ids

  tags = {
    Environment = var.env
    Project     = "project-a"
  }
}
```

### Tfvars primjer

```hcl
# terraform/envs/prod/prod.tfvars

# ─── Normalno kreiranje ──────────────────────────
snapshot_identifier = ""
db_name             = "projecta"
db_username         = "admin"
# db_password je u Secrets Manager / environment varijabli, ne ovdje

# ─── Restore iz snapshota ────────────────────────
# snapshot_identifier = "project-a-prod-20240315-2200"
# db_name se ignorira pri restore-u
# db_username ostaje isti (preuzima se iz snapshot-a)
# db_password RESETUJE password na master useru

# ─── Destroy settings ────────────────────────────
skip_final_snapshot       = false
final_snapshot_identifier = ""  # Prazno = auto-generiše ime

# ─── Dev/Staging (brzi destroy) ─────────────────
# skip_final_snapshot = true
```

---

## Prod Pause Skripta

```bash
#!/bin/bash
# scripts/prod-pause.sh

set -euo pipefail

ENV="prod"
REGION="eu-west-1"
SNAPSHOT_ID="project-a-prod-$(date +%Y%m%d-%H%M)"
SNAPSHOT_FILE=".last-prod-snapshot"

echo "=== PROD PAUSE WORKFLOW ==="
echo "Snapshot ID: $SNAPSHOT_ID"
echo ""

# ─── KORAK 1: Provjeri da je app zdrava prije snapshot-a ──────────────────
echo "[1/6] Pre-pause health check..."
if kubectl cluster-info &>/dev/null; then
  RUNNING=$(kubectl get pods -n "project-a-$ENV" \
    --field-selector=status.phase=Running \
    --no-headers 2>/dev/null | wc -l)
  echo "  Running pods: $RUNNING"
  [ "$RUNNING" -eq 0 ] && echo "  WARNING: No running pods" || echo "  ✓ Pods OK"
else
  echo "  WARNING: K8s not accessible, skipping pod check"
fi

# ─── KORAK 2: RDS Snapshot ────────────────────────────────────────────────
echo "[2/6] Creating RDS snapshot..."
aws rds create-db-snapshot \
  --db-instance-identifier "project-a-$ENV" \
  --db-snapshot-identifier "$SNAPSHOT_ID" \
  --tags Key=Environment,Value=$ENV Key=Project,Value=project-a \
  --output table

echo "  Waiting for snapshot to complete (5-15 minutes)..."
aws rds wait db-snapshot-completed \
  --db-snapshot-identifier "$SNAPSHOT_ID"

SNAPSHOT_SIZE=$(aws rds describe-db-snapshots \
  --db-snapshot-identifier "$SNAPSHOT_ID" \
  --query 'DBSnapshots[0].AllocatedStorage' \
  --output text)
echo "  ✓ Snapshot created: $SNAPSHOT_ID (${SNAPSHOT_SIZE}GB)"

# ─── KORAK 3: Spremi snapshot ID ──────────────────────────────────────────
echo "[3/6] Saving snapshot ID..."
echo "$SNAPSHOT_ID" > "$SNAPSHOT_FILE"

if git rev-parse --is-inside-work-tree &>/dev/null; then
  git add "$SNAPSHOT_FILE"
  git commit -m "ops: save prod snapshot $SNAPSHOT_ID"
  git push origin main
  echo "  ✓ Snapshot ID committed to git"
else
  echo "  ✓ Snapshot ID saved to $SNAPSHOT_FILE"
  echo "  WARNING: Not in git repo — backup this file manually"
fi

# ─── KORAK 4: Helm uninstall ──────────────────────────────────────────────
echo "[4/6] Uninstalling Helm releases..."
if kubectl cluster-info &>/dev/null; then
  helm uninstall project-a -n "project-a-$ENV" 2>/dev/null && echo "  ✓ project-a" || echo "  - project-a not found"
  helm uninstall monitoring -n monitoring 2>/dev/null && echo "  ✓ monitoring" || echo "  - monitoring not found"
  helm uninstall aws-load-balancer-controller -n kube-system 2>/dev/null && echo "  ✓ alb-controller" || echo "  - alb-controller not found"

  echo "  Waiting for ALB deletion (up to 2 minutes)..."
  for i in $(seq 1 8); do
    ALB_COUNT=$(aws elbv2 describe-load-balancers \
      --query "length(LoadBalancers[?contains(LoadBalancerName,'project-a')])" \
      --output text 2>/dev/null || echo "0")
    [ "$ALB_COUNT" = "0" ] && echo "  ✓ ALB deleted" && break
    [ "$i" = "8" ] && echo "  WARNING: ALB still active, proceeding anyway"
    sleep 15
  done
else
  echo "  WARNING: K8s not accessible, skipping Helm uninstall"
fi

# ─── KORAK 5: Terraform destroy ───────────────────────────────────────────
echo "[5/6] Destroying infrastructure..."
cd "terraform/envs/$ENV"
terraform init -input=false -no-color 2>&1 | tail -3
terraform destroy -var-file=$ENV.tfvars -auto-approve -no-color
echo "  ✓ Terraform destroy completed"

# ─── KORAK 6: Verifikacija ────────────────────────────────────────────────
echo "[6/6] Verifying..."

EKS_EXISTS=$(aws eks list-clusters \
  --query "clusters[?contains(@,'project-a-$ENV')]" \
  --output text 2>/dev/null)
[ -n "$EKS_EXISTS" ] && echo "  WARNING: EKS still exists" || echo "  ✓ EKS deleted"

VPC_EXISTS=$(aws ec2 describe-vpcs \
  --filters "Name=tag:Environment,Values=$ENV" \
  --query 'Vpcs[*].VpcId' \
  --output text 2>/dev/null)
[ -n "$VPC_EXISTS" ] && echo "  WARNING: VPC still exists: $VPC_EXISTS" || echo "  ✓ VPC deleted"

echo ""
echo "=== PROD PAUSED ==="
echo "Snapshot:     $SNAPSHOT_ID"
SNAPSHOT_COST=$(echo "scale=2; $SNAPSHOT_SIZE * 0.023" | bc 2>/dev/null || echo "~\$0.46")
echo "Monthly cost: \$$SNAPSHOT_COST (snapshot storage)"
echo ""
echo "To resume: bash scripts/prod-resume.sh $SNAPSHOT_ID"
echo "           or: bash scripts/prod-resume.sh  (reads from $SNAPSHOT_FILE)"
```

---

## Prod Resume Skripta

```bash
#!/bin/bash
# scripts/prod-resume.sh
# Koristi se: bash scripts/prod-resume.sh [SNAPSHOT_ID]

set -euo pipefail

ENV="prod"
REGION="eu-west-1"
SNAPSHOT_FILE=".last-prod-snapshot"

# Odredi snapshot ID
SNAPSHOT_ID=${1:-}
if [ -z "$SNAPSHOT_ID" ]; then
  if [ -f "$SNAPSHOT_FILE" ]; then
    SNAPSHOT_ID=$(cat "$SNAPSHOT_FILE")
    echo "Using snapshot from $SNAPSHOT_FILE: $SNAPSHOT_ID"
  else
    echo "ERROR: No snapshot ID provided and $SNAPSHOT_FILE not found."
    echo "Usage: $0 project-a-prod-20240315-2200"
    echo ""
    echo "Available snapshots:"
    aws rds describe-db-snapshots \
      --query "DBSnapshots[?contains(DBSnapshotIdentifier,'project-a-prod')].{ID:DBSnapshotIdentifier,Date:SnapshotCreateTime,Size:AllocatedStorage}" \
      --output table
    exit 1
  fi
fi

# Provjeri da snapshot postoji
echo "Verifying snapshot: $SNAPSHOT_ID"
SNAP_STATUS=$(aws rds describe-db-snapshots \
  --db-snapshot-identifier "$SNAPSHOT_ID" \
  --query 'DBSnapshots[0].Status' \
  --output text 2>/dev/null || echo "not-found")

if [ "$SNAP_STATUS" != "available" ]; then
  echo "ERROR: Snapshot '$SNAPSHOT_ID' not found or status is '$SNAP_STATUS'"
  exit 1
fi
echo "  ✓ Snapshot available"

echo ""
echo "=== PROD RESUME ==="
echo "Restoring from: $SNAPSHOT_ID"

# ─── KORAK 1: Postavi snapshot_identifier u tfvars ────────────────────────
echo "[1/7] Setting snapshot_identifier in tfvars..."
TFVARS="terraform/envs/$ENV/$ENV.tfvars"

# Backup tfvars
cp "$TFVARS" "$TFVARS.bak"

# Postavi snapshot identifier
sed -i.tmp "s|snapshot_identifier.*=.*|snapshot_identifier = \"$SNAPSHOT_ID\"|" "$TFVARS"
rm -f "$TFVARS.tmp"

grep "snapshot_identifier" "$TFVARS"
echo "  ✓ tfvars updated"

# ─── KORAK 2: Terraform apply ─────────────────────────────────────────────
echo "[2/7] Applying Terraform (restore from snapshot)..."
cd "terraform/envs/$ENV"
terraform init -input=false -no-color 2>&1 | tail -3
terraform apply -var-file=$ENV.tfvars -auto-approve -no-color
echo "  ✓ Infrastructure created"

# ─── KORAK 3: Kubeconfig ──────────────────────────────────────────────────
echo "[3/7] Configuring kubectl..."
aws eks update-kubeconfig \
  --name "project-a-$ENV" \
  --region "$REGION" \
  --alias "$ENV"
kubectl config use-context "$ENV"
echo "  ✓ kubectl configured"

# ─── KORAK 4: ALB Controller ──────────────────────────────────────────────
echo "[4/7] Installing AWS Load Balancer Controller..."
ALB_ROLE_ARN=$(terraform output -raw alb_controller_role_arn)

helm repo add eks https://aws.github.io/eks-charts 2>/dev/null || true
helm repo update eks

helm upgrade --install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName="project-a-$ENV" \
  --set serviceAccount.create=true \
  --set "serviceAccount.annotations.eks\.amazonaws\.com/role-arn=$ALB_ROLE_ARN" \
  --wait --timeout=5m

echo "  ✓ ALB Controller installed"

# ─── KORAK 5: Deploy app sa posljednjim production tag-om ─────────────────
echo "[5/7] Deploying application..."

LAST_TAG=$(aws ecr describe-images \
  --repository-name "project-a/go-service" \
  --region "$REGION" \
  --query 'sort_by(imageDetails,&imagePushedAt)[-1].imageTags[0]' \
  --output text 2>/dev/null || echo "latest")

echo "  Using image tag: $LAST_TAG"

helm upgrade --install project-a ./helm/project-a \
  -n "project-a-$ENV" --create-namespace \
  -f "helm/project-a/values/$ENV.yaml" \
  --set image.tag="$LAST_TAG" \
  --wait --timeout=10m

echo "  ✓ Application deployed"

# ─── KORAK 6: Health check ────────────────────────────────────────────────
echo "[6/7] Verifying deployment health..."

kubectl rollout status deployment/go-service  -n "project-a-$ENV" --timeout=5m
kubectl rollout status deployment/php-service -n "project-a-$ENV" --timeout=5m

RUNNING=$(kubectl get pods -n "project-a-$ENV" \
  --field-selector=status.phase=Running \
  --no-headers | wc -l)
echo "  Running pods: $RUNNING"

# ─── KORAK 7: Obrisi snapshot_identifier iz tfvars ────────────────────────
echo "[7/7] Cleaning up tfvars..."
cd - > /dev/null
sed -i.tmp 's|snapshot_identifier.*=.*|snapshot_identifier = ""|' "$TFVARS"
rm -f "$TFVARS.tmp" "$TFVARS.bak"
echo "  ✓ snapshot_identifier cleared (next apply creates fresh DB)"

# Finalni URL output
echo ""
bash scripts/get-urls.sh "$ENV"
echo ""
echo "=== RESUME COMPLETE ==="
echo "All data restored from snapshot: $SNAPSHOT_ID"
```

---

## Snapshot Upravljanje

```bash
# Lista svih snapshota za project-a
aws rds describe-db-snapshots \
  --query "DBSnapshots[?contains(DBSnapshotIdentifier,'project-a')].{
    ID:DBSnapshotIdentifier,
    Date:SnapshotCreateTime,
    Status:Status,
    SizeGB:AllocatedStorage
  }" \
  --output table

# Obrisi stari snapshot (uštedjeti novac)
aws rds delete-db-snapshot \
  --db-snapshot-identifier project-a-prod-20240115-1800

# Troškovi snapshota
# $0.023/GB/mj za svaki GB koji PRELAZI veličinu baze
# Ako baza ima 20GB, snapshot od 20GB = ~$0.46/mj
# Ako čuvaš 3 snapshot-a od 20GB = ~$1.38/mj

# Preporučeno: čuvaj samo zadnja 2 snapshot-a
aws rds describe-db-snapshots \
  --query "sort_by(DBSnapshots[?contains(DBSnapshotIdentifier,'project-a-prod')],&SnapshotCreateTime)[*].DBSnapshotIdentifier" \
  --output text
# Obrisi sve osim posljednja 2
```
