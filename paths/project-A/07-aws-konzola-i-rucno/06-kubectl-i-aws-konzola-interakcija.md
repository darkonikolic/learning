# 06 — kubectl i AWS Konzola Interakcija

## Cilj

Naučiti raditi s EKS clusterom kroz kubectl i pratiti stanje kroz AWS konzolu. Deployati hello-world aplikaciju ručno (bez Helm-a) da razumiješ svaki K8s objekt koji Helm kasnije generiše.

---

## kubectl kroz Docker s EKS Kubeconfig

Kubeconfig (~/.kube/config) sadrži cluster endpoint, CA certifikat i instrukciju za generisanje auth tokena. Auth token se generiše kroz `aws eks get-token` — zato `~/.aws` mora biti mount-ovan.

```bash
# Provjera koja kontekst je aktivan
docker run --rm \
  -v ~/.aws:/root/.aws \
  -v ~/.kube:/root/.kube \
  bitnami/kubectl:1.29 config current-context
```

Output mora biti: `arn:aws:eks:eu-west-1:123456789012:cluster/project-a-dev`

### Alias za kraće kucanje

Dodaj u `~/.zshrc` ili `~/.bashrc`:

```bash
alias k='docker run --rm -v ~/.aws:/root/.aws -v ~/.kube:/root/.kube bitnami/kubectl:1.29'
```

Sada možeš koristiti: `k get nodes`, `k get pods -A`, itd.

---

## AWS Konzola — EKS Resources Tab

**EKS → Clusters → project-a-dev → Resources tab**

Ovdje možeš pregledati K8s objekte direktno u konzoli bez kubectl-a:

- **Workloads**: Deployments, StatefulSets, DaemonSets, Jobs
- **Pods**: lista svih podova, status, node na kom teku
- **Networking**: Services, Ingress, NetworkPolicies
- **Config and Storage**: ConfigMaps, Secrets (vrijednosti su maskirane), PVCs
- **Authorization**: ServiceAccounts, Roles, ClusterRoles

Ovo je korisno za brzu provjeru statusa — ne treba kubectl za prost pregled. Edit nije moguć iz konzole (use kubectl apply).

---

## Deploy Hello-World na EKS — Ručno, Bez Helma

Cilj: razumjeti svaki K8s objekt u izolaciji. Helm u pozadini generiše ove iste objekte.

### Korak 1 — Kreiranje Namespace-a

```bash
docker run --rm -v ~/.aws:/root/.aws -v ~/.kube:/root/.kube \
  bitnami/kubectl:1.29 create namespace project-a-dev
```

Namespace je logička izolacija unutar clustera. Resursi u jednom namespace-u su odvojeni od drugog (RBAC, NetworkPolicy, Resource Quotas).

### Korak 2 — Deployment Manifest

Kreiraj lokalno `deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hello-world
  namespace: project-a-dev
  labels:
    app: hello-world
    version: "1.0"
spec:
  replicas: 2
  selector:
    matchLabels:
      app: hello-world
  template:
    metadata:
      labels:
        app: hello-world
        version: "1.0"
    spec:
      containers:
        - name: hello-world
          image: nginx:1.25-alpine
          ports:
            - containerPort: 80
          resources:
            requests:
              cpu: "100m"
              memory: "64Mi"
            limits:
              cpu: "200m"
              memory: "128Mi"
          readinessProbe:
            httpGet:
              path: /
              port: 80
            initialDelaySeconds: 5
            periodSeconds: 10
          livenessProbe:
            httpGet:
              path: /
              port: 80
            initialDelaySeconds: 15
            periodSeconds: 20
```

Ključni dijelovi:
- `resources.requests`: garantovani resursi po podu — scheduler koristi ovo za placement
- `resources.limits`: maksimum — pod koji pređe limit CPU se throttla, limit RAM-a se killa
- `readinessProbe`: pod prima saobraćaj tek kad ova proba prođe
- `livenessProbe`: K8s restartuje pod ako ova proba ne prolazi

### Korak 3 — Service Manifest

Kreiraj `service.yaml`:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: hello-world
  namespace: project-a-dev
spec:
  selector:
    app: hello-world
  ports:
    - protocol: TCP
      port: 80
      targetPort: 80
  type: ClusterIP
