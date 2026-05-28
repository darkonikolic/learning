# 03 — EKS Cluster kroz AWS Konzolu

## Cilj

Kreirati EKS cluster i Node Group ručno. Razumjeti šta AWS kreira u pozadini i kako se kubectl spaja na cluster. Ovo je osnova za sve što slijedi — aplikacija, Helm deploymenti, monitoring.

---

## Šta EKS Zapravo Kreira

EKS = managed Kubernetes control plane. AWS maintaina:
- `kube-apiserver` (HA, u više AZ)
- `etcd` (cluster state storage)
- `kube-controller-manager`
- `kube-scheduler`

Ti maintanaješ:
- Node Group (EC2 instance = worker nodes)
- Addone (DNS, networking, storage drivers)
- Workloade koji teku na nodovima

Control plane je u AWS-ovoj infrastrukturi, plaćaš $0.10/sat po clusteru. Node Group su tvoje EC2 instance — plaćaš per-instance.

---

## IAM Role za EKS Cluster

Mora se kreirati **prije** EKS clustera.

**Console → IAM → Roles → Create role**

- **Trusted entity type**: AWS service
- **Use case**: scroll down → EKS → **EKS - Cluster**
- Next → policy `AmazonEKSClusterPolicy` je automatski dodana
- **Role name**: `project-a-dev-eks-cluster-role`
- Create role

Ova rola dozvoljava EKS control plane-u da kreira i upravlja mrežnim resursima u tvom imenu (load balanceri, security groups za control plane komunikaciju).

---

## Kreiranje EKS Clustera

**Console → EKS → Clusters → Create cluster**

### Korak 1 — Configure cluster

- **Name**: `project-a-dev`
- **Kubernetes version**: 1.29
- **Cluster service role**: `project-a-dev-eks-cluster-role`
- Next

### Korak 2 — Specify networking

- **VPC**: `project-a-dev-vpc`
- **Subnets**: izaberi SVE 4 (public-1a, public-1b, private-1a, private-1b)
  - Zašto sve 4? EKS control plane ENI-ji se plasiraju u odabrane subnete. Davanje sva 4 daje AWS-u fleksibilnost.
- **Security groups**: `eks-nodes-sg`
- **Cluster endpoint access**: **Public**
  - Public: kubectl radi s tvog laptopa (OK za learning)
  - Private: kubectl mora biti unutar VPC-a (za prod)
  - Public and private: hybrid (za tranziciju)
- Next

### Korak 3 — Configure observability

- Cluster logging: za sada ostavi sve isključeno (CloudWatch naplaćuje)
- Next

### Korak 4 — Select add-ons

Izaberi:
- ✓ **CoreDNS** — DNS za K8s servis discovery (bez ovoga ništa ne radi)
- ✓ **kube-proxy** — iptables pravila za K8s Services
- ✓ **Amazon VPC CNI** — pod networking, svaki pod dobija IP iz VPC CIDR-a
- ✓ **Amazon EBS CSI Driver** — dinamičko kreiranje EBS volumena za PVC-ove

- Next → Create

**Kreiranje traje ~15 minuta.** U pozadini:

1. AWS kreira managed control plane u svojoj infrastrukturi
2. Konfigurira kube-apiserver s tvoje VPC informacije
3. Plasira ENI-je u tvoje subnete (otuda zahtjev za subnete)
4. Instalira odabrane addone
5. Generira cluster CA certifikat

Za to vrijeme u konzoli: **Clusters → project-a-dev → Status: Creating**. Možeš pratiti u **Events tabu** (kad postane dostupan).

---

## IAM Role za Node Group

**Console → IAM → Roles → Create role**

- **Trusted entity type**: AWS service
- **Use case**: EC2
- Next

Dodaj ove 3 policy-ja (traži svaku posebno):
1. `AmazonEKSWorkerNodePolicy` — dozvoljava nodovima da se registruju u cluster
2. `AmazonEKS_CNI_Policy` — dozvoljava VPC CNI da kreira i briše ENI-je
3. `AmazonEC2ContainerRegistryReadOnly` — dozvoljava pullanje Docker images iz ECR-a

- **Role name**: `project-a-dev-node-role`
- Create role

---

## Kreiranje Node Group

Nakon što je cluster u stanju **Active**:

**EKS → Clusters → project-a-dev → Compute tab → Add node group**

### Node Group Configuration

- **Name**: `project-a-dev-nodes`
- **Node IAM role**: `project-a-dev-node-role`
- Next

### Node Group Compute Configuration

- **AMI type**: Amazon Linux 2 (AL2_x86_64) — default, najstabilniji
- **Capacity type**: On-Demand
- **Instance types**: `t3.medium` (2 vCPU, 4GB RAM — minimum za EKS)
  - t3.small (2GB) je premalo, system podovi troše ~1.5GB
- **Disk size**: 20 GiB
- Next

### Node Group Scaling Configuration

