# EKS: Managed Kubernetes na AWS-u

## Šta EKS radi umjesto tebe

Kubernetes zahtijeva control plane: API server, etcd, controller manager, scheduler. Na lokalnom kinu (kind) sve ovo radi u jednom Dockeru. U produkciji, ovo je odgovornost managed servisa.

EKS upravlja control plane-om:
- API server je visoko dostupan (3 instance unutar AWS)
- etcd je managed i backup-ovan
- Kubernetes verzija upgrade-i su automatizirani
- AWS plaća za control plane HA

Ti upravljaš worker nodovima (EC2 instance) i workload-ovima koji tamo teku.

Cijena: **$0.10/h po clusteru = $72/mj** — ovo plaćaš bez obzira na veličinu workload-a.

## Node grupe: koji tip izabrati

**Managed Node Groups** (project-A izbor):
- AWS kreira i upravlja Auto Scaling Group za EC2 instance
- Kubernetes verzija update je upravljana
- Node draining i terminacija su automatizirani
- Integracija sa Cluster Autoscaler-om

**Fargate**:
- Serverless — nema EC2 instance, AWS alocira compute per Pod
- Skuplje per-Pod, ali nula overhead za upravljanje nodovima
- Ne podržava sve workload-e (DaemonSet-i ne rade)
- Nema smisla za Prometheus/Grafana koji trebaju persistent storage

**Self-managed**:
- Ti kreiraš EC2 instance i dodaješ ih u cluster
- Puna kontrola, puna odgovornost
- Jedino ako treba custom AMI ili specijalni hardware

Za project-A: Managed Node Groups. Balans kontrole i automatizacije.

## EKS Add-ons

Add-oni su managed verzije ključnih Kubernetes komponenti:

| Add-on | Uloga |
|--------|-------|
| **VPC CNI** | Dodjeljuje AWS VPC IP adrese Podovima |
| **CoreDNS** | DNS rezolucija unutar clustera |
| **kube-proxy** | Mrežni pravila za Service routing |
| **EBS CSI Driver** | Persistent Volume support za EBS diskove |

Add-oni se posebno update-uju od Kubernetes verzije. Terraform ih kreira:

```hcl
resource "aws_eks_addon" "vpc_cni" {
  cluster_name = aws_eks_cluster.main.name
  addon_name   = "vpc-cni"
}
```

## Cluster Autoscaler

Cluster Autoscaler prati Podove koji ne mogu biti scheduled (Pending) i dodaje worker nodove. Prati i nodove koji su dugo idle i uklanja ih.

Instalira se kao Helm chart, autentifikuje prema AWS Auto Scaling API-u kroz IRSA. Konfiguriše se sa min/max node count per node group.

Za project-A:
- dev: min=1, max=3 nodova
- staging: min=2, max=5 nodova
- prod: min=3, max=10 nodova (HPA skalira Podove, CA skalira nodove)

## Kubeconfig za EKS

Nakon `terraform apply`, EKS cluster postoji ali lokalni kubectl ne zna za njega. Update kubeconfig:

```bash
aws eks update-kubeconfig --name project-a-dev --region eu-west-1
```

Ovo dodaje context u `~/.kube/config`. Provjera:

```bash
kubectl config get-contexts
kubectl config use-context arn:aws:eks:eu-west-1:123456789:cluster/project-a-dev
kubectl get nodes
```

Isti kubectl komande koje koristiš sa kind-om rade sa EKS-om — jedina razlika je context.

## Lokalno (kind) vs EKS razlike

| Aspekt | kind | EKS |
|--------|------|-----|
| Control plane | Docker container | AWS managed |
| Nodes | Docker container | EC2 instance |
| Load Balancer | MetalLB / port-forward | AWS ALB |
| Storage | hostPath | EBS PersistentVolume |
| DNS | localhost | Route53 subdomen |
| Trošak | $0 | $72+/mj |
| Startup | 30 sekundi | 10-15 minuta |

Isti Helm chart deploya na oba okruženja — jedina razlika su values fajlovi koji konfigurišu ALB annotations ili MetalLB, i domain.

## Node sizing za project-A

t3 familija je dobar balans cijene i performansi za dev workload-e:

| Tip | vCPU | RAM | Cijena (eu-west-1) | Za environment |
|-----|------|-----|--------------------|----------------|
| t3.small | 2 | 2 GB | ~$14/mj | Pretijesno za monitoring stack |
| t3.medium | 2 | 4 GB | ~$30/mj | Dev (nginx + monitoring) |
| t3.large | 2 | 8 GB | ~$60/mj | Staging |
| t3.xlarge | 4 | 16 GB | ~$120/mj | Prod (sa HPA) |

Monitoring stack (Prometheus + Grafana + Loki) je zahtjevan — t3.medium je minimum za dev.
