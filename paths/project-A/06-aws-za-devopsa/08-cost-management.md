# AWS Cost Management

## Zašto je cost awareness dio DevOps kulture

Infrastruktura kao kod znači i infrastruktura kao trošak. Terraform `apply` na prod okruženje može generisati $500/mj računanja — i nastaviti da naplaćuje dok se ne doda `destroy`. DevOps inženjer je odgovoran i za operativne troškove, ne samo za uptime.

Princip project-A: kreativna upotreba kratkoživućih environment-a. Niko ne plaća za dev env koji radi 24/7 kada programeri rade 8 sati dnevno.

## Procjena troškova za project-A

### Per-environment troškovi (eu-west-1, on-demand)

| Komponenta | Dev | Staging | Prod |
|-----------|-----|---------|------|
| EKS control plane | $72/mj | $72/mj | $72/mj |
| EC2 t3.medium (×1) | $30/mj | - | - |
| EC2 t3.large (×2) | - | $120/mj | - |
| EC2 t3.xlarge (×3) | - | - | $360/mj |
| ALB | $16/mj | $16/mj | $16/mj |
| NAT Gateway | $32/mj | $32/mj | $32/mj |
| Route53 | $1/mj | $1/mj | $1/mj |
| S3 (state) | <$1/mj | <$1/mj | <$1/mj |
| **Ukupno** | **~$151/mj** | **~$241/mj** | **~$481/mj** |

Sva tri environment-a uvijek aktivna: **~$873/mj**. Staging i prod imaju opravdanje. Dev nema.

### Realan trošak sa cost optimizacijom

Dev env koji radi samo radnim danima, 8h/dan (40h/sedmicu od 168h):
- Dev cost × (40/168) = $151 × 0.24 = **$36/mj**

Ukupno: staging ($241) + prod ($481) + dev optimizovani ($36) = **~$758/mj**

## Strategije smanjenja troška

### 1. Dev environment on-demand

```bash
# Jutro (automatski scheduled pipeline ili ručno)
cd terraform/envs/dev && terraform apply -var-file=dev.tfvars -auto-approve

# Večer (scheduled pipeline, svaki dan u 20:00)
helm uninstall --all --namespace helloworld-dev
terraform destroy -var-file=dev.tfvars -auto-approve
```

GitLab scheduled pipeline za `terraform destroy` svake večeri.

### 2. Uklanjanje NAT Gateway za dev

Dev environment može koristiti public subnete za EKS node-ove:
```hcl
# dev.tfvars
enable_nat_gateway = false
eks_nodes_public   = true  # node-ovi u public subnet, bez javnih IP
```

Ušteda: **$32/mj**. Worker nodovi i dalje nisu direktno dostupni (Security Group), ali mogu da pullaju Docker images bez NAT-a.

### 3. Spot instance za dev/staging

EC2 Spot instance koriste neiskorišćene AWS kapacitete po cijeni 60-90% nižoj od on-demand:

```hcl
resource "aws_eks_node_group" "dev" {
  capacity_type = "SPOT"  # umjesto "ON_DEMAND"
  instance_types = ["t3.medium", "t3.large"]  # više tipova = manje interruption
}
```

Spot instance mogu biti terminirane sa 2 minute upozorenja. Za dev — prihvatljivo. Za prod — ne.

### 4. Review environment troškovi

Dynamic review envovi ne kreiraju novi EKS cluster (to bi bilo $72 + nodovi po MR-u). Koriste **namespace unutar dev clustera**:
- Novi namespace: $0
- Helm release: $0
- Route53 record: $0.00001/mj

Jedini dodatan trošak je ako MR workload preoptereti dev nodove i autoscaler doda novi.

### 5. Saved Plans / Reserved Instances za prod

Ako prod radi 12+ mjeseci, Reserved Instance daje 30-40% uštede u zamjenu za jednogodišnju ili trogodišnju obavezu.

## AWS Budget Alerts

Obavezno za svaki nalog. Terraform kreira budget:

```hcl
resource "aws_budgets_budget" "monthly" {
  name         = "project-a-monthly"
  budget_type  = "COST"
  limit_amount = "600"
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 80
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = ["devops@firma.com"]
  }
}
```

Notifikacija kada stvarni trošak pređe 80% budžeta ($480 od $600). Daje dovoljno vremena da se reaguje prije kraja mjeseca.

## Terraform lifecycle za cost control

```hcl
# Samo prod dobija prevent_destroy
lifecycle {
  prevent_destroy = true
}
```

Dev i staging nikad ne dobijaju `prevent_destroy`. Greška u destroy-u treba biti moguća — to je feature, ne bug.

```hcl
# Dev EKS nema multi-AZ (ušteda na NAT i nodovima)
variable "availability_zones" {
  default = {
    dev     = ["eu-west-1a"]          # jedan AZ, bez HA
    staging = ["eu-west-1a", "eu-west-1b"]
    prod    = ["eu-west-1a", "eu-west-1b", "eu-west-1c"]
  }
}
```
