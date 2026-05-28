# 01 - Kubernetes: Zašto i Arhitektura

## Problem: Docker Compose nije dovoljan

Docker Compose je odličan alat za lokalni razvoj. Definirate servise, mreže, volumene u jednom YAML fajlu i pokrenete sve s jednom komandom. Ali u produkciji naletite na zidove:

**Nema self-healing.** Ako kontejner crasha, ostaje down dok ga ručno ne restartujete (ili dok `restart: always` ne pokuša — ali bez limita pokušaja i bez notifikacije).

**Nema rolling deploy.** Ažuriranje slike znači downtime: `docker compose down && docker compose up`. Ili složeni ručni proces s dva servisa i load balancerom.

**Jedan server.** Compose ne zna za više mašina. Ako server padne — sve pada.

**Nema automatskog skaliranja.** Više saobraćaja = ručno dizanje novih kontejnera.

**Kubernetes** rješava sve ove probleme. To je orkestrator kontejnera: sistem koji upravlja kontejnerima na više mašina, automatski ih pokreće, restartuje, skalira i deplouja bez downtime-a.

## Kubernetes = desired state machine

Ključni koncept: Kubernetes je sistem koji neprekidno uspoređuje **željeno stanje** (što ste definisali) s **stvarnim stanjem** (što zapravo radi) i radi sve potrebno da ih uskladi.

Kažete: "Želim 3 kopije nginx kontejnera." Kubernetes ih pokreće. Jedan padne? Kubernetes pokreće novi. Server s dva kontejnera nestane? Kubernetes pokreće zamjene na preostalim serverima. Vi ne upravljate procesima — upravljate **namjerama**.

## Arhitektura: control plane i worker nodes

Kubernetes cluster se sastoji od dvije vrste mašina:

**Control Plane** — "mozak" clustera, donosi sve odluke:

- **API Server** — ulazna tačka za sve operacije. `kubectl` komande idu ovde. REST API.
- **etcd** — distribuovana key-value baza podataka koja čuva cijelo stanje clustera. Ako etcd nestane, cluster "zaboravi" sve.
- **Scheduler** — odlučuje na koji worker node ići s novim Podem. Uzima u obzir dostupne resurse, afinitete, ograničenja.
- **Controller Manager** — skup kontrolera koji prate stanje i reaguju. ReplicaSet controller osigurava tačan broj Podova. Node controller detektuje nedostupne nodove.

**Worker Nodes** — mašine koje zapravo pokreću kontejnere:

- **kubelet** — agent koji prima instrukcije od control plane-a i pokreće/zaustavlja kontejnere
- **kube-proxy** — mrežni proxy, implementira Kubernetes Service apstrakciju
- **Container Runtime** — Docker, containerd ili CRI-O — stvarno pokretanje kontejnera

```
┌─────────────────────────────────┐
│         CONTROL PLANE           │
│  API Server ← etcd              │
│  Scheduler                      │
│  Controller Manager             │
└─────────────┬───────────────────┘
              │
     ┌────────┴────────┐
     ▼                 ▼
┌─────────┐       ┌─────────┐
│ Worker  │       │ Worker  │
│  Node   │       │  Node   │
│ kubelet │       │ kubelet │
│  pods   │       │  pods   │
└─────────┘       └─────────┘
```

## kind: Kubernetes u Docker kontejnerima

Za lokalni razvoj, pokretanje pravog Kubernetes clustera (čak i minikube-a) znači VM, Hypervisor, gigabajte RAM-a.

**kind** (Kubernetes IN Docker) rješava to elegantno: svaki Kubernetes node je Docker kontejner. Cijeli cluster živi unutar Docker-a na vašem laptopu.

Zašto kind za project-A umjesto alternaiva:

- **vs minikube**: kind je lakši, ne treba VM, bolje za CI
- **vs Docker Desktop K8s**: kind je eksplicitan i prenosiv — isti setup radi svugdje gdje je Docker
- **vs k3s/k3d**: kind je "vanilla" Kubernetes — ono što naučite direktno se prenosi na EKS

**Instalacija kubectl kroz Docker** (bez bare metal instalacije):

```bash
# Alias koji pokrecete kao docker kontejner
alias kubectl='docker run --rm -it \
  -v ~/.kube:/root/.kube \
  -v $(pwd):/workspace \
  -w /workspace \
  bitnami/kubectl:latest'
```

Ili instalirajte kubectl direktno (preporučeno za lokalni rad jer je brže):

```bash
# macOS
brew install kubectl

# Linux
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl && sudo mv kubectl /usr/local/bin/

# Provjera
kubectl version --client
```

kind instalacija:

```bash
# macOS
brew install kind

# Linux (direktno)
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
chmod +x ./kind && sudo mv ./kind /usr/local/bin/kind

# ili kroz Docker (ne preporučuje se za regularnu upotrebu)
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock kindest/node:v1.29.0
```

## Kreiranje kind clustera za project-A

```bash
# Minimalni cluster (jedan node)
kind create cluster --name project-a

# Provjera
kubectl cluster-info --context kind-project-a
kubectl get nodes
```

Za project-A koristit ćemo konfiguraciju s jednim control plane i dva worker node-a (da simuliramo višenode produkcijski setup):

```yaml
# kind-config.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
    kubeadmConfigPatches:
      - |
        kind: InitConfiguration
        nodeRegistration:
          kubeletExtraArgs:
            node-labels: "ingress-ready=true"
    extraPortMappings:
      - containerPort: 80
        hostPort: 80
        protocol: TCP
      - containerPort: 443
        hostPort: 443
        protocol: TCP
  - role: worker
  - role: worker
```

```bash
kind create cluster --name project-a --config kind-config.yaml
```

`extraPortMappings` prosleđuje portove s host mašine u kind control plane node — potrebno za pristup Ingress kontroleru.

## Veza sa project-A

Isti Kubernetes manifesti koje koristite lokalno na kind-u rade na AWS EKS-u. Razlike su minimalne:

| Lokalno (kind) | AWS EKS |
|----------------|---------|
| NodePort / kubectl port-forward | LoadBalancer / ALB |
| Self-signed TLS cert | ACM cert |
| emptyDir storage | EBS/EFS |
| /etc/hosts za DNS | Route 53 |

Kada savladate lokalni flow (deploy, skaliranje, debugging), prelaz na EKS je promjena konfiguracije, ne promjena konceptova.
