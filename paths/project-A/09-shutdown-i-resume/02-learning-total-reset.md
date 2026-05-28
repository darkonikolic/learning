# 02 — Learning Mode: Total Reset

Kompletan workflow za learning okruženje — od nule do nule.
Nema podataka koje trebaš čuvati. `terraform destroy` je norma, ne iznimka.

---

## Pre-Destroy Checklist

Provjeri što postoji prije nego kreneš uništavati:

```bash
# 1. Kubernetes resursi
kubectl get all -n project-a-dev 2>/dev/null || echo "No K8s resources / cluster not accessible"

# 2. RDS instance
aws rds describe-db-instances \
  --query 'DBInstances[*].[DBInstanceIdentifier,DBInstanceStatus]' \
  --output table

# 3. EKS cluster
aws eks list-clusters --output table

# 4. Load Balancers
aws elbv2 describe-load-balancers \
  --query 'LoadBalancers[*].[LoadBalancerName,State.Code]' \
  --output table

# 5. Terraform state
cd terraform/envs/dev
terraform state list | wc -l
echo "Resources in state"
```

---

## Destroy Redosljed

Redosljed je kritičan. Pogrešan redosljed = orphan resursi koji blokiraju ili koštaju.

```bash
#!/bin/bash
# scripts/total-destroy.sh
# Koristi se: bash scripts/total-destroy.sh [ENV]

set -euo pipefail

ENV=${1:-dev}
NAMESPACE="project-a-$ENV"
CLUSTER_NAME="project-a-$ENV"
REGION="eu-west-1"

echo "=== TOTAL DESTROY: $ENV ==="
echo "Namespace: $NAMESPACE"
echo "Cluster:   $CLUSTER_NAME"
echo ""

# ─── KORAK 1: Uninstall Helm releases ─────────────────────────────────────
# ALB se briše automatski kad se Ingress resource obriše (ALB Controller to radi)
echo "[1/4] Uninstalling Helm releases..."

helm uninstall project-a       -n "$NAMESPACE"   2>/dev/null && echo "  ✓ project-a uninstalled"       || echo "  - project-a not found"
helm uninstall monitoring      -n monitoring      2>/dev/null && echo "  ✓ monitoring uninstalled"      || echo "  - monitoring not found"
helm uninstall aws-load-balancer-controller \
                               -n kube-system     2>/dev/null && echo "  ✓ alb-controller uninstalled"  || echo "  - alb-controller not found"

# ─── KORAK 2: Čekaj da ALB nestane ────────────────────────────────────────
echo "[2/4] Waiting for ALB to be deleted (up to 3 minutes)..."

WAIT_SECS=0
MAX_WAIT=180

while true; do
  ALB_COUNT=$(aws elbv2 describe-load-balancers \
    --query "length(LoadBalancers[?contains(LoadBalancerName,'$ENV')])" \
    --output text 2>/dev/null || echo "0")

  if [ "$ALB_COUNT" = "0" ] || [ "$ALB_COUNT" = "None" ]; then
    echo "  ✓ ALB deleted"
    break
  fi

  if [ "$WAIT_SECS" -ge "$MAX_WAIT" ]; then
    echo "  WARNING: ALB still exists after ${MAX_WAIT}s. Proceeding anyway."
    echo "  You may need to delete Ingress resources manually."
    break
  fi

  echo "  ALB still active ($ALB_COUNT). Waiting... (${WAIT_SECS}s/${MAX_WAIT}s)"
  sleep 15
  WAIT_SECS=$((WAIT_SECS + 15))
done

# ─── KORAK 3: Terraform destroy ───────────────────────────────────────────
echo "[3/4] Running terraform destroy..."

cd terraform/envs/$ENV
terraform init -input=false -no-color 2>&1 | tail -3

terraform destroy \
  -var-file=$ENV.tfvars \
  -auto-approve \
  -no-color

echo "  ✓ Terraform destroy completed"

# ─── KORAK 4: Post-destroy verifikacija ───────────────────────────────────
echo "[4/4] Post-destroy verification..."
echo ""
echo "=== POST-DESTROY VERIFICATION: $ENV ==="

# EKS
EKS_EXISTS=$(aws eks list-clusters \
  --query "clusters[?contains(@,'project-a-$ENV')]" \
  --output text 2>/dev/null)
[ -n "$EKS_EXISTS" ] \
  && echo "  WARNING: EKS cluster still exists: $EKS_EXISTS" \
  || echo "  ✓ EKS deleted"

# RDS
RDS_EXISTS=$(aws rds describe-db-instances \
  --query "DBInstances[?contains(DBInstanceIdentifier,'project-a-$ENV')].DBInstanceIdentifier" \
  --output text 2>/dev/null)
[ -n "$RDS_EXISTS" ] \
  && echo "  WARNING: RDS still exists: $RDS_EXISTS" \
  || echo "  ✓ RDS deleted"

# ALB
ALB_EXISTS=$(aws elbv2 describe-load-balancers \
  --query "LoadBalancers[?contains(LoadBalancerName,'$ENV')].LoadBalancerName" \
  --output text 2>/dev/null)
[ -n "$ALB_EXISTS" ] \
  && echo "  WARNING: ALB still exists: $ALB_EXISTS" \
  || echo "  ✓ ALB deleted"

# NAT Gateway
NAT_EXISTS=$(aws ec2 describe-nat-gateways \
  --filter "Name=tag:Environment,Values=$ENV" "Name=state,Values=available,pending,deleting" \
  --query 'NatGateways[*].NatGatewayId' \
  --output text 2>/dev/null)
[ -n "$NAT_EXISTS" ] \
  && echo "  WARNING: NAT Gateway still active: $NAT_EXISTS" \
  || echo "  ✓ NAT Gateway deleted"

# VPC
VPC_EXISTS=$(aws ec2 describe-vpcs \
  --filters "Name=tag:Environment,Values=$ENV" \
  --query 'Vpcs[*].VpcId' \
  --output text 2>/dev/null)
[ -n "$VPC_EXISTS" ] \
  && echo "  WARNING: VPC still exists: $VPC_EXISTS" \
  || echo "  ✓ VPC deleted"

echo "========================================="
echo ""
echo "Cost: \$0/h while destroyed."
echo "To recreate: bash scripts/recreate.sh $ENV"
```

