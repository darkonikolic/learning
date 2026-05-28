# Spot Instances

## Zašto Spot instances

AWS Spot instances su neiskorišćeni EC2 kapacitet koji AWS nudi po znatno nižoj cijeni od On-Demand. Jedini tradeoff: AWS ih može prekinuti uz 2-minutno upozorenje kada mu trebaju nazad.

**Poređenje cijena (eu-west-1, januar 2024):**

```
t3.medium On-Demand:  $0.047/h
t3.medium Spot:       ~$0.015/h  (68% jeftinije)

Za 2 dev node-a, 8h/dan radnim danima:
  On-Demand: 2 × $0.047 × 8 × 22 = $16.50/mj
  Spot:      2 × $0.015 × 8 × 22 = $5.28/mj
  Ušteda:    ~$11/mj za dev (mali projekt, ali princip vrijedi)

Za veće instance (m5.xlarge):
  On-Demand:  $0.192/h
  Spot:       ~$0.058/h  (70% jeftinije)
  Ušteda:     8-node cluster × $0.134 razlike × 8h = ~$8.60/dan
```

**Kad koristiti Spot:**
- Dev i staging okruženja — prekid je prihvatljiv, K8s restarta podove
- Batch jobs, data processing — stateless, mogu se ponavljati
- Horizontalno skaliranje prod-a — Spot za burst capacity, On-Demand za baseline

**Kad NE koristiti Spot:**
- Production baseline — rizik od interupcije nije prihvatljiv za kritične servise
- Stateful workloadi bez replikacije — baza podataka direktno na EC2
- Workloadi koji ne podnose 2-minutni graceful shutdown

---

## Spot instance lifecycle

```
Normalan rad:
  Spot instance radi identično kao On-Demand

2-minutno upozorenje (Spot interruption notice):
  AWS šalje signal na EC2 instance metadata endpoint
  AWS Node Termination Handler (NTH) detektuje signal
  NTH cordonuje node (nema novih podova)
  NTH drainuje node (premješta podove na druge node-ove)

Nakon 2 minute:
  AWS gasi instancu
  K8s rescheduler podiže prekinute podove na preostalim node-ovima

Utjecaj na aplikaciju:
  K8s graceful shutdown + liveness/readiness probi
  Kratki period povećanog latency tokom rescheduling-a
  Bez gubitka podataka (stateless aplikacija)
```

**Spot Savings Plan alternativa:** Reserved Instances za baseline, Spot za burst. Za project-a koji nema predvidljiv promet, Spot za dev i On-Demand za prod je najjednostavnija strategija.

---

## Terraform Managed Node Group sa Spot

```hcl
# terraform/modules/eks/node_group.tf

resource "aws_eks_node_group" "main" {
  cluster_name    = aws_eks_cluster.main.name
  node_group_name = "${var.env}-nodes"
  node_role_arn   = aws_iam_role.node.arn
  subnet_ids      = var.private_subnet_ids

  # Spot ili On-Demand — kontroliše se kroz tfvars
  capacity_type = var.use_spot ? "SPOT" : "ON_DEMAND"

  # Više instance tipova povećava dostupnost Spot kapaciteta
  # AWS bira dostupan tip — svi moraju biti sličnih resursa
  instance_types = var.use_spot ? [
    "t3.medium",   # 2 vCPU, 4GB RAM
    "t3a.medium",  # AMD ekvivalent, često jeftiniji
    "t2.medium",   # Starija generacija, veća Spot dostupnost
  ] : ["t3.medium"]

  scaling_config {
    desired_size = var.desired_nodes
    min_size     = var.min_nodes
    max_size     = var.max_nodes
  }

  update_config {
    max_unavailable = 1
  }

  labels = {
    capacity-type = var.use_spot ? "spot" : "on-demand"
    environment   = var.env
  }

  tags = {
    Environment = var.env
    Project     = "project-a"
  }
}
```

**Varijable za node group:**

```hcl
# terraform/modules/eks/variables.tf

variable "use_spot" {
  type        = bool
  description = "Use Spot instances for cost savings. Not recommended for production baseline."
  default     = false
}

variable "desired_nodes" {
  type    = number
  default = 2
}

variable "min_nodes" {
  type    = number
  default = 1
}

variable "max_nodes" {
  type    = number
  default = 5
}
```

---

## tfvars po environmentu

```hcl
# terraform/environments/dev/terraform.tfvars

use_spot      = true   # Dev: Spot za uštedu, prekid je prihvatljiv
desired_nodes = 1      # Minimalno u dev
min_nodes     = 0      # Može se skalirati na 0 van radnog vremena
max_nodes     = 3
```

```hcl
# terraform/environments/prod/terraform.tfvars

use_spot      = false  # Prod: On-Demand za stabilnost
desired_nodes = 3      # Minimalno 3 za HA
min_nodes     = 2      # Nikad ispod 2 u prod
max_nodes     = 10     # Autoscaling ceiling
```

```hcl
# terraform/environments/staging/terraform.tfvars

use_spot      = true   # Staging: kao dev, ali malo više node-ova
desired_nodes = 2
min_nodes     = 1
max_nodes     = 4
```

---

## Toleration za Spot node-ove

