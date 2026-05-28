# 07 — Lokalni Kubernetes: kind multi-service

## kind vs minikube vs Docker Desktop K8s

kind (Kubernetes in Docker) je izbor za multi-service lokalni razvoj jer:
- Podrška za multi-node klaster (1 control plane + N worker node-ova u Docker kontejnerima)
- `extraPortMappings` za nginx Ingress bez složene konfiguracije
- Identičan K8s API kao produkcija (EKS, GKE) — nema "kind-specific" quirk-ova
- Lakši reset: `kind delete cluster && kind create cluster` = čist početak za 30s

---

## kind klaster konfiguracija sa Ingress podrškom

```yaml
# kind-config.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
name: project-a

nodes:
  - role: control-plane
    # extraPortMappings: mapira port na host mašinu
    # nginx Ingress Controller sluša na nodePort 80/443
    # hostPort mapira na localhost:80 i localhost:443
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

  # Opcionalno: worker node-ovi za realističniji test
  - role: worker
  - role: worker
```

```bash
# Kreiraj klaster
kind create cluster --config kind-config.yaml

# Provjeri da je spreman
kubectl cluster-info --context kind-project-a
kubectl get nodes
```

---

## nginx Ingress Controller za kind

```bash
# Instaliraj nginx Ingress Controller sa kind-specific konfiguracijama
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

# Čekaj da controller bude spreman
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=90s
```

---

## Build Docker image-a lokalno

```bash
# Build svih image-a lokalno
# --no-cache za clean build pri problemu sa zavisnostima
docker build -t project-a/nginx-frontend:local ./frontend
docker build -t project-a/php-service:local ./php-service
docker build -t project-a/go-service:local ./go-service

# Provjeri veličine image-a
docker images | grep project-a
# REPOSITORY                     TAG    IMAGE ID    SIZE
# project-a/go-service           local  abc123...   18MB   ← scratch image
# project-a/php-service          local  def456...   115MB  ← php:8.3-fpm-alpine
# project-a/nginx-frontend       local  ghi789...   45MB   ← nginx:1.25-alpine + vue build
```

---

## kind load docker-image — zašto je ovo neophodno

kind pokreće K8s unutar Docker kontejnera. Ti kontejneri imaju svoj Docker daemon, odvojen od host Docker daemon-a. Image koji je lokalno buildan nije automatski dostupan unutar kind klastera.

```bash
# Učitaj lokalne image-ove u kind klaster
# Ovo kopira image iz host Docker-a u kind node containerd
kind load docker-image project-a/nginx-frontend:local --name project-a
kind load docker-image project-a/php-service:local --name project-a
kind load docker-image project-a/go-service:local --name project-a

# Provjeri da su image-ovi dostupni na kind node-u
docker exec -it project-a-control-plane crictl images | grep project-a
```

Alternativa: lokalni image registry unutar kind-a. Korisno za CI pipeline simulaciju:

```bash
# Lokalni registry na localhost:5001
docker run -d --restart=always -p 5001:5000 --name kind-registry registry:2

# Povezi registry sa kind klasterom
docker network connect kind kind-registry

# Tag i push na lokalni registry
docker tag project-a/go-service:local localhost:5001/go-service:local
docker push localhost:5001/go-service:local
```

---

## MySQL i Redis lokalno: zašto docker-compose za data layer

Pokretanje MySQL i Redis kao K8s StatefulSet lokalno je tehnički moguće, ali nepreporučivo:

**StatefulSet problemi lokalno**:
- MySQL StatefulSet zahtijeva PersistentVolume konfiguraciju
- kind nema built-in storage provisioner za perzistentne volume-e (zahtijeva `local-path-provisioner`)
- MySQL replikacija u K8s zahtijeva custom Operator (Percona, MySQL Operator) ili ručnu konfiguraciju
- Svaki restart klastera = potencijalni gubitak podataka bez pravilne PV konfiguracije

**docker-compose za data layer** je pragmatično rješenje lokalno:
- MySQL i Redis rade izvan K8s, na Docker mreži
- K8s servisi ih dosežu putem `host.docker.internal` (Docker Desktop) ili hostovog IP-a
- Pod restarts ne utiče na podatke
- Brže iteracije: `docker compose restart mysql-master` vs `kubectl rollout restart`