```

`ClusterIP` = interna IP, dostupna samo unutar clustera. Za eksterni pristup treba `LoadBalancer` ili `Ingress`.

### Korak 4 — Apply

```bash
# Mount lokalnog direktorija gdje su yamli
docker run --rm \
  -v ~/.aws:/root/.aws \
  -v ~/.kube:/root/.kube \
  -v $(pwd):/manifests \
  bitnami/kubectl:1.29 apply -f /manifests/deployment.yaml -n project-a-dev

docker run --rm \
  -v ~/.aws:/root/.aws \
  -v ~/.kube:/root/.kube \
  -v $(pwd):/manifests \
  bitnami/kubectl:1.29 apply -f /manifests/service.yaml -n project-a-dev
```

---

## Provjera Deploymenta

### Stanje Podova

```bash
docker run --rm -v ~/.aws:/root/.aws -v ~/.kube:/root/.kube \
  bitnami/kubectl:1.29 get pods -n project-a-dev -w
```

`-w` = watch mode, ažurira se u realnom vremenu. Prati tok:
```
NAME                           READY   STATUS              RESTARTS   AGE
hello-world-6d8f9b7c4-xk2p9   0/1     ContainerCreating   0          5s
hello-world-6d8f9b7c4-xk2p9   1/1     Running             0          12s
```

`0/1 ContainerCreating` → `1/1 Running` je normalan tok. Ako ostaje na `Pending` dulje od minute:

```bash
docker run --rm -v ~/.aws:/root/.aws -v ~/.kube:/root/.kube \
  bitnami/kubectl:1.29 describe pod <pod-name> -n project-a-dev
```

Gledaj **Events** sekciju na kraju. Česte poruke:
- `0/1 nodes are available: insufficient cpu` — node nema dovoljno CPU (requests pre-empt)
- `ImagePullBackOff` — ne može pullati image (network, credentials, pogrešan image tag)
- `OOMKilled` — pod je prekoračio memory limit

### Deployment Rollout Status

```bash
docker run --rm -v ~/.aws:/root/.aws -v ~/.kube:/root/.kube \
  bitnami/kubectl:1.29 rollout status deployment/hello-world -n project-a-dev
```

Output kad je sve OK: `deployment "hello-world" successfully rolled out`

### Provjera u AWS Konzoli

**EKS → Clusters → project-a-dev → Resources → Workloads → Deployments**

Vidiš `hello-world` deployment, 2/2 replika ready, namespace `project-a-dev`.

**Resources → Pods** — oba poda u stanju Running.

---

## CloudWatch Container Insights

Ako je Container Insights aktiviran (modul 03):

**CloudWatch → Container Insights → Resources → project-a-dev (EKS Cluster)**

Prikazuje:
- CPU/RAM utilization po clusteru, namespaceu, deployment-u, podu
- Network throughput
- Disk I/O za podove s PVC-ima

Za detaljne logove:

**CloudWatch → Log groups → `/aws/containerinsights/project-a-dev/application`**

Svaki pod šalje stdout i stderr u ovaj log group. Filtriranje:

```
{ $.kubernetes.namespace_name = "project-a-dev" && $.kubernetes.container_name = "hello-world" }
```

---

## Skaliranje

### Manuelno Skaliranje

```bash
docker run --rm -v ~/.aws:/root/.aws -v ~/.kube:/root/.kube \
  bitnami/kubectl:1.29 scale deployment hello-world \
  --replicas=4 \
  -n project-a-dev
```

Kubernetes scheduler raspoređuje nove podove na dostupne nodove. Ako nema dovoljno resursa na jednom nodu, novi pod ide na drugi node (ili ostaje Pending ako nema slobodnog kapaciteta).

Provjeri distribution po nodovima:

```bash
docker run --rm -v ~/.aws:/root/.aws -v ~/.kube:/root/.kube \
  bitnami/kubectl:1.29 get pods -n project-a-dev -o wide
```

`-o wide` prikazuje NODE kolonu — vidiš na kom nodu teče svaki pod.

### Vraćanje na 2 replike

```bash
docker run --rm -v ~/.aws:/root/.aws -v ~/.kube:/root/.kube \
  bitnami/kubectl:1.29 scale deployment hello-world \
  --replicas=2 \
  -n project-a-dev
