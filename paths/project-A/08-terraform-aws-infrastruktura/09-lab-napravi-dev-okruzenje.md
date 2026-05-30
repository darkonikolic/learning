# LAB: Kreiraj dev AWS okruženje

## Šta ćeš izgraditi

Na kraju ovog laba imat ćeš:
- EKS cluster u AWS-u sa jednim t3.medium worker nodom
- VPC sa public i private subnetima
- ALB Controller instaliran i spreman
- hello-world nginx dostupan na `https://app.dev.firma.com`
- Sve kreirano Terraformom, ništa ručno

Na kraju laba: sve UNIŠTI (obavezan korak — ne ostavljaj running resurse).

## Prerekviziti

Provjeri da imaš:

```bash
# AWS CLI konfigurisan
aws sts get-caller-identity
# Treba vratiti tvoj account ID i user/role

# Terraform
terraform version
# Terraform v1.7+ 

# kubectl
kubectl version --client

# Helm
helm version

# AWS nalog sa dovoljnim pravima za kreiranje EKS, VPC, IAM resursa
```

GitLab repo za project-A treba biti kreiran (modul 02). Deploy token za registry treba biti spreman.

## Korak 1: Bootstrap (jednom)

```bash
cd terraform/bootstrap
terraform init
terraform apply
```

Potvrdi sa `yes`. Output:
```
state_bucket_name = "project-a-terraform-state"
lock_table_name   = "project-a-terraform-locks"
```

Ove vrijednosti su već unesene u `backend.tf` fajlove. Bootstrap state (`terraform.tfstate` u bootstrap direktoriju) commiti u git.

## Korak 2: Popuni dev.tfvars

Otvori `terraform/envs/dev/dev.tfvars` i popuni:

```hcl
aws_region         = "eu-west-1"          # ili region koji koristiš
vpc_cidr           = "10.0.0.0/16"
availability_zones = ["eu-west-1a"]

enable_nat_gateway = false                 # dev ušteda
node_instance_type = "t3.medium"
desired_nodes      = 1
min_nodes          = 1
max_nodes          = 3

gitlab_project_path      = "tvoj-username/project-a"   # zamijeni
gitlab_oidc_provider_arn = ""              # popuni nakon što kreiraš OIDC provider
```

## Korak 3: Kreiranje dev env

```bash
cd terraform/envs/dev
terraform init
```

Očekivani output:
```
Initializing the backend...
Successfully configured the backend "s3"!
Initializing provider plugins...
Terraform has been successfully initialized!
```

```bash
terraform plan -var-file=dev.tfvars
```

Pregledaj plan — treba biti ~40-60 resursa za kreiranje. Nema destroy akcija.

```bash
terraform apply -var-file=dev.tfvars
```

Unesi `yes`. Čekaj 10-15 minuta.

## Korak 4: Verifikacija infrastrukture

```bash
# Kubeconfig update
aws eks update-kubeconfig \
  --name project-a-dev \
  --region eu-west-1

# Provjeri nodove
kubectl get nodes
# NAME                           STATUS   ROLES    AGE   VERSION
# ip-10-0-10-xxx.ec2.internal    Ready    <none>   2m    v1.29.x

# Provjeri system Podove
kubectl -n kube-system get pods
# CoreDNS, kube-proxy trebaju biti Running
```

Provjeri i u AWS konzoli (samo za posmatranje): EC2 → Instances, EKS → Clusters.

## Korak 5: Instaliraj ALB Controller

```bash
helm repo add eks https://aws.github.io/eks-charts
helm repo update

ALB_ROLE_ARN=$(cd terraform/envs/dev && terraform output -raw alb_controller_role_arn)

helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  --namespace kube-system \
  --set clusterName=project-a-dev \
  --set serviceAccount.annotations."eks\.amazonaws\.com/role-arn"=${ALB_ROLE_ARN}

# Provjeri da je controller Running
kubectl -n kube-system get deployment aws-load-balancer-controller
```

## Korak 6: Deploy hello-world

```bash
ACM_CERT_ARN=$(cd terraform/envs/dev && terraform output -raw acm_certificate_arn)

helm upgrade --install helloworld ./helm/helloworld \
  --namespace helloworld-dev \
  --create-namespace \
  --set image.tag=main-latest \
  --set ingress.host=app.dev.firma.com \
  --set ingress.enabled=true \
  --set ingress.certificateArn=${ACM_CERT_ARN}

# Prati deployment
kubectl -n helloworld-dev rollout status deployment/helloworld

# Dočekaj ALB kreiranje (1-3 minute)
kubectl -n helloworld-dev get ingress -w
```