```yaml
# values/local.yaml — override za lokalni razvoj
goService:
  image:
    tag: "local"
  replicaCount: 1  # Manje replika lokalno
  hpa:
    enabled: false  # HPA nije potreban lokalno

phpService:
  image:
    tag: "local"
  replicaCount: 1

nginx:
  image:
    tag: "local"

# MySQL i Redis su na host mašini (docker-compose)
# host.docker.internal je DNS koji K8s pod-ovi mogu koristiti za host mašinu
# Na Linux-u koristiti `172.17.0.1` ili `-add-host` u kind config-u
```

---

## Deploy Helm chart na kind

```bash
# Namespace kreacija
kubectl create namespace project-a

# Kreiraj Secret za lokalni razvoj (u produkciji: External Secrets Operator)
kubectl create secret generic project-a-secrets \
  --namespace project-a \
  --from-literal=mysql-master-dsn="app_user:local_app_secret@tcp(host.docker.internal:3306)/project_a?parseTime=true" \
  --from-literal=mysql-replica-dsn="app_user:local_app_secret@tcp(host.docker.internal:3307)/project_a?parseTime=true" \
  --from-literal=redis-password="local_redis_secret" \
  --from-literal=php-session-secret="local_session_secret_32chars_min"

# Deploy chart
helm upgrade --install project-a ./helm/project-a \
  -f helm/project-a/values/local.yaml \
  --namespace project-a \
  --wait \
  --timeout 5m

# Provjeri status svih resursa
kubectl get all -n project-a
```

---

## /etc/hosts za lokalni domen

```bash
# Dodaj u /etc/hosts
sudo sh -c 'echo "127.0.0.1 project-a.local" >> /etc/hosts'
```

`project-a.local` sada otvara nginx Ingress na localhost:80.

---

## Debugging multi-service u K8s

```bash
# Provjeri logove svakog servisa
kubectl logs -n project-a -l app.kubernetes.io/component=go-service --tail=50 -f
kubectl logs -n project-a -l app.kubernetes.io/component=php-service --tail=50

# Exec u kontejner (php ima shell, go/scratch nema)
kubectl exec -n project-a -it deploy/project-a-php -- sh

# Port-forward za direktan pristup servisu (bypass ingress)
kubectl port-forward -n project-a svc/project-a-go 8080:8080

# Provjeri connectivity između pod-ova
# Koristiti ephemeral debug container jer Go scratch nema curl/ping
kubectl debug -n project-a \
  deploy/project-a-go \
  -it --image=curlimages/curl:8.5.0 \
  -- curl http://project-a-php.project-a.svc.cluster.local:9000/

# Provjeri Ingress routing
kubectl describe ingress -n project-a
kubectl get events -n project-a --sort-by='.lastTimestamp'

# Provjeri resource usage
kubectl top pods -n project-a
kubectl top nodes

# Opis poda koji ne starta (CrashLoopBackOff debug)
kubectl describe pod -n project-a <pod-name>
```

---

## Tipični problemi i rješenja

**ImagePullBackOff za lokalne image-ove**:
```bash
# Provjeriti da je image učitan u kind
docker exec -it project-a-control-plane crictl images
# Rješenje: kind load docker-image ponovo
```

**Go servis crashuje: "x509: certificate signed by unknown authority"**:
```
# CA certifikati nisu uključeni u scratch image
# Rješenje: COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/ u Dockerfile
```

**PHP-FPM: "connect() failed to 172.x.x.x:9000"**:
```
# nginx ne može dosegnuti PHP-FPM
# Provjeriti da nginx.conf koristi K8s DNS ime, ne IP
# upstream php_fpm { server php-service.project-a.svc.cluster.local:9000; }
```

**MySQL konekcija iz K8s poda na host machine**:
```bash
# host.docker.internal ne radi na Linux kind
# Dobavi host IP:
ip route show default | awk '{print $3}'
# Koristiti taj IP u connection string-u
```