---

## Recreate Workflow

```bash
#!/bin/bash
# scripts/recreate.sh
# Koristi se: bash scripts/recreate.sh [ENV]

set -euo pipefail

ENV=${1:-dev}
NAMESPACE="project-a-$ENV"
CLUSTER_NAME="project-a-$ENV"
REGION="eu-west-1"

echo "=== RECREATE: $ENV ==="

# ─── KORAK 1: Terraform apply ─────────────────────────────────────────────
echo "[1/6] Applying Terraform infrastructure..."
cd terraform/envs/$ENV
terraform init -input=false
terraform apply -var-file=$ENV.tfvars -auto-approve -no-color
echo "  ✓ Infrastructure created"

# ─── KORAK 2: Kubeconfig ──────────────────────────────────────────────────
echo "[2/6] Configuring kubectl..."
aws eks update-kubeconfig \
  --name "$CLUSTER_NAME" \
  --region "$REGION" \
  --alias "$ENV"

kubectl config use-context "$ENV"
echo "  ✓ kubectl configured"

# ─── KORAK 3: ALB Controller ──────────────────────────────────────────────
echo "[3/6] Installing AWS Load Balancer Controller..."

ALB_ROLE_ARN=$(terraform output -raw alb_controller_role_arn)

helm repo add eks https://aws.github.io/eks-charts 2>/dev/null || true
helm repo update eks

helm upgrade --install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName="$CLUSTER_NAME" \
  --set serviceAccount.create=true \
  --set "serviceAccount.annotations.eks\.amazonaws\.com/role-arn=$ALB_ROLE_ARN" \
  --wait --timeout=5m

echo "  ✓ ALB Controller installed"

# ─── KORAK 4: Deploy aplikacija ───────────────────────────────────────────
echo "[4/6] Deploying application..."

IMAGE_TAG=$(git rev-parse --short HEAD 2>/dev/null || echo "latest")

helm upgrade --install project-a ./helm/project-a \
  -n "$NAMESPACE" --create-namespace \
  -f helm/project-a/values/$ENV.yaml \
  --set image.tag="$IMAGE_TAG" \
  --wait --timeout=5m

echo "  ✓ Application deployed (tag: $IMAGE_TAG)"

# ─── KORAK 5: Database setup ──────────────────────────────────────────────
echo "[5/6] Running database migrations and seed..."

# Čekaj da pod bude ready
kubectl wait pod \
  -l app=go-service \
  -n "$NAMESPACE" \
  --for=condition=Ready \
  --timeout=3m

kubectl exec -n "$NAMESPACE" deployment/go-service -- /server migrate
kubectl exec -n "$NAMESPACE" deployment/go-service -- /server seed
echo "  ✓ Database migrated and seeded"

# ─── KORAK 6: URL-ovi ─────────────────────────────────────────────────────
echo "[6/6] Fetching URLs..."
echo ""
bash scripts/get-urls.sh "$ENV"
echo ""
echo "=== RECREATE COMPLETE ==="
```

---

## Script: Pronalaženje URL-ova

