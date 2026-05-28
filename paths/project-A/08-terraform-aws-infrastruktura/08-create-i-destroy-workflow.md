# Create i Destroy workflow

## Zašto je redosljed bitan

Terraform destroy briše resurse u obrnutom redoslijedu od kreiranja. Ali: ako Kubernetes resursi drže reference na AWS resurse (ALB, EBS volumeni), AWS neće dozvoliti brisanje dok K8s resursi postoje.

Konkretni problem:
```
terraform destroy pokušava brisati ALB
    ↓
ALB ne može biti obrisan — Target Group ima registrovane ciljeve
    ↓
Target Group ne može biti obrisana — Kubernetes Ingress controller je kreira
    ↓
Ingress controller radi na EKS nodovima koji su dio node group-e
    ↓
Node group ne može biti obrisana — ima nodova
    ↓
DEADLOCK
```

Rješenje: uvijek prvo uninstaluj Helm release-ove koji kreiraju AWS resurse, pa onda `terraform destroy`.

## Kompletni CREATE workflow

### Korak 1: Bootstrap (samo jednom, nikad ponavljati)

```bash
cd terraform/bootstrap
terraform init
terraform apply

# Output: bucket name i DynamoDB table name
# Sačuvaj ove vrijednosti u dokumentaciju tima
```

### Korak 2: Inicijalizacija environment-a

```bash
cd terraform/envs/dev
terraform init
```

`terraform init` download-uje providere i inicijalizuje S3 backend. Mora se pokrenuti pri prvom setup-u i nakon svakog `rm -rf .terraform/`.

### Korak 3: Plan

```bash
terraform plan -var-file=dev.tfvars -out=dev.plan
```

`-out=dev.plan` sprema plan u fajl. Garantuje da `apply` izvršava tačno ono što je pregledano — ne postoji mogućnost da stanje promjeni između plan-a i apply-a.

Pregledaj plan! Obrati pažnju na:
- Broj resursa koji se kreiraju (prvi put ~30-50)
- Ikakve `destroy` akcije (crvene linije) — zašto postoje?
- `known after apply` vrijednosti — OK za ID-ove, ali pazi na neočekivano

### Korak 4: Apply

```bash
terraform apply dev.plan
```

Bez `dev.plan` argumenta, Terraform ponovi plan i pita za potvrdu. Sa planom — direktno izvršava. Za CI/CD uvijek koristiti `-out` + `apply plan` pattern.

Trajanje: 10-15 minuta za kompletan EKS + VPC setup.

### Korak 5: Kubeconfig update

```bash
aws eks update-kubeconfig \
  --name project-a-dev \
  --region eu-west-1
```

Provjera:
```bash
kubectl config current-context
# arn:aws:eks:eu-west-1:123456789:cluster/project-a-dev

kubectl get nodes
# NAME                          STATUS   ROLES    AGE   VERSION
# ip-10-0-10-xxx.ec2.internal   Ready    <none>   2m    v1.29.x
```

### Korak 6: Instaliraj infrastrukturne komponente

```bash
# ALB Controller (čita Ingress i kreira ALB)
helm repo add eks https://aws.github.io/eks-charts
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  --namespace kube-system \
  --set clusterName=project-a-dev \
  --set serviceAccount.annotations."eks\.amazonaws\.com/role-arn"=$(terraform output -raw alb_controller_role_arn)
```

### Korak 7: Deploy aplikacije

```bash
helm upgrade --install helloworld ./helm/helloworld \
  --namespace helloworld-dev \
  --create-namespace \
  --set image.tag=main-a1b2c3d \
  --set ingress.host=app.dev.firma.com \
  --set ingress.certificateArn=$(terraform -chdir=terraform/envs/dev output -raw acm_certificate_arn)
```

### Korak 8: Verifikacija

```bash
kubectl -n helloworld-dev get pods
kubectl -n helloworld-dev get ingress

# Ingress ADDRESS treba biti ALB DNS
# k8s-helloworld-dev-abc123.eu-west-1.elb.amazonaws.com

curl https://app.dev.firma.com
# <html><body>Hello World</body></html>
```

## Kompletni DESTROY workflow

### Korak 1: Helm uninstall (OBAVEZNO PRVO)

```bash
# Briše Ingress → ALB Controller briše ALB i Target Groups u AWS
helm uninstall helloworld -n helloworld-dev

# Ako ima više release-ova:
helm uninstall aws-load-balancer-controller -n kube-system

# Pričekaj da ALB bude obrisan u AWS
# (može potrajati 1-2 minute)
aws elbv2 describe-load-balancers \
  --query 'LoadBalancers[?contains(LoadBalancerName, `dev`)]'
```

### Korak 2: Terraform destroy plan

```bash
cd terraform/envs/dev
terraform plan -destroy -var-file=dev.tfvars -out=dev-destroy.plan
```

Pregledaj plan — treba vidjeti sve resurse koji se brišu. Ako ima resursa koji nisu u planu (manualno kreirani kroz konzolu), Terraform ih neće obrisati.

### Korak 3: Destroy

```bash
terraform destroy -var-file=dev.tfvars
```

Ili sa planom:
```bash
terraform apply dev-destroy.plan
```

Trajanje: 5-10 minuta. VPC se briše na kraju jer drugi resursi ovise o njemu.

### Korak 4: Verifikacija

```bash
# Provjeri da nema orphan resursa
aws eks list-clusters
aws ec2 describe-vpcs --filters "Name=tag:Name,Values=project-a-dev*"
aws elbv2 describe-load-balancers
```

## AI workflow za Terraform

Terraform plan output može biti dugačak i zbunjujući, posebno pri promjenama modula.

Praksa za project-A:
```bash
# Sačuvaj plan output
terraform plan -var-file=dev.tfvars 2>&1 | tee plan-output.txt

# Kopiraj sadržaj i daj Claude-u:
# "Ovdje je terraform plan output. Provjeri:
#  1. Ima li destruktivnih akcija koje nisu očekivane?
#  2. Ima li security propusta u IAM politikama?
#  3. Ima li resoursa koji se ponovo kreiraju umjesto da se update-uju?"
```

Isti pristup za error poruke:
```bash
terraform apply dev.plan 2>&1 | tail -50 | pbcopy
# Paste u Claude: "Dobio sam ovu grešku pri terraform apply..."
```