Kada Ingress dobije ADDRESS (ALB DNS), aplikacija je dostupna.

## Korak 7: Verifikacija pristupa

```bash
ALB_DNS=$(kubectl -n helloworld-dev get ingress helloworld -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
echo "ALB DNS: ${ALB_DNS}"

# Direktno na ALB (zaobilazeći DNS)
curl -k https://${ALB_DNS} -H "Host: app.dev.firma.com"
# Treba vratiti Hello World HTML

# Ako Route53 record postoji:
curl https://app.dev.firma.com
```

## Korak 8: DESTROY (obavezan!)

Ne zaboravi brisati! Svaki sat running = novac.

```bash
# 1. Uninstaliraj Helm release-ove (ALB mora biti obrisan PRIJE terraform destroy)
helm uninstall helloworld -n helloworld-dev
helm uninstall aws-load-balancer-controller -n kube-system

# 2. Pričekaj da AWS obriše ALB (provjeri)
aws elbv2 describe-load-balancers --query 'LoadBalancers[].LoadBalancerName'

# 3. Terraform destroy
cd terraform/envs/dev
terraform destroy -var-file=dev.tfvars

# Unesi 'yes' i čekaj 5-10 minuta

# 4. Verifikacija
aws eks list-clusters
aws ec2 describe-vpcs --filters "Name=tag:Name,Values=project-a-dev*"
# Trebaju biti prazne liste
```

## Troubleshooting: česte greške

**"Error: configuring Terraform AWS Provider: no valid credential sources found"**
→ AWS CLI nije konfigurisan: `aws configure` ili provjeri OIDC rolu

**"Error: creating EKS Node Group: InvalidParameterException: The provided role doesn't have the necessary permissions"**
→ Node IAM role nema sve potrebne politike. Daj error output Claude-u.

**Ingress ADDRESS ostaje prazan 5+ minuta:**
→ ALB Controller možda nema ispravnu IAM rolu. Provjeri: `kubectl -n kube-system logs -l app.kubernetes.io/name=aws-load-balancer-controller`

**"timeout while waiting for state to become 'active'":**
→ EKS kreiranje traje duže nego Terraform čeka. Ponovo pokreni `terraform apply` — idempotent je.

## AI workflow za lab

Kada zaglavlješ:
1. Kopiraj kompletnu error poruku (ne samo zadnji red)
2. Dodaj kontekst: koji korak, šta si prethodno radio
3. Daj Claude-u: "Radim project-A lab, korak X, dobio sam ovu grešku..."

Claude može čitati Terraform plan output i preporučiti izmjene — ovo je standardni workflow za debuggovanje infrastrukture.

---

## Makefile — dodaj u ovom poglavlju

Ovo poglavlje uvodi Terraform za AWS infrastrukturu sa S3 backendom. Dodaj u `Makefile` u korenu projekta:

```makefile
# === OBLAST 08: Terraform AWS infrastruktura ===

infra-init: ## Inicijalizuj Terraform za AWS infra (s3 backend) (ENV=dev make infra-init)
	docker run --rm \
	  -v $(PWD)/infra:/workspace -w /workspace \
	  -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -e AWS_SESSION_TOKEN \
	  hashicorp/terraform:$(TF_VERSION) init \
	  -backend-config="key=envs/$(ENV)/terraform.tfstate"

infra-plan: ## Plan AWS infrastrukture za okruženje (ENV=dev make infra-plan)
	docker run --rm \
	  -v $(PWD)/infra:/workspace -w /workspace \
	  -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -e AWS_SESSION_TOKEN \
	  hashicorp/terraform:$(TF_VERSION) plan \
	  -var-file="environments/$(ENV).tfvars" -out=tfplan

infra-apply: ## Primijeni infrastrukturni plan (uvijek nakon infra-plan) (ENV=dev make infra-apply)
	docker run --rm \
	  -v $(PWD)/infra:/workspace -w /workspace \
	  -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -e AWS_SESSION_TOKEN \
	  hashicorp/terraform:$(TF_VERSION) apply tfplan

infra-destroy: ## ⚠️ Uništi svu AWS infrastrukturu za okruženje (ENV=dev make infra-destroy)
	docker run --rm \
	  -v $(PWD)/infra:/workspace -w /workspace \
	  -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -e AWS_SESSION_TOKEN \
	  hashicorp/terraform:$(TF_VERSION) destroy \
	  -var-file="environments/$(ENV).tfvars"
```

Centralni Makefile već sadrži ove targete — ovo je referenca šta si dodao u ovoj oblasti.

Provjeri da targeti rade:
```bash
ENV=dev make infra-init
ENV=dev make infra-plan
make help | grep infra
```