```bash
#!/bin/bash
# scripts/get-urls.sh
# Koristi se: bash scripts/get-urls.sh [ENV]
# Radi u bilo kom trenutku — ne treba destroy/recreate

ENV=${1:-dev}
NAMESPACE="project-a-$ENV"

echo "=== URLs za environment: $ENV ==="

# App Ingress URL
APP_URL=$(kubectl get ingress project-a \
  -n "$NAMESPACE" \
  -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null)
if [ -n "$APP_URL" ] && [ "$APP_URL" != "null" ]; then
  echo "  App:      http://$APP_URL"
else
  echo "  App:      Not deployed / Ingress not ready"
fi

# Grafana URL
GF_URL=$(kubectl get ingress \
  -n monitoring \
  -o jsonpath='{.items[0].status.loadBalancer.ingress[0].hostname}' 2>/dev/null)
if [ -n "$GF_URL" ] && [ "$GF_URL" != "null" ]; then
  echo "  Grafana:  http://$GF_URL"
else
  echo "  Grafana:  Not deployed"
fi

# ALB direktno iz AWS-a
ALB_DNS=$(aws elbv2 describe-load-balancers \
  --query "LoadBalancers[?contains(LoadBalancerName,'$ENV')].DNSName | [0]" \
  --output text 2>/dev/null)
if [ -n "$ALB_DNS" ] && [ "$ALB_DNS" != "None" ]; then
  echo "  ALB DNS:  http://$ALB_DNS"
fi

# Terraform output
TF_URL=$(cd "terraform/envs/$ENV" && terraform output -raw alb_dns_name 2>/dev/null || true)
if [ -n "$TF_URL" ]; then
  echo "  TF out:   http://$TF_URL"
fi

echo "=================================="
```

---

## Česti Problemi i Rješenja

### Problem: `terraform destroy` čeka na Load Balancer koji se ne briše

```bash
# Uzrok: Ingress resource postoji u K8s — ALB Controller ne može obrisati ALB
# Simptom: terraform destroy visi na "Deleting..." za aws_lb resource

# Fix 1: Obriši Ingress resurse ručno
kubectl delete ingress --all -n project-a-dev
kubectl delete ingress --all -n monitoring
sleep 60  # Daj ALB Controlleru vrijeme

# Fix 2: Ako ALB Controller više ne radi (jer je EKS node gone), obriši ALB ručno
aws elbv2 describe-load-balancers \
  --query "LoadBalancers[?contains(LoadBalancerName,'dev')].LoadBalancerArn" \
  --output text | xargs -I{} aws elbv2 delete-load-balancer --load-balancer-arn {}

# Pa ponovi terraform destroy
cd terraform/envs/dev
terraform destroy -var-file=dev.tfvars -auto-approve
```

### Problem: "DependencyViolation" pri brisanju VPC

```bash
# Uzrok: ENI (Elastic Network Interface) ostao od ALB-a ili EKS nodova
# Simptom: Error deleting VPC: DependencyViolation

# Pronađi orphan ENI-je
VPC_ID=$(aws ec2 describe-vpcs \
  --filters "Name=tag:Environment,Values=dev" \
  --query 'Vpcs[0].VpcId' --output text)

aws ec2 describe-network-interfaces \
  --filters "Name=vpc-id,Values=$VPC_ID" \
  --query 'NetworkInterfaces[*].[NetworkInterfaceId,Description,Status,InterfaceType]' \
  --output table

# Identifikuj koji su orphan (status: available, description: sadržava ELB/EKS)
# Obriši ih
ENI_ID="eni-xxxxxxxxxxxxxxxxx"
aws ec2 delete-network-interface --network-interface-id "$ENI_ID"

# Pa ponovi terraform destroy
```

### Problem: EKS Node Group ne može se obrisati

```bash
# Uzrok: Pod sa PodDisruptionBudget blokira drain
# Simptom: Error: NodeGroup update failed - Instances failed to drain

# Fix
kubectl delete pdb --all -n project-a-dev
kubectl delete pdb --all -n kube-system

# Pa ponovi terraform destroy
```

### Problem: RDS ne može se obrisati — traži final snapshot

```bash
# Uzrok: skip_final_snapshot = false u Terraform konfiguraciji
# Simptom: Error: RDS requires FinalDBSnapshotIdentifier

# Provjeri dev.tfvars
grep skip_final_snapshot terraform/envs/dev/dev.tfvars

# Fix za dev: mora biti true od početka
# Dodaj u dev.tfvars:
# skip_final_snapshot = true

# Privremeni fix ako već imaš problem:
terraform destroy \
  -var-file=dev.tfvars \
  -var="skip_final_snapshot=true" \
  -auto-approve
```

### Problem: Terraform state je desinhronizovan

```bash
# Uzrok: Resursi obrisani ručno kroz konzolu
# Simptom: Error: resource already exists / resource not found

# Provjeri state vs stvarnost
terraform plan -var-file=dev.tfvars 2>&1 | grep -E "will be|must be|Error"

# Ukloni orphan resource iz statea
terraform state rm aws_eks_cluster.main

# Ili refresh state
terraform refresh -var-file=dev.tfvars

# Pa ponovi destroy
```