Spot node-ovi mogu imati taint koji sprječava da se kritični podovi rasporede na njih bez eksplicitne dozvole.

**Taint na node-u (opcionalno za strikte razdvajanje):**

```hcl
# U node_group.tf — dodaj taint samo ako želiš eksplicitno razdvajanje
# Za dev/staging obično nije potrebno

# lifecycle { ignore_changes = [taint] }  # Ako NTH upravlja taintovima
```

**Toleration u Helm values:**

```yaml
# helm/values/dev.yaml

tolerations:
  - key: "spot-instance"
    operator: "Equal"
    value: "true"
    effect: "NoSchedule"

# Za batch jobove koji preferiraju Spot:
affinity:
  nodeAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        preference:
          matchExpressions:
            - key: capacity-type
              operator: In
              values:
                - spot
```

```yaml
# helm/values/prod.yaml

# Prod podovi ne idu na Spot node-ove
affinity:
  nodeAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      nodeSelectorTerms:
        - matchExpressions:
            - key: capacity-type
              operator: In
              values:
                - on-demand
```

---

## AWS Node Termination Handler

NTH prati Spot interruption notice-e i gracefully drainuje node-ove prije nego AWS ugasi instancu.

```bash
# Helm install — kube-system namespace
helm repo add eks https://aws.github.io/eks-charts
helm repo update

helm upgrade --install aws-node-termination-handler \
  eks/aws-node-termination-handler \
  --namespace kube-system \
  --set enableSpotInterruptionDraining=true \
  --set enableScheduledEventDraining=true \
  --set enableRebalanceMonitoring=true \
  --set enableRebalanceDraining=false \
  --set nodeSelector."kubernetes\\.io/os"=linux
```

**Šta NTH radi:**
1. Pokreće se kao DaemonSet na svakom node-u
2. Prati EC2 instance metadata za Spot interruption notice
3. Kada detektuje notice: cordon node (ne prima nove podove) → drain (premješta podove)
4. K8s rescheduler raspoređuje podove na preostale node-ove
5. AWS terminira instancu

**Verifikacija da NTH radi:**

```bash
kubectl get daemonset -n kube-system aws-node-termination-handler
# Trebao bi imati DESIRED = CURRENT = AVAILABLE

kubectl logs -n kube-system -l app.kubernetes.io/name=aws-node-termination-handler --tail=50
```

---

## Cluster Autoscaler za Spot

Kada pod ne može biti raspoređen (nema kapaciteta), Cluster Autoscaler dodaje node-ove.

```bash
helm upgrade --install cluster-autoscaler \
  autoscaler/cluster-autoscaler \
  --namespace kube-system \
  --set autoDiscovery.clusterName=project-a-dev \
  --set awsRegion=eu-west-1 \
  --set extraArgs.balance-similar-node-groups=true \
  --set extraArgs.skip-nodes-with-system-pods=false \
  --set extraArgs.scale-down-delay-after-add=5m \
  --set extraArgs.scale-down-unneeded-time=10m
```

**Skaliranje na 0 za dev van radnog vremena:**

```bash
# Skripte za uštedu — pokretanje ručno ili kroz GitLab scheduled pipeline
# Isključi dev cluster van radnog vremena

# dev-scale-down.sh
aws eks update-nodegroup-config \
  --cluster-name project-a-dev \
  --nodegroup-name dev-nodes \
  --scaling-config minSize=0,maxSize=3,desiredSize=0 \
  --region eu-west-1

# dev-scale-up.sh
aws eks update-nodegroup-config \
  --cluster-name project-a-dev \
  --nodegroup-name dev-nodes \
  --scaling-config minSize=1,maxSize=3,desiredSize=1 \
  --region eu-west-1
```

```yaml
# GitLab scheduled pipeline za scale-down
dev-scale-down:
  rules:
    - if: $CI_PIPELINE_SOURCE == "schedule"  # Pokretati scheduled pipeline u 18:00
  script:
    - aws eks update-nodegroup-config --cluster-name project-a-dev
        --nodegroup-name dev-nodes
        --scaling-config minSize=0,maxSize=3,desiredSize=0
```

---

## Monitoring Spot troškova

```bash
# AWS Cost Explorer CLI — Spot troškovi za prošli mjesec
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-02-01 \
  --granularity MONTHLY \
  --filter '{"Dimensions":{"Key":"PURCHASE_TYPE","Values":["Spot"]}}' \
  --metrics BlendedCost

# Provjeri Spot savings u AWS konzoli:
# EC2 → Spot Requests → Savings Summary
```

---

## Checklist

- [ ] Dev i staging koriste Spot (`use_spot = true` u tfvars)
- [ ] Prod koristi On-Demand (`use_spot = false`)
- [ ] Više instance tipova konfigurisano za veću dostupnost Spot-a
- [ ] AWS Node Termination Handler instaliran u kube-system
- [ ] Cluster Autoscaler instaliran i konfigurisan
- [ ] Helm values imaju odgovarajući affinity za prod (samo on-demand node-ovi)
- [ ] Scale-to-zero skripte za dev van radnog vremena
- [ ] Aplikacija ima graceful shutdown (sigterm handling, preStop hook)