- **Minimum size**: 1
- **Maximum size**: 3
- **Desired size**: 1

Za dev environment 1 node je dovoljno. Maximum 3 ostavlja prostor za auto-scaling testiranje.

### Node Group Network Configuration

- **Subnets**: SAMO private subnete!
  - ✓ `project-a-dev-private-1a`
  - ✓ `project-a-dev-private-1b`
  - public-1a i public-1b: **NEMOJ kvačiti**

Zašto samo private? Nodovi ne trebaju direktan inbound pristup s interneta. Outbound ide kroz NAT Gateway. Workload je dostupan kroz Load Balancer koji je u public subnetu.

- **Configure remote access to nodes**: ostavi isključeno (koristiti `kubectl exec` ili SSM umjesto SSH-a)
- Next → Create

Node Group kreiranje traje ~5 minuta. EC2 instance se boot-uju, instalira se kubelet, registruju se u cluster.

---

## Spajanje kubectl na Cluster

Cluster je aktivan — sada treba lokalni kubeconfig.

```bash
# Generiraj/ažuriraj kubeconfig
docker run --rm \
  -v ~/.aws:/root/.aws \
  -v ~/.kube:/root/.kube \
  amazon/aws-cli:latest \
  eks update-kubeconfig \
  --region eu-west-1 \
  --name project-a-dev
```

Ovo kreira/ažurira `~/.kube/config` s cluster endpoint-om, CA certifikatom i auth token generatorom.

### Provjera spajanja

```bash
docker run --rm \
  -v ~/.aws:/root/.aws \
  -v ~/.kube:/root/.kube \
  bitnami/kubectl:1.29 get nodes
```

Očekivani output:
```
NAME                                       STATUS   ROLES    AGE   VERSION
ip-10-0-3-47.eu-west-1.compute.internal   Ready    <none>   3m    v1.29.x
```

Ako node nije **Ready** nakon 5 minuta:
```bash
# Provjeri node events
docker run --rm -v ~/.aws:/root/.aws -v ~/.kube:/root/.kube \
  bitnami/kubectl:1.29 describe node <node-name>
```

Česte greške:
- Node role nema tražene policy-je → node se ne može registrovati
- Subneti nemaju izlaz na internet (NAT nije aktivan) → node ne može povući system images
- Security group blokira port 10250 → kubelet nije dostupan API serveru

---

## EKS Add-ons Verifikacija

```bash
# System podovi moraju svi biti Running
docker run --rm -v ~/.aws:/root/.aws -v ~/.kube:/root/.kube \
  bitnami/kubectl:1.29 get pods -n kube-system
```

Mora vidjeti:
- `aws-node-*` (VPC CNI) — Running
- `coredns-*` (2 replika) — Running
- `kube-proxy-*` — Running
- `ebs-csi-*` — Running

Ako neki pod je u `CrashLoopBackOff` ili `Pending`:
```bash
docker run --rm -v ~/.aws:/root/.aws -v ~/.kube:/root/.kube \
  bitnami/kubectl:1.29 describe pod <pod-name> -n kube-system
```

Events na kraju output-a govore šta je pošlo po krivu.

---

## AWS Konzola za EKS Monitoring

**EKS → Clusters → project-a-dev**:

- **Overview tab**: cluster info, K8s verzija, status
- **Compute tab**: Node Groups i Fargate profiles
- **Networking tab**: VPC, subnete, SG
- **Add-ons tab**: instalirani addoni i jejich verzije
- **Resources tab**: K8s objekti direktno u konzoli (Pods, Deployments, Services)
  - Ovo je korisno za brzu provjeru bez kubectl

---

## ALB Controller — Napomena

Za inbound HTTP/HTTPS saobraćaj treba AWS Load Balancer Controller (ALB Ingress Controller). Instalira se kroz Helm:

```bash
# Detaljan setup je u modulu 08-gitlab-pipelines
# Ali logika je:
helm repo add eks https://aws.github.io/eks-charts
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=project-a-dev \
  --set serviceAccount.create=true \
  --set serviceAccount.annotations."eks\.amazonaws\.com/role-arn"=<IRSA_ROLE_ARN>
```

ALB Controller kreira AWS Application Load Balancer za svaki Kubernetes `Ingress` objekt. Bez njega, Ingress objekti nemaju efekta.

---

## CloudWatch Container Insights

Za log agregaciju i metriku s nodova i podova:

**EKS → Clusters → project-a-dev → Observability tab → Enable Container Insights**

Ili kroz CLI:
```bash
docker run --rm -v ~/.aws:/root/.aws amazon/aws-cli:latest \
  eks update-cluster-config \
  --name project-a-dev \
  --region eu-west-1 \
  --logging '{"clusterLogging":[{"types":["api","audit","authenticator"],"enabled":true}]}'
```

Napomena: CloudWatch Logs se naplaćuju. Za dev environment drži enabled samo ako aktivno debuguješ.
