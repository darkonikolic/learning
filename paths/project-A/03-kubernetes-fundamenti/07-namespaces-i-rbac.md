# 07 - Namespaces i RBAC

## Namespace: logična izolacija

Kubernetes cluster može hostovati stotine aplikacija i okruženja. Bez organizacije, sve bi bila kaotična gomila Podova i Servisa.

**Namespace** je logična particija unutar clustera. Resursi (Podovi, Deploymenti, Servicei) postoje unutar namespace-a. Isti naziv može postojati u različitim namespace-ima bez konflikta.

Važno razumjeti: namespace je **logična izolacija, ne sigurnosna**. Pod u jednom namespace-u može (bez RBAC) komunicirati s Pod-om u drugom namespace-u. Za stvarnu izolaciju trebate Network Policies (napredna tema).

## Struktura namespace-a za project-A

```
cluster/
├── helloworld-dev          # razvojno okruženje
├── helloworld-staging      # staging okruženje
├── helloworld-prod         # produkcija
├── helloworld-review-mr42  # dinamički MR review env (automatski se briše)
├── monitoring              # Prometheus, Grafana, Loki (dijele se)
└── ingress-nginx           # Ingress Controller
```

Kreiranje namespace-a:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: helloworld-dev
  labels:
    project: project-a
    environment: dev
    team: devops
```

```bash
kubectl apply -f namespace.yaml
# ili
kubectl create namespace helloworld-dev

# Rad unutar namespace-a
kubectl get pods -n helloworld-dev
kubectl get all -n helloworld-dev

# Podrazumijevani namespace (ne preporučuje se za projekate)
kubectl config set-context --current --namespace=helloworld-dev
```

## RBAC: kontrola pristupa

**RBAC (Role-Based Access Control)** kontroliše ko može raditi šta unutar clustera. Princip minimalnih privilegija: svaki korisnik i proces dobija samo ona prava koja su mu potrebna.

Četiri osnovna objekta:

**Role** — skup dozvola unutar **jednog** namespace-a
**ClusterRole** — skup dozvola za **cijeli** cluster
**RoleBinding** — veže Role na korisnika/group/ServiceAccount
**ClusterRoleBinding** — veže ClusterRole na korisnika/group/ServiceAccount

```yaml
# Role: deploy korisnik može čitati i ažurirati Deploymente
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: deployer
  namespace: helloworld-dev
rules:
  - apiGroups: ["apps"]
    resources: ["deployments"]
    verbs: ["get", "list", "watch", "update", "patch"]
  - apiGroups: [""]
    resources: ["pods", "services", "configmaps"]
    verbs: ["get", "list", "watch"]
  - apiGroups: [""]
    resources: ["pods/log"]
    verbs: ["get"]
```

```yaml
# RoleBinding: CI/CD ServiceAccount dobija deployer rolu
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: deployer-binding
  namespace: helloworld-dev
subjects:
  - kind: ServiceAccount
    name: gitlab-runner
    namespace: helloworld-dev
roleRef:
  kind: Role
  name: deployer
  apiGroup: rbac.authorization.k8s.io
```

## ServiceAccount za GitLab Runner

Kada GitLab pipeline deploya na K8s, radi to kao ServiceAccount — ne kao čovjek. ServiceAccount je identitet za procese unutar clustera.

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: gitlab-runner
  namespace: helloworld-dev
  annotations:
    description: "GitLab CI pipeline ServiceAccount za deploy"
```

Na EKS-u, ServiceAccount se može vezati za IAM rolu (IRSA — IAM Roles for Service Accounts). To znači da pipeline može pristupiti AWS servisima (ECR, S3, Secrets Manager) bez hardcoded kredencijala.

```yaml
# EKS specifično: IRSA anotacija
apiVersion: v1
kind: ServiceAccount
metadata:
  name: gitlab-runner
  namespace: helloworld-dev
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::123456789:role/project-a-deployer
```

## Praktičan primer: namespace + role za deploy

```bash
# 1. Kreiraj namespace
kubectl apply -f k8s/namespaces/helloworld-dev.yaml

# 2. Kreiraj ServiceAccount
kubectl apply -f k8s/rbac/serviceaccount.yaml

# 3. Kreiraj Role
kubectl apply -f k8s/rbac/role.yaml

# 4. Kreiraj RoleBinding
kubectl apply -f k8s/rbac/rolebinding.yaml

# 5. Provjera — što ovaj ServiceAccount smije
kubectl auth can-i update deployments \
  --as=system:serviceaccount:helloworld-dev:gitlab-runner \
  -n helloworld-dev
# yes

kubectl auth can-i delete namespaces \
  --as=system:serviceaccount:helloworld-dev:gitlab-runner
# no
```

Za GitLab CI pipeline, trebate kubeconfig koji koristi ovaj ServiceAccount. Na EKS-u generišete ga kroz AWS CLI i dodajete u GitLab CI/CD Variables kao masked, protected varijablu `KUBECONFIG`.

## Princip minimalnih privilegija u praksi

Greška početnika: dati pipeline ServiceAccount-u `cluster-admin` ClusterRole jer "radi". To znači pipeline može brisati namespace-ove, čitati sve Secrets, modificirati RBAC. Kompromitovan pipeline = kompromitovan cijeli cluster.

Granularno:
- Dev pipeline: `update deployments`, `get pods/logs` u dev namespace-u
- Staging pipeline: isto, ali u staging namespace-u
- Prod pipeline: `update deployments` u prod, **ručni approval** za deploy
- Niko nema `cluster-admin` osim backup mehanizma

```yaml
# Što NE raditi
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: gitlab-cluster-admin  # LOŠE!
subjects:
  - kind: ServiceAccount
    name: gitlab-runner
roleRef:
  kind: ClusterRole
  name: cluster-admin          # LOŠE!
```

Za project-A: svaki okruženjski namespace ima vlastiti `gitlab-runner` ServiceAccount s minimalnim pravima. Prod namespace dodaje `manual` stage u pipeline koji zahtijeva klik inženjera.