```

Kubernetes gracefully terminira "višak" podova (SIGTERM → čeka `terminationGracePeriodSeconds` → SIGKILL).

---

## Rolling Update

Promijeni image tag u deployment.yaml: `nginx:1.25-alpine` → `nginx:1.26-alpine`, pa:

```bash
docker run --rm -v ~/.aws:/root/.aws -v ~/.kube:/root/.kube \
  -v $(pwd):/manifests \
  bitnami/kubectl:1.29 apply -f /manifests/deployment.yaml
```

Prati rolling update:
```bash
docker run --rm -v ~/.aws:/root/.aws -v ~/.kube:/root/.kube \
  bitnami/kubectl:1.29 rollout status deployment/hello-world -n project-a-dev -w
```

Kubernetes kreira novi pod s novim image-om, čeka da postane Ready, pa tek onda ubija stari. `maxSurge: 1` i `maxUnavailable: 0` su defaulti koji osiguravaju zero-downtime deploy.

Rollback ako novi image puca:
```bash
docker run --rm -v ~/.aws:/root/.aws -v ~/.kube:/root/.kube \
  bitnami/kubectl:1.29 rollout undo deployment/hello-world -n project-a-dev
```

---

## Logovi

```bash
# Logovi jednog poda
docker run --rm -v ~/.aws:/root/.aws -v ~/.kube:/root/.kube \
  bitnami/kubectl:1.29 logs <pod-name> -n project-a-dev

# Follow (live stream)
docker run --rm -v ~/.aws:/root/.aws -v ~/.kube:/root/.kube \
  bitnami/kubectl:1.29 logs -f <pod-name> -n project-a-dev

# Logovi svih podova s labelom app=hello-world
docker run --rm -v ~/.aws:/root/.aws -v ~/.kube:/root/.kube \
  bitnami/kubectl:1.29 logs -l app=hello-world -n project-a-dev --prefix
```

`--prefix` dodaje ime poda ispred svakog loga — korisno kad patiš više podova.

---

## Destroy Deploymenta

```bash
# Briše sve resurse u namespace-u
docker run --rm -v ~/.aws:/root/.aws -v ~/.kube:/root/.kube \
  bitnami/kubectl:1.29 delete namespace project-a-dev
```

`delete namespace` briše namespace i SVE što je u njemu: Deployments, Services, ConfigMaps, Secrets, PVCs. Ako je ALB Ingress bio u ovom namespace-u i bio properly annotiran, AWS Load Balancer se automatski briše.

**Provjera** da je namespace uklonjen:
```bash
docker run --rm -v ~/.aws:/root/.aws -v ~/.kube:/root/.kube \
  bitnami/kubectl:1.29 get namespace project-a-dev
```

Output: `Error from server (NotFound): namespaces "project-a-dev" not found` — OK.

---

## Šta Helm Radi Drugačije

Helm generiše ove iste YAML manifeste iz templateova, ali dodaje:
- **Release tracking**: pamti koja verzija je deployovana
- **Rollback**: `helm rollback` vraća na prethodnu Helm release verziju
- **Dependency management**: instalira zavisne chartove
- **Values override**: jedan `values.yaml` za sve environment-specifične vrijednosti

Manuelni `kubectl apply` koji si upravo radio ekvivalent je `helm install` bez release trackinga. U produkciji uvijek Helm.

---

## Makefile — dodaj u ovom poglavlju

Ovo poglavlje uvodi AWS CLI i EKS. Dodaj u `Makefile` u korenu projekta:

```makefile
# === OBLAST 06-07: AWS ===

aws-whoami: ## Provjeri AWS identitet (koji nalog/rola je aktivan)
	docker run --rm \
	  -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -e AWS_SESSION_TOKEN \
	  amazon/aws-cli:latest sts get-caller-identity

aws-kubeconfig: ## Preuzmi kubeconfig za EKS cluster (CLUSTER=project-a-dev make aws-kubeconfig)
	docker run --rm \
	  -v ~/.kube:/root/.kube \
	  -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -e AWS_SESSION_TOKEN \
	  amazon/aws-cli:latest eks update-kubeconfig \
	  --region $(AWS_REGION) --name $(CLUSTER)
```

Centralni Makefile već sadrži ove targete — ovo je referenca šta si dodao u ovoj oblasti.

Provjeri da targeti rade:
```bash
make aws-whoami
CLUSTER=project-a-dev make aws-kubeconfig
make help | grep aws
```
