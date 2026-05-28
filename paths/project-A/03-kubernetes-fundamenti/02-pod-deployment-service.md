# 02 - Pod, Deployment i Service

## Pod: najmanja jedinica

Pod je osnovna jedinica u Kubernetes-u. Pod može sadržavati jedan ili više kontejnera koji **dijele mrežu i storage**: svaki kontejner unutar Pod-a komunicira na `localhost`, i svi vide iste volume mountove.

Zašto više kontejnera u Podu? Sidecar pattern: glavni kontejner (nginx) + log shipper (Fluent Bit) koji čita iste log fajlove. Ili init kontejner koji preuzme config fajlove prije nego što glavni počne.

Za project-A: jedan Pod = jedan nginx kontejner.

```yaml
# Direktno kreiranje Poda — NE radite ovo u produkciji
apiVersion: v1
kind: Pod
metadata:
  name: hello-world
  namespace: helloworld-dev
spec:
  containers:
    - name: nginx
      image: registry.gitlab.com/firma/project-a:a3f9c21
      ports:
        - containerPort: 80
```

## Zašto ne deploovati direktno Podove

Pod koji kreirate direktno nema nikoga ko ga čuva. Ako node na kome živi padne, Pod nestaje i ne vraća se. Nema self-healing, nema skaliranja.

Kubernetes ima hijerarhiju:
```
Deployment → ReplicaSet → Pod
```

**ReplicaSet** osigurava da uvijek postoji tačan broj kopija Pod-a. Ako Pod padne, ReplicaSet kreira novi. Ali ReplicaSet ne zna ništa o rolling update-ovima.

**Deployment** upravlja ReplicaSet-ima. Kada ažurirate image tag, Deployment kreira novi ReplicaSet s novim image-om i postepeno mijenja stari s novim (rolling update).

## Deployment: desired state

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hello-world
  namespace: helloworld-dev
  labels:
    app: hello-world
    version: "1.0"
spec:
  replicas: 2              # željeni broj Pod-ova
  selector:
    matchLabels:
      app: hello-world     # koji Podovi su "moji"
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1          # maksimalno 1 Pod više od replicas tokom update-a
      maxUnavailable: 0    # nula Pod-ova može biti down tokom update-a
  template:                # ovako izgleda svaki Pod
    metadata:
      labels:
        app: hello-world
    spec:
      containers:
        - name: nginx
          image: registry.gitlab.com/firma/project-a:a3f9c21
          ports:
            - containerPort: 80
          resources:
            requests:
              cpu: "50m"
              memory: "64Mi"
            limits:
              cpu: "200m"
              memory: "128Mi"
          readinessProbe:
            httpGet:
              path: /health
              port: 80
            initialDelaySeconds: 5
            periodSeconds: 10
          livenessProbe:
            httpGet:
              path: /health
              port: 80
            initialDelaySeconds: 15
            periodSeconds: 20
```

**Rolling update strategija** s `maxUnavailable: 0` znači zero-downtime deploy: Kubernetes pokrene novi Pod, čeka da postane ready, tek onda ubija stari.

**selector** i **template labels** moraju se podudarati — to je kako Deployment "prepoznaje" svoje Podove.

## Service: stabilan endpoint

Pod-ovi dolaze i odlaze. Svaki dobija svoju IP adresu koja se mijenja kada Pod restartuje. Kako da drugi servisi komuniciraju s Podovima ako se IP stalno mijenja?

Service je apstrakcija koja daje stabilan endpoint (IP + DNS ime) koji uvijek usmjerava na zdrave Podove koji matchaju `selector`.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: hello-world
  namespace: helloworld-dev
spec:
  selector:
    app: hello-world       # šalje saobraćaj na Podove s ovim labelom
  ports:
    - protocol: TCP
      port: 80             # port Servicea
      targetPort: 80       # port na Pod-u
  type: ClusterIP          # dostupan samo unutar clustera
```

Tri tipa Service-a:

**ClusterIP** (default) — interni IP unutar clustera. Drugi Podovi mogu mu pristupiti po DNS imenu: `hello-world.helloworld-dev.svc.cluster.local`. Nije dostupan izvana.

**NodePort** — otvara isti port na svakom worker node-u (30000-32767 opseg). Dostupan izvana na `<node-ip>:<nodeport>`. Korisno za lokalni razvoj.

**LoadBalancer** — kreira cloud load balancer (AWS ELB, GCP LB...). Produkcija na cloud-u.

Za kind lokalno koristimo ClusterIP + Ingress (objašnjeno u sljedećem fajlu). Na EKS-u Ingress kreira ALB.

## Kubectl komande za svakodnevni rad

```bash
# Listanje resursa
kubectl get pods -n helloworld-dev
kubectl get deployments -n helloworld-dev
kubectl get services -n helloworld-dev
kubectl get all -n helloworld-dev          # sve odjednom

# Detalji o resursu
kubectl describe pod hello-world-abc123 -n helloworld-dev
kubectl describe deployment hello-world -n helloworld-dev

# Logovi
kubectl logs hello-world-abc123 -n helloworld-dev
kubectl logs -l app=hello-world -n helloworld-dev   # svi Podovi s labelom
kubectl logs -f hello-world-abc123 -n helloworld-dev  # stream (tail -f)
kubectl logs --previous hello-world-abc123 -n helloworld-dev  # prethodni kontejner

# Ulaz u kontejner
kubectl exec -it hello-world-abc123 -n helloworld-dev -- sh

# Port forward (za lokalni pristup ClusterIP servisu)
kubectl port-forward svc/hello-world 8080:80 -n helloworld-dev
# Sada: curl http://localhost:8080

# Primjena manifesta
kubectl apply -f deployment.yaml
kubectl apply -f k8s/                      # svi fajlovi u direktoriju

# Ažuriranje image taga (direktna komanda)
kubectl set image deployment/hello-world nginx=registry.gitlab.com/firma/project-a:b4e8d12 -n helloworld-dev

# Praćenje rolling update-a
kubectl rollout status deployment/hello-world -n helloworld-dev

# Rollback na prethodnu verziju
kubectl rollout undo deployment/hello-world -n helloworld-dev

# Brisanje
kubectl delete pod hello-world-abc123 -n helloworld-dev
kubectl delete -f deployment.yaml
```

## Veza sa project-A

Struktura K8s manifesta za hello-world:

```
k8s/
├── base/
│   ├── namespace.yaml
│   ├── deployment.yaml
│   └── service.yaml
└── overlays/
    ├── dev/
    │   └── kustomization.yaml   # 1 replika, manje resurse
    ├── staging/
    │   └── kustomization.yaml   # 2 replike
    └── prod/
        └── kustomization.yaml   # 3 replike, HPA
```

Kustomize (objasniće se u kasnijim modulima) omogućava iste bazne manifeste s razlikama po okruženju. Nema copy-paste YAML-a.
